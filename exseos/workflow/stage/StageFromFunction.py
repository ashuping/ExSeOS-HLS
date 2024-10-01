"""
ExSeOS-H Hardware ML Workflow Manager
Copyright (C) 2024  Alexis Maya-Isabelle Shuping

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from exseos.data.Variable import Variable, UnboundVariable
from exseos.types.Option import Option, Some, Nothing
from exseos.workflow.stage.Stage import Stage, StageResult

from abc import abstractmethod
import inspect
from inspect import Parameter, Signature
from typing import Callable


def _input_list_to_kwargs(input_list: tuple[Variable]) -> dict[str, any]:
	kwargs = {}
	for v in input_list:
		kwargs[v.name] = v.val

	return kwargs


class StageFromFunction(Stage):
	"""
	A `Stage` constructed automatically from a function.

	To construct a `StageFromFunction`, use `make_StageFromFunction`.
	"""

	@abstractmethod
	def inner_function(self, *args, **kwargs):
		"""The actual function encapsulated in a StageFromFunction."""
		...  # pragma: no cover

	def run(self, inputs: tuple[Variable]) -> StageResult:
		rval = self.inner_function(**_input_list_to_kwargs(inputs))

		return StageResult(
			self, (self.output_vars[0].bind(rval),) if len(self.output_vars) > 0 else ()
		)


def _extract_func_args_and_ret(fn: Callable) -> tuple[list[Variable], Option[Variable]]:
	"""
	Extract the arguments and (if present) return-type annotation from a
	function.

	:param fn: The function to extract data from.
	:returns: A tuple whose first element is the list of input `Variable`s
	          and the second element is an `Option`al return-type `Variable`
	"""
	sig = inspect.signature(fn)

	args = [
		UnboundVariable(
			param.name,
			Some(param.annotation)
			if param.annotation != Parameter.empty
			else Nothing(),
			default=Some(param.default)
			if param.default != Parameter.empty
			else Nothing(),
		)
		for param in sig.parameters.values()
	]

	ret = (
		Some(UnboundVariable("return", Some(sig.return_annotation)))
		if sig.return_annotation != Signature.empty
		else Nothing()
	)

	return (args, ret)


def make_StageFromFunction(fn: Callable) -> type[StageFromFunction]:
	"""
	Return a concrete subclass of `StageFromFunction`, with its inner
	function set to the provided `fn`. Unlike `StageFromFunction` itself,
	these subclasses can be directly instantiated.

	:param fn: The function to convert.
	:returns: A concrete subclass of `StageFromFunction`
	"""
	args, ret = _extract_func_args_and_ret(fn)

	inputs = tuple(args)
	outputs = (ret.val,) if ret != Nothing() else ()

	print(f"inputs: {inputs}")
	print(f"outputs: {outputs}")

	return type(
		f"StageFromFunction_{fn.__name__}_{hash(fn)}",
		(StageFromFunction,),
		{
			"input_vars": inputs,
			"output_vars": outputs,
			"inner_function": lambda self, *args, **kwargs: fn(*args, **kwargs),
		},
	)

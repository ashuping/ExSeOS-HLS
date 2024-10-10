# ExSeOS-H Hardware ML Workflow Manager
# Copyright (C) 2024  Alexis Maya-Isabelle Shuping

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Utilities for automatically constructing a ``Stage`` from a function. Useful for
quickly converting existing code to use ExSeOS.

To construct a stage from a function, use ``make_StageFromFunction``.
"""

from exseos.data.Variable import (
	Variable,
	UnboundVariable,
	BoundVariable,
	ensure_from_name_arr,
)
from exseos.types import type_check, TypeCheckWarning
from exseos.types.Option import Some, Nothing
from exseos.types.Result import Result, Okay, Warn, Fail, merge_all, MergeStrategies
from exseos.workflow.stage.Stage import Stage

from abc import abstractmethod
import inspect
from inspect import Parameter, Signature
from typing import Callable


class ReturnBindingMismatchWarning(Warning):
	"""
	Retuned when a ``StageFromFunction``'s internal function returns too many or
	too few values for the preset output variables.

	If there are more return values than output variables, the excess return
	values will be ignored. If there are fewer return values than output
	variables, then some output variables will not be bound - this will probably
	cause issues futher down the line!
	"""

	def __init__(
		self,
		stage: "StageFromFunction",
		num_return_vals: int,
		num_outputs: int,
		note: str = "",
	):
		"""
		Construct a ``ReturnBindingMismatchWarning``.

		:param stage: The ``StageFromFunction`` that did not return the correct
		    number of outputs.
		:param num_return_vals: The number of values returned by the function
		    (the actual count)
		:param num_outputs: The number of outputs registered for the Stage (the
		    expected count)
		"""

		consequence_msg = (
			" Extra values will be discarded."
			if num_return_vals > num_outputs
			else " Some outputs will be unbound!"
			if num_return_vals < num_outputs
			else ""
		)

		overall_msg = (
			f"While binding outputs for stage {type(stage).__name__}: User "
			+ f"code returned {num_return_vals} values, but we expected it "
			+ f"to return {num_outputs}!{consequence_msg}"
		)

		super().__init__(overall_msg)

		self.stage = stage
		self.num_return_vals = num_return_vals
		self.num_outputs = num_outputs


def _input_list_to_kwargs(input_list: tuple[Variable]) -> dict[str, any]:
	kwargs = {}
	for v in input_list:
		kwargs[v.name] = v.val.val

	return kwargs


def _bind_outputs_from_rval(
	stage: Stage, rval: any, outputs: tuple[UnboundVariable]
) -> Result[Exception, Exception, tuple[BoundVariable]]:
	def _bind_single_output(
		val: any, output: UnboundVariable
	) -> Result[Exception, Exception, BoundVariable]:
		if output.var_type.has_val and not type_check(val, output.var_type.val):
			return Warn(
				[
					TypeCheckWarning(
						val,
						output.var_type.val,
						f"(while binding output variable {output.name} for "
						+ f"{type(stage).__name__})",
					)
				],
				output.bind(val),
			)
		else:
			return Okay(output.bind(val))

	def _bind_all_outputs(
		vs: any, os: tuple[UnboundVariable]
	) -> Result[Exception, Exception, tuple[BoundVariable]]:
		try:
			len(vs)
		except TypeError:
			vs = [vs]  # Interpret ``vs`` as a single value if we can't iterate over it

		collected_results = [_bind_single_output(x, y) for x, y in zip(vs, os)]

		final_result = (
			collected_results[0].map(lambda a: [a])
			if len(collected_results) == 1
			else merge_all(*collected_results, fn=MergeStrategies.APPEND)
		)

		if len(vs) != len(os):
			final_result <<= Warn(
				[ReturnBindingMismatchWarning(stage, len(vs), len(os))], None
			)

		if len(vs) < len(os):
			# Add in the unbound variables to the result
			to_add = (len(os) - len(vs)) * -1
			final_result = final_result.map(
				lambda bindings: tuple(bindings) + os[to_add:]
			)

		return final_result.map(lambda x: tuple(x))

	if len(outputs) == 0:
		return Okay(())
	elif len(outputs) == 1:
		return _bind_single_output(rval, outputs[0]).map(lambda x: (x,))
	else:
		return _bind_all_outputs(rval, outputs)


class StageFromFunction(Stage):
	"""
	A ``Stage`` constructed automatically from a function.

	To construct a ``StageFromFunction``, use ``make_StageFromFunction``.
	"""

	@abstractmethod
	def inner_function(self, *args, **kwargs):
		"""The actual function encapsulated in a ``StageFromFunction``."""
		...  # pragma: no cover

	def run(self, inputs: tuple[Variable]) -> Result:
		try:
			rval = self.inner_function(**_input_list_to_kwargs(inputs))
		except Exception as e:
			return Fail(
				[
					e,
				]
			)
		else:
			return _bind_outputs_from_rval(self, rval, self.output_vars)


def _extract_func_args_and_ret(
	fn: Callable, outputs: tuple[str | Variable]
) -> tuple[list[Variable], list[Variable]]:
	"""
	Extract the arguments and (if present) return-type annotation from a
	function.

	:param fn: The function to extract data from.
	:param outputs: List of outputs that the function will return.
	:returns: A tuple whose first element is the list of input ``Variable``'s
	          and the second element is a list of return-type ``Variable``'s
	"""
	sig = inspect.signature(fn)

	args = [
		UnboundVariable(
			param.name,
			var_type=Some(param.annotation)
			if param.annotation != Parameter.empty
			else Nothing(),
			default=Some(param.default)
			if param.default != Parameter.empty
			else Nothing(),
		)
		for param in sig.parameters.values()
	]

	inferred_return_type = (
		[
			UnboundVariable("return", Some(sig.return_annotation)),
		]
		if sig.return_annotation != Signature.empty
		else []
	)

	ret = ensure_from_name_arr(outputs) if outputs is not None else inferred_return_type

	return (args, ret)


def make_StageFromFunction(
	fn: Callable, outputs: tuple[str | Variable] = None
) -> type[StageFromFunction]:
	"""
	Return a concrete subclass of ``StageFromFunction``, with its inner function
	set to the provided ``fn``. Unlike ``StageFromFunction`` itself, these
	subclasses can be directly instantiated.

	To bind function outputs, use the ``outputs`` parameter. This can be a list
	of names or Variables - the function's return value(s) will be assigned to
	the relevant names in the order provided. If ``outputs`` is ``None`` or not
	provided, then an output variable named 'return' will be inferred from the
	function's return-type annotation. If ``outputs`` is an empty array, the
	function's return-type annotation is ``None``, or the function has no
	return-type annotation at all, it will be assumed to have no outputs and any
	return value will be discarded.

	If the function raises an exception, it will be caught and the stage will
	return ``Result.Error``. Otherwise, it will return ``Result.Okay``, and the
	function's return values will be bound as output variables, per the
	``outputs`` parameter.

	:param fn: The function to convert.
	:param outputs: List of outputs that the function will return.
	:returns: A concrete subclass of ``StageFromFunction``
	"""
	args, ret = _extract_func_args_and_ret(fn, outputs)

	inputs = tuple(args)
	outputs = tuple(ret)

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

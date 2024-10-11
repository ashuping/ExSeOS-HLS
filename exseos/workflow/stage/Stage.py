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
A ``Stage`` is a single step in a ``Workflow``. It is the base unit of
computation within ExSeOS.
"""

from exseos.types.Variable import Variable, UnboundVariable, VariableSet
from exseos.types.Option import Option, Some, Nothing
from exseos.types.Result import Result

from abc import ABC, abstractmethod


def _process_stage_io(
	dex: int, i: Variable, args: list[Variable | str], kwargs: dict[str, Variable | str]
) -> Option[Variable]:
	"""
	Match a single input (or output) from our variable list to the provided
	parameters.

	:param dex: Offset in our input ``Variable`` list for ``i``
	:param i: Input ``Variable`` to match
	:param args: Positional function args to match against
	:param kwargs: Keyword function args to match against
	:returns: The matching ``Variable`` if found, or ``Nothing`` if not.
	"""

	def __atov(a: Variable | str) -> Variable:
		if type(a) is str:
			return UnboundVariable(a)
		else:
			return a

	if args and len(args) > dex:
		return Some(__atov(args[dex]))
	elif kwargs and i.name in kwargs.keys():
		return Some(__atov(kwargs[i.name]))
	else:
		return Nothing()


class Stage(ABC):
	"""
	Represents a step in a ``Workflow``.

	``Stage``'s are immutable - their inputs (and outputs, if applicable), do
	not change once set. Functions modifying ``Stage``'s will return a new
	``Stage`` with the desired modifications, rather than modifying the existing
	``Stage`` in-place.
	"""

	input_vars: tuple[UnboundVariable] = ()
	output_vars: tuple[UnboundVariable] = ()

	def __init__(
		self,
		*args: list[str | Variable],
		_to: tuple[list[str | Variable], dict[str, str | Variable]] = ([], {}),
		**kwargs: dict[str, str | Variable],
	):
		"""
		Create a ``Stage`` and bind its input variables.

		All arguments should be either ``Variable``'s or strings. Strings are
		automatically converted to ``UnboundVariable``'s. Keyword arguments are
		matched by name; positional arguments are matched by position.

		:param _to: Internal-use constructor for supplying output variable
		    information.
		"""
		self.__inputs = tuple(
			[
				(i, _process_stage_io(dex, i, args, kwargs))
				for dex, i in enumerate(self.input_vars)
			]
		)

		self.__outputs = tuple(
			[
				(o, _process_stage_io(dex, o, _to[0], _to[1]))
				for dex, o in enumerate(self.output_vars)
			]
		)

		self.__args = tuple(args)
		self.__kwargs = kwargs
		self.__to = _to

	@abstractmethod
	def run(self, inputs: VariableSet) -> Result[Exception, Exception, tuple[Variable]]:
		"""
		Run this ``stage``, returning a ``Result`` containing output
		information.

		:param inputs: A set of all ``Variables`` needed for this ``Stage`` to
		    run.
		:returns: A ``Result`` containing output ``Variable``'s for this
		    ``Stage``.
		"""
		...  # pragma: no cover

	@property
	def _input_bindings(self) -> tuple[Variable, Option[Variable]]:
		"""
		A tuple of input bindings for this stage. Used for internal wiring.

		Bindings take the form ``(internal_var, Option[bound_var])``.

		:meta private:
		"""
		return self.__inputs

	@property
	def _output_bindings(self) -> tuple[Variable, Option[Variable]]:
		"""
		A tuple of output bindings for this stage. Used for internal wiring.

		Bindings take the form ``(internal_var, Option[bound_var])``.

		:meta private:
		"""
		return self.__outputs

	@property
	def _is_implicit(self) -> bool:
		"""
		``True`` iff the stage is marked as implicit-binding. Used for internal
		wiring.

		:meta private:
		"""
		...

	def to(self, *args, **kwargs) -> "Stage":
		"""
		Bind the outputs of the ``Stage`` to a ``Variable`` or name.

		:param args: Outputs to be bound by position
		:params kwargs: Outputs to be bound by name
		:returns: A copy of this ``Stage`` with the outputs bound.
		"""
		_to = (args, kwargs)

		return type(self)(_to=_to, *self.__args, **self.__kwargs)

	def depends(self, *args: tuple[str]) -> "Stage":
		"""
		Define one or more dependencies needed by this ``Stage``.

		In a ``Workflow``, ``Stage``'s may be reorganized and/or run in parallel
		if they have no dependencies. Matching input and output variables
		between two stages automatically count as dependencies; however, if
		stages have dependencies based on side effects (e.g. one stage creates a
		file that another stage needs), ``depends()`` / ``provides()`` can be
		used to establish explicit dependencies. If a stage ``depends()`` on
		something, it will not run until another stage ``provides()`` it. If
		multiple stages provide the same dependency, only one of them has to run
		for the dependency to be considered met.

		:param *args: List of explicit dependencies (as strings) that this
		    ``Stage`` needs.
		:returns: A ``Stage`` with the requested dependencies added.
		"""
		...

	def provides(self, *args: tuple[str]) -> "Stage":
		"""
		Define one or more dependencies provided by this ``Stage``.

		Along with ``depends()``, this function provides explicit dependency
		declaration between stages to assist with parallelism support.

		:param *args: List of explicit dependencies (as strings) that this
		    ``Stage`` provides.
		:returns: A ``Stage`` with the requested dependencies added.
		"""
		...

	def bind_implicitly(self) -> "Stage":
		"""
		Mark this stage as implicit-binding. This allows its inputs to be
		matched to previous stages' outputs automatically, without needing to
		explicitly use ``to`` and constructor params.

		This is not recommended, as it can easily lead to ambiguity and highly
		dependent on the stage's input names.

		:returns: A ``Stage`` marked as implicit-binding
		"""
		...

	def always(self) -> "Stage":
		"""
		Mark this stage as 'always-run.' Normally, the result of a ``Stage`` is
		cached for future stages unless its inputs change. This directive
		indicates that this stage has a side-effect that requires it to be
		re-run every time.

		:returns: This ``Stage`` marked as always-run
		"""
		...

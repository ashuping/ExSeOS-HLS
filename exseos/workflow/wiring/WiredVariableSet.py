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
A ``WiredVariableSet`` holds the ``WiredStageVariable`` mappings for a set of
``Variable``'s. Usually this is the inputs or outputs of a ``Stage``.
"""

from exseos.types.Option import Option, Some, Nothing
from exseos.types.Variable import Variable
from exseos.workflow.stage.Stage import Stage
from exseos.workflow.wiring.WiredStageVariable import WiredStageVariable


class WiredVariableSet:
	"""
	A ``WiredVariableSet`` holds the ``WiredStageVariable`` mappings for a set of
	``Variable``'s. Usually this is the inputs or outputs of a ``Stage``.
	"""

	def __init__(self, vars: tuple[WiredStageVariable]):
		self.__vars = vars

	@property
	def vars(self) -> tuple[WiredStageVariable]:
		return self.__vars

	def get_by_local(self, to_get: str | Variable) -> Option[WiredStageVariable]:
		"""
		Retrieve a ``WiredStageVariable`` by its *local* name - that is, the
		name used within the ``Stage`` definition.

		:param to_get: The ``Variable`` to search for, either directly by name
		    or as a ``Variable``.
		:returns: ``Some(WiredStageVariable)``, or ``Nothing()`` if no matching
		    ``Variable`` exists in this set.
		"""
		name = to_get.name if issubclass(type(to_get), Variable) else to_get
		matches = [v for v in self.vars if v.local_name == name]
		return Some(matches[0]) if len(matches) > 0 else Nothing()

	def get_by_wire(self, to_get: str | Variable) -> Option[WiredStageVariable]:
		"""
		Retrieve a ``WiredStageVariable`` by its *wire* name - that is, the name
		used within the ``Workflow`` definition.

		:param to_get: The ``Variable`` to search for, either directly by name
		    or as a ``Variable``.
		:returns: ``Some(WiredStageVariable)``, or ``Nothing()`` if no matching
		    ``Variable`` exists in this set.
		"""
		name = to_get.name if issubclass(type(to_get), Variable) else to_get
		matches = [
			v for v in self.vars if v.wire_name.has_val and v.wire_name.val == name
		]
		return Some(matches[0]) if len(matches) > 0 else Nothing()

	def bind_local(self, bind_to: tuple[Variable]) -> "WiredVariableSet":
		"""
		Bind a set of variables to this ``WiredStageIO`` by local-name.

		All variables with local-names matching those in ``bind_to`` will have
		both their local and wire values updated; however, non-matching
		variables in ``bind_to`` will not be added to the set.
		"""
		bind_to_names = [v.name for v in bind_to]
		new_vars = []
		for v in self.vars:
			if v.local_name in bind_to_names:
				dex = bind_to_names.index(v.local_name)
				new_vars.append(v.bind(bind_to[dex].val.val))
			else:
				new_vars.append(v)

		return WiredVariableSet(tuple(new_vars))

	def bind_wire(self, bind_to: tuple[Variable]) -> "WiredVariableSet":
		"""
		Bind a set of variables to this ``WiredStageIO`` by wire-name.

		All variables with wire-names matching those in ``bind_to`` will have
		both their local and wire values updated; however, non-matching
		variables in ``bind_to`` will not be added to the set.
		"""
		bind_to_names = [v.name for v in bind_to]
		new_vars = []
		for v in self.vars:
			if v.has_wire and (v.wire_name.val in bind_to_names):
				dex = bind_to_names.index(v.wire_name.val)
				new_vars.append(v.bind(bind_to[dex].val.val))
			else:
				new_vars.append(v)

		return WiredVariableSet(tuple(new_vars))

	@classmethod
	def from_input(cls, stage: Stage) -> "WiredVariableSet":
		"""
		Generate a ``WiredVariableSet`` automatically from the inputs to a
		``Stage``.

		:param stage: The ``Stage`` whose inputs should be extracted.
		:returns: A ``WiredVariableSet`` mapping over the ``Stage``'s inputs.
		"""
		if stage._is_implicit:
			return cls(
				tuple([WiredStageVariable(Some(var), var) for var in stage.input_vars])
			)
		else:
			return cls(
				tuple(
					[
						WiredStageVariable(wvar, lvar)
						for lvar, wvar in stage._input_bindings
					]
				)
			)

	@classmethod
	def from_output(cls, stage: Stage) -> "WiredVariableSet":
		"""
		Generate a ``WiredVariableSet`` automatically from the outputs to a
		``Stage``.

		:param stage: The ``Stage`` whose inputs should be extracted.
		:returns: A ``WiredVariableSet`` mapping over the ``Stage``'s outputs.
		"""
		if stage._is_implicit:
			return cls(
				tuple([WiredStageVariable(Some(var), var) for var in stage.output_vars])
			)
		else:
			return cls(
				tuple(
					[
						WiredStageVariable(wvar, lvar)
						for lvar, wvar in stage._output_bindings
					]
				)
			)

	@classmethod
	def from_variable_set(cls, vars: tuple[Variable]):
		"""
		Generate a ``WiredVariableSet`` directly from a set of ``Variable``'s.

		Each resultant ``WiredStageVariable`` will have both its local and wire
		name set to the ``Variable``'s name.

		:param vars: The ``Variable``'s to be converted.
		:returns: A ``WiredVariableSet`` mapping over those ``Variable``'s.
		"""
		return cls(tuple([WiredStageVariable(Some(var), var) for var in vars]))

	def __eq__(self, other: "WiredVariableSet") -> bool:
		if not issubclass(type(other), WiredVariableSet):
			return False

		return all([x == y for x, y in zip(self.vars, other.vars)])

	def __str__(self) -> str:
		return "WiredVariableSet:" + "".join(["\n  " + str(s) for s in self.vars])

	def __repr__(self) -> str:
		return f"WiredVariableSet({self.vars})"

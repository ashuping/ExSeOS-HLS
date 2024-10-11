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
A ``Wiring`` object contains a lookup table that matches intermediate
``Variable``'s to ``Stage`` inputs.
"""

from exseos.types.Option import Option, Some, Nothing
from exseos.types.Result import Result, Okay, Fail, merge_all, MergeStrategies
from exseos.types.Variable import Variable, VariableSet
from exseos.workflow.stage.Stage import Stage

from typing import Callable


class UnwiredVariableWarning(Warning):
	"""
	Warns that a ``Variable`` could not be wired.
	"""

	def __init__(self, path: str, note: str = ""):
		msg = f"Couldn't wire {path} - it will be unbound!" + (
			f" {note}" if note else ""
		)

		super().__init__(msg)

		self.path = path
		self.note = note


class AmbiguousWiringWarning(Warning):
	"""
	Warns that there was more than one candidate for wiring ``Variable``. The
	first candidate encountered will be chosen - this may not be the user's
	intention!
	"""

	def __init__(
		self,
		to_wire: str,
		candidates: tuple[str],
		note: str = "",
	):
		msg = (
			f"While wiring {to_wire}: "
			+ "multiple candidates available to wire! Candidates:\n"
			+ "".join([f"  {c}\n" for c in candidates])
			+ "The first candidate will be chosen."
			+ (f" {note}" if note else "")
		)
		super().__init__(msg)

		self.to_wire = to_wire
		self.candidates = candidates
		self.note = note


class LookupError(Exception):
	"""
	Indicates that a ``Wiring`` lookup has failed.
	"""

	def __init__(self, path: str, note: str = ""):
		msg = f"Couldn't resolve path {path} to a Variable!" + (
			f" {note}" if note else ""
		)
		super().__init__(msg)

		self.path = path
		self.note = note


class WireBinding:
	"""
	Enumeration for binding types.

	:meta private:
	"""

	pass


class SelfBinding(WireBinding):
	"""
	This input is already bound, so it doesn't need to be bound anywhere else.

	:meta private:
	"""

	pass


class LinkBinding(WireBinding):
	"""
	This input has an unambiguous binding to somewhere else.

	:meta private:
	"""

	__match_args__ = ("link",)

	def __init__(self, link: str):
		self.__link = link

	@property
	def link(self) -> str:
		return self.__link

	def map(self, fn: Callable[[str], str]) -> "LinkBinding":
		return self.__class__(fn(self.link))


class DefaultBinding(WireBinding):
	"""
	This input could not be bound anywhere, but it has a default value.

	:meta private:
	"""

	pass


class NoBinding(WireBinding):
	"""
	This input could not be bound anywhere.

	:meta private:
	"""

	pass


class WiredStageVariable:
	__match_args__ = ("wire_name", "wire_var", "local_name", "local_var")

	def __init__(self, wire_var: Option[Variable], local_var: Variable):
		self.__wire_var = wire_var
		self.__local_var = local_var

	def bind(self, val: any) -> "WiredStageVariable":
		"""
		Bind this ``WiredStageVariable`` to a concrete value.

		This will override both the local and global variables to have the new
		value.
		"""
		return WiredStageVariable(
			self.wire_var.map(lambda v: v.bind(val)),
			self.local_var.bind(val),
		)

	@property
	def has_wire(self) -> bool:
		return self.__wire_var.has_val

	@property
	def wire_name(self) -> Option[str]:
		return self.__wire_var.map(lambda v: v.name)

	@property
	def local_name(self) -> str:
		return self.__local_var.name

	@property
	def wire_var(self) -> Variable:
		return self.__wire_var

	@property
	def local_var(self) -> Variable:
		return self.__local_var

	@property
	def is_bound(self) -> bool:
		"""
		Returns True if either the local or wire vars is bound
		"""
		return self.local_var.is_bound or (self.has_wire and self.wire_var.val.is_bound)

	@property
	def has_default(self) -> bool:
		"""
		Returns True if either the local or wire vars has a default value
		"""
		return self.local_var.default.has_val or (
			self.has_wire and self.wire_var.val.default.has_val
		)

	@property
	def val(self) -> Option[any]:
		"""
		Returns, in order of priority:
		  - The Wire var's value
		  - The Wire var's default
		  - The local var's value (should never happen)
		  - The local var's default
		"""
		if self.has_wire:
			if self.wire_var.val.is_bound:
				return Some(self.wire_var.val.val.val)
			elif self.wire_var.val.default.has_val:
				return Some(self.wire_var.val.default.val)
		if self.local_var.is_bound:
			return Some(self.local_var.val.val)  # should never happen
		elif self.local_var.default.has_val:
			return Some(self.local_var.default.val)

		return Nothing()


class WiredStageIO:
	def __init__(self, vars: tuple[WiredStageVariable]):
		self.__vars = vars

	@property
	def vars(self) -> tuple[WiredStageVariable]:
		return self.__vars

	def get_by_local(self, to_get: str | Variable) -> Option[WiredStageVariable]:
		name = to_get.name if issubclass(type(to_get), Variable) else to_get
		matches = [v for v in self.vars if v.local_name == name]
		return Some(matches[0]) if len(matches) > 0 else Nothing()

	def get_by_wire(self, to_get: str | Variable) -> Option[WiredStageVariable]:
		name = to_get.name if issubclass(type(to_get), Variable) else to_get
		matches = [
			v for v in self.vars if v.wire_name.has_val and v.wire_name.val == name
		]
		return Some(matches[0]) if len(matches) > 0 else Nothing()

	def bind(self, bind_to: tuple[Variable]) -> "WiredStageIO":
		"""
		Bind a set of variables to this ``WiredStageIO``.

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

		return WiredStageIO(tuple(new_vars))

	@classmethod
	def from_input(cls, stage: Stage) -> "WiredStageIO":
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
	def from_output(cls, stage: Stage) -> "WiredStageIO":
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
	def from_global_io(cls, vars: tuple[Variable]):
		return cls(tuple([WiredStageVariable(Some(var), var) for var in vars]))


class Wire:
	__match_args__ = ("var", "binding")

	def __init__(self, var: WiredStageVariable, binding: WireBinding):
		self.__var = var
		self.__binding = binding

	@property
	def var(self) -> WiredStageVariable:
		return self.__var

	@property
	def binding(self) -> WireBinding:
		return self.__binding


def _find_binding_path(
	stages: tuple[WiredStageIO],
	inputs: WiredStageIO,
	to_find_wire_name: str,
) -> Option[str]:
	for dex, stage in enumerate(reversed(stages)):
		found = stage.get_by_wire(to_find_wire_name)
		if found.has_val:
			return Some(f"/stage/{len(stages) - (1 + dex)}/{to_find_wire_name}")

	found = inputs.get_by_wire(to_find_wire_name)
	if found.has_val:
		return Some(f"/inputs/{to_find_wire_name}")

	return Nothing()


class Wiring:
	def __init__(
		self,
		inputs: WiredStageIO,
		outputs: WiredStageIO,
		stages: tuple[WiredStageIO],
		wires: tuple[Wire],
		wire_status: Result[Exception, Exception, None],
		bound_inputs: Option[WiredStageIO] = Nothing(),
		bound_intermediate_outputs: tuple[WiredStageIO] = (),
	):
		self.__inputs = inputs
		self.__outputs = outputs
		self.__stages = stages
		self.__wires = wires

		self.__bound_inputs = bound_inputs
		self.__bound_intermediate_outputs = bound_intermediate_outputs

		self.__status = wire_status

	@property
	def status(self) -> Result[Exception, Exception, None]:
		return self.__status

	@property
	def wires(self) -> tuple[Wire]:
		return self.__wires

	@property
	def bound_inputs(self) -> Option[WiredStageIO]:
		return self.__bound_inputs

	@property
	def bound_intermediate_outputs(self) -> tuple[WiredStageIO]:
		return self.__bound_intermediate_outputs

	def bind_inputs(self, inputs: tuple[Variable]) -> "Result[Wiring]":
		return self.__class__(
			self.__inputs,
			self.__outputs,
			self.__stages,
			self.__wires,
			self.__status,
			WiredStageIO.from_global_io(inputs),
			self.__bound_intermediate_outputs,
		)

	def bind_stage(
		self, stage_index: int, stage_outputs: tuple[Variable]
	) -> "Result[Wiring]":
		return self.__class__(
			self.__inputs,
			self.__outputs,
			self.__stages,
			self.__wires,
			self.__status,
			self.__bound_inputs,
			self.__bound_intermediate_outputs
			+ (self.__stages[stage_index].bind(stage_outputs),),
		)

	def get_stage_inputs(self, stage_index: int) -> "Result[VariableSet]":
		try:
			return (
				merge_all(
					*[
						self._resolve(wire)
						for wire in self.wires["stages"][str(stage_index)]
					],
					fn=MergeStrategies.APPEND,
				)
				.map(lambda wsvars: [v.local_var for v in wsvars] if wsvars else [])
				.map(lambda vars: VariableSet(tuple(vars)))
			)
		except KeyError:
			return Fail([KeyError(f"Wiring has no stage {stage_index}.")])
		# except Exception as e:
		# return Fail([e])

	def get_outputs(self) -> "Result[VariableSet]":
		try:
			return (
				merge_all(
					*[self._resolve(wire) for wire in self.wires["outputs"]],
					fn=MergeStrategies.APPEND,
				)
				.map(lambda wsvars: [v.local_var for v in wsvars])
				.map(lambda vars: VariableSet(tuple(vars)))
			)
		except Exception as e:
			return Fail([e])

	def _lookup_wire_path(
		self, pth: str
	) -> Result[Exception, Exception, WiredStageVariable]:
		segs = pth.split("/")
		match segs:
			case "inputs":
				if len(segs) != 2:
					return Fail([LookupError(pth, "(no such input)")])

				wire_name = segs[1]

				if (
					self.__bound_inputs.has_val
					and (
						matched := self.__bound_inputs.val.get_by_wire(wire_name)
					).has_val
				):
					return Okay(matched.val)
				else:
					return Fail([LookupError(pth, "(no such input)")])
			case "stages":
				if len(segs) != 3:
					return Fail([LookupError(pth, "(no such stage variable)")])

				_, stage_index, wire_name = segs

				if (
					len(self.__bound_intermediate_outputs) > int(stage_index)
					and (
						matched := self.__bound_intermediate_outputs[
							stage_index
						].get_by_wire(wire_name)
					).has_val
				):
					return Okay(matched.val)
				else:
					return Fail([LookupError(pth, "(no such stage variable)")])
			case _:
				return Fail([LookupError(pth)])

	def _resolve(self, wire: Wire) -> Result[Exception, Exception, WiredStageVariable]:
		match wire.binding:
			case SelfBinding() | DefaultBinding() | NoBinding():
				return Okay(wire.var)
			case LinkBinding(path):
				return self._lookup_wire_path(path)
			case _:
				return Fail(
					ValueError(f"For Wire {wire}: unknown binding type {wire.binding}")
				)

	@classmethod
	def wire(
		cls, inputs: tuple[Variable], outputs: tuple[Variable], stages: tuple[Stage]
	):
		"""
		Generate a wiring for a workflow
		"""

		stage_inputs = tuple([WiredStageIO.from_input(s) for s in stages])
		stage_outputs = tuple([WiredStageIO.from_output(s) for s in stages])
		global_inputs = WiredStageIO.from_global_io(inputs)
		global_outputs = WiredStageIO.from_global_io(outputs)

		def _make_wire_binding(dex: int, v: WiredStageVariable) -> WireBinding:
			if v.is_bound:
				return SelfBinding()
			elif v.has_wire and (
				(
					res_path := _find_binding_path(
						stage_outputs[:dex], global_inputs, v.wire_name.val
					)
				).has_val
			):
				return LinkBinding(res_path.val)
			elif v.has_default:
				return DefaultBinding()
			else:
				return NoBinding()

		wires = {"stages": {}, "outputs": {}}

		status = Okay(None)

		for dex, s_input in enumerate(stage_inputs):
			wires["stages"][str(dex)] = [
				Wire(v, _make_wire_binding(dex, v)) for v in s_input.vars
			]

		wires["outputs"] = [
			Wire(o, _make_wire_binding(len(stages), o)) for o in global_outputs.vars
		]

		return cls(global_inputs, global_outputs, stage_outputs, wires, status)

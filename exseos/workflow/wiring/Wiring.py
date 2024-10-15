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
from exseos.types.Result import Result, Okay, Warn, Fail, merge_all, MergeStrategies
from exseos.types.Variable import Variable, VariableSet
from exseos.workflow.stage.Stage import Stage
from exseos.workflow.wiring.WiredStageVariable import WiredStageVariable
from exseos.workflow.wiring.WiredVariableSet import WiredVariableSet

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
	stages: tuple[WiredVariableSet],
	inputs: WiredVariableSet,
	to_find_wire_name: str,
) -> Option[str]:
	for dex, stage in enumerate(reversed(stages)):
		found = stage.get_by_wire(to_find_wire_name)
		if found.has_val:
			return Some(f"/stages/{len(stages) - (1 + dex)}/{to_find_wire_name}")

	found = inputs.get_by_wire(to_find_wire_name)
	if found.has_val:
		return Some(f"/inputs/{to_find_wire_name}")

	return Nothing()


def _validate_and_bind_results(
	bind_to: WiredVariableSet, vars_to_bind: tuple[WiredStageVariable]
) -> Result[Exception, Exception, tuple[Variable]]:
	warnings = Okay(None)

	wire_vars = [wv.wire_var.val for wv in vars_to_bind if wv.has_wire]

	if len(wire_vars) < len(vars_to_bind):
		warnings <<= Warn(
			[
				ValueError(
					"While calculating stage inputs: "
					+ "Wiring._resolve() returned Variables without "
					+ "wire names! This is likely an internal bug!"
				)
			],
			None,
		)

	return (
		Okay(bind_to.bind_wire(wire_vars))
		.map(lambda wsvars: [v.local_var for v in wsvars.vars])
		.map(lambda vars: VariableSet(tuple(vars)))
		<< warnings
	)


class Wiring:
	def __init__(
		self,
		inputs: WiredVariableSet,
		outputs: WiredVariableSet,
		stage_inputs: tuple[WiredVariableSet],
		stage_outputs: tuple[WiredVariableSet],
		wires: tuple[Wire],
		wire_status: Result[Exception, Exception, None],
		bound_inputs: Option[WiredVariableSet] = Nothing(),
		bound_intermediate_outputs: tuple[WiredVariableSet] = (),
	):
		self.__inputs = inputs
		self.__outputs = outputs
		self.__stage_inputs = stage_inputs
		self.__stage_outputs = stage_outputs
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
	def bound_inputs(self) -> Option[WiredVariableSet]:
		return self.__bound_inputs

	@property
	def bound_intermediate_outputs(self) -> tuple[WiredVariableSet]:
		return self.__bound_intermediate_outputs

	def bind_inputs(self, inputs: tuple[Variable]) -> "Result[Wiring]":
		return self.__class__(
			self.__inputs,
			self.__outputs,
			self.__stage_inputs,
			self.__stage_outputs,
			self.__wires,
			self.__status,
			Some(WiredVariableSet.from_variable_set(inputs)),
			self.__bound_intermediate_outputs,
		)

	def bind_stage(
		self, stage_index: int, stage_outputs: tuple[Variable]
	) -> "Result[Wiring]":
		return self.__class__(
			self.__inputs,
			self.__outputs,
			self.__stage_inputs,
			self.__stage_outputs,
			self.__wires,
			self.__status,
			self.__bound_inputs,
			self.__bound_intermediate_outputs
			+ (self.__stage_outputs[stage_index].bind_local(stage_outputs),),
		)

	def get_stage_inputs(
		self, stage_index: int
	) -> "Result[Exception, Exception, VariableSet]":
		try:
			return merge_all(
				*[
					self._resolve(wire)
					for wire in self.wires["stages"][str(stage_index)]
				],
				fn=MergeStrategies.APPEND,
				empty=[],
			).flat_map(
				lambda resolved_vars: _validate_and_bind_results(
					self.__stage_inputs[stage_index], resolved_vars
				)
			)
		except KeyError:
			return Fail([KeyError(f"Wiring has no stage {stage_index}.")])
		# except Exception as e:
		# 	return Fail([e])

	def get_outputs(self) -> "Result[VariableSet]":
		try:
			return merge_all(
				*[self._resolve(wire) for wire in self.wires["outputs"]],
				fn=MergeStrategies.APPEND,
				empty=[],
			).flat_map(
				lambda resolved_vars: _validate_and_bind_results(
					self.__outputs, resolved_vars
				)
			)
		except Exception as e:
			return Fail([e])

	def _lookup_wire_path(
		self, pth: str
	) -> Result[Exception, Exception, WiredStageVariable]:
		segs = pth.split("/")
		if len(segs) < 2:
			return Fail([LookupError(pth)])

		match segs[1]:
			case "inputs":
				if len(segs) != 3:
					return Fail([LookupError(pth, "(no such input)")])

				wire_name = segs[2]

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
				if len(segs) != 4:
					return Fail([LookupError(pth, "(no such stage variable)")])

				_, _, stage_index, wire_name = segs

				if (
					len(self.__bound_intermediate_outputs) > int(stage_index)
					and (
						matched := self.__bound_intermediate_outputs[
							int(stage_index)
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
	) -> "Wiring":
		"""
		Generate a wiring for a workflow
		"""

		stage_inputs = tuple([WiredVariableSet.from_input(s) for s in stages])
		stage_outputs = tuple([WiredVariableSet.from_output(s) for s in stages])
		global_inputs = WiredVariableSet.from_variable_set(inputs)
		global_outputs = WiredVariableSet.from_variable_set(outputs)

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

		return cls(
			global_inputs, global_outputs, stage_inputs, stage_outputs, wires, status
		)

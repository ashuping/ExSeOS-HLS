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
A sequence of operations.
"""

from exseos.types.Variable import (
	Variable,
	VariableSet,
	UnboundVariable,
	ensure_from_name_arr,
)
from exseos.types.Option import Some
from exseos.types.Result import Result, Okay, Warn, Fail
from exseos.ui.message.UIMessage import ResultMessage
from exseos.ui.UIManager import UIManager
from exseos.ui.terminal.TerminalUIManager import TerminalUIManager
from exseos.workflow.stage.Stage import Stage
from exseos.workflow.wiring.Wiring import Wiring

import logging
import random

log = logging.getLogger(__name__)


class MalformedWorkflowError(Exception):
	"""
	Used when a ``Workflow`` is malformed and cannot be run.

	Call ``message(True)`` to generate a message that includes stack-traces.
	"""

	def __init__(
		self,
		workflow: "Workflow",
		reason: Result[Exception, Exception, None],
		note: str = "",
	):
		self.workflow = workflow
		self.reason = reason
		self.note = note

		super().__init__(self.message())

	def message(self, include_traces=False):
		match self.reason:
			case Okay(_):
				reason_str = ""
			case Warn(_, _):
				sep = "\n\n" if include_traces else "\n  "
				warning_list = (
					self.reason.warnings_traced
					if include_traces
					else self.reason.warnings
				)

				reason_str = " Caused by the following warnings:\n" + sep.join(
					[str(w) for w in warning_list]
				)
			case Fail(_, _):
				sep = "\n\n" if include_traces else "\n  "
				warning_list = (
					self.reason.warnings_traced
					if include_traces
					else self.reason.warnings
				)
				error_list = (
					self.reason.errors_traced if include_traces else self.reason.errors
				)

				reason_str = (
					" Caused by the following errors:\n"
					+ sep.join([str(e) for e in error_list])
					+ (
						(
							"\n\nAnd the following warnings:\n"
							+ sep.join([str(w) for w in warning_list])
						)
						if warning_list
						else ""
					)
				)

		return (
			f"Workflow {self.workflow.name} is malformed and cannot be run!"
			+ reason_str
			+ f" {self.note}"
			if self.note
			else ""
		)


class Workflow:
	"""
	Base class for ``Workflow``'s.

	Instead of instantiating this directly, use ``MakeWorkflow``.
	"""

	def __init__(
		self,
		name: str,
		stages: tuple[Stage],
		inputs: tuple[Variable],
		outputs: tuple[Variable],
		wiring: Wiring,
		ui: UIManager,
		status: Result[Exception, Exception, None],
	):
		self.__name = name
		self.__stages = stages
		self.__inputs = inputs
		self.__outputs = outputs
		self.__wiring = wiring
		self.__ui = ui
		self.__status = status

	@property
	def name(self) -> str:
		return self.__name

	@property
	def status(self) -> Result[Exception, Exception, None]:
		return self.__status

	@property
	def is_runnable(self) -> bool:
		match self.status:
			case Okay(_):
				return True
			case Warn(_, _):
				return True
			case Fail(_, _):
				return False

	@property
	def stages(self) -> tuple[Stage]:
		return self.__stages

	@property
	def inputs(self) -> tuple[Variable]:
		return self.__inputs

	@property
	def outputs(self) -> tuple[Variable]:
		return self.__outputs

	@property
	def wiring(self) -> Wiring:
		return self.__wiring

	@property
	def ui(self) -> UIManager:
		return self.__ui

	async def run(
		self, inputs: tuple[Variable]
	) -> Result[Exception, Exception, VariableSet]:
		if not self.is_runnable:
			return MalformedWorkflowError(self, self.status)

		run_result = Okay(None)
		wiring = self.wiring

		log.info(f"Binding inputs for workflow {self.name}")
		wiring = wiring.bind_inputs(inputs)

		for dex, stage in enumerate(self.stages):
			log.info(f"Running stage {0}: {type(stage).__name__}")
			stage_input_res = wiring.get_stage_inputs(dex)
			run_result <<= stage_input_res

			if run_result.is_fail:
				log.error("Encountered an error while retrieving stage inputs!")
				await self.ui.display(ResultMessage(run_result))
				return run_result

			try:
				stage_res = await stage.run(stage_input_res.val, self.ui)
			except Exception as e:
				log.error(f"User code threw an exception: {type(e).__name__}!")
				await self.ui.display(ResultMessage(run_result))
				return run_result << Fail([e])

			run_result <<= stage_res

			if run_result.is_fail:
				log.error("User code returned a failure result!")
				await self.ui.display(ResultMessage(run_result))
				return run_result

			run_result <<= stage_res

			wiring = wiring.bind_stage(dex, stage_res.val)

		final_outputs = wiring.get_outputs()
		run_result <<= final_outputs

		if run_result.is_fail:
			log.error("Encountered an error while retrieving final outputs!")
			await self.ui.display(ResultMessage(run_result))

		return run_result.map(lambda _: final_outputs.val)


class MakeWorkflow:
	"""
	``Workflow`` factory. Use this class to construct a ``Workflow`` that can
	then be instantiated.
	"""

	def __init__(
		self,
		name: str = None,
		stages: tuple[Stage] = (),
		inputs: tuple[Variable] = (),
		outputs: tuple[Variable] = (),
		ui: UIManager = None,
	):
		if name is None:
			name = f"Unnamed Workflow {random.randrange(0, 999999):06}"

		if ui is None:
			ui = TerminalUIManager()

		self.__name = name
		self.__stages = stages
		self.__inputs = inputs
		self.__outputs = outputs
		self.__ui = ui

	@property
	def name(self) -> str:
		return self.__name

	@property
	def stages(self) -> tuple[Stage]:
		return self.__stages

	@property
	def inputs(self) -> tuple[Variable]:
		return self.__inputs

	@property
	def outputs(self) -> tuple[Variable]:
		return self.__outputs

	@property
	def ui(self) -> UIManager:
		return self.__ui

	def copy(self, **changes) -> "MakeWorkflow":
		"""
		Create a copy with specific changes.

		Changes should use the same keyword argument names that would be
		provided to ``__init__()``.

		:param **changes: Keyword-args of changes to make
		:return: A copy of this ``MakeWorkflow``, with values specified in
		    ``changes`` replacing the ones in the current ``MakeWorkflow``.
		"""
		params = {
			"name": self.name,
			"stages": self.stages,
			"inputs": self.inputs,
			"outputs": self.outputs,
			"ui": self.ui,
		} | changes

		return MakeWorkflow(**params)

	def given(
		self, *args: list[str | Variable], **kwargs: dict[str, any]
	) -> "MakeWorkflow":
		"""
		Add one or more inputs to the Workflow.

		Arguments should either be ``Variable``'s or strings. In the latter
		case, appropriate variables are created for the strings.

		Keyword arguments may be provided - these are interpreted as default
		values for the variable. For example, providing ``my_var=1`` creates a
		new ``UnboundVariable`` called ``my_var`` with a default value of ``1``.

		Keyword argument names must, of course, be strings. To provide a
		pre-existing ``Variable`` with a default value, the default must be
		provided in the ``Variable``'s instantiation

		A modified ``MakeWorkflow`` will be returned. Existing inputs will be
		preserved; however, if a new input has the same name as an existing one,
		the new one will replace the old one.

		:param *args: Inputs to the ``Workflow``, as strings or ``Variable``
		    objects.
		:param **kwargs: Inputs to the ``Workflow`` as strings with default
		    arguments.
		:returns: A ``MakeWorkflow`` with the requested inputs added.
		"""

		arg_vars = tuple(ensure_from_name_arr(args))
		kwarg_vars = tuple(
			[
				UnboundVariable(name, default=Some(default))
				for name, default in kwargs.items()
			]
		)

		inputs = _ensure_unique_names(kwarg_vars + arg_vars + self.inputs)

		return self.copy(inputs=inputs)

	def output_to(self, *args: list[str | Variable]) -> "MakeWorkflow":
		"""
		Add one or more outputs to the ``Workflow``.

		Arguments should either be ``Variable``'s or strings. In the latter
		case, wiring will search for the latest ``Variable`` with the provided
		name.

		A modified ``MakeWorkflow`` will be returned. Existing outputs will be
		preserved; however, if a new output has the same name as an existing
		one, the new one will take priority.

		:param *args: List of arguments (names or ``Variable`` objects) to add
		    as outputs.
		:return: Updated ``MakeWorkflow``
		"""
		new_outputs = tuple(ensure_from_name_arr(args))

		total_outputs = _ensure_unique_names(new_outputs + self.outputs)

		return self.copy(outputs=total_outputs)

	def from_stages(self, *args: list[Stage]) -> "MakeWorkflow":
		"""
		Add stages to the ``Workflow``.

		A modified ``MakeWorkflow`` will be returned. The new stages will be
		added on after existing stages.

		:param *args: List of ``Stage``'s to add to the ``Workflow``.
		:return: Updated ``MakeWorkflow``.
		"""
		return self.copy(stages=self.stages + tuple(args))

	@property
	def status(self) -> Result[Exception, Exception, None]:
		"""
		Validate the ``Workflow`` under construction and return any errors or
		warnings.
		"""
		return Okay(None)

	def __call__(self) -> Workflow:
		"""
		Instantiate the ``Workflow``.

		:returns: The resultant ``Workflow``.
		"""
		wiring = Wiring.wire(self.inputs, self.outputs, self.stages)

		return Workflow(
			self.name,
			self.stages,
			self.inputs,
			self.outputs,
			wiring,
			self.ui,
			self.status << wiring.status,
		)


def _ensure_unique_names(vars: tuple[Variable]) -> tuple[Variable]:
	"""
	Resolves any name conflicts that may exist in ``vars``. Earlier occurences
	are prioritized over later ones.

	:param vars: Variables to ensure uniqueness of
	:return: List of unique variables, with earlier variables overriding later
	    ones.
	"""

	def _name_exists(v: Variable, vs: tuple[Variable]) -> bool:
		return any([v.name == vv.name for vv in vs])

	return tuple(
		[var for dex, var in enumerate(vars) if not _name_exists(var, vars[:dex])]
	)

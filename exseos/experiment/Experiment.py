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
Classes and functions for automatically re-running and optimizing ``Workflow``
objects.
"""

from typing import Any, Callable
from exseos.experiment.Constant import (
	BasicExperimentConstant,
	ExperimentConstant,
	LambdaExperimentConstant,
	ConstantResolutionError,
)
from exseos.experiment.optimizer.Optimizer import Optimizer, OptimizerIteration
from exseos.types.Option import Nothing, Option, Some
from exseos.types.Result import Result, Okay, Fail
from exseos.types.Variable import (
	BoundVariable,
	Variable,
	VariableSet,
	ensure_from_name_arr,
)
from exseos.ui.NullUIManager import NullUIManager
from exseos.ui.UIManager import UIManager
from exseos.workflow.Workflow import Workflow


class Experiment:
	def __init__(
		self,
		name: str,
		workflow: Workflow,
		optimizer: Optimizer,
		constants: tuple[ExperimentConstant],
		ui: UIManager = NullUIManager(),
	):
		self.__name = name
		self.__workflow = workflow
		self.__optimizer = optimizer
		self.__constants = constants
		self.__ui = ui

	@property
	def name(self) -> str:
		return self.__name

	@property
	def workflow(self) -> Workflow:
		return self.__workflow

	@property
	def optimizer(self) -> Optimizer:
		return self.__optimizer

	@property
	def constants(self) -> tuple[ExperimentConstant]:
		return self.__constants

	@property
	def ui(self) -> UIManager:
		return self.__ui

	def copy(self, **delta) -> "Experiment":
		params = {
			"name": self.name,
			"workflow": self.workflow,
			"optimizer": self.optimizer,
			"constants": self.constants,
		} | delta

		return Experiment(**params)

	def _resolve_constants(
		self, opt_inputs: tuple[Variable]
	) -> Result[Exception, Exception, tuple[Variable]]:
		unresolved_constants = self.constants

		vars = opt_inputs

		while unresolved_constants:
			newly_resolved = tuple(
				[
					BoundVariable(c.name, c.resolve(VariableSet(vars)))
					for c in unresolved_constants
					if c.can_resolve(VariableSet(vars))
				]
			)

			unresolved_constants = tuple(
				c for c in unresolved_constants if not c.can_resolve(VariableSet(vars))
			)

			if len(newly_resolved) == 0:
				return Fail(
					[ConstantResolutionError(unresolved_constants, vars)]
				)  # Can't resolve all constants.

			vars += newly_resolved

		return Okay(vars)

	async def run(self) -> "Result[Exception, Exception, ExperimentResult]":
		iteration: int = 0
		history: tuple[OptimizerIteration] = ()
		status = Okay(None)

		while True:
			next_iteration_inputs = self.optimizer.next(iteration, 1, history)

			if len(next_iteration_inputs) == 0:
				break

			run_inputs = self._resolve_constants(
				tuple(next_iteration_inputs[0].vars.values())
			)

			status <<= run_inputs
			if status.is_fail:
				return status

			run_res = await self.workflow.run(run_inputs.val, self.ui)

			status <<= run_res
			if status.is_fail:
				return status

			history += (
				OptimizerIteration(
					VariableSet(run_inputs.val),
					run_res.val,
				),
			)

			iteration += 1

		return status >> Okay(ExperimentResult(self.optimizer, history))


class ExperimentResult:
	def __init__(self, optimizer: Optimizer, history: tuple[OptimizerIteration, ...]):
		self.__optimizer = optimizer
		self.__history = history

	@property
	def optimizer(self) -> Optimizer:
		return self.__optimizer

	@property
	def history(self) -> tuple[OptimizerIteration, ...]:
		return self.__history

	def get_best(self, count: int = 1) -> tuple[OptimizerIteration]:
		return self.optimizer.get_best(self.history, count)


class MakeExperiment:
	def __init__(
		self,
		name: str,
		workflow: Workflow = None,
		optimizer: Optimizer = None,
		constants: tuple[ExperimentConstant] = (),
		ui: UIManager = NullUIManager(),
	):
		self.__name = name
		self.__workflow = workflow
		self.__optimizer = optimizer
		self.__constants = constants
		self.__ui = ui

	@property
	def name(self) -> str:
		return self.__name

	@property
	def workflow(self) -> Workflow:
		return self.__workflow

	@property
	def optimizer(self) -> Optimizer:
		return self.__optimizer

	@property
	def constants(self) -> tuple[ExperimentConstant]:
		return self.__constants

	@property
	def ui(self) -> UIManager:
		return self.__ui

	def copy(self, **delta) -> "MakeExperiment":
		params = {
			"name": self.name,
			"workflow": self.workflow,
			"optimizer": self.optimizer,
			"constants": self.constants,
			"ui": self.ui,
		} | delta

		return MakeExperiment(**params)

	def from_workflow(self, workflow: Workflow) -> "MakeExperiment":
		return self.copy(workflow=workflow)

	def with_constants(
		self,
		*raw_new_constants: list[LambdaExperimentConstant],
		**new_constants: dict[str, Any],
	) -> "MakeExperiment":
		return self.copy(
			constants=tuple(
				[
					BasicExperimentConstant(key, val)
					for key, val in new_constants.items()
				]
			)
			+ tuple(raw_new_constants)
			+ self.constants
		)

	def calculate(
		self,
		*raw_calcs: list[LambdaExperimentConstant],
		**calcs: dict[str, tuple[Callable, tuple[str, ...]]],
	) -> "MakeExperiment":
		def _inner(
			fn: Callable, dependencies: tuple[Variable], params: VariableSet
		) -> Option[any]:
			if params.check(*dependencies):
				return Some(fn(*[params.get_var(v.name) for v in dependencies]))
			else:
				return Nothing()

		return self.copy(
			constants=tuple(
				[
					LambdaExperimentConstant(
						key,
						lambda vs: _inner(val[0], ensure_from_name_arr(val[1]), vs),
					)
					for key, val in calcs.items()
				]
			)
			+ tuple(raw_calcs)
			+ self.constants
		)

	def optimize(self, optimizer: Optimizer) -> "MakeExperiment":
		return self.copy(optimizer=optimizer)

	def with_ui(self, ui: UIManager) -> "MakeExperiment":
		return self.copy(ui=ui)

	def __call__(self) -> Experiment:
		if not self.workflow:
			raise ValueError("Experiment must have a Workflow!")

		if not self.optimizer:
			raise ValueError("Experiment must have an Optimizer!")

		return Experiment(self.name, self.workflow, self.optimizer, self.constants)

# ExSeOS-HLS Hardware ML Workflow Manager
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

from exseos.experiment.Experiment import MakeExperiment
from exseos.experiment.optimizer.GridOptimizer import GridOptimizer
from exseos.experiment.optimizer.OptimizerParameter import ContinuousOptimizerParameter
from exseos.experiment.optimizer.OptimizerTarget import TargetMaximize
from exseos.types.Result import Fail, Result, Okay
from exseos.types.Variable import UnboundVariable, VariableSet
from exseos.workflow.stage.Stage import Stage
from exseos.workflow.Workflow import MakeWorkflow

import pytest


class MustBe2X(Stage):
	input_vars = (
		UnboundVariable("x", float, "Value to check against"),
		UnboundVariable("must_be_2x", float, "Must be 2*x"),
	)

	output_vars = ()

	async def run(self, inputs: VariableSet, _) -> Result:
		res = inputs.check_all()
		if res.is_fail:
			return res

		if abs(2 * inputs.x - inputs.must_be_2x) > 0.00001:
			return Fail([ValueError("it wasn't 2x!!!")])


class MysteryEquation(Stage):
	input_vars = (UnboundVariable("x", float, "input to the calculation"),)

	output_vars = UnboundVariable("y", float, "result of the calculation")

	async def run(self, inputs: VariableSet, _) -> Result:
		res = inputs.check_all()
		if res.is_fail:
			return res

		x = inputs.x

		return Okay((self.output_vars[0].bind(0.333 * x**3 + x**2 - 3 * x + 1),))


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xfail
async def test_experiment_integration():
	workflow = (
		MakeWorkflow("The Mystery Equation")
		.given("x", "xx")
		.from_stages(
			MustBe2X("x", "xx"),
			MysteryEquation("x").to("y"),
		)
		.output_to("y")()
	)

	experiment = (
		MakeExperiment("Search for peaks of the mystery equation")
		.from_workflow(workflow)
		.calculate(xx=(lambda x: 2 * x, ("x",)))
		.optimize(
			GridOptimizer(
				params=(ContinuousOptimizerParameter("x", -10, 10),),
				grid_size=5,
				targets=(TargetMaximize("y", -100, 100)),
			)
		)()
	)

	experiment_res = await experiment.run()

	assert experiment_res.is_okay

	print(experiment_res.val)

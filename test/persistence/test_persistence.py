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

from exseos.persistence import load_from_file, save_to_file
from exseos.types.Result import Result, Okay
from exseos.types.Variable import BoundVariable, UnboundVariable, VariableSet
from exseos.workflow.stage.Stage import Stage
from exseos.workflow.Workflow import MakeWorkflow
from exseos.ui.NullUIManager import NullUIManager
from exseos.ui.UIManager import UIManager

from pathlib import Path
import pytest


class RaiseToPower(Stage):
	input_vars = (
		UnboundVariable("x", int, "Int to raise to ``pow``.", 0),
		UnboundVariable("pow", int, "Power to raise ``x`` to.", 1),
	)
	output_vars = (
		UnboundVariable("result", int, "``x`` raised to the ``pow`` power."),
	)

	async def run(
		self, inputs: VariableSet, ui: UIManager = NullUIManager()
	) -> Result[Exception, Exception, VariableSet]:
		res = inputs.check_all()
		if res.is_fail:
			return res

		return Okay((self.output_vars[0].bind(inputs.x**inputs.pow),))


class MakeBase(Stage):
	input_vars = ()
	output_vars = (UnboundVariable("x", int, "A random number between 1 and 100"),)

	async def run(
		self, inputs: VariableSet, ui: UIManager = NullUIManager()
	) -> Result[Exception, Exception, VariableSet]:
		return Okay(
			(self.output_vars[0].bind(71),)
		)  # Random number selected by rolling a fair 100-sided die


@pytest.mark.asyncio
async def test_persist_stage(tmp_path: Path):
	persist_file = tmp_path / "persist_stage.exseos"

	stage = MakeBase().to("x_wire")

	expected = await stage.run(VariableSet(()))

	assert save_to_file(stage, persist_file).is_okay

	load_res = load_from_file(persist_file)

	assert load_res.is_okay

	stage_loaded: Stage = load_res.val

	actual = await stage_loaded.run(VariableSet(()))

	assert expected == actual


@pytest.mark.asyncio
async def test_persist_workflow(tmp_path: Path):
	persist_file = tmp_path / "persist_stage.exseos"

	workflow = (
		MakeWorkflow("Random number to power")
		.given("to_pow")
		.from_stages(
			MakeBase().to("x_wire"), RaiseToPower("x_wire", "to_pow").to("res_wire")
		)
		.output_to("res_wire")()
	)

	inputs = (BoundVariable("to_pow", 2),)

	expected = await workflow.run(inputs)

	assert save_to_file(workflow, persist_file).is_okay

	load_res = load_from_file(persist_file)

	assert load_res.is_okay

	loaded_stage: Stage = load_res.val

	actual = await loaded_stage.run(inputs)

	assert expected == actual

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

from exseos.types.Option import Some
from exseos.types.Result import Result, Okay
from exseos.types.Variable import BoundVariable, UnboundVariable, VariableSet
from exseos.workflow.stage.Stage import Stage
from exseos.workflow.wiring.Wiring import Wiring
from exseos.ui.NullUIManager import NullUIManager
from exseos.ui.UIManager import UIManager

import random
import pytest


class RaiseToPower(Stage):
	input_vars = (
		UnboundVariable("x", int, "Int to raise to ``pow``.", 0),
		UnboundVariable("pow", int, "Power to raise ``x`` to.", 1),
	)
	output_vars = (
		UnboundVariable("result", int, "``x`` raised to the ``pow`` power."),
	)

	async def run(self, inputs: VariableSet, ui: UIManager = NullUIManager()) -> Result:
		res = inputs.check_all()
		if res.is_fail:
			return res

		return Okay((self.output_vars[0].bind(inputs.x**inputs.pow),))


class MakeBase(Stage):
	input_vars = ()
	output_vars = (UnboundVariable("x", int, "A random number between 1 and 100"),)

	async def run(self, inputs: VariableSet, ui: UIManager = NullUIManager()) -> Result:
		return Okay((self.output_vars[0].bind(random.randint(1, 100)),))


@pytest.mark.integration
@pytest.mark.asyncio
async def test_wire_integration():
	sequence = (MakeBase().to("my_x"), RaiseToPower("my_x", "my_pow").to("my_res"))

	input_vars = (UnboundVariable("my_pow"),)

	output_vars = (UnboundVariable("my_res"), UnboundVariable("my_x"))

	wiring = Wiring.wire(input_vars, output_vars, sequence)

	wiring = wiring.bind_inputs((BoundVariable("my_pow", 2),))

	assert wiring.get_stage_inputs(0) == Okay(VariableSet(()))

	# print(sequence[0].run(wiring.get_stage_inputs(0).val))

	res = await sequence[0].run(wiring.get_stage_inputs(0).val)

	wiring = wiring.bind_stage(0, res.val)

	res_random_num = wiring.bound_intermediate_outputs[0].get_by_local("x")
	assert res_random_num.has_val

	random_num = res_random_num.val
	assert random_num.wire_name == Some("my_x")
	assert random_num.local_name == "x"
	assert random_num.is_bound
	assert type(random_num.val.val) is int

	expect = Okay(
		VariableSet(
			(
				BoundVariable(
					"x", random_num.val.val, int, "Int to raise to ``pow``.", 0
				),
				BoundVariable("pow", 2, int, "Power to raise ``x`` to.", 1),
			)
		)
	)

	print(f"expected: {expect}")
	print(f"actual  : {wiring.get_stage_inputs(1)}")

	assert wiring.get_stage_inputs(1) == expect

	res = await sequence[1].run(wiring.get_stage_inputs(1).val)

	wiring = wiring.bind_stage(1, res.val)

	res_num_to_pow = wiring.bound_intermediate_outputs[1].get_by_local("result")
	assert res_num_to_pow.has_val

	num_to_pow = res_num_to_pow.val
	assert (
		num_to_pow.wire_name == Some("my_res")
		and num_to_pow.local_name == "result"
		and num_to_pow.is_bound
		and num_to_pow.val.val == random_num.val.val**2
	)

	assert wiring.get_outputs() == Okay(
		VariableSet(
			(
				BoundVariable("my_res", random_num.val.val**2),
				BoundVariable("my_x", random_num.val.val),
			)
		)
	)

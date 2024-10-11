from exseos.types.Option import Some
from exseos.types.Result import Result, Okay
from exseos.types.Variable import BoundVariable, UnboundVariable, VariableSet
from exseos.workflow.stage.Stage import Stage
from exseos.workflow.wiring.Wiring import Wiring

import pytest
import random


class RaiseToPower(Stage):
	input_vars = (
		UnboundVariable("x", int, "Int to raise to ``pow``.", 0),
		UnboundVariable("pow", int, "Power to raise ``x`` to.", 1),
	)
	output_vars = (
		UnboundVariable("result", int, "``x`` raised to the ``pow`` power."),
	)

	def run(self, inputs: VariableSet) -> Result:
		res = inputs.check_all()
		if res.is_fail:
			return res

		return Okay((self.output_vars[0].bind(inputs.x**inputs.p),))


class MakeBase(Stage):
	input_vars = ()
	output_vars = (UnboundVariable("x", int, "A random number between 1 and 100"),)

	def run(self, inputs: VariableSet) -> Result:
		return Okay((self.output_vars[0].bind(random.randint(1, 100)),))


@pytest.mark.xfail
def test_wire_real_sequence():
	sequence = (MakeBase().to("my_x"), RaiseToPower("my_x", "my_pow").to("my_res"))

	input_vars = (UnboundVariable("my_pow"),)

	output_vars = (UnboundVariable("my_res"), UnboundVariable("my_x"))

	wiring = Wiring.wire(input_vars, output_vars, sequence)

	wiring = wiring.bind_inputs((BoundVariable("my_pow", 2),))

	assert wiring.get_stage_inputs(0) == Okay(VariableSet(()))

	# print(sequence[0].run(wiring.get_stage_inputs(0).val))

	wiring = wiring.bind_stage(0, sequence[0].run(wiring.get_stage_inputs(0).val).val)

	res_random_num = wiring.bound_intermediate_outputs[0].get_by_local("x")
	assert res_random_num.has_val

	random_num = res_random_num.val
	assert random_num.wire_name == Some("my_x")
	assert random_num.local_name == "x"
	assert random_num.is_bound
	assert type(random_num.val.val) is int

	assert wiring.get_stage_inputs(1) == Okay(
		VariableSet((BoundVariable("x", random_num.val.val), BoundVariable("pow", 2)))
	)

	wiring = wiring.bind_stage(1, sequence[1].run(wiring.get_stage_inputs(1).val).val)

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

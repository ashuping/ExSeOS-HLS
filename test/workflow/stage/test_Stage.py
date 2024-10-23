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

from exseos.types.Option import Some
from exseos.types.Result import Result, Okay
from exseos.types.Variable import UnboundVariable, VariableSet
from exseos.ui.NullUIManager import NullUIManager
from exseos.ui.UIManager import UIManager
from exseos.workflow.stage.Stage import Stage


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


def test_init():
	s = RaiseToPower("my_x", "my_pow").to("my_result")

	assert s.input_vars == (
		UnboundVariable("x", int, "Int to raise to ``pow``.", 0),
		UnboundVariable("pow", int, "Power to raise ``x`` to.", 1),
	)
	assert s.output_vars == (
		UnboundVariable("result", int, "``x`` raised to the ``pow`` power."),
	)

	assert s._input_bindings == (
		(
			UnboundVariable("x", int, "Int to raise to ``pow``.", 0),
			Some(UnboundVariable("my_x")),
		),
		(
			UnboundVariable("pow", int, "Power to raise ``x`` to.", 1),
			Some(UnboundVariable("my_pow")),
		),
	)

	assert s._output_bindings == (
		(
			UnboundVariable("result", int, "``x`` raised to the ``pow`` power."),
			Some(UnboundVariable("my_result")),
		),
	)


def test_flags():
	s = RaiseToPower("my_x", "my_pow").to("my_result")

	assert not s._is_always_run
	assert s.always_run()._is_always_run

	assert not s._is_implicit
	assert s.bind_implicitly()._is_implicit


def test_depends_provides():
	s = RaiseToPower("my_x", "my_pow").to("my_result")

	assert s._dependencies == ()
	assert s.depends("test_A")._dependencies == ("test_A",)
	assert s.depends("test_A", "test_B")._dependencies == ("test_A", "test_B")
	assert s.depends("test_A").depends("test_B")._dependencies == ("test_A", "test_B")

	assert s._providers == ()
	assert s.provides("test_A")._providers == ("test_A",)
	assert s.provides("test_A", "test_B")._providers == ("test_A", "test_B")
	assert s.provides("test_A").provides("test_B")._providers == ("test_A", "test_B")

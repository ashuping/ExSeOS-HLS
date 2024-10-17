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
from exseos.types.Result import Fail
from exseos.types.Variable import VariableSet, UnboundVariable
from exseos.ui.UIManager import UIManager
from exseos.ui.message.UIMessage import BasicNotice
from exseos.workflow.stage.Stage import Stage

from typing import Any


class DisplayVal(Stage):
	input_vars = (
		UnboundVariable("val", Any, "The value to display"),
		UnboundVariable("name", str, "The name of the val to display", Some("")),
	)
	output_vars = ()

	async def run(self, inputs: VariableSet, ui: UIManager):
		stat = inputs.check_all()
		if stat.is_fail:
			return stat

		try:
			return await ui.display(
				BasicNotice(
					"[DisplayVal] " + " {inputs.name}"
					if inputs.name
					else "" + str(inputs.val)
				)
			)

		except Exception as e:
			return Fail([e])

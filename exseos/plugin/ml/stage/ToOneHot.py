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

from exseos.types.Result import Okay
from exseos.types.Variable import VariableSet, UnboundVariable
from exseos.workflow.stage.Stage import Stage

import numpy as np


class ToOneHot(Stage):
	input_vars = (
		UnboundVariable("y", np.array, "The y-data to convert to one-hot."),
		UnboundVariable(
			"num_classes",
			int,
			"The number of classes in `y`. If not provided, it will be "
			+ "inferred. from `y`.",
			-1,
		),
	)
	output_vars = (UnboundVariable("y_onehot", np.array, "y-data as one-hot"),)

	async def run(self, inputs: VariableSet, _):
		stat = inputs.check_all()
		if stat.is_fail:
			return stat

		if inputs.num_classes <= 0:
			num_classes = np.max(inputs.y) + 1
		else:
			num_classes = inputs.num_classes

		y_reshape = inputs.y.reshape(-1, 1)

		y_onehot = np.eye(num_classes)[y_reshape].reshape(
			inputs.y.shape[0], num_classes
		)

		return Okay((self.output_vars[0].bind(y_onehot),))

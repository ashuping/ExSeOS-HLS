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

from exseos.types.Result import Okay, Fail
from exseos.types.Variable import VariableSet, UnboundVariable
from exseos.workflow.stage.Stage import Stage

import numpy as np
from sklearn.preprocessing import LabelEncoder


class ApplyLabelEncoder(Stage):
	input_vars = (
		UnboundVariable("y", np.array, "The labels to encode."),
		UnboundVariable(
			"encoder_to_use",
			LabelEncoder,
			(
				"[Optional] A pre-trained encoder to use. If not provided, an "
				+ "encoder will be trained on the input data."
			),
		),
	)
	output_vars = (
		UnboundVariable("y_encoded", np.array, "y encoded by encoder_to_use"),
		UnboundVariable(
			"trained_encoder",
			LabelEncoder,
			(
				"The trained encoder. If encoder_to_use was provided, then "
				+ "this will be the same as encoder_to_use; otherwise, it will "
				+ "be a new encoder trained on y."
			),
		),
	)

	async def run(self, inputs: VariableSet, _):
		stat = inputs.check("y")
		if stat.is_fail:
			return stat

		try:
			if inputs.check("encoder_to_use").is_fail:
				encoder: LabelEncoder = LabelEncoder()
				encoder.fit(inputs.y)
			else:
				encoder: LabelEncoder = inputs.scaler_to_use

			y_scaled = encoder.transform(inputs.y)

			return Okay(
				(self.output_vars[0].bind(y_scaled), self.output_vars[1].bind(encoder))
			)
		except Exception as e:
			return Fail([e])

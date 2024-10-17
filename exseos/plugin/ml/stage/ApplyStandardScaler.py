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
from sklearn.preprocessing import StandardScaler


class ApplyStandardScaler(Stage):
	input_vars = (
		UnboundVariable("X", np.array, "The data to scale."),
		UnboundVariable(
			"scaler_to_use",
			StandardScaler,
			(
				"[Optional] A pre-trained scaler to use. If not provided, a "
				+ "scaler will be trained on the input data."
			),
		),
	)
	output_vars = (
		UnboundVariable("X_scaled", np.array, "X scaled by scaler_to_use"),
		UnboundVariable(
			"trained_scaler",
			StandardScaler,
			(
				"The trained scaler. If scaler_to_use was provided, then this "
				+ "will be the same as scaler_to_use; otherwise, it will be a "
				+ "new scaler trained on X."
			),
		),
	)

	async def run(self, inputs: VariableSet, _):
		stat = inputs.check("X")
		if stat.is_fail:
			return stat

		try:
			if inputs.check("scaler_to_use").is_fail:
				scaler: StandardScaler = StandardScaler()
				scaler = scaler.fit(inputs.X)
			else:
				scaler: StandardScaler = inputs.scaler_to_use

			X_scaled = scaler.transform(inputs.X, copy=True)

			return Okay(
				(self.output_vars[0].bind(X_scaled), self.output_vars[1].bind(scaler))
			)
		except Exception as e:
			return Fail([e])

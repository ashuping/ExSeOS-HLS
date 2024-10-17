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
from exseos.types.Result import Okay, Fail
from exseos.types.Variable import VariableSet, UnboundVariable
from exseos.workflow.stage.Stage import Stage

from keras import Model
from tensorflow.data import Dataset
from tensorflow import Tensor
import numpy as np
from sklearn.metrics import accuracy_score


class EvalKerasModel(Stage):
	input_vars = (
		UnboundVariable("model", Model, "The model to train."),
		UnboundVariable(
			"X",
			np.ndarray | Tensor | dict[str, np.ndarray | Tensor] | Dataset,
			"Test data.",
			default=Some(None),
		),
		UnboundVariable(
			"y", np.ndarray | Tensor, "Test data labels", default=Some(None)
		),
		UnboundVariable("batch_size", int | None, default=Some(None)),
	)
	output_vars = (
		UnboundVariable("accuracy", np.array, "Model accuracy score"),
		UnboundVariable("predictions", desc="Model-generated predictions"),
	)

	async def run(self, inputs: VariableSet, _):
		stat = inputs.check_all()
		if stat.is_fail:
			return stat

		try:
			y_predicted = inputs.model.predict(inputs.X, batch_size=inputs.batch_size)

			accuracy = accuracy_score(
				np.argmax(inputs.y, axis=1), np.argmax(y_predicted, axis=1)
			)

			return Okay(
				(
					self.output_vars[0].bind(accuracy),
					self.output_vars[1].bind(y_predicted),
				)
			)

		except Exception as e:
			return Fail([e])

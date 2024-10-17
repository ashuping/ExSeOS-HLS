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
from keras.callbacks import Callback
from tensorflow.data import Dataset
from tensorflow import Tensor
import numpy as np


class TrainKerasModel(Stage):
	input_vars = (
		UnboundVariable("model", Model, "The model to train."),
		UnboundVariable(
			"X",
			np.ndarray | Tensor | dict[str, np.ndarray | Tensor] | Dataset,
			"Training data.",
			default=Some(None),
		),
		UnboundVariable(
			"y", np.ndarray | Tensor, "Training data labels", default=Some(None)
		),
		UnboundVariable("batch_size", int | None, default=Some(None)),
		UnboundVariable("epochs", int, default=1),
		UnboundVariable("verbose", int | str, default="auto"),
		UnboundVariable("callbacks", list[Callback] | None, default=Some(None)),
		UnboundVariable("validation_split", float, default=0.0),
		UnboundVariable(
			"validation_data",
			tuple[np.ndarray | Tensor, np.ndarray | Tensor]
			| tuple[np.ndarray, np.ndarray, np.ndarray]
			| None,
			default=Some(None),
		),
		UnboundVariable("shuffle", bool, default=True),
	)
	output_vars = (
		UnboundVariable("model", np.array, "Trained model"),
		UnboundVariable("History", desc="Model training history"),
	)

	async def run(self, inputs: VariableSet, _):
		stat = inputs.check_all()
		if stat.is_fail:
			return stat

		try:
			history = inputs.model.fit(
				inputs.X,
				inputs.y,
				batch_size=inputs.batch_size,
				epochs=inputs.epochs,
				verbose=inputs.verbose,
				callbacks=inputs.callbacks,
				validation_split=inputs.validation_split,
				validation_data=inputs.validation_data,
				shuffle=inputs.shuffle,
			)

			return Okay(
				(
					self.output_vars[0].bind(inputs.model),
					self.output_vars[1].bind(history),
				)
			)

		except Exception as e:
			return Fail([e])

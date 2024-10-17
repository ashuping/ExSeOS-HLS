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

import numpy as np
from numpy.random import RandomState
from sklearn.model_selection import train_test_split


class TrainTestSplit(Stage):
	input_vars = (
		UnboundVariable("X", np.ndarray, "The data to split."),
		UnboundVariable("y", np.ndarray, "Labels for X"),
		UnboundVariable("test_size", float | int | None, default=Some(None)),
		UnboundVariable("train_size", float | int | None, default=Some(None)),
		UnboundVariable("random_state", int | RandomState | None, default=Some(None)),
		UnboundVariable("shuffle", bool, default=True),
		UnboundVariable("stratify", np.ndarray | None, default=None),
	)
	output_vars = (
		UnboundVariable("X_train", np.ndarray, "Training data"),
		UnboundVariable("X_test", np.ndarray, "Test data"),
		UnboundVariable("y_train", np.ndarray, "Labels for training data"),
		UnboundVariable("y_test", np.ndarray, "Labels for test data"),
	)

	async def run(self, inputs: VariableSet, _):
		stat = inputs.check_all()
		if stat.is_fail:
			return stat

		try:
			X_tr, X_te, y_tr, y_te = train_test_split(
				inputs.X,
				inputs.y,
				test_size=inputs.test_size,
				train_size=inputs.train_size,
				random_state=inputs.random_state,
				shuffle=inputs.shuffle,
				stratify=inputs.stratify,
			)

			return Okay(
				(
					self.output_vars[0].bind(X_tr),
					self.output_vars[1].bind(X_te),
					self.output_vars[2].bind(y_tr),
					self.output_vars[3].bind(y_te),
				)
			)

		except Exception as e:
			return Fail([e])

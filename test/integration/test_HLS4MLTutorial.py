# """
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
# """

from exseos.types.Variable import (
	constant,
)

from exseos.experiment.Experiment import MakeExperiment
from exseos.experiment.optimizer.GridOptimizer import GridOptimizer
from exseos.experiment.optimizer.OptimizerParameter import (
	DiscreteOptimizerParamter,
)
from exseos.experiment.optimizer.OptimizerTarget import TargetMaximize, TargetMinimize
from exseos.workflow.Workflow import MakeWorkflow
from exseos.workflow.stage.StageFromFunction import make_StageFromFunction
from exseos.ui.terminal.TerminalUIManager import TerminalUIManager


import pytest
import numpy as np
from sklearn.datasets import fetch_openml


@pytest.mark.asyncio
@pytest.mark.long
@pytest.mark.needs_vendor_tools
async def test_hls4ml_tutorial():
	from exseos.plugin.ml.stage.ApplyStandardScaler import ApplyStandardScaler
	from exseos.plugin.ml.stage.ApplyLabelEncoder import ApplyLabelEncoder
	from exseos.plugin.ml.stage.ToOneHot import ToOneHot
	from exseos.plugin.ml.stage.TrainTestSplit import TrainTestSplit
	from exseos.plugin.ml.stage.TrainKerasModel import TrainKerasModel
	from exseos.plugin.ml.stage.EvalKerasModel import EvalKerasModel
	from exseos.plugin.hls4ml.stage.ConvertKerasModel import (
		ConvertKerasModel as HLS4ML_ConvertKerasModel,
	)
	from exseos.plugin.hls4ml.stage.EvalModel import EvalModel as HLS4ML_EvalModel
	from exseos.plugin.hls4ml.stage.SynthModel import SynthModel as HLS4ML_SynthModel
	from exseos.plugin.hls4ml.stage.ParseVivadoReport import (
		ParseVivadoReport as HLS4ML_ParseVivadoReport,
	)
	from exseos.ui.stage.DisplayVal import DisplayVal
	from keras import Model

	def fetch_dataset() -> tuple[np.ndarray, np.ndarray]:
		data = fetch_openml("hls4ml_lhc_jets_hlf")
		return (data["data"], data["target"])

	def build_my_model(layer_1_size: int) -> Model:
		import keras.models
		import keras.layers
		import keras.regularizers

		model = keras.models.Sequential()
		model.add(
			keras.layers.Dense(
				layer_1_size,
				input_shape=(16,),
				name="fc1",
				kernel_initializer="lecun_uniform",
				kernel_regularizer=keras.regularizers.l1(0.0001),
			)
		)
		model.add(keras.layers.Activation("relu", name="relu1"))

		model.add(
			keras.layers.Dense(
				32,
				name="fc2",
				kernel_initializer="lecun_uniform",
				kernel_regularizer=keras.regularizers.l1(0.0001),
			)
		)
		model.add(keras.layers.Activation("relu", name="relu2"))

		model.add(
			keras.layers.Dense(
				32,
				name="fc3",
				kernel_initializer="lecun_uniform",
				kernel_regularizer=keras.regularizers.l1(0.0001),
			)
		)
		model.add(keras.layers.Activation("relu", name="relu3"))

		model.add(
			keras.layers.Dense(
				5,
				name="output",
				kernel_initializer="lecun_uniform",
				kernel_regularizer=keras.regularizers.l1(0.0001),
			)
		)
		model.add(keras.layers.Activation("softmax", name="softmax"))

		return model

	FetchDataset = make_StageFromFunction(fetch_dataset, ("X", "y"))
	BuildMyModel = make_StageFromFunction(build_my_model, ("model",))

	tutorial_workflow = (
		MakeWorkflow("HLS4ML Tutorial Model")
		.given("batch_size", "layer_1_size", "work_dir")
		.from_stages(
			FetchDataset().to("X", "y"),
			ApplyStandardScaler("X").to("X"),
			ApplyLabelEncoder("y").to("y"),
			ToOneHot("y").to("y"),
			TrainTestSplit("X", "y", test_size=0.2, random_state=constant(42)).to(
				"X_tr", "y_tr", "X_te", "y_te"
			),
			BuildMyModel().to("my_model"),
			TrainKerasModel("my_model", "X_tr", "y_tr").to("trained_model"),
			EvalKerasModel("trained_model", "X_te", "y_te").to("accuracy"),
			DisplayVal("accuracy", constant("Soft accuracy: ")),
			HLS4ML_ConvertKerasModel(
				"trained_model",
				output_dir="work_dir",
				part=constant("xcu250-figd2104-2L-e"),
				backend=constant("Vitis"),
			).to("hls4ml_model", "config"),
			DisplayVal("config", constant("HLS config: ")),
			HLS4ML_EvalModel("hls4ml_model", "X_te", "y_te").to("hls_accuracy"),
			DisplayVal("hls_accuracy", constant("HLS accuracy: ")),
			HLS4ML_SynthModel(
				"hls4ml_model", backend_kwargs=constant({"csim": False})
			).provides("synthesis_data"),
			HLS4ML_ParseVivadoReport("work_dir")
			.depends("synthesis_data")
			.to(
				LUT="synth_luts",
				WorstLatency="synth_worst_latency",
				FF="synth_ffs",
				report="report",
			),
			DisplayVal("report", constant("Report: ")),
		)
		.output_to(
			"synth_worst_latency", "synth_luts", "synth_ffs", "accuracy", "hls_accuracy"
		)()
	)

	ui = TerminalUIManager()

	my_experiment = (
		MakeExperiment("Test batch size")
		.from_workflow(tutorial_workflow)
		.with_ui(ui)
		.calculate(
			work_dir=(
				lambda bs, l1: f"work/bs_exp_{bs}_l1{l1}",
				("batch_size", "layer_1_size"),
			)
		)
		.optimize(
			GridOptimizer(
				params=(
					DiscreteOptimizerParamter("batch_size", [512, 1024, 2048]),
					DiscreteOptimizerParamter("layer_1_size", [16, 32, 64, 96]),
				),
				targets=(
					TargetMaximize("accuracy", 0.0, 100.0),
					TargetMaximize("hls_accuracy", 0.0, 100.0),
					TargetMinimize("synth_luts", 30000, 60000),
					TargetMinimize("synth_ffs", 6000, 9000),
					TargetMinimize("synth_worst_latency", 0, 20),
				),
				grid_size=(3, 4),
			)
		)()
	)

	end_result = await my_experiment.run()

	from exseos.ui.message.UIMessage import ResultMessage

	await ui.display(ResultMessage(end_result))

	assert end_result.is_okay

	best_iteration = end_result.val.get_best(1)[0]

	print(best_iteration)

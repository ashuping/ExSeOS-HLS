# # """
# # ExSeOS-H Hardware ML Workflow Manager
# # Copyright (C) 2024  Alexis Maya-Isabelle Shuping

# # This program is free software: you can redistribute it and/or modify
# # it under the terms of the GNU General Public License as published by
# # the Free Software Foundation, either version 3 of the License, or
# # (at your option) any later version.

# # This program is distributed in the hope that it will be useful,
# # but WITHOUT ANY WARRANTY; without even the implied warranty of
# # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# # GNU General Public License for more details.

# # You should have received a copy of the GNU General Public License
# # along with this program.  If not, see <https://www.gnu.org/licenses/>.
# # """

# from exseos.types.Variable import (
# 	Variable,
# 	UnboundVariable,
# 	UnboundVariableError,
# 	constant,
# 	VariableSet,
# )

# from exseos.experiment.optimizer.GridOptimizer import GridOptimizer
# from exseos.experiment.optimizer.OptimizerParameter import ContinuousOptimizerParameter, DiscreteOptimizerParamter
# from exseos.experiment.optimizer.OptimizerTarget import TargetMaximize
# from exseos.types.Result import Result, Okay, Warn, Fail
# from exseos.workflow.Workflow import MakeWorkflow
# from exseos.workflow.stage.Stage import Stage
# from exseos.workflow.stage.StageFromFunction import make_StageFromFunction


# import pytest


# class FetchDataset(Stage):
# 	"""
# 	Fetches a dataset and saves it to a provided path.

# 	If ``save_location`` already exists and ``force`` is False (the default),
# 	then the file will not be re-downloaded.
# 	"""

# 	input_vars = (
# 		UnboundVariable("dataset_name", var_type=str),
# 		UnboundVariable("save_location", var_type=str),
# 		UnboundVariable("force", var_type=bool, default=False),
# 	)

# 	def run(self, inputs: VariableSet) -> Result[Exception, Exception, VariableSet]:
# 		res = inputs.check_all()
# 		if res.is_fail:
# 			return res

# 		from sklearn.datasets import fetch_openml
# 		import numpy as np
# 		import os.path

# 		if os.path.isfile(inputs.save_location) or inputs.force is True:
# 			try:
# 				data = fetch_openml(inputs.dataset_name)
# 				with open(inputs.save_location, "w") as save_f:
# 					np.save(save_f, data)
# 			except Exception as e:
# 				res <<= Fail([e])

# 		return res

# def my_test():
# 	pass

# @pytest.mark.xfail
# @pytest.mark.long
# def test_hls4ml_tutorial():

# 	from keras import Model
# 	def build_my_model() -> Model:
# 		import keras.models
# 		import keras.layers
# 		import keras.regularizers

# 		model = keras.models.Sequential()
# 		model.add(
# 			keras.layers.Dense(
# 				64,
# 				input_shape=(16,),
# 				name='fc1',
# 				kernel_initializer='lecun_uniform',
# 				kernel_regularizer=keras.regularizers.l1(0.0001)
# 			)
# 		)
# 		model.add(keras.layers.Activation('relu', name='relu1'))

# 		model.add(
# 			keras.layers.Dense(
# 				32,
# 				name='fc2',
# 				kernel_initializer='lecun_uniform',
# 				kernel_regularizer=keras.regularizers.l1(0.0001)
# 			)
# 		)
# 		model.add(keras.layers.Activation('relu', name='relu2'))

# 		model.add(
# 			keras.layers.Dense(
# 				32,
# 				name='fc3',
# 				kernel_initializer='lecun_uniform',
# 				kernel_regularizer=keras.regularizers.l1(0.0001)
# 			)
# 		)
# 		model.add(keras.layers.Activation('relu', name='relu3'))

# 		model.add(
# 			keras.layers.Dense(
# 				5,
# 				name='output',
# 				kernel_initializer='lecun_uniform',
# 				kernel_regularizer=keras.regularizers.l1(0.0001)
# 			)
# 		)
# 		model.add(keras.layers.Activation('softmax', name='softmax'))

# 		return model

# 	BuildMyModel = make_StageFromFunction(build_my_model, ('model',))

# 	test_Workflow = (
# 		MakeWorkflow("HLS4ML Tutorial Model")
# 		.given("batch_size", "input_file", "work_dir")
# 		.from_stages(
# 			FetchDataset(
# 				constant("hls4ml_lhc_jets_hlf"),
# 				"input_file"
# 			)
# 				.provides("dset_file"),
# 			BuildMyModel().to('my_model'),
# 			LoadNumpyAsTFDataset("input_file")
# 				.to("input_data")
# 				.requires("dset_file"),
# 			Demodulate("input_data").to(demodulated_input="input_data"),
# 			ToOneHot("input_data").to("input_data"),
# 			SplitTrainTest("input_data").to("train_data", "test_data"),
# 			BuildModel().to("model"),
# 			TrainKerasModel("model", "train_data", batch_size="batch_size").to(
# 				"trained_model"
# 			),
# 			EvalKerasModel("trained_model", "test_data").to(
# 				accuracy="model_overall_accuracy",
# 				loss="model_overall_loss",
# 				predicted="eval_pred",
# 				actual="eval_actual",
# 			),
# 			ExtractPerQubitAccuracies("eval_pred", "eval_actual").to(
# 				"accuracy_per_qubit"
# 			),
# 			ConvertKerasModel(
# 				"model",
# 				prj_dir=UnboundVariable("work_dir").map(lambda l: f"{l}/hls4ml_prj"),
# 			).provides("hls4ml_output"),
# 			SynthesizeVitisModel(
# 				UnboundVariable("work_dir").map(lambda l: f"{l}/hls4ml_prj")
# 			)
# 			.depends("hls4ml_output")
# 			.provides("synthesized_model"),
# 			ExtractSynthRunData(
# 				UnboundVariable("work_dir").map(lambda l: f"{l}/hls4ml_prj")
# 			)
# 			.depends("synthesized_model")
# 			.to(
# 				ii="synth_ii",
# 				util_lut_pct="synth_luts",
# 				util_ff_pct="synth_ffs",
# 				util_bram_pct="synth_brams",
# 			),
# 		)
# 		.outputs(
# 			"synth_ii",
# 			"synth_luts",
# 			"synth_ffs",
# 			"model_overall_accuracy",
# 			"accuracy_per_qubit",
# 		)
# 		()
# 	)

# 	my_experiment = (
# 		MakeExperiment("Test batch size")
# 			.from_workflow(tutorial_workflow)
# 			.with_constants(
# 				input_file="data/qubit_dataset.npy"
# 			)
# 			.calculate(
# 				work_dir=(
# 					lambda bs: f"work/bs_exp_{bs}",
# 					('batch_size',)
# 				)
# 			)
# 			.optimize(
# 				GridOptimizer(
# 					params=(
# 						DiscreteOptimizerParamter(
# 							'batch_size',
# 							range(1, 2048)
# 						)
# 					),
# 					targets=(
# 						TargetMaximize(
# 							'accuracy',
# 							0.0,
# 							100.0
# 						)
# 					),
# 					grid_size=32
# 				)
# 			)
# 			()
# 	)

# 	end_result = my_experiment.run()

# 	best_iteration = end_result.get_best(1)[0]

# 	assert True

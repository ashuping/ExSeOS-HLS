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
from hls4ml.model import ModelGraph
from hls4ml.utils import config_from_keras_model
from hls4ml.converters import convert_from_keras_model


class ConvertKerasModel(Stage):
	input_vars = (
		UnboundVariable("model", Model, "The model to convert."),
		UnboundVariable("granularity", str, default="model"),
		UnboundVariable("default_precision", str, default="fixed<16,6>"),
		UnboundVariable("default_reuse_factor", int, default=1),
		UnboundVariable("output_dir", str, default="my-hls-test"),
		UnboundVariable("project_name", "myproject"),
		UnboundVariable("input_data_tb", str | None, default=Some(None)),
		UnboundVariable("output_data_tb", str | None, default=Some(None)),
		UnboundVariable("backend", str, "HLS4ML backend to use", default="Vivado"),
		UnboundVariable("board", str | None, default=Some(None)),
		UnboundVariable("part", str | None, default=Some(None)),
		UnboundVariable("io_type", str, default="io_parallel"),
		UnboundVariable("hls_config", dict | None, default=None),
	)
	output_vars = (
		UnboundVariable("hls_model", ModelGraph, "Converted model"),
		UnboundVariable("config", desc="Final HLS4ML-generated model configuration"),
	)

	async def run(self, inputs: VariableSet, _):
		stat = inputs.check_all()
		if stat.is_fail:
			return stat

		try:
			config = config_from_keras_model(
				inputs.model,
				inputs.granularity,
				inputs.backend,
				inputs.default_precision,
				inputs.default_reuse_factor,
			)

			hls_model = convert_from_keras_model(
				inputs.model,
				output_dir=inputs.output_dir,
				project_name=inputs.project_name,
				input_data_tb=inputs.input_data_tb,
				output_data_tb=inputs.output_data_tb,
				backend=inputs.backend,
				board=inputs.board,
				part=inputs.part,
				clock_period=inputs.clock_period,
				io_type=inputs.io_type,
				hls_config=inputs.hls_config,
			)

			return Okay(
				(self.output_vars[0].bind(hls_model), self.output_vars[1].bind(config))
			)

		except Exception as e:
			return Fail([e])

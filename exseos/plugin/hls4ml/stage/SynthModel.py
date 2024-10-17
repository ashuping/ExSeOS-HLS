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

from hls4ml.model import ModelGraph


class SynthModel(Stage):
	input_vars = (
		UnboundVariable("model", ModelGraph, "The model to synthesize."),
		UnboundVariable(
			"backend_kwargs", dict, "Arguments for individual backends", default={}
		),
	)
	output_vars = ()

	async def run(self, inputs: VariableSet, _):
		stat = inputs.check_all()
		if stat.is_fail:
			return stat

		try:
			inputs.model.build(**inputs.backend_kwargs)

			return Okay(())
		except Exception as e:
			return Fail([e])

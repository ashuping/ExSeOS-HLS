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
from hls4ml.report.vivado_report import parse_vivado_report


class ParseVivadoReport(Stage):
	input_vars = (
		UnboundVariable(
			"location", ModelGraph, "Location of the project to parse files for."
		),
	)
	output_vars = (
		UnboundVariable("report", dict),
		UnboundVariable("LUT", int),
		UnboundVariable("FF", int),
		UnboundVariable("WorstLatency", int),
	)

	async def run(self, inputs: VariableSet, _):
		stat = inputs.check_all()
		if stat.is_fail:
			return stat

		try:
			report = parse_vivado_report(inputs.location)

			luts = report["CSynthesisReport"]["LUT"]
			ffs = report["CSynthesisReport"]["FF"]
			worst_latency = report["CSynthesisReport"]["WorstLatency"]

			return Okay(
				(
					self.output_vars[0].bind(report),
					self.output_vars[1].bind(luts),
					self.output_vars[2].bind(ffs),
					self.output_vars[3].bind(worst_latency),
				)
			)
		except Exception as e:
			return Fail([e])

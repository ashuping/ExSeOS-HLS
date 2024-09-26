"""
Chicory ML Workflow Manager
Copyright (C) 2024  Alexis Maya-Isabelle Shuping

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from modules.data import DataStore
from modules.args.ArgumentProvider import ArgumentProvider
from modules.report.ReportProvider import ReportProvider
import logging


class WorkflowModule:
	def __init__(
		self,
		report: ReportProvider,
		log: logging.Logger,
	):
		self.report = report
		self.log = log

	def run(self, store: DataStore, args: ArgumentProvider):
		raise NotImplementedError

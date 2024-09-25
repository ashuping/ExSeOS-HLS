'''
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
'''

import logging
import random

from modules.data.Variable import Variable, UnboundVariable
from modules.types.Option import Nothing, Some

log = logging.get_logger(__name__)

class Workflow():
	''' Base class for Workflows.

	    Instead of instantiating this directly, use `MakeWorkflow`.
	'''
	def __init__(self, stages, inputs=[], outputs=[]):
		pass

class MakeWorkflow():
	''' Workflow factory. Use this class to construct a Workflow that can then
	    be instantiated.
	'''

	def __init__(self, name=None):
		if name is None:
			name = f'Unnamed Workflow {random.randrange(0, 999999):06}'
		
		self.name = name
		self.stages = []
		self.inputs = []
		self.outputs = []

	def given(self, *args, **kwargs):
		''' Add one or more inputs to the Workflow.

			Arguments should either be `Variable`s or strings. In the latter
			case, appropriate variables are created for the strings.

			Keyword arguments may be provided - these are interpreted as default
			values for the variable. For example, providing `my_var=1` creates a
			new `UnboundVariable` called `my_var` with a default value of `1`.

			Keyword argument names must, of course, be strings. To provide a
			pre-existing `Variable` with a default value, the default must be
			provided in the `Variable`'s instantiation
		'''
		for arg in args:
			if issubclass(type(arg), Variable):
				self.inputs.append(arg)
			elif type(arg) is str:
				self.inputs.append(UnboundVariable(arg))
			else:
				raise TypeError('Workflow inputs must be `Variable`s or strings.')

		for kwarg, kwdefault in kwargs.items():
			self.inputs.append(UnboundVariable(
				kwarg,
				default=Some(kwdefault)
			))

	def output(self, *args):
		''' Add one or more outputs to the Workflow.

			Arguments should either be `Variable`s or strings. In the latter
			case, wiring will search for the latest `Variable` with the provided
			name.
		'''
		for arg in args:
			if issubclass(type(arg), Variable):
				self.outputs.append(arg)
			elif type(arg) is str:
				self.outputs.append(UnboundVariable(arg))
			else:
				raise TypeError('Workflow outputs must be `Variable`s or strings.')

	def from_stages(self, *args):
		''' Add stages to the Workflow.
		'''
		self.stages = args

	def __call__(self, *args, **kwargs):
		''' Instantiate the Workflow and bind the provided arguments to its
		    inputs.
		'''
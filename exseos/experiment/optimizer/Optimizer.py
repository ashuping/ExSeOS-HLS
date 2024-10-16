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

"""
Base implementation for ``Experiment`` optimizers.
"""

from exseos.experiment.optimizer import OptimizerParameter
from exseos.types.Option import Nothing, Some
from exseos.types.Variable import VariableSet

from abc import ABC, abstractmethod
import logging

log = logging.getLogger(__name__)


class OptimizerIteration:
	"""
	Represents a set of ``Workflow`` inputs and their corresponding outputs.
	"""

	def __init__(self, inputs: VariableSet, outputs: VariableSet):
		self.__inputs = inputs
		self.__outputs = outputs

	@property
	def inputs(self) -> VariableSet:
		return self.__inputs

	@property
	def outputs(self) -> VariableSet:
		return self.__outputs

	def __str__(self) -> str:
		return (
			f"OptimizerIteration with inputs {self.inputs} "
			+ f" and outputs {self.outputs}."
		)

	def __repr__(self) -> str:
		return f"OptimizerIteration({self.inputs}, {self.outputs})"


class Optimizer(ABC):
	"""
	Base implementation for ``Experiment`` optimizers.

	An ``Optimizer`` generates sets of ``Workflow`` inputs, with the aim of
	optimizing for a specific output or set of outputs.
	"""

	def __init__(
		self,
		params: tuple[OptimizerParameter, ...],
		targets: tuple[OptimizerParameter, ...],
		max_iterations: int = -1,
	):
		self.__params = params
		self.__targets = targets
		self.__max_iterations = max_iterations

	@property
	def params(self) -> tuple[OptimizerParameter, ...]:
		return self.__params

	@property
	def targets(self) -> tuple[OptimizerParameter, ...]:
		return self.__targets

	@property
	def max_iterations(self) -> int:
		return self.__max_iterations

	@abstractmethod
	def next(
		self,
		iteration_num: int,
		batch_size: int,
		history: "tuple[OptimizerIteration]",
	) -> tuple[VariableSet]:
		"""
		Generate the inputs for the next optimizer pass in the sequence.

		Note that, for parallel ``Experiment`` runs, the ``Optimizer`` may be
		asked to generate more than one set of input parameters at once,
		represented as ``batch_size``. If supported, the ``Optimizer`` will
		return ``batch_size`` ``VariableSet`` objects for the next
		``batch_size`` iterations. However, some algorithms may not support
		batching, so the length of the return tuple may not be equal to
		``batch_size``.

		:param iteration_num: Iteration number to start from
		:param batch_size: The number of iterations to generate
		:param history: Inputs and outputs for each previous optimizer pass.
		:return: No fewer than one and no more than ``batch_size``
		    ``VariableSet`` objects, representing the inputs for the next
		    ``Workflow`` run(s).
		"""
		...  # pragma: no cover

	def get_best(
		self, history: "tuple[OptimizerIteration]", count: int = 1
	) -> "tuple[OptimizerIteration, ...]":
		"""
		Return the best ``count`` iterations, in descending order.

		If ``count`` is -1, then all iterations will be returned.
		"""

		def _calculate_target_score(it: OptimizerIteration) -> float:
			scores: list[float] = []
			vars = it.outputs.vars
			for target in self.targets:
				if target.var.name not in vars.keys():
					log.warning(
						f"Target variable {target.var.name} not found "
						+ "in stage outputs! Ignoring this optimization target."
					)
					continue

				var = vars[target.var.name].val
				match var:
					case Some(val):
						scores.append(
							(target.range_max - val)
							/ (target.range_max - target.range_min)
						)
					case Nothing():
						log.warning(
							f"Target variable {target.var.name} is unbound! "
							+ "Ignoring this optimization target."
						)
						continue

			return sum(scores) / len(scores)

		sorted_best = sorted(history, key=_calculate_target_score)

		return tuple(sorted_best[:count]) if count != -1 else tuple(sorted_best)

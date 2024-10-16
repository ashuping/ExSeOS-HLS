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

import itertools
from math import ceil
from exseos.experiment.optimizer.Optimizer import Optimizer, OptimizerIteration
from exseos.experiment.optimizer.OptimizerParameter import (
	OptimizerParameter,
	ContinuousOptimizerParameter,
	DiscreteOptimizerParamter,
)
from exseos.experiment.optimizer.OptimizerTarget import OptimizerTarget
from exseos.types.Variable import BoundVariable, VariableSet


class GridOptimizer(Optimizer):
	def __init__(
		self,
		params: tuple[OptimizerParameter, ...],
		grid_size: int | tuple[int, ...],
		targets: tuple[OptimizerTarget, ...],
		max_iterations: int = -1,
	):
		super().__init__(params, targets, max_iterations)

		def _iterable(obj: any) -> bool:
			try:
				iter(obj)
			except Exception:
				return False
			else:
				return True

		grid_size: tuple[int] = (
			grid_size if _iterable(grid_size) else [grid_size for _ in params]
		)  # Convert to tuple if `grid_size` is an int

		grid_size += [
			0 for _ in range(len(params) - len(grid_size))
		]  # Pad the length of `grid_size`

		# Limit to the number of discrete options, if applicable
		for dex, param in enumerate(params):
			match param:
				case DiscreteOptimizerParamter(_, opts):
					if len(opts) < grid_size[dex]:
						grid_size[dex] = len(opts)

		def _generate_points(
			p: OptimizerParameter, n_points: int
		) -> list[BoundVariable]:
			match p:
				case DiscreteOptimizerParamter(name, opts):
					if n_points >= len(opts):
						return opts
					step = ceil(len(opts) / n_points)
					picked = [
						BoundVariable(name, opt)
						for dex, opt in enumerate(opts)
						if dex % step == 0
					]

					if len(picked) < n_points:
						for _ in range(n_points - picked):
							for opt in opts:
								if opt not in picked:
									picked.append(BoundVariable(name, opt))
									break

					return picked
				case ContinuousOptimizerParameter(name, min, max):
					step = (max - min) / n_points
					picked = [
						BoundVariable(name, min + dex * step) for dex in range(n_points)
					]

					return picked

		param_points = [
			_generate_points(par, points) for par, points in zip(params, grid_size)
		]

		self.__grid = tuple([VariableSet(x) for x in itertools.product(*param_points)])

		if max_iterations > 0:
			self.__grid = self.__grid[:max_iterations]

	@property
	def grid(self) -> tuple[VariableSet, ...]:
		return self.__grid

	def next(
		self, iteration_num: int, batch_size: int, history: tuple[OptimizerIteration]
	) -> tuple[VariableSet]:
		ret_count = (
			batch_size
			if iteration_num + batch_size <= len(self.grid)
			else len(self.grid) - iteration_num
		)

		if ret_count <= 0:
			return ()

		return tuple(
			[self.grid[dex] for dex in range(iteration_num, iteration_num + ret_count)]
		)

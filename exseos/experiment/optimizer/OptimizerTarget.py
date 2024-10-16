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

from exseos.types.Variable import Variable, ensure_from_name

from abc import ABC


class OptimizerTarget(ABC):
	"""
	A target for optimization
	"""

	__match_args__ = ("var", "range_min", "range_max")

	def __init__(self, var: Variable | str, range_min: float, range_max: float):
		self.__var = ensure_from_name(var)
		self.__range_min = range_min
		self.__range_max = range_max

	@property
	def var(self) -> Variable:
		return self.__var

	@property
	def range_min(self) -> float:
		return self.__range_min

	@property
	def range_max(self) -> float:
		return self.__range_max


class TargetMaximize(OptimizerTarget):
	"""
	Indicates that the ``Variable`` should be made as high as possible.
	"""

	__match_args__ = ("var", "range_min", "range_max")
	pass


class TargetMinimize(OptimizerTarget):
	"""
	Indicates that the ``Variable`` should be made as low as possible.
	"""

	__match_args__ = ("var", "range_min", "range_max")
	pass


class TargetCloseTo(OptimizerTarget):
	"""
	Indicates that the ``Variable`` should be made as close to a specific number
	as possible.
	"""

	__match_args__ = ("var", "target", "range_min", "range_max")

	def __init__(
		self,
		var: Variable | str,
		target: float | int,
		range_min: float,
		range_max: float,
	):
		super().__init__(var, range_min, range_max)
		self.__target = target

	@property
	def target(self) -> float | int:
		return self.__target

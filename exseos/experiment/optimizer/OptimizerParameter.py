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

from abc import ABC
from typing import TypeVar

A = TypeVar("A")


class OptimizerParameter(ABC):
	"""
	A paramter to provide to an ``Optimizer``.
	"""

	def __init__(self, name: str):
		self.__name = name

	@property
	def name(self) -> str:
		return self.__name


class DiscreteOptimizerParamter(OptimizerParameter):
	"""
	An optimizer parameter that takes one of a discrete series of options.
	"""

	__match_args__ = (
		"name",
		"options",
	)

	def __init__(self, name: str, options: tuple[A]):
		super().__init__(name)
		self.__options = options

	@property
	def options(self) -> tuple[A]:
		return self.__options


class ContinuousOptimizerParameter(OptimizerParameter):
	"""
	An optimizer paramter that can be selected from a continuum. Generally only
	used for numeric types. ``min`` is inclusive; ``max`` is exclusive.
	"""

	__match_args__ = ("name", "min", "max")

	def __init__(self, name: str, min: A, max: A):
		super().__init__(name)
		self.__min = min
		self.__max = max

	@property
	def min(self) -> A:
		return self.__min

	@property
	def max(self) -> A:
		return self.__max

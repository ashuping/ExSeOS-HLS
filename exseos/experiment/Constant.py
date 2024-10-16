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
from typing import Any, Callable, TypeVar

from exseos.types.Option import Option
from exseos.types.Variable import VariableSet

A = TypeVar("A")


class ExperimentConstant[A](ABC):
	@property
	def name(self) -> str: ...  # pragma: no cover

	def can_resolve(self, vars: VariableSet) -> bool: ...  # pragma: no cover

	def resolve(self, vars: VariableSet) -> A: ...  # pragma: no cover


class BasicExperimentConstant[A](ExperimentConstant):
	def __init__(self, name: str, val: A):
		self.__name = name
		self.__val = val

	@property
	def name(self) -> str:
		return self.__name

	def can_resolve(self, _) -> bool:
		return True

	def resolve(self, _) -> A:
		return self.__val


class LambdaExperimentConstant[A](ExperimentConstant):
	def __init__(self, name: str, fn: Callable[[VariableSet], Option[Any]]):
		self.__name = name
		self.__fn = fn

	@property
	def name(self) -> str:
		return self.__name

	def can_resolve(self, vars: VariableSet) -> bool:
		return self.__fn(vars).has_val

	def resolve(self, vars: VariableSet) -> Any:
		return self.__fn(vars).val

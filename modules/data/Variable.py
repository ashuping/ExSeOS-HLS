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
from modules.types.Option import Option, Nothing

from typing import TypeVar
from abc import ABC, abstractmethod

A = TypeVar("A")

class Variable[A](ABC):
	''' Stores a quantity whose value can vary from workflow to workflow,
		controlled either statically (manually set in configuration) or
		dynamically (controlled by an optimizer)
	'''
	@property
	@abstractmethod
	def is_bound(self) -> bool:
		''' `True` iff this variable has been bound to a value.

			Note that `Variable.val` will only return a value if the variable is
			bound; otherwise, a `TypeError` will be raised.
		'''
		... # pragma: no cover

	@property
	@abstractmethod
	def name(self) -> str:
		''' The name of this Variable.
		'''
		... # pragma: no cover

	@property
	@abstractmethod
	def desc(self) -> Option[str]:
		''' An optional long-form description for this Variable.
		'''
		... # pragma: no cover

	@property
	@abstractmethod
	def val(self) -> A:
		''' The bound value of this Variable. Only exists if `is_bound` is True;
			otherwise, a `TypeError` will be raised.
		'''
		... # pragma: no cover

	@property
	@abstractmethod
	def var_type(self) -> Option[type]:
		''' Optional type annotation for this Variable.
		'''
		... # pragma: no cover

	@property
	@abstractmethod
	def default(self) -> Option[A]:
		''' Optional default value for this Variable.
		'''
		... # pragma: no cover

	@abstractmethod
	def bind(self, val: A) -> 'BoundVariable[A]':
		''' Bind a value to this Variable. 
		'''
		... # pragma: no cover

	def __eq__(self, other: 'Variable') -> bool:
		return all([
			self.name == other.name,
			self.is_bound == other.is_bound,
			self.desc == other.desc,
			(self.val == other.val) if self.is_bound else True,
			self.var_type == other.var_type,
			self.default == other.default
		])

class BoundVariable[A](Variable):
	''' A Variable that has already been given a value.
	'''
	def __init__(self, name: str, val: A, var_type: Option[type] = Nothing(), desc: Option[str] = Nothing(), default: Option[A] = Nothing()):
		self.__name = name
		self.__val = val
		self.__type = var_type
		self.__desc = desc
		self.__default = default

	@property
	def is_bound(self) -> bool:
		return True

	@property
	def name(self) -> str:
		return self.__name
	
	@property
	def desc(self) -> Option[str]:
		return self.__desc

	@property
	def val(self) -> A:
		return self.__val

	@property
	def var_type(self) -> Option[type]:
		return self.__type

	@property
	def default(self) -> Option[A]:
		return self.__default

	def bind(self, val: A) -> 'BoundVariable[A]':
		return BoundVariable(
			self.name, val, self.var_type, self.desc, self.default
		)

	def __str__(self) -> str:
		return ''.join([
			'BoundVariable',
			f'[{self.var_type.val.__name__}]' if self.var_type != Nothing() else '',
			f' {self.name}',
			f' = {self.val}',
			f' (default {self.default.val})' if self.default != Nothing() else '',
			f': {self.desc.val}' if self.desc != Nothing() else ''
		])


class UnboundVariable[A](Variable):
	''' A Variable which has not yet been given a value.
	'''
	def __init__(self, name: str, var_type: Option[type] = Nothing(), desc: Option[str] = Nothing(), default: Option[A] = Nothing()):
		self.__name    = name
		self.__type    = var_type
		self.__desc    = desc
		self.__default = default

	@property
	def is_bound(self) -> bool:
		return False

	@property
	def name(self) -> str:
		return self.__name

	@property
	def desc(self) -> Option[str]:
		return self.__desc

	@property
	def val(self) -> A:
		raise TypeError("Tried to access `val` on an unbound variable!")

	@property
	def var_type(self) -> Option[type]:
		return self.__type

	@property
	def default(self) -> Option[A]:
		return self.__default

	def bind(self, val: A) -> BoundVariable[A]:
		return BoundVariable(
			self.name, val, self.var_type, self.desc, self.default
		)

	def __str__(self) -> str:
		return ''.join([
			'UnboundVariable',
			f'[{self.var_type.val.__name__}]' if self.var_type != Nothing() else '',
			f' {self.name}',
			f' (default {self.default.val})' if self.default != Nothing() else '',
			f': {self.desc.val}' if self.desc != Nothing() else ''
		])
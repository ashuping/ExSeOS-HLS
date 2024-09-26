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


class BasicDataStore[T](DataStore):
	"""
	Basic data store that keeps all of its values in memory.
	"""

	def __init__(self, label: str):
		self.__label = label
		self.__data = {}

	@property
	def label(self) -> str:
		return self.__label

	def insert(self, label: str, t: T) -> bool:
		if label in self.__data.keys:
			return False
		else:
			self.__data[label] = t

	def __iter__(self):
		return self.__data.items()

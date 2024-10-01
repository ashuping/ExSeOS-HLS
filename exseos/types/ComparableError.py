"""
ExSeOS-H Hardware ML Workflow Manager
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

from typing import List


class ComparableError:
	"""Encapsulates an Exception, providing a sensible `__eq__` operation."""

	def __init__(self, exc: Exception):
		self.__exc = exc

	@property
	def exc(self):
		return self.__exc

	@classmethod
	def encapsulate(cls, exc: any):
		"""
		Encapsulate an Exception in a ComparableError.

		If this method is called on anything other than an Exception, the
		parameter is returned unchanged.
		"""
		if issubclass(type(exc), Exception):
			return cls(exc)
		else:
			return exc

	@classmethod
	def array_encapsulate(cls, arr: List[any]):
		"""
		Encapsulate an entire array of Exceptions

		This method is useful for performing array comparisons.
		"""
		return [ComparableError.encapsulate(e) for e in arr]

	def __eq__(self, other):
		"""
		Check whether the encapsulated Exceptions are equal.

		Two Exceptions are defined as equal if:
			- Both are of the same type
			- If one has an `args` attribute:
				- The other has an `args` attribute
				- The two `args` attributes evaluate to equal.
		"""
		other = ComparableError.encapsulate(other)  # ensure `other` is comparable

		if not isinstance(other, ComparableError):
			return False

		if type(self.exc) is not type(other.exc):
			return False

		if hasattr(self.exc, "args"):
			if not hasattr(other.exc, "args"):
				return False
			else:
				return self.exc.args == other.exc.args
		else:
			return True

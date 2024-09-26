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

from modules.types.ComparableError import ComparableError

from typing import TypeVar, Callable, List
from abc import ABC, abstractmethod

A = TypeVar("A")
B = TypeVar("B")
C = TypeVar("C")
D = TypeVar("D")


class Result[A, B, C](ABC):
	"""Represents the result of a computation.

	Can either be `Okay[C]`, `Warning[B, C]`, or `Error[A, B]`.

	`val` of type `C` represents the return type of the computation. It is
	present in `Okay` and `Warning` types, but not `Error` types.

	`warn` of type `B` represents non-fatal warnings. It is present in
	`Warning` and `Error` types, but not `Okay` types.

	`err` of type `A` represents fatal errors. It is only present in `Error`
	types.
	"""

	@property
	@abstractmethod
	def is_okay(self) -> bool:
		# True IFF the result is `Okay`.
		...  # pragma: no cover

	@property
	@abstractmethod
	def is_warning(self) -> bool:
		# True IFF the result is `Warning`
		...  # pragma: no cover

	@property
	@abstractmethod
	def is_error(self) -> bool:
		# True IFF the result is `Error`
		...  # pragma: no cover

	@property
	@abstractmethod
	def val(self) -> C:
		"""Return the result of the computation.

		This is present for `Okay` and `Warning` types. It is NOT present
		for `Error` types.
		"""
		...  # pragma: no cover

	@property
	@abstractmethod
	def warnings(self) -> List[B]:
		"""Return the list of warnings generated during the computation.

		This is present for `Warning` and `Error` types. It is NOT present
		for `Okay` types.
		"""
		...  # pragma: no cover

	@property
	@abstractmethod
	def errors(self) -> List[A]:
		"""Return the list of fatal errors generated during the computation.

		This is only present for `Error` types.
		"""
		...  # pragma: no cover

	@abstractmethod
	def map(self, f: Callable[[C], D]) -> "Result[A, B, D]":
		"""If this `Result` is `Okay` or `Warning`, call `f` on its value and
		return an `Okay` or `Warning` of the result.
		"""
		...  # pragma: no cover

	@abstractmethod
	def flat_map(self, f: Callable[[C], "Result[A, B, D]"]) -> "Result[A, B, D]":
		"""If this `Result` is `Okay` or `Warning`, call `f` on its value and
		return the output, which must itself be a `Result`.
		"""
		...  # pragma: no cover

	def __eq__(self, other):
		if not issubclass(type(other), Result):
			return False

		if self.is_okay:
			if not other.is_okay:
				return False

			return self.val == other.val

		elif self.is_warning:
			if not other.is_warning:
				return False

			if self.val != other.val:
				return False

			if len(self.warnings) != len(other.warnings):
				return False

			if ComparableError.array_encapsulate(
				self.warnings
			) != ComparableError.array_encapsulate(other.warnings):
				return False

			return True

		else:  # self.is_error
			if not other.is_error:
				return False

			if len(self.warnings) != len(other.warnings):
				return False

			if len(self.errors) != len(other.errors):
				return False

			if ComparableError.array_encapsulate(
				self.warnings
			) != ComparableError.array_encapsulate(other.warnings):
				return False

			if ComparableError.array_encapsulate(
				self.errors
			) != ComparableError.array_encapsulate(other.errors):
				return False

			return True


class Okay[C](Result):
	"""Represents a computation that has succeeded without any errors or warnings.

	Has a `val`, but no `warnings` or `errors`
	"""

	def __init__(self, val: C):
		self.__val = val

	@property
	def is_okay(self) -> bool:
		return True

	@property
	def is_warning(self) -> bool:
		return False

	@property
	def is_error(self) -> bool:
		return False

	@property
	def val(self) -> C:
		return self.__val

	@property
	def warnings(self) -> List[B]:
		raise TypeError("Can't return warnings from `Okay`!")

	@property
	def errors(self) -> List[A]:
		raise TypeError("Can't return errors from `Okay`!")

	def map(self, f: Callable[[C], D]) -> Result[A, B, D]:
		return Okay(f(self.__val))

	def flat_map(self, f: Callable[[C], Result[A, B, D]]) -> Result[A, B, D]:
		return self >> f(self.__val)

	def __str__(self) -> str:
		return f"Okay[{self.__val.__class__.__name__}]({self.__val})"


class Warning[B, C](Result):
	"""Represents a computation that encountered non-fatal errors.

	Has a `val` and `warnings`, but no `errors`
	"""

	def __init__(self, warn: List[B], val: C):
		self.__warn = warn
		self.__val = val

	@property
	def is_okay(self) -> bool:
		return False

	@property
	def is_warning(self) -> bool:
		return True

	@property
	def is_error(self) -> bool:
		return False

	@property
	def val(self) -> C:
		return self.__val

	@property
	def warnings(self) -> List[B]:
		return self.__warn

	@property
	def errors(self) -> List[A]:
		raise TypeError("Can't return errors from `Warning`!")

	def map(self, f: Callable[[C], D]) -> Result[A, B, D]:
		return Warning(self.__warn, f(self.__val))

	def flat_map(self, f: Callable[[C], Result[A, B, D]]) -> Result[A, B, D]:
		return self >> f(self.__val)

	def __str__(self) -> str:
		if len(self.__warn) > 0:
			warn_fmt = "with the following warnings:\n" + "".join(
				[f"    > [{x.__class__.__name__}] {x}\n" for x in self.__warn]
			)
		else:
			warn_fmt = "with no warnings"
		return f"Warning[{self.__val.__class__.__name__}]({self.__val}) {warn_fmt}"


class Error[A, B](Result):
	"""Represents a computation which failed with errors.

	Has `warnings` and `errors`, but no `val`.
	"""

	def __init__(self, errors: List[A], warnings: List[B] = []):
		self.__warn = warnings
		self.__err = errors

	@property
	def is_okay(self) -> bool:
		return False

	@property
	def is_warning(self) -> bool:
		return False

	@property
	def is_error(self) -> bool:
		return True

	@property
	def val(self) -> C:
		raise TypeError("Can't return a value from `Error`!")

	@property
	def warnings(self) -> List[B]:
		return self.__warn

	@property
	def errors(self) -> List[A]:
		return self.__err

	def map(self, f: Callable[[C], D]) -> Result[A, B, D]:
		return Error(self.__err, self.__warn)

	def flat_map(self, f: Callable[[B, C], Result[A, B, D]]) -> Result[A, B, D]:
		return Error(self.__err, self.__warn)

	def __str__(self) -> str:
		if len(self.__warn) > 0:
			warn_fmt = "with the following warnings:\n" + "".join(
				[f"    > [{x.__class__.__name__}] {x}\n" for x in self.__warn]
			)
		else:
			warn_fmt = "with no warnings"

		if len(self.__err) > 0:
			err_fmt = "and the following errors:\n" + "".join(
				[f"    > [{x.__class__.__name__}] {x}\n" for x in self.__err]
			)
		else:
			err_fmt = "and no errors"

		return f"Error {warn_fmt} {err_fmt}"


def __rshift__(self: Result[A, B, C], o: Result[A, B, C]) -> Result[A, B, C]:
	if self.is_okay and o.is_okay:
		return Okay(o.val)
	elif (not self.is_error) and (not o.is_error):
		return Warning(
			(self.warnings if not self.is_okay else [])
			+ (o.warnings if not o.is_okay else []),
			o.val,
		)
	else:
		return Error(
			(self.errors if self.is_error else []) + (o.errors if o.is_error else []),
			(self.warnings if not self.is_okay else [])
			+ (o.warnings if not o.is_okay else []),
		)


Result.__rshift__ = __rshift__

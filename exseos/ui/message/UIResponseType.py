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
Enum of response types for UI messages.
"""

from exseos.types.Option import Option, Nothing
from exseos.types.Result import Result, Okay, Fail

from abc import ABC, abstractmethod


class ConstraintViolation(Exception):
	"""
	Returned when a value is of the correct type, but violates some constraint.
	"""

	__match_args__ = ("val", "constraint", "note")

	def __init__(self, val: any, constraint: str, note: str = ""):
		msg = (
			f"Value {val} violates constraint {constraint}!" + f" {note}"
			if note
			else ""
		)

		super().__init__(msg)

		self.__val = val
		self.__constraint = constraint
		self.__note = note

	@property
	def val(self) -> any:
		return self.__val

	@property
	def constraint(self) -> str:
		return self.__constraint

	@property
	def note(self) -> str:
		return self.__note


class UIResponseType(ABC):
	@abstractmethod
	def validate(self, raw: str) -> bool:
		"""
		Validate a raw user response.

		:param raw: The raw response input by the user.
		:return: ``True`` if ``raw`` is a valid response; else ``False``
		"""
		...

	@abstractmethod
	def convert(self, raw: str) -> Result[Exception, Exception, any]:
		"""
		Convert a raw user response to this ``UIResponseType``'s data-type.

		:param raw: The raw response input by the user.
		:return: ``raw`` converted into the appropriate type.
		"""
		...


class ShortText(UIResponseType):
	"""
	A short (one-line) text response.
	"""

	def validate(self, raw: str) -> bool:
		return True

	def convert(self, raw: str) -> Result[Exception, Exception, any]:
		return raw


class LongText(UIResponseType):
	"""
	A long (multi-line) text response.
	"""

	def validate(self, raw: str) -> bool:
		return True

	def convert(self, raw: str) -> Result[Exception, Exception, any]:
		return raw


class Integer(UIResponseType):
	"""
	An integer. An optional inclusive range (min, max) can be specified, which
	will be used to validate user input.
	"""

	__match_args__ = ("range_min", "range_max")

	def __init__(
		self, range_min: Option[int] = Nothing(), range_max: Option[int] = Nothing()
	):
		self.__range_min = range_min
		self.__range_max = range_max

	@property
	def range_min(self) -> Option[int]:
		return self.__range_min

	@property
	def range_max(self) -> Option[int]:
		return self.__range_max

	def validate(self, raw: str) -> bool:
		try:
			conv = int(raw)
			if self.range_min.has_val and conv < self.range_min.val:
				return False

			if self.range_max.has_val and conv > self.range_max.has_val:
				return False

			return True
		except ValueError:
			return False

	def convert(self, raw: str) -> Result[Exception, Exception, any]:
		try:
			conv = int(raw)
			if self.range_min.has_val and conv < self.range_min.val:
				return Fail(
					[
						ConstraintViolation(
							conv, f"Value must be at least {self.range_min.val}"
						)
					]
				)

			if self.range_max.has_val and conv > self.range_max.has_val:
				return Fail(
					[
						ConstraintViolation(
							conv, f"Value must be at most {self.range_max.val}"
						)
					]
				)

			return Okay(conv)
		except ValueError as e:
			return Fail([e])


class Decimal(UIResponseType):
	"""
	A decimal number. An optional inclusive range (min, max) can be specified,
	which will be used to validate user input.
	"""

	__match_args__ = ("range_min", "range_max")

	def __init__(
		self, range_min: Option[float] = Nothing(), range_max: Option[float] = Nothing()
	):
		self.__range_min = range_min
		self.__range_max = range_max

	@property
	def range_min(self) -> Option[float]:
		return self.__range_min

	@property
	def range_max(self) -> Option[float]:
		return self.__range_max

	def validate(self, raw: str) -> bool:
		try:
			conv = float(raw)
			if self.range_min.has_val and conv < self.range_min.val:
				return False

			if self.range_max.has_val and conv > self.range_max.has_val:
				return False

			return True
		except ValueError:
			return False

	def convert(self, raw: str) -> Result[Exception, Exception, any]:
		try:
			conv = float(raw)
			if self.range_min.has_val and conv < self.range_min.val:
				return Fail(
					[
						ConstraintViolation(
							conv, f"Value must be at least {self.range_min.val}"
						)
					]
				)

			if self.range_max.has_val and conv > self.range_max.has_val:
				return Fail(
					[
						ConstraintViolation(
							conv, f"Value must be at most {self.range_max.val}"
						)
					]
				)

			return Okay(conv)
		except ValueError as e:
			return Fail([e])


class Boolean(UIResponseType):
	"""
	A boolean value, True or False.
	"""

	yes_answers = ["y", "yes", "true", "1"]
	no_answers = ["n", "no", "false", "0"]

	def validate(self, raw: str) -> bool:
		return (
			raw.lower().strip() in self.yes_answers
			or raw.lower().strip() in self.no_answers
		)

	def convert(self, raw: str) -> bool:
		return (
			Okay(True)
			if raw.lower().strip() in self.yes_answers
			else Okay(False)
			if raw.lower().strip() in self.no_answers
			else Fail(ValueError(f"Value {raw} can't be interpreted as yes or no!"))
		)

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
A ``StackTraced`` object stores stack-trace information along with another
object; it is commonly used to print usable stack traces for non-raised
Exceptions (like those found in ``Result`` objects.)
"""

import traceback
from traceback import FrameSummary, format_exception
from typing import TypeVar, Callable

A: TypeVar = TypeVar("A")


class StackTraced[A]:
	"""
	A ``StackTraced`` object stores stack-trace information along with another
	object; it is commonly used to print usable stack traces for non-raised
	Exceptions (like those found in ``Result`` objects.)
	"""

	def __init__(
		self, val: A, stack_trace: tuple[FrameSummary] = None, exclude_frames: int = 1
	):
		"""
		Instantiate a ``StackTraced``.

		:param val: The value to save stack data for.
		:param stack_trace: Stack-trace information to use. If not provided,
		    stack-trace information will be generated from the current context.
		:param exclude_frames: How many function calls should be ignored from
		    the stack trace? A value of 1 will exclude the call within
		    ``__init__()``; higher values will exclude more stack frames.
		"""
		self.__val = val
		self.__stack_trace = (
			stack_trace
			if stack_trace is not None
			else tuple(traceback.extract_stack()[: -1 * exclude_frames])
		)

	@property
	def val(self) -> A:
		return self.__val

	@property
	def stack_trace(self) -> tuple[FrameSummary]:
		return self.__stack_trace

	def map(self, fn: Callable[[A], A]) -> "StackTraced[A]":
		return StackTraced(fn(self.val), self.stack_trace)

	def flat_map(self, fn: Callable[[A], "StackTraced[A]"]) -> "StackTraced[A]":
		return fn(self.val)

	@staticmethod
	def encapsulate(
		val: "A|StackTraced[A]", exclude_frames: int = 2
	) -> "StackTraced[A]":
		"""
		If ``val`` is already a ``StackTraced``, it is returned unchanged;
		however, if it is anything else, it is encapsulated in a ``StackTraced``
		(and exception information is captured)

		:param val: The value to encapsulate in a ``StackTraced``.
		:param exclude_frames: As in ``StackTraced.__init__()``. Note that the
		    call to ``__init__()`` within ``encapsulate`` adds an additional
		    frame; the default value (2) reflects this.
		"""

		return (
			val
			if issubclass(type(val), StackTraced)
			else StackTraced(val, exclude_frames=exclude_frames)
		)

	def __str__(self) -> str:
		return "\n".join(traceback.format_list(list(self.stack_trace))) + (
			"\n" + "".join(format_exception(self.val))
			if issubclass(type(self.val), Exception)
			else f"\n[{type(self.val).__name__}]: {self.val}"
		)

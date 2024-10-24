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
Utility functions to check and compare types.
"""

from exseos.types.Result import Result, Okay, Warn, Fail

from abc import ABC
from typing import Generic


class TypeCheckWarning(Exception):
	"""
	Indicates that a type check has failed. This does not usually stop
	execution; however, it may cause issues later.
	"""

	def __init__(self, obj: any, should_be: type, note: str = ""):
		"""
		Construct a ``TypeCheckWarning``.

		:param obj: The object that failed type-checking
		:param should_be: The type that ``obj`` should be
		"""
		msg = (
			f"Type-check failed: Object {obj} should have type "
			+ f"{should_be.__name__}, but it has type {type(obj).__name__} "
			+ "instead!"
			+ (f" {note}" if note else "")
		)

		super().__init__(msg)

		self.obj = obj
		self.should_be = should_be
		self.note = note


class BroadCommonTypeWarning(Exception):
	"""
	Used when looking for common types. When the common type between two values
	is extremely broad (e.g. ``ABC``), this warning is given.

	Note that ``object`` is NOT considered a common type at all - if the only
	common type between two objects is ``object``, then ``NoCommonTypeError``
	will be returned.
	"""

	def __init__(self, types: list[any], common: type, note: str = ""):
		"""
		Construct a ``BroadCommonTypeWarning``.

		:param types: List of types that triggered this warning.
		:param common: The common type that triggered this warning.
		:param note: Further information about this warning.
		"""
		type_str = (
			"<no types provided>"
			if len(types) == 0
			else f"`{types[0].__name__}`"
			if len(types) == 1
			else ", ".join([f"`{o.__name__}`" for o in types[:-1]])
			+ " and "
			+ f"`{types[-1].__name__}`"
		)

		super().__init__(
			f'Types {type_str} only share the broad common type `{common.__name__}`.{(" " + note) if note else ""}'
		)

		self.types = types
		self.common = common
		self.note = note


class NoCommonTypeError(Exception):
	"""
	Used when looking for common types. When there is no common type at all
	between two values (except for ``object``), this error is raised.
	"""

	def __init__(self, types: list[any], note: str = ""):
		"""
		Construct a NoCommonTypeError

		:param types: List of types that triggered this error
		:param note: Further information about this error
		"""
		type_str = (
			"<no types provided>"
			if len(types) == 0
			else f"`{types[0].__name__}`"
			if len(types) == 1
			else ", ".join([f"`{o.__name__}`" for o in types[:-1]])
			+ " and "
			+ f"`{types[-1].__name__}`"
		)

		super().__init__(
			f'Types {type_str} do not share a common type.{(" " + note) if note else ""}'
		)

		self.types = types
		self.note = note


def type_check(val: any, t: type) -> bool:
	"""
	Perform a basic, permissive type-check, ensuring that ``val`` can be
	reasonably considered to have type ``t``.

	This function is used internally for basic verification of, e.g.,
	``Variable`` values. It considers subclasses, but it does not consider any
	of the more complex, type-annotation style details. For example, ``t`` can
	be a ``list``, but not a ``list[str]``.

	:param val: The value to check
	:param t: The type that ``val`` should have
	:returns: Whether ``val`` has type ``t``
	"""
	return issubclass(type(val), t)


def common_t(a: type, b: type) -> Result[Exception, Exception, type]:
	"""
	As ``common``, except that ``a`` and ``b`` are types rather than values.

	:param a: The first type to compare
	:param b: The second type to compare
	:returns: ``Okay(t)`` where ``t`` is the most specific common type, or
	    ``Warn(BroadCommonTypeWarning, t)`` if the common type is too broad,
	    or ``Fail(NoCommonTypeError)`` if there is no common type besides
	    ``object``.
	"""
	if issubclass(b, a):
		return Okay(a)

	if issubclass(a, b):
		return Okay(b)

	def _candidate_search(a, b, ignore_broad=True):
		# Search `a` to find common ancestors of `b`
		BROAD_CLASSES = [ABC, type, Generic]
		candidate = None
		superclasses = a.__bases__
		while candidate is None and len(superclasses) > 0:
			next_cycle_superclasses = []
			for scls in superclasses:
				if scls is object:
					continue
				if issubclass(b, scls) and (
					scls not in BROAD_CLASSES or ignore_broad is False
				):
					candidate = scls
					break
				else:
					next_cycle_superclasses += list(scls.__bases__)
			superclasses = next_cycle_superclasses

		return candidate

	candidate = _candidate_search(a, b)  # First pass - ignore too-broad types
	if candidate:
		return Okay(candidate)

	candidate = _candidate_search(a, b, False)  # Second pass - include too-broad types
	if candidate:
		return Warn([BroadCommonTypeWarning([a, b], candidate)], candidate)
	else:
		return Fail([NoCommonTypeError([a, b])])


def common(a: any, b: any) -> Result[Exception, Exception, type]:
	"""
	Return the most specifc type that ``a`` and ``b`` have in common.

	If ``a`` and ``b`` have an extremely broad common type (e.g. ``ABC``), then
	the result will include a ``BroadCommonTypeWarning``. If there is no common
	type at all (except for ``object``), the result will be a
	``NoCommonTypeError``.

	Note that if ``a`` and ``b`` have the same type, or if one is a subclass of
	the other, the result will always be ``Okay()``, even if one or the other's
	type is broad. ``BroadCommonTypeWarning`` only applies when this function
	has to look for 'common ancestors.'

	:param a: The first value to compare
	:param b: The second value to compare
	:returns: ``Okay(t)`` where ``t`` is the most specific common type, or
	    ``Warn(BroadCommonTypeWarning, t)`` if the common type is too broad, or
	    ``Fail(NoCommonTypeError)`` if there is no common type besides
	    ``object``.
	"""
	return common_t(type(a), type(b))

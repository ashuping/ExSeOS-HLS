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

from modules.types.Result import Result, Okay, Warning, Error

from abc import ABC
from typing import Generic

class BroadCommonTypeWarning(Exception):
	''' Used when looking for common types. When the common type between two
	    values is extremely broad (e.g. `object`), this warning is given.
	'''
	def __init__(self, objs: list[any], common: type, note: str = ''):
		''' Construct a BroadCommonTypeWarning.

			:param objs: List of objects that triggered this warning.
			:param common: The common type that triggered this warning.
			:param note: Further information about this warning.
		'''
		obj_str = '<no objects provided>' if len(objs) == 0 \
			else str(objs[0])             if len(objs) == 1 \
			else ', '.join([str(o) for o in objs[:-1]]) + ' and ' + str(objs[-1])

		super().__init__(f'Objects {obj_str} only share the broad common type {common.__name__}.{(" " + note) if note else ""}')

		self.objs = objs
		self.common = common
		self.note = note


class NoCommonTypeError(Exception):
	def __init__(self, objs: list[any], note: str = ''):
		''' Construct a NoCommonTypeError

			:param objs: List of objects that triggered this error
			:param note: Further information about this error
		'''
		obj_str = '<no objects provided>' if len(objs) == 0 \
			else str(objs[0])             if len(objs) == 1 \
			else ', '.join([str(o) for o in objs[:-1]]) + ' and ' + str(objs[-1])

		super().__init__(f'Objects {obj_str} do not share a common type.{(" " + note) if note else ""}')

		self.objs = objs
		self.note = note


def type_check(val: any, t: type) -> bool:
	''' Perform a basic, permissive type-check, ensuring that `val` can be
	    reasonably considered to have type `t`.

		This function is used internally for basic verification of, e.g.,
		`Variable` values. It considers subclasses, but it does not consider any
		of the more complex, type-annotation style details. For example, `t` can
		be a `list`, but not a `list[str]`.

		:param val: The value to check
		:param t: The type that `val` should have
		:returns: Whether `val` has type `t`
	'''
	return issubclass(type(val), t)

def common_t(a: type, b: type) -> Result[Exception, Exception, type]:
	''' As `common`, except that `a` and `b` are types rather than values.

		:param a: The first type to compare
		:param b: The second type to compare
		:returns: `Okay(t)` where `t` is the most specific common type, or
		    `Warning(BroadCommonTypeWarning, t)` if the common type is too
		    broad, or `Error(NoCommonTypeError)` if there is no common type at
		    all.
	'''
	if issubclass(b, a):
		return Okay(a)

	if issubclass(a, b):
		return Okay(b)

	def _candidate_search(a, b, ignore_broad=True):
		# Search `a` to find common ancestors of `b`
		BROAD_CLASSES = [object, ABC, type, Generic]
		candidate = None
		superclasses = a.__bases__
		while candidate is None and len(superclasses) > 0:
			next_cycle_superclasses = []
			for scls in superclasses:
				if issubclass(b, scls) and (scls not in BROAD_CLASSES or ignore_broad == False):
					candidate = scls
					break
				else:
					next_cycle_superclasses += list(scls.__bases__)
			superclasses = next_cycle_superclasses

		return candidate

	candidate = _candidate_search(a, b) # First pass - ignore too-broad types
	if candidate:
		return Okay(candidate)

	candidate = _candidate_search(a, b, False) # Second pass - include too-broad types
	if candidate:
		return Warning([BroadCommonTypeWarning([a, b], candidate)], candidate)
	else:
		return Error([NoCommonTypeError([a, b])])

def common(a: any, b: any) -> Result[Exception, Exception, type]:
	''' Return the most specifc type that `a` and `b` have in common.

		If `a` and `b` have an extremely broad common type (e.g. `object`), then
		the result will include a `BroadCommonTypeWarning`. If there is no
		common type at all, the result will be a `NoCommonTypeError`.

		Note that if `a` and `b` have the same type, or if one is a subclass of
		the other, the result will always be `Okay()`, even if one or the
		other's type is `object`. `BroadCommonTypeWarning` only applies when
		this function has to look for 'common ancestors.'

		:param a: The first value to compare
		:param b: The second value to compare
		:returns: `Okay(t)` where `t` is the most specific common type, or
		    `Warning(BroadCommonTypeWarning, t)` if the common type is too
		    broad, or `Error(NoCommonTypeError)` if there is no common type at
		    all.
	'''
	return common_t(type(a), type(b))
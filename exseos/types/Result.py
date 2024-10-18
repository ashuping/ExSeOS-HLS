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
A ``Result`` holds the result of a computation in a sequenceable way.

``Result``'s can be one of the following:

* ``Okay(r)``: The computation completed with result ``r``, without errors.
* ``Warn(w, r)``: The computation encountered issues, but was still able to
  complete with result ``r``. Warnings are held in ``w``
* ``Fail(e, w)``: The computation encountered fatal errors and was unable to
  complete. The fatal error(s) encountered are held in ``e``, and non-fatal
  warnings are held in ``w``.

Resultant values can be extracted from ``Okay`` and ``Warn`` objects using
``Result.val``; however, attempting to do so with a ``Fail`` object will result
in a ``TypeError``.

A list of warnings (usually in the form of ``Exception``'s) can be extracted
from ``Warn`` and ``Fail`` objects using ``Result.warnings``; however,
attempting to do so with an ``Okay`` object will result in a ``TypeError``.

A list of fatal errors (also usually in the form of ``Exception``'s) can be
extracted from ``Fail`` objects using ``Result.errors``; however, attempting to
do so with an ``Okay`` or ``Warn`` object will result in a ``TypeError``.

Computations that return ``Result`` objects can be sequenced using
``Result.flat_map()``.

The right-shift operator can be used to merge ``Result`` objects. The resultant
object will always be the worst of all the inputs (i.e. ``Okay`` >> ``Warn`` >>
``Fail`` will result in a ``Fail``). ``val``, if present, will be the ``val`` of
the last object in the chain. ``warnings`` will be the combination of all input
objects' ``warnings``, and ``errors`` will be the combination of all input
objects' ``errors``.

The left-shift operator works as the right-shift operator, except that the
resultant ``val`` (if present) will be the ``val`` of the *first* object in the
chain rather than the last.

For a more customizeable combination operator, see the ``merge()`` function.
"""

from __future__ import annotations

from exseos.types.ComparableError import ComparableError
from exseos.types.StackTraced import StackTraced

from abc import ABC, abstractmethod
from typing import TypeVar, Callable, List, Generic

A: TypeVar = TypeVar("A")
B: TypeVar = TypeVar("B")
C: TypeVar = TypeVar("C")
D: TypeVar = TypeVar("D")


class Result(ABC, Generic[A, B, C]):
	"""
	Represents the result of a computation.

	Can either be ``Okay[C]``, ``Warn[B, C]``, or ``Fail[A, B]``.

	``val`` of type ``C`` represents the return type of the computation. It is
	present in ``Okay`` and ``Warn`` types, but not ``Fail`` types.

	``warn`` of type ``B`` represents non-fatal warnings. It is present in
	``Warn`` and ``Fail`` types, but not ``Okay`` types.

	``err`` of type ``A`` represents fatal errors. It is only present in
	``Fail`` types.

	Note that Result stores stack-trace information for warnings and errors,
	regardless of whether they are Exceptions or not.
	"""

	@property
	@abstractmethod
	def is_okay(self) -> bool:
		"""True IFF the result is ``Okay``."""
		...  # pragma: no cover

	@property
	@abstractmethod
	def is_warn(self) -> bool:
		"""True IFF the result is ``Warn``"""
		...  # pragma: no cover

	@property
	@abstractmethod
	def is_fail(self) -> bool:
		"""True IFF the result is ``Fail``"""
		...  # pragma: no cover

	@property
	@abstractmethod
	def val(self) -> C:
		"""
		Return the result of the computation.

		This is present for ``Okay`` and ``Warn`` types. It is NOT present for
		``Fail`` types.

		:raises TypeError: if called on a ``Fail``
		"""
		...  # pragma: no cover

	@property
	@abstractmethod
	def warnings(self) -> List[B]:
		"""
		Return the list of warnings generated during the computation.

		This is present for ``Warn`` and ``Fail`` types. It is NOT present for
		``Okay`` types.

		:raises TypeError: if called on an ``Okay``
		"""
		...  # pragma: no cover

	@property
	@abstractmethod
	def warnings_traced(self) -> List[StackTraced[B]]:
		"""
		As ``warnings()``  (with all the caveats), except that it returns
		``StackTraced`` objects which include stack-trace information.

		:raises TypeError: if called on an ``Okay``
		"""

	...  # pragma: no cover

	@property
	@abstractmethod
	def errors(self) -> List[A]:
		"""
		Return the list of fatal errors generated during the computation.

		This is only present for ``Fail`` types.

		:raises TypeError: if called on an ``Okay`` or ``Warning``
		"""
		...  # pragma: no cover

	@property
	@abstractmethod
	def errors_traced(self) -> List[StackTraced[A]]:
		"""
		As ``errors()`` (with all the caveats), except that it returns
		``StackTraced`` objects which include stack-trace information.

		:raises: TypeError: if called on an ``Okay`` or ``Warning``
		"""
		...  # pragma: no cover

	@abstractmethod
	def map(self, f: Callable[[C], D]) -> "Result[A, B, D]":
		"""
		If this ``Result`` is ``Okay`` or ``Warning``, call ``f`` on its value
		and return an ``Okay`` or ``Warning`` of the result.

		:param f: A mapping function that maps ``C``'s to another type ``D``.
		:return: A ``Result`` of the same type as this, where the internal value
		    (if present) has been run through ``f``.
		"""
		...  # pragma: no cover

	@abstractmethod
	def flat_map(self, f: Callable[[C], "Result[A, B, D]"]) -> "Result[A, B, D]":
		"""
		If this ``Result`` is ``Okay`` or ``Warning``, call ``f`` on its value
		and return the output, which must itself be a ``Result``.

		If this ``Result`` is ``Fail``, then this function acts as a no-op.

		:param f: A mapping function that maps ``C``'s to a ``Result[A, B, D]``.
		:return: If this is ``Okay`` or ``Warn``, the return value of ``f`` with
		    any pre-existing warnings added (which may change an ``Okay`` result
		    to a ``Warn``). Otherwise, the current ``Result`` unchanged.
		"""
		...  # pragma: no cover

	@abstractmethod
	def recover(
		self, f: "Callable[[StackTraced(A), StackTraced(B)], Result[A, B, D]]"
	) -> "Result[A, B, D]":
		"""
		If this ``Result`` is ``Fail``, call ``f`` on the errors and warnings,
		and return the output, which must itself be a ``Result``.

		If this ``Result`` is *not* ``Fail``, this function acts as a no-op.

		:param f: A recovery function that maps a list of errors and a list of
		    warnings to a new ``Result``. Unlike ``flat_map()``, pre-existing
		    warnings and errors are not automatically added to the new
		    ``Result``.
		:return: If this is ``Fail``, then the return value of ``f``. Otherwise,
		    the current ``Result`` unchanged.
		"""
		...  # pragma: no cover

	def __eq__(self, other):
		if not issubclass(type(other), Result):
			return False

		if self.is_okay:
			if not other.is_okay:
				return False

			return self.val == other.val

		elif self.is_warn:
			if not other.is_warn:
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

		else:  # self.is_fail
			if not other.is_fail:
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


class Okay(Result):
	"""
	Represents a computation that has succeeded without any errors or warnings.

	Has a value, but no warnings or errors
	"""

	__match_args__ = ("val",)

	def __init__(self, val: C):
		self.__val = val

	@property
	def is_okay(self) -> bool:
		return True

	@property
	def is_warn(self) -> bool:
		return False

	@property
	def is_fail(self) -> bool:
		return False

	@property
	def val(self) -> C:
		return self.__val

	@property
	def warnings(self) -> List[B]:
		raise TypeError("Can't return warnings from `Okay`!")

	@property
	def warnings_traced(self) -> List[B]:
		raise TypeError("Can't return stack-traced warnings from `Okay`!")

	@property
	def errors(self) -> List[A]:
		raise TypeError("Can't return errors from `Okay`!")

	@property
	def errors_traced(self) -> List[A]:
		raise TypeError("Can't return stack-traced errors from `Okay`!")

	def map(self, f: Callable[[C], D]) -> Result[A, B, D]:
		return Okay(f(self.__val))

	def flat_map(self, f: Callable[[C], Result[A, B, D]]) -> Result[A, B, D]:
		return self >> f(self.__val)

	def recover(
		self, f: Callable[[StackTraced(A), StackTraced(B)], Result[A, B, D]]
	) -> Result[A, B, D]:
		return self

	def __str__(self) -> str:
		return f"Result.Okay[{self.val.__class__.__name__}]({self.val})"

	def __repr__(self) -> str:
		return f"Okay({repr(self.val)})"


class Warn(Result):
	"""
	Represents a computation that encountered non-fatal errors.

	Has a value and warnings, but no errors
	"""

	__match_args__ = ("warnings", "val")

	def __init__(self, warnings: List[B], val: C):
		self.__warn = [StackTraced.encapsulate(w) for w in warnings]
		self.__val = val

	@property
	def is_okay(self) -> bool:
		return False

	@property
	def is_warn(self) -> bool:
		return True

	@property
	def is_fail(self) -> bool:
		return False

	@property
	def val(self) -> C:
		return self.__val

	@property
	def warnings(self) -> List[B]:
		return [w.val for w in self.__warn]

	@property
	def warnings_traced(self) -> List[B]:
		return self.__warn

	@property
	def errors(self) -> List[A]:
		raise TypeError("Can't return errors from `Warn`!")

	@property
	def errors_traced(self) -> List[A]:
		raise TypeError("Can't return stack-traced errors from `Warn`!")

	def map(self, f: Callable[[C], D]) -> Result[A, B, D]:
		return Warn(self.__warn, f(self.__val))

	def flat_map(self, f: Callable[[C], Result[A, B, D]]) -> Result[A, B, D]:
		return self >> f(self.__val)

	def recover(
		self, f: Callable[[StackTraced(A), StackTraced(B)], Result[A, B, D]]
	) -> Result[A, B, D]:
		return self

	def __str__(self) -> str:
		if len(self.warnings) > 0:
			warn_fmt = "with the following warnings:\n" + "".join(
				[f"    > [{x.__class__.__name__}] {x}\n" for x in self.warnings]
			)
		else:
			warn_fmt = "with no warnings"
		return f"Result.Warn[{self.val.__class__.__name__}]({self.val}) {warn_fmt}"

	def __repr__(self) -> str:
		return f"Warn({self.warnings}, {self.val})"


class Fail(Result):
	"""
	Represents a computation which failed with errors.

	Has warnings and errors, but no value.
	"""

	__match_args__ = ("errors", "warnings")

	def __init__(self, errors: List[A], warnings: List[B] = []):
		self.__warn = [StackTraced.encapsulate(w) for w in warnings]
		self.__err = [StackTraced.encapsulate(e) for e in errors]

	@property
	def is_okay(self) -> bool:
		return False

	@property
	def is_warn(self) -> bool:
		return False

	@property
	def is_fail(self) -> bool:
		return True

	@property
	def val(self) -> C:
		raise TypeError("Can't return a value from `Fail`!")

	@property
	def warnings(self) -> List[B]:
		return [w.val for w in self.__warn]

	@property
	def warnings_traced(self) -> List[StackTraced[B]]:
		return self.__warn

	@property
	def errors(self) -> List[A]:
		return [e.val for e in self.__err]

	@property
	def errors_traced(self) -> List[StackTraced[A]]:
		return self.__err

	def map(self, f: Callable[[C], D]) -> Result[A, B, D]:
		return Fail(self.__err, self.__warn)

	def flat_map(self, f: Callable[[B, C], Result[A, B, D]]) -> Result[A, B, D]:
		return Fail(self.__err, self.__warn)

	def recover(
		self, f: Callable[[StackTraced(A), StackTraced(B)], Result[A, B, D]]
	) -> Result[A, B, D]:
		return f(self.__err, self.__warn)

	def __str__(self) -> str:
		if len(self.warnings) > 0:
			warn_fmt = "with the following warnings:\n" + "".join(
				[f"    > [{x.__class__.__name__}] {x}\n" for x in self.warnings]
			)
		else:
			warn_fmt = "with no warnings"

		if len(self.errors) > 0:
			err_fmt = "and the following errors:\n" + "".join(
				[f"    > [{x.__class__.__name__}] {x}\n" for x in self.errors]
			)
		else:
			err_fmt = "and no errors"

		return f"Result.Fail {warn_fmt} {err_fmt}"

	def __repr__(self) -> str:
		return f"Fail({self.errors}, {self.warnings})"


class MergeStrategies:
	"""
	Static class that holds functions to be used in ``merge()``.
	"""

	def KEEP_FIRST(a: C, b: C) -> C:
		"""
		``val`` is taken from the first object in the chain. This is equivalent
		to using ``<<``.

		:param a: The first ``val``
		:param b: The second ``val``
		:returns: The resultant ``val``
		"""
		return a

	def KEEP_FIRST_EMPTY(args: list[Result]) -> Result:
		"""
		Corresponding ``empty`` parameter for ``KEEP_FIRST`` - the "empty"
		element should be the first element in the list, unless there is no
		first element or the first element is ``Fail``.
		"""
		return (
			args[0].val
			if len(args) > 0 and (args[0].is_okay or args[0].is_warn)
			else None
		)

	def KEEP_LAST(a: C, b: C) -> C:
		"""
		``val`` is taken from the last object in the chain. This is equivalent
		to using ``>>``.

		:param a: The first ``val``
		:param b: The second ``val``
		:returns: The resultant ``val``
		"""
		return b

	KEEP_LAST_EMPTY = None

	def APPEND(a: C, b: C) -> C:
		"""
		Each ``val`` is appended to the last, from left to right. The first
		value in the chain will be converted into a one-element list if it is
		not already a list.

		:param a: The first ``val``
		:param b: The second ``val``
		:returns: The resultant ``val``
		"""
		try:
			(c := a[:]).append(b)
			return c
		except Exception:
			(c := [a]).append(b)
			return c

	APPEND_EMPTY = []


def merge(
	a: Result[A, B, C],
	b: Result[A, B, C],
	fn: Callable[[C, C], C] = MergeStrategies.KEEP_LAST,
) -> Result[A, B, C]:
	"""
	Combine two ``Result``'s with a custom value-merge strategy.

	This acts as the right-shift operator, except that the new ``Result``'s
	``val`` (if applicable) is calculated based on a user-defined funciton
	``fn``. Common merge strategies are defined in ``MergeStrategies``.

	:param a: The 'left-side' ``Result``
	:param b: The 'right-side' ``Result``
	:param fn: The merge strategy to use. If both ``a`` and ``b`` have a ``val``
	    field, then ``fn`` is called in the form ``fn(a.val, b.val)``. It should
	    return the resultant ``val`` for the combined ``Result``.
	:returns: The ``Result`` created by combining ``a`` and ``b``
	"""
	if a.is_okay and b.is_okay:
		return Okay(fn(a.val, b.val))
	elif (not a.is_fail) and (not b.is_fail):
		print(str(a), str(b))
		return Warn(
			(a.warnings_traced if not a.is_okay else [])
			+ (b.warnings_traced if not b.is_okay else []),
			fn(a.val, b.val),
		)
	else:
		return Fail(
			(a.errors_traced if a.is_fail else [])
			+ (b.errors_traced if b.is_fail else []),
			(a.warnings_traced if not a.is_okay else [])
			+ (b.warnings_traced if not b.is_okay else []),
		)


def merge_all(
	*args: List[Result[A, B, C]],
	fn: Callable[[C, C], C] = MergeStrategies.KEEP_LAST,
	empty: any = None,
) -> Result[A, B, C]:
	"""
	As ``merge()``, but it flattens a list of ``Result``'s.

	If ``args`` has zero elements, this will return ``Okay(None)``.

	If ``args`` has only one element, it will return that element unchanged.

	If ``args`` has more than one element, then the list will be processed in
	sequence using ``fn``.

	:param *args: List of ``Result``'s to flatten.
	:param fn: Merge strategy (see ``merge()`` for more information)
	:returns: The final ``Result`` of merging all elements.
	"""
	if callable(empty):
		empty = empty(args)

	if len(args) == 0:
		return Okay(empty)
	elif len(args) == 1:
		return merge(Okay(empty), args[0], fn)
	else:
		res = merge(Okay(empty), args[0], fn)
		for r in args[1:]:
			res = merge(res, r, fn)
		return res


def __rshift__(self: Result[A, B, C], o: Result[A, B, C]) -> Result[A, B, C]:
	return merge(self, o, MergeStrategies.KEEP_LAST)


def __lshift__(self: Result[A, B, C], o: Result[A, B, C]) -> Result[A, B, C]:
	return merge(self, o, MergeStrategies.KEEP_FIRST)


Result.__rshift__ = __rshift__
Result.__lshift__ = __lshift__

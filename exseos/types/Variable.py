# ExSeOS-HLS Hardware ML Workflow Manager
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
A ``Variable`` is a quantity that can vary from workflow to workflow. They are
used to store inputs, outputs, and intermediate values flowing between
``WorkflowStage``'s.
"""

from exseos.types.util import common, type_check
from exseos.types.Option import Option, Nothing, Some
from exseos.types.Result import Result, Okay, Warn, Fail, merge_all

from abc import ABC, abstractmethod
import logging
import numpy as np
from typing import TypeVar, Generic

A: TypeVar = TypeVar("A")

log = logging.getLogger(__name__)


class Variable(ABC, Generic[A]):
	"""
	Stores a quantity whose value can vary from workflow to workflow,
	controlled either statically (manually set in configuration) or
	dynamically (controlled by an optimizer)
	"""

	@property
	@abstractmethod
	def is_bound(self) -> bool:
		"""
		``True`` iff this variable has been bound to a value.
		"""
		...  # pragma: no cover

	@property
	@abstractmethod
	def name(self) -> str:
		"""The name of this Variable."""
		...  # pragma: no cover

	@property
	@abstractmethod
	def desc(self) -> Option[str]:
		"""An optional long-form description for this Variable."""
		...  # pragma: no cover

	@property
	@abstractmethod
	def val(self) -> Option[A]:
		"""
		The bound value of this Variable. Only exists if ``is_bound`` is True or
		the variable has a ``default``; otherwise, it will return ``Nothing``
		"""
		...  # pragma: no cover

	@property
	@abstractmethod
	def var_type(self) -> Option[type]:
		"""Optional type annotation for this Variable."""
		...  # pragma: no cover

	@property
	@abstractmethod
	def var_type_inferred(self) -> bool:
		"""
		True if ``var_type`` was automatically inferred (and thus potentially
		inaccurate); False if it was explicitly provided.
		"""
		...  # pragma: no cover

	@property
	@abstractmethod
	def default(self) -> Option[A]:
		"""Optional default value for this Variable."""
		...  # pragma: no cover

	@abstractmethod
	def bind(self, val: A) -> "BoundVariable[A]":
		"""Bind a value to this Variable."""
		...  # pragma: no cover

	@abstractmethod
	def copy(self, **changes) -> "Variable[A]":
		"""Make a copy of this Variable with changes."""
		...  # pragma: no cover

	def __eq__(self, other: "Variable") -> bool:
		if not issubclass(type(other), Variable):
			return False

		if self.is_bound:
			if not other.is_bound:
				return False
			
			if type(self.val.val) is not type(other.val.val):
				return False

			# Some types must be handled specially
			match type(self.val.val):
				case np.ndarray:
					# Need to check dimensions and dtype
					if self.val.val.shape != other.val.val.shape:
						return False

					if self.val.val.dtype != other.val.val.dtype:
						return False

					# Numpy arrays have to have `.all()` called at the end
					if not (self.val.val == other.val.val).all():
						return False
				case _:
					# All other types are compared directly
					if self.val.val != other.val.val:
						return False

		return all(
			[
				self.name == other.name,
				self.is_bound == other.is_bound,
				self.desc == other.desc,
				self.var_type == other.var_type,
				self.default == other.default,
			]
		)


class BoundVariable(Variable, Generic[A]):
	"""A Variable that has already been given a value."""

	def __init__(
		self,
		name: str,
		val: A,
		var_type: Option[type] = Nothing(),
		desc: Option[str] = Nothing(),
		default: Option[A] = Nothing(),
	):
		var_type = Option.make_from(var_type)
		desc = Option.make_from(desc)
		default = Option.make_from(default)

		self.__name = name
		self.__val = val
		self.__desc = desc
		self.__default = default

		if var_type == Nothing():
			if default == Nothing():
				# Infer type from `val`
				self.__type = Some(type(val))
				self.__inferred = True
				log.debug(
					f"Inferred type {self.__type} from val {val} for BoundVariable {name}."
				)
			else:
				# Try to find a common type between `val` and `default`
				ctype = common(val, default.val)
				if ctype.is_okay:
					log.debug(
						f"Inferred type {ctype.val} from val {val} and default {default.val} for BoundVariable {name}"
					)
					self.__type = Some(ctype.val)
					self.__inferred = True
				elif ctype.is_warn:
					log.debug(
						f"Tried to infer type for BoundVariable {name} from val {val} and default {default.val}, but resultant type {ctype.val} seems overly broad. Using it anyway."
					)
					self.__type = Some(ctype.val)
					self.__inferred = True
				else:
					log.debug(
						f"Failed to infer type for BoundVariable {name} - val ({val}) and default ({default.val}) have no types in common!"
					)
					self.__type = Nothing()
					self.__inferred = False
		else:
			# Type was explicitly provided
			self.__type = Option.make_from(var_type)
			self.__inferred = False

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
	def val(self) -> Option[A]:
		return Some(self.__val)

	@property
	def var_type(self) -> Option[type]:
		return self.__type

	@property
	def var_type_inferred(self) -> bool:
		return self.__inferred

	@property
	def default(self) -> Option[A]:
		return self.__default

	def bind(self, val: A) -> "BoundVariable[A]":
		return BoundVariable(self.name, val, self.var_type, self.desc, self.default)

	def copy(self, **changes) -> "BoundVariable[A]":
		params = {
			"name": self.name,
			"val": self.val.val,
			"var_type": Nothing() if self.var_type_inferred else self.var_type,
			"desc": self.desc,
			"default": self.default,
		} | changes

		return BoundVariable(**params)

	def __str__(self) -> str:
		return "".join(
			[
				"BoundVariable",
				f"[{self.var_type.val.__name__}]" if self.var_type != Nothing() else "",
				f" {self.name}",
				f" = {self.val}",
				f" (default {self.default.val})" if self.default != Nothing() else "",
				f": {self.desc.val}" if self.desc != Nothing() else "",
			]
		)

	def __repr__(self) -> str:
		return "".join(
			[
				"BoundVariable(",
				f"{self.name}, ",
				f"{self.val}, ",
				f"{self.var_type}, ",
				f"{self.desc}, ",
				f"{self.default}",
				")",
			]
		)


class UnboundVariable(Variable):
	"""A Variable which has not yet been given a value."""

	def __init__(
		self,
		name: str,
		var_type: Option[type] = Nothing(),
		desc: Option[str] = Nothing(),
		default: Option[A] = Nothing(),
	):
		desc = Option.make_from(desc)
		default = Option.make_from(default)

		self.__name = name
		self.__desc = desc
		self.__default = default

		if var_type == Nothing():
			if default != Nothing():
				log.debug(
					f"Inferred type {type(default.val)} from default {default.val} for UnboundVariable {name}"
				)
				self.__type = Some(type(default.val))
				self.__inferred = True
			else:
				self.__type = Nothing()
				self.__inferred = False
		else:
			self.__type = Option.make_from(var_type)
			self.__inferred = False

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
	def val(self) -> Option[A]:
		return self.default

	@property
	def var_type(self) -> Option[type]:
		return self.__type

	@property
	def var_type_inferred(self) -> bool:
		return self.__inferred

	@property
	def default(self) -> Option[A]:
		return self.__default

	def bind(self, val: A) -> BoundVariable[A]:
		return BoundVariable(self.name, val, self.var_type, self.desc, self.default)

	def copy(self, **changes) -> "UnboundVariable[A]":
		params = {
			"name": self.name,
			"var_type": Nothing() if self.var_type_inferred else self.var_type,
			"desc": self.desc,
			"default": self.default,
		} | changes

		return UnboundVariable(**params)

	def __str__(self) -> str:
		return "".join(
			[
				"UnboundVariable",
				f"[{self.var_type.val.__name__}]" if self.var_type != Nothing() else "",
				f" {self.name}",
				f" (default {self.default.val})" if self.default != Nothing() else "",
				f": {self.desc.val}" if self.desc != Nothing() else "",
			]
		)

	def __repr__(self) -> str:
		return "".join(
			[
				"UnboundVariable(",
				f"{self.name}, ",
				f"{self.var_type}, ",
				f"{self.desc}, ",
				f"{self.default}",
				")",
			]
		)


class UnboundVariableError(Exception):
	"""
	An ``UnboundVariable`` with no default value was provided where a
	``BoundVariable`` or an ``UnboundVariable`` with a default is required.
	"""

	def __init__(self, var: Variable, note: str = ""):
		msg = (
			f"Can't get value of {var}, because it is unbound and has no "
			+ "defaults!"
			+ f" {note}"
			if note
			else ""
		)

		super().__init__(msg)

		self.var = var
		self.note = note


class AmbiguousVariableError(Exception):
	"""
	Used when there is more than one candidate ``Variable`` for a situation -
	for example, when a ``VariableSet`` is constructed using multiple
	``Variable``'s with the same name.
	"""

	def __init__(self, name: str, candidates: tuple[Variable] = (), note: str = ""):
		msg = (
			f"Couldn't select an unambiguous candidate for {name} "
			+ (
				f"(candidates: {candidates})."
				if candidates
				else "(no candidates found)."
			)
			+ f" {note}"
			if note
			else ""
		)

		super().__init__(msg)

		self.name = name
		self.candidates = candidates
		self.note = note


class InferredTypeMismatchWarning(Warning):
	"""
	Raised when two ``Variable`` objects that should have the same type have
	incompatible types, and one or both of the ``Variable`` objects' types are
	*inferred*.
	"""

	def __init__(self, v1: Variable, v2: Variable, note: str = ""):
		v1_exp_inf = "explicit" if v1.var_type_inferred else "implicit"
		v1_type = (
			f"{v1_exp_inf} type {v1.var_type.val}" if v1.var_type.has_val else "no type"
		)

		v2_exp_inf = "explicit" if v2.var_type_inferred else "implicit"
		v2_type = (
			f"{v2_exp_inf} type {v2.var_type.val}" if v2.var_type.has_val else "no type"
		)

		msg = (
			f"{type(v1).__name__} {v1.name} has {v1_type}, "
			+ f"but {type(v2).__name__} {v2.name} has {v2_type}!"
			+ (f" {note}" if note else "")
		)

		super().__init__(msg)

		self.v1 = v1
		self.v2 = v2
		self.note = note


class ExplicitTypeMismatchError(Exception):
	"""
	Raised when two ``Variable`` objects that should have the same type have
	incompatible types, both of the ``Variable`` objects' types are *explicit*.
	This is more severe, as implicit mismatches may just be a result of
	incorrect type inference.
	"""

	def __init__(self, v1: Variable, v2: Variable, note: str = ""):
		v1_exp_inf = "explicit" if v1.var_type_inferred else "implicit"
		v1_type = (
			f"{v1_exp_inf} type {v1.var_type.val}" if v1.var_type.has_val else "no type"
		)

		v2_exp_inf = "explicit" if v2.var_type_inferred else "implicit"
		v2_type = (
			f"{v2_exp_inf} type {v2.var_type.val}" if v2.var_type.has_val else "no type"
		)

		msg = (
			f"{type(v1).__name__} {v1.name} has {v1_type}, "
			+ f"but {type(v2).__name__} {v2.name} has {v2_type}!"
			+ (f" {note}" if note else "")
		)

		super().__init__(msg)

		self.v1 = v1
		self.v2 = v2
		self.note = note


class VariableSet:
	"""
	Encapsulates a set of ``Variable``'s in a way that makes it easier to access
	them.

	To access a ``Variable``, use ``get_var`` or just access it as an attribute.
	For example:

	.. code-block:: python

	    >>> my_set = VariableSet((BoundVariable('x', 1), BoundVariable('y', 2)))
	    >>> my_set.get_var('x')
	    1
	    >>> my_set.y
	    2

	Note that if a ``Variable`` isn't present this will raise an
	``AttributeError``, and if the ``Variable`` is present but has no value,
	this will raise an ``UnboundVariableError``.

	If an issue occured while initializing the ``VariableSet``, it will be
	stored in the ``status`` attribute.

	Stored ``Variable``'s can be checked automatically, to ensure that they
	won't return errors on access. To do this, call ``check()`` with the
	``Variable``'s to check, or ``check_all()`` to check *all* ``Variable``'s
	present in this ``VariableSet``.
	"""

	def __init__(self, vars: tuple[Variable]):
		self.__status = Okay(None)

		var_pairs = [(v.name, v) for v in vars]
		var_dict = dict(var_pairs)

		if len(var_dict.items()) < len(var_pairs):
			buckets = []
			var_names = [v.name for v in vars]
			for dex, v in enumerate(vars):
				if var_names[dex:].count(v.name) > 1:
					buckets.append(tuple([vr for vr in vars if vr.name == v.name]))

			for dupe_bucket in buckets:
				# print(dupe_bucket)
				self.__status <<= Warn(
					[
						AmbiguousVariableError(
							dupe_bucket[0].name,
							dupe_bucket,
							"(while constructing a `VariableSet`)",
						)
					],
					None,
				)

		self.__vars = var_dict

	@property
	def status(self) -> Result[Exception, Exception, None]:
		"""
		Return the status of the ``VariableSet``. This will include any
		warnings produced while the set was generated.

		:returns: The result of generating the set.
		"""
		return self.__status

	@property
	def vars(self) -> dict[str, Variable]:
		"""
		Return the mapping between ``Variable`` name and ``Variable``'s.

		:returns: The ``Variable`` name mapping.
		"""
		return self.__vars

	def __check_one(
		self, to_check: str | Variable
	) -> Result[Exception, Exception, None]:
		"""
		Check a single ``Variable``. Users should use ``check()`` instead.

		:param v: ``Variable`` or name to check
		:returns: ``Okay(None)`` if the ``Variable`` exists and has a value;
		    ``Fail(AttributeError)`` if the ``Variable`` does not exist;
		    ``Fail(UnboundVariableError)`` if it exists but has no value.
		"""
		v = to_check.name if type_check(to_check, Variable) else to_check

		return (
			Okay(None)
			if v in self.__vars.keys() and self.__vars[v].val != Nothing()
			else Fail(
				[
					UnboundVariableError(
						self.__vars[v],
						"(while retrieving a `Variable` from a `VariableSet`)",
					)
				]
			)
			if v in self.__vars.keys()
			else Fail([AttributeError(f"No variable named {v} in this `VariableSet`!")])
		)

	def check(self, *args: list[str | Variable]) -> Result[Exception, Exception, None]:
		"""
		Check one or more ``Variable``'s in this ``VariableSet``. For each
		``Variable`` that has no value (i.e. is unbound and has no default),
		``Fail(UnboundVariableError)`` is added to ``Result``. If all
		``Variable``'s are defined, ``Okay(None)`` is returned.

		If one of the provided arguments does not match any of this
		``VariableSet``'s ``Variable``'s, then ``Fail(AttributeError)`` is added
		to the ``Result``.

		:param *args: List of ``Variable``'s or variable names to check.
		:returns: ``Okay(None)`` if all ``Variable``'s are defined; otherwise,
		    ``Fail(UnboundVariableError)`` for every unbound ``Variable``.
		"""
		return merge_all(*[self.__check_one(arg) for arg in args])

	def check_all(self) -> Result[Exception, Exception, None]:
		"""
		Check that all ``Variable``'s in this ``VariableSet`` have accessible
		values. Functions otherwise like ``check()``


		:returns: ``Okay(None)`` if all ``Variable``'s are defined; otherwise,
		    ``Fail(UnboundVariableError)`` for every unbound ``Variable``.
		"""
		return self.check(*tuple(self.__vars.keys()))

	def get_var(self, name: str) -> any:
		"""
		Retrieve an item from the built-in variable dictionary.

		:param name: The ``Variable`` name to retrieve
		:returns: The contents of the ``Variable``
		:raises: ``UnboundVariableError`` if the ``Variable`` has no contents.
		:raises: ``AttributeError`` if there is no such ``Variable``.
		"""
		if name in self.__vars.keys():
			if self.__vars[name].val == Nothing():
				raise UnboundVariableError(
					self.__vars[name],
					"(while retrieving a `Variable` from a `VariableSet`)",
				)
			else:
				return self.__vars[name].val.val
		else:
			raise AttributeError(f"No variable named {name} in this `VariableSet`!")

	def __getattr__(self, name: str) -> any:
		"""
		Shorthand for ``get_var(name)``. If the name of a variable conflicts
		with a ``VariableSet`` function / property name (e.g. ``status``,
		``check``, etc), then this won't work - call ``get_var()`` directly
		instead.

		:param name: The ``Variable`` name to retrieve
		:returns: The contents of the ``Variable``
		:raises: ``UnboundVariableError`` if the ``Variable has no contents.
		"""
		return self.get_var(name)

	def __eq__(self, other: "VariableSet") -> bool:
		if not issubclass(type(other), VariableSet):
			return False

		return self.vars == other.vars

	def __str__(self) -> str:
		return (
			"VariableSet {\n"
			+ "".join([f"  {k}: {v}\n" for (k, v) in self.vars.items()])
			+ "}"
		)

	def __repr__(self) -> str:
		return (
			"VariableSet("
			+ ", ".join([f"{repr(v)}" for (_, v) in self.vars.items()])
			+ ")"
		)


def ensure_from_name(x: Variable | str) -> Variable:
	"""
	If ``x`` is a string, convert it to a ``Variable`` with that name.

	In many cases, users are allowed to instantiate a ``Variable`` indirectly,
	by providing the name of the ``Variable`` in place of the ``Variable``
	itself. This reduces boilerplate, but requries extra checking to ensure that
	the names are converted to ``Variable``'s. This function passes through
	``Variable``'s while converting any strings to ``Variables``.

	:param x: Either a ``Variable`` or a name
	:returns: ``x`` if ``x`` is a ``Variable``; otherwise, an
	    ``UnboundVariable`` with the name ``x``.
	"""
	return x if type_check(x, Variable) else UnboundVariable(x)


def ensure_from_name_arr(xs: list[Variable | str]) -> list[Variable]:
	"""
	Convenience function to call ``ensure_from_name`` on a list.

	:param xs: List of any combination of ``Variable``'s and names.
	:returns: Array of ``Variables``.
	"""
	return [ensure_from_name(x) for x in xs]


def assert_types_match(
	v1: Variable, v2: Variable, fail_on_explicit_mismatch: bool = True
) -> Result[Exception, Exception, None]:
	"""
	Check whether ``v1`` and ``v2`` have compatible types.

	If ``v1`` and ``v2`` have compatible types (or either one has no type at
	all), then return Okay(None).

	If ``v1`` and ``v2`` have incompatible types, but one or both of their types
	was inferred, then return ``Warn([InferredTypeMismatchWarning], None)``.

	If ``v1`` and ``v2`` have incompatible types *and* both types are explicit,
	then return ``Fail([ExplicitTypeMismatchError], [])`` (unless
	``fail_on_explicit_mismatch`` is ``False``, in which case it will be
	``Warn([ExplicitTypeMismatchError], None)``).

	Note that compatibility is one-way. If ``v2``'s type is a subclass of
	``v1``'s type, then they are considered compatible; however, this does not
	hold the other way around.

	:param v1: The variable to check against.
	:param v2: The variable that should be compatible with ``v1``.
	:param fail_on_explicit_mismatch: Whether incompatible explicitly-declared
	    types should result in ``Fail()`` or ``Warn()``.
	:return: A ``Result`` containing any compatibility issues.
	"""

	if v1.var_type == Nothing() or v2.var_type == Nothing():
		return Okay(None)

	if issubclass(v2.var_type.val, v1.var_type.val) and not (
		# Special case: bools are apparently a subclass of int in python.
		# We don't want that behavior here.
		v2.var_type.val is bool and v1.var_type.val is int
	):
		return Okay(None)

	if v1.var_type_inferred or v2.var_type_inferred:
		return Warn([InferredTypeMismatchWarning(v1, v2)], None)
	elif fail_on_explicit_mismatch:
		return Fail([ExplicitTypeMismatchError(v1, v2)])
	else:
		return Warn([ExplicitTypeMismatchError(v1, v2)], None)


def constant(val: any) -> BoundVariable:
	"""
	Convenience function to create a ``BoundVariable`` from a constant value.
	"""
	return BoundVariable(f"Constant::{val}", val)

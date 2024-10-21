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
A ``WiredStageVariable`` holds both the "local" (i.e. expected by the ``Stage``)
and "wire" (i.e. set by the user when defining the ``Workflow``) versions of a
given ``Variable``, and allows for easy mapping between them.
"""

from exseos.types.Option import Option, Some, Nothing
from exseos.types.Result import Result, Okay, Fail
from exseos.types.Variable import Variable, assert_types_match as var_assert_types_match


class WiredStageVariable:
	"""
	A ``WiredStageVariable`` holds both the "local" (i.e. expected by the
	``Stage``) and "wire" (i.e. set by the user when defining the ``Workflow``)
	versions of a given ``Variable``, and allows for easy mapping between them.

	Note that, while every ``Variable`` *will* have a local name, not every
	variable will have a wire name.

	If the wire-var has an inferred type and the local-var has an explicit type,
	the wire-var will have its type set to the local-var's
	"""

	__match_args__ = ("wire_name", "local_name", "wire_var", "local_var")

	def __init__(self, wire_var: Option[Variable], local_var: Variable):
		self.__wire_var = wire_var.map(
			lambda v: (
				v.copy(var_type=local_var.var_type)
				if (v.var_type_inferred or v.var_type == Nothing())
				and not (local_var.var_type_inferred or local_var.var_type == Nothing())
				else v
			)
		)

		self.__local_var = local_var

	def bind(self, val: any) -> "WiredStageVariable":
		"""
		Bind this ``WiredStageVariable`` to a concrete value.

		This will override both the local and global variables to have the new
		value.
		"""
		return WiredStageVariable(
			self.wire_var.map(lambda v: v.bind(val)),
			self.local_var.bind(val),
		)

	@property
	def has_wire(self) -> bool:
		return self.__wire_var.has_val

	@property
	def assert_has_wire(self) -> Result[Exception, Exception, None]:
		return (
			Okay(None)
			if self.has_wire
			else Fail(
				[ValueError(f"WiredStageVariable {self} does not have a wire-name!")]
			)
		)

	@property
	def wire_name(self) -> Option[str]:
		return self.__wire_var.map(lambda v: v.name)

	@property
	def local_name(self) -> str:
		return self.__local_var.name

	@property
	def wire_var(self) -> Option[Variable]:
		return self.__wire_var

	@property
	def local_var(self) -> Variable:
		return self.__local_var

	@property
	def is_bound(self) -> bool:
		"""
		Returns True if either the local or wire vars is bound
		"""
		return self.local_var.is_bound or (self.has_wire and self.wire_var.val.is_bound)

	@property
	def has_default(self) -> bool:
		"""
		Returns True if either the local or wire vars has a default value
		"""
		return self.local_var.default.has_val or (
			self.has_wire and self.wire_var.val.default.has_val
		)

	@property
	def val(self) -> Option[any]:
		"""
		Returns, in order of priority:
		  - The Wire var's value
		  - The Wire var's default
		  - The local var's value (should never happen)
		  - The local var's default
		"""
		if self.has_wire:
			if self.wire_var.val.is_bound:
				return Some(self.wire_var.val.val.val)
			elif self.wire_var.val.default.has_val:
				return Some(self.wire_var.val.default.val)
		if self.local_var.is_bound:
			return Some(self.local_var.val.val)  # should never happen
		elif self.local_var.default.has_val:
			return Some(self.local_var.default.val)

		return Nothing()

	def assert_types_match(self) -> Result[Exception, Exception, None]:
		"""
		Return any type mismatch issues between the local and wire variables.
		"""
		if not self.has_wire:
			print('hasn\'t wire')
			return Okay(None)

		print('has wire')
		return var_assert_types_match(self.local_var, self.wire_var.val)

	def __eq__(self, other: "WiredStageVariable") -> bool:
		if not issubclass(type(other), WiredStageVariable):
			return False

		if self.has_wire != other.has_wire:
			return False

		if self.has_wire:
			return self.wire_var == other.wire_var and self.local_var == other.local_var
		else:
			return self.local_var == other.local_var

	def __repr__(self) -> str:
		return (
			f"WiredStageVariable(wire_var={self.wire_var}, local_var={self.local_var})"
		)

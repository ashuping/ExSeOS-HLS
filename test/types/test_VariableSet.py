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

from exseos.types.Variable import (
	UnboundVariable,
	BoundVariable,
	VariableSet,
	UnboundVariableError,
	AmbiguousVariableError,
)
from exseos.types.Result import Okay, Warn, Fail

from pytest import raises


def test_basic():
	vs = [
		BoundVariable("x", 1),
		BoundVariable("y", "test"),
		UnboundVariable("z", default=-1.22),
	]

	vset = VariableSet(vs)

	assert vset.status == Okay(None)
	assert vset.x == 1
	assert vset.y == "test"
	assert vset.z == -1.22


def test_eq():
	vs = [
		BoundVariable("x", 1),
		BoundVariable("y", "test"),
		UnboundVariable("z", default=-1.22),
	]

	vs_eq = [
		BoundVariable("x", 1),
		BoundVariable("y", "test"),
		UnboundVariable("z", default=-1.22),
	]

	vs_neq = [
		BoundVariable("x", 2),
		BoundVariable("5", "test"),
		UnboundVariable("z", default=-1.22),
	]

	vs_extra = [
		BoundVariable("x", 1),
		BoundVariable("y", "test"),
		UnboundVariable("z", default=-1.22),
		UnboundVariable("ϑ"),
	]

	assert VariableSet(vs) == VariableSet(vs_eq)
	assert VariableSet(vs) != VariableSet(vs_neq)
	assert VariableSet(vs) != VariableSet(vs_extra)
	assert VariableSet(vs) != vs


def test_ambiguous():
	vs = [
		BoundVariable("x", 1),
		BoundVariable("y", "test"),
		UnboundVariable("z", default=-1.22),
		BoundVariable("x", 2),
	]

	vset = VariableSet(vs)

	expect = Warn(
		[
			AmbiguousVariableError(
				"x",
				(
					BoundVariable("x", 1),
					BoundVariable("x", 2),
				),
				"(while constructing a `VariableSet`)",
			)
		],
		None,
	)

	print(f"expected: {expect}")
	print(f"actual   : {vset.status}")

	assert vset.status == expect

	assert vset.y == "test"
	assert vset.z == -1.22

	# note that which variable takes precedence is undefined
	assert vset.x == 1 or vset.x == 2


def test_unbound():
	vs = [BoundVariable("x", 1), BoundVariable("y", "test"), UnboundVariable("z")]

	vset = VariableSet(vs)

	with raises(UnboundVariableError):
		vset.z


def test_undefined():
	vs = [BoundVariable("x", 1), BoundVariable("y", "test"), UnboundVariable("z")]

	vset = VariableSet(vs)

	with raises(AttributeError):
		vset.potatoes


def test_check():
	vs = [
		BoundVariable("x", 1),
		BoundVariable("y", "test"),
		UnboundVariable("z", default=-1.22),
		UnboundVariable("undefined"),
		UnboundVariable("undefined2"),
	]

	vset = VariableSet(vs)

	assert vset.check("x") == Okay(None)
	assert vset.check("x", "y") == Okay(None)
	assert vset.check("undefined") == Fail(
		[
			UnboundVariableError(
				UnboundVariable("undefined"),
				"(while retrieving a `Variable` from a `VariableSet`)",
			)
		]
	)

	assert vset.check("x", "undefined") == Fail(
		[
			UnboundVariableError(
				UnboundVariable("undefined"),
				"(while retrieving a `Variable` from a `VariableSet`)",
			)
		]
	)

	assert vset.check("x", "undefined", "undefined2") == Fail(
		[
			UnboundVariableError(
				UnboundVariable("undefined"),
				"(while retrieving a `Variable` from a `VariableSet`)",
			),
			UnboundVariableError(
				UnboundVariable("undefined2"),
				"(while retrieving a `Variable` from a `VariableSet`)",
			),
		]
	)

	assert vset.check("not in set") == Fail(
		[AttributeError("No variable named not in set in this `VariableSet`!")]
	)

	assert vset.check("not in set", "undefined", "undefined2") == Fail(
		[
			AttributeError("No variable named not in set in this `VariableSet`!"),
			UnboundVariableError(
				UnboundVariable("undefined"),
				"(while retrieving a `Variable` from a `VariableSet`)",
			),
			UnboundVariableError(
				UnboundVariable("undefined2"),
				"(while retrieving a `Variable` from a `VariableSet`)",
			),
		]
	)


def test_check_all():
	vs_good = [
		BoundVariable("x", 1),
		BoundVariable("y", "test"),
		UnboundVariable("z", default=-1.22),
	]

	vs_bad = [
		BoundVariable("x", 1),
		BoundVariable("y", "test"),
		UnboundVariable("z", default=-1.22),
		UnboundVariable("undefined"),
		UnboundVariable("undefined2"),
	]

	vset_good = VariableSet(vs_good)
	vset_bad = VariableSet(vs_bad)

	assert vset_good.check_all() == Okay(None)
	assert vset_bad.check_all() == Fail(
		[
			UnboundVariableError(
				UnboundVariable("undefined"),
				"(while retrieving a `Variable` from a `VariableSet`)",
			),
			UnboundVariableError(
				UnboundVariable("undefined2"),
				"(while retrieving a `Variable` from a `VariableSet`)",
			),
		]
	)


def test_str():
	vs = [
		BoundVariable("x", 1),
		BoundVariable("y", "test"),
		UnboundVariable("ϕ", default=-1.22),
	]

	assert str(VariableSet(vs)) == (
		"VariableSet {\n"
		+ f"  x: {str(vs[0])}\n"
		+ f"  y: {str(vs[1])}\n"
		+ f"  ϕ: {str(vs[2])}\n"
		+ "}"
	)


def test_repr():
	vs = [
		BoundVariable("x", 1),
		BoundVariable("y", "test"),
		UnboundVariable("ϕ", default=-1.22),
	]

	assert (
		repr(VariableSet(vs))
		== f"VariableSet({repr(vs[0])}, {repr(vs[1])}, {repr(vs[2])})"
	)

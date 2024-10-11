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

from exseos.types.Variable import (
	UnboundVariable,
	BoundVariable,
	VariableSet,
	UnboundVariableError,
	AmbiguousVariableError,
	constant,
	ensure_from_name,
	ensure_from_name_arr,
)
from exseos.types.Option import Nothing, Some
from exseos.types.Result import Okay, Warn, Fail

import pytest
from pytest import raises


def test_val():
	assert BoundVariable("x", 2).val == Some(2)
	assert BoundVariable("x", None).val == Some(None)
	assert UnboundVariable("x").val == Nothing()


def test_default():
	assert UnboundVariable("x", default=Some(2)).val == Some(2)
	assert BoundVariable("x", 4, default=Some(2)).val == Some(4)
	assert UnboundVariable("x", default=Nothing()).val == Nothing()


def test_bind():
	assert UnboundVariable("x", Some(int), Some("the test variable x"), Some(1)).bind(
		2
	) == BoundVariable("x", 2, Some(int), Some("the test variable x"), Some(1))

	assert BoundVariable("x", 2, Some(int), Some("the test variable x"), Some(1)).bind(
		4
	) == BoundVariable("x", 4, Some(int), Some("the test variable x"), Some(1))


def test_is_bound():
	assert BoundVariable("x", 2).is_bound
	assert BoundVariable("x", None).is_bound
	assert not UnboundVariable("x").is_bound


def test_name():
	assert BoundVariable("x", 2).name == "x"
	assert UnboundVariable("y").name == "y"
	assert UnboundVariable("multi-word name").name == "multi-word name"


def test_var_type():
	assert BoundVariable("x", 2, Some(int)).var_type == Some(int)
	assert UnboundVariable("y", Some(str)).var_type == Some(str)


def test_basic_type_inference():
	assert BoundVariable("x", 2).var_type == Some(int)
	assert BoundVariable("x", 2).var_type_inferred is True
	assert BoundVariable("x", 2, Some(int)).var_type_inferred is False

	assert UnboundVariable("y", default=Some(2)).var_type == Some(int)
	assert UnboundVariable("y", default=Some(2)).var_type_inferred is True
	assert UnboundVariable("y", Some(int), default=Some(2)).var_type_inferred is False

	assert BoundVariable("x", 2, default=Some(2)).var_type == Some(int)
	assert BoundVariable("x", 2, default=Some(2)).var_type_inferred is True

	assert BoundVariable("x", 2, Some(int), default=Some(2)).var_type == Some(int)
	assert BoundVariable("x", 2, Some(int), default=Some(2)).var_type_inferred is False


def test_explicit_type_overrides_inference():
	assert BoundVariable("x", 2, Some(str), default=Some(2)).var_type == Some(str)
	assert BoundVariable("x", 2, Some(str), default=Some(2)).var_type_inferred is False


def test_type_inference_uses_common_ancestors():
	class TestSuperclass:
		pass

	class TestSubclass1(TestSuperclass):
		pass

	class TestSubclass2(TestSuperclass):
		pass

	# BoundVariables should choose the closest common ancestor of `val` and `default` when performing type inference.
	assert BoundVariable(
		"x", TestSubclass1(), default=Some(TestSubclass2())
	).var_type == Some(TestSuperclass)

	# If the only common ancestor is `object`, reject the inferred type.
	assert BoundVariable("x", TestSubclass1(), default=Some(1)).var_type == Nothing()


@pytest.mark.parametrize(
	"c", [1, 2, -1, None, "test", True, BoundVariable("test_var", 1)]
)
def test_constant(c):
	assert constant(c) == BoundVariable(f"Constant::{c}", c)


def test_set():
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


def test_set_ambiguous():
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


def test_set_unbound():
	vs = [BoundVariable("x", 1), BoundVariable("y", "test"), UnboundVariable("z")]

	vset = VariableSet(vs)

	with raises(UnboundVariableError):
		vset.z


def test_set_undefined():
	vs = [BoundVariable("x", 1), BoundVariable("y", "test"), UnboundVariable("z")]

	vset = VariableSet(vs)

	with raises(AttributeError):
		vset.potatoes


def test_set_check():
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


def test_set_check_all():
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


@pytest.mark.parametrize("name", ["test", "a", "b", "name with spaces"])
def test_ensure_from_name_str(name):
	assert ensure_from_name(name) == UnboundVariable(name)


@pytest.mark.parametrize(
	"var",
	[
		BoundVariable("test", 1),
		UnboundVariable("a"),
		UnboundVariable("b", int, "description", default=0),
		BoundVariable("name with spaces", bool, "desc with spaces", default=False),
	],
)
def test_ensure_from_name_var(var):
	assert ensure_from_name(var) == var


def test_ensure_from_name_arr():
	ar = [
		BoundVariable("test", 1),
		"a",
		UnboundVariable("b", int, "description", default=0),
		"name with spaces",
	]

	assert ensure_from_name_arr(ar) == [
		BoundVariable("test", 1),
		UnboundVariable("a"),
		UnboundVariable("b", int, "description", default=0),
		UnboundVariable("name with spaces"),
	]

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

import itertools
from exseos.types.Result import Fail, Okay, Warn
from exseos.types.Variable import (
	ExplicitTypeMismatchError,
	InferredTypeMismatchWarning,
	UnboundVariable,
	BoundVariable,
	Variable,
	assert_types_match,
	constant,
	ensure_from_name,
	ensure_from_name_arr,
)
from exseos.types.Option import Nothing, Some

from abc import ABC
import numpy as np
import pytest


def test_eq():
	assert BoundVariable("x", 2) == BoundVariable("x", 2)
	assert UnboundVariable("y") == UnboundVariable("y")

	assert BoundVariable("x", 2) != UnboundVariable("x")

	assert BoundVariable("x", 2, int) == BoundVariable("x", 2, int)
	assert BoundVariable("x", 1, int) != BoundVariable("x", "1", str)
	assert BoundVariable("x", 1, int) != BoundVariable("x", 1, str)
	assert UnboundVariable("y", int) == UnboundVariable("y", int)
	assert UnboundVariable("y", int) != UnboundVariable("y", str)

	assert BoundVariable("x", 1, desc="My Test Variable") == BoundVariable(
		"x", 1, desc="My Test Variable"
	)
	assert BoundVariable("x", 1, desc="My Test Variable") != BoundVariable(
		"x", 1, desc="My Other Test Variable"
	)
	assert UnboundVariable("y", desc="My Test Variable") == UnboundVariable(
		"y", desc="My Test Variable"
	)
	assert UnboundVariable("y", desc="My Test Variable") != UnboundVariable(
		"y", desc="My Other Test Variable"
	)

	assert BoundVariable("x", 1) != BoundVariable("x", 2)

	assert BoundVariable("x", 1, default=1) == BoundVariable("x", 1, default=1)
	assert BoundVariable("x", 1, default=1) != BoundVariable("x", 1, default=2)
	assert UnboundVariable("y", default="yes") == UnboundVariable("y", default="yes")
	assert UnboundVariable("y", default="yes") != UnboundVariable("y", default="no")

	assert BoundVariable("x", 2) != 2
	assert UnboundVariable("y") != "y"


def test_numpy_arr_eq():
	assert BoundVariable("a", np.array([1, 2, 3])) == BoundVariable(
		"a", np.array([1, 2, 3])
	)
	assert BoundVariable("a", np.array([1, 2, 3])) != BoundVariable(
		"a", np.array([3, 2, 1])
	)
	assert BoundVariable("a", np.array([1, 2, 3])) != BoundVariable(
		"a", np.array([1, 2])
	)
	assert BoundVariable("a", np.array([1, 2, 3])) != BoundVariable(
		"a", np.array(["1", "2", "3"])
	)


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


def test_overbroad_type_inference():
	class OverbroadA(ABC):
		pass

	class OverbroadB(ABC):
		pass

	b = BoundVariable("x", OverbroadA(), default=Some(OverbroadB()))

	assert b.var_type == Some(ABC)
	assert b.var_type_inferred


@pytest.mark.parametrize(
	"c", [1, 2, -1, None, "test", True, BoundVariable("test_var", 1)]
)
def test_constant(c):
	assert constant(c) == BoundVariable(f"Constant::{c}", c)


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


tm_base_vars_explicit: tuple[Variable] = (
	UnboundVariable("x", int),
	UnboundVariable("φ", int),
	BoundVariable("σ", 1, var_type=int),
)

tm_base_vars_implicit: tuple[Variable] = (
	BoundVariable("ψ", 1),
	UnboundVariable("y", default=1),
)

tm_mismatched_vars_explicit: tuple[Variable] = (
	UnboundVariable("x", str),
	UnboundVariable("φ", bool),
	BoundVariable("σ", Exception(), var_type=Exception),
)

tm_mismatched_vars_implicit: tuple[Variable] = (
	BoundVariable("ψ", "oops"),
	UnboundVariable("y", default=False),
)

tm_ambiguous_vars: tuple[Variable] = (
	UnboundVariable("τ"),
	BoundVariable("η", 1.0, default="whoops this isn't a float"),
)


test_assert_types_match_params = itertools.product(
	itself := tm_base_vars_explicit + tm_base_vars_implicit, itself
)


@pytest.mark.parametrize(("v1", "v2"), test_assert_types_match_params)
def test_assert_types_match(v1, v2):
	assert assert_types_match(v1, v2, True) == Okay(None)
	assert assert_types_match(v1, v2, False) == Okay(None)


test_assert_types_inferred_mismatch_params = itertools.product(
	tm_base_vars_explicit + tm_base_vars_implicit, tm_mismatched_vars_implicit
)


@pytest.mark.parametrize(("v1", "v2"), test_assert_types_inferred_mismatch_params)
def test_assert_types_inferred_mismatch(v1, v2):
	assert assert_types_match(v1, v2, True) == Warn(
		[InferredTypeMismatchWarning(v1, v2)], None
	)

	assert assert_types_match(v1, v2, False) == Warn(
		[InferredTypeMismatchWarning(v1, v2)], None
	)


test_assert_types_explicit_mismatch_params = itertools.product(
	tm_base_vars_explicit, tm_mismatched_vars_explicit
)


@pytest.mark.parametrize(("v1", "v2"), test_assert_types_explicit_mismatch_params)
def test_assert_types_explicit_mismatch(v1, v2):
	assert assert_types_match(v1, v2, True) == Fail([ExplicitTypeMismatchError(v1, v2)])

	assert assert_types_match(v1, v2, False) == Warn(
		[ExplicitTypeMismatchError(v1, v2)], None
	)


test_assert_types_explicit_ambiguous_params = itertools.product(
	tm_base_vars_explicit + tm_base_vars_implicit, tm_ambiguous_vars
)


@pytest.mark.parametrize(("v1", "v2"), test_assert_types_explicit_ambiguous_params)
def test_assert_types_ambiguous(v1, v2):
	assert assert_types_match(v1, v2, True) == Okay(None)
	assert assert_types_match(v1, v2, False) == Okay(None)

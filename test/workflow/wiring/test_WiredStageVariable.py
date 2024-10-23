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

from exseos.types.Option import Some, Nothing
from exseos.types.Result import Okay
from exseos.types.Variable import BoundVariable, UnboundVariable, Variable
from exseos.types.Variable import assert_types_match as var_assert_types_match
from exseos.workflow.wiring.WiredStageVariable import WiredStageVariable

import itertools
import pytest
import random


def test_has_wire():
	assert (
		WiredStageVariable(
			Some(BoundVariable("test_wire", 1)), UnboundVariable("test_local")
		).has_wire
		is True
	)

	assert (
		WiredStageVariable(Nothing(), UnboundVariable("test_local")).has_wire is False
	)


def test_wire_name():
	assert WiredStageVariable(
		Some(BoundVariable("test_wire", 1)), UnboundVariable("test_local")
	).wire_name == Some("test_wire")

	assert (
		WiredStageVariable(Nothing(), UnboundVariable("test_local")).wire_name
		== Nothing()
	)


def test_local_name():
	assert (
		WiredStageVariable(
			Some(BoundVariable("test_wire", 1)), UnboundVariable("test_local")
		).local_name
		== "test_local"
	)

	assert (
		WiredStageVariable(Nothing(), UnboundVariable("test_local")).local_name
		== "test_local"
	)


def test_wire_var():
	assert WiredStageVariable(
		Some(BoundVariable("test_wire", 1)), UnboundVariable("test_local")
	).wire_var == Some(BoundVariable("test_wire", 1))

	assert (
		WiredStageVariable(Nothing(), UnboundVariable("test_local")).wire_var
		== Nothing()
	)


def test_local_var():
	assert WiredStageVariable(
		Some(BoundVariable("test_wire", 1)), UnboundVariable("test_local")
	).local_var == UnboundVariable("test_local")

	assert WiredStageVariable(
		Nothing(), UnboundVariable("test_local")
	).local_var == UnboundVariable("test_local")


def test_is_bound():
	assert (
		WiredStageVariable(
			Some(BoundVariable("test_wire", 1)), UnboundVariable("test_local")
		).is_bound
		is True
	)

	assert (
		WiredStageVariable(
			Some(UnboundVariable("test_wire")), BoundVariable("test_local", 1)
		).is_bound
		is True
	)

	assert (
		WiredStageVariable(Nothing(), UnboundVariable("test_local")).is_bound is False
	)

	assert (
		WiredStageVariable(
			Some(UnboundVariable("test_wire")), UnboundVariable("test_local")
		).is_bound
		is False
	)


def test_has_default():
	assert (
		WiredStageVariable(
			Some(BoundVariable("test_wire", 1, default=2)),
			BoundVariable("test_local", 4, default=8),
		).has_default
		is True
	)

	assert (
		WiredStageVariable(
			Some(BoundVariable("test_wire", 1, default=2)),
			UnboundVariable("test_local"),
		).has_default
		is True
	)

	assert (
		WiredStageVariable(
			Some(BoundVariable("test_wire", 1)),
			UnboundVariable("test_local", default=2),
		).has_default
		is True
	)

	assert (
		WiredStageVariable(
			Some(UnboundVariable("test_wire", default=2)),
			BoundVariable("test_local", 1),
		).has_default
		is True
	)

	assert (
		WiredStageVariable(
			Some(UnboundVariable("test_wire")),
			BoundVariable("test_local", 1, default=2),
		).has_default
		is True
	)

	assert (
		WiredStageVariable(
			Nothing(), UnboundVariable("test_local", default=2)
		).has_default
		is True
	)

	assert (
		WiredStageVariable(
			Nothing(), BoundVariable("test_local", 1, default=2)
		).has_default
		is True
	)

	assert (
		WiredStageVariable(
			Some(UnboundVariable("test_wire", default=2)), UnboundVariable("test_local")
		).has_default
		is True
	)

	assert (
		WiredStageVariable(Nothing(), UnboundVariable("test_local")).has_default
		is False
	)

	assert (
		WiredStageVariable(Nothing(), BoundVariable("test_local", 1)).has_default
		is False
	)

	assert (
		WiredStageVariable(
			Some(UnboundVariable("test_wire")), UnboundVariable("test_local")
		).has_default
		is False
	)

	assert (
		WiredStageVariable(
			Some(BoundVariable("test_wire", 1)), UnboundVariable("test_local")
		).has_default
		is False
	)

	assert (
		WiredStageVariable(
			Some(UnboundVariable("test_wire")), BoundVariable("test_local", 1)
		).has_default
		is False
	)

	assert (
		WiredStageVariable(
			Some(BoundVariable("test_wire", 1)), BoundVariable("test_local", 1)
		).has_default
		is False
	)


def test_wire_inheritance():
	assert WiredStageVariable(
		Some(UnboundVariable("wire_var")), UnboundVariable("local_var", var_type=int)
	).wire_var == Some(UnboundVariable("wire_var", var_type=int))

	assert WiredStageVariable(
		Some(UnboundVariable("wire_var", var_type=str)),
		UnboundVariable("local_var", var_type=int),
	).wire_var == Some(UnboundVariable("wire_var", var_type=str))

	assert WiredStageVariable(
		Some(UnboundVariable("wire_var", default="my_str")),
		UnboundVariable("local_var", var_type=int),
	).wire_var == Some(UnboundVariable("wire_var", default="my_str", var_type=int))

	assert WiredStageVariable(
		Some(UnboundVariable("wire_var", default="my_str")),
		UnboundVariable("local_var", default=5),
	).wire_var == Some(UnboundVariable("wire_var", default="my_str"))


random.seed(0)
test_val_params = random.sample(
	list(
		itertools.permutations(
			[0, -12, 0.1123, None, "test", Nothing(), Some(1), (1, 2, 3)], 4
		)
	),
	128,
)


@pytest.mark.parametrize(["a", "b", "c", "d"], test_val_params)
def test_val(a, b, c, d):
	assert WiredStageVariable(
		Some(BoundVariable("test_wire", a, default=Some(b))),
		BoundVariable("test_local", c, default=Some(d)),
	).val == Some(a)

	assert WiredStageVariable(
		Some(UnboundVariable("test_wire", default=Some(b))),
		BoundVariable("test_local", c, default=Some(d)),
	).val == Some(b)

	assert WiredStageVariable(
		Some(UnboundVariable("test_wire")),
		BoundVariable("test_local", c, default=Some(d)),
	).val == Some(c)

	assert WiredStageVariable(
		Some(UnboundVariable("test_wire")),
		UnboundVariable("test_local", default=Some(d)),
	).val == Some(d)

	assert (
		WiredStageVariable(
			Some(UnboundVariable("test_wire")), UnboundVariable("test_local")
		).val
		== Nothing()
	)


test_eq_input = itertools.permutations(
	(
		UnboundVariable("a"),
		UnboundVariable("b"),
		UnboundVariable("a", default=1),
		UnboundVariable("a", default=2),
		UnboundVariable("a", desc="test description"),
		UnboundVariable("a", desc="different description"),
		BoundVariable("a", 1),
		BoundVariable("a", 2),
		BoundVariable("a", 1, default=1),
	),
	2,
)


@pytest.mark.parametrize(["a", "b"], test_eq_input)
def test_eq(a, b):
	assert WiredStageVariable(Some(a), b) == WiredStageVariable(Some(a), b)
	assert WiredStageVariable(Some(a), b) != WiredStageVariable(Some(b), a)
	assert WiredStageVariable(Some(a), b) != WiredStageVariable(Nothing(), b)
	assert WiredStageVariable(Some(a), b) != WiredStageVariable(Nothing(), a)
	assert WiredStageVariable(Some(a), b) != Some(a)


assert_types_match_inputs = itertools.permutations(
	(
		UnboundVariable("a", var_type=int),
		UnboundVariable("ξ", var_type=str),
		UnboundVariable("ι", var_type=bool),
		UnboundVariable("π", default=1),
		UnboundVariable("σ", default=False),
		UnboundVariable("ω"),
		BoundVariable("aa", 1, var_type=int),
		BoundVariable("ξξ", "beep!", var_type=str),
		BoundVariable("ιι", True, var_type=bool),
	),
	2,
)


@pytest.mark.parametrize(["a", "b"], assert_types_match_inputs)
def test_assert_types_match(a: Variable, b: Variable):
	wsv = WiredStageVariable(Some(a), b)

	if (a.var_type_inferred or a.var_type == Nothing()) and not (
		b.var_type_inferred or b.var_type == Nothing()
	):
		# Spread inferred type to wire-var
		a = a.copy(var_type=b.var_type)

	assert wsv.assert_types_match() == var_assert_types_match(b, a)

	wsv_none = WiredStageVariable(Nothing(), b)
	assert wsv_none.assert_types_match() == Okay(None)

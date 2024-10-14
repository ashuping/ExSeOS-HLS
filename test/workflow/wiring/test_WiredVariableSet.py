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

from exseos.types.Option import Option, Some, Nothing
from exseos.types.Variable import BoundVariable, UnboundVariable
from exseos.workflow.wiring.WiredStageVariable import WiredStageVariable
from exseos.workflow.wiring.WiredVariableSet import WiredVariableSet

wired_variables = (
	wv_a := WiredStageVariable(
		Some(BoundVariable("wire_a", 1)),
		UnboundVariable(
			"local_a", desc="this is local variable a", var_type=int, default=0
		),
	),
	wv_b := WiredStageVariable(
		Nothing(),
		UnboundVariable(
			"unbound_b",
			desc="this is an unbound local variable",
			var_type=bool,
			default=True,
		),
	),
	wv_c := WiredStageVariable(
		Some(
			UnboundVariable(
				"same_c",
				desc="the local and wire variables are the same!",
				var_type=str,
				default="cool!",
			)
		),
		UnboundVariable(
			"same_c",
			desc="the local and wire variables are the same!",
			var_type=str,
			default="cool!",
		),
	),
	wv_d := WiredStageVariable(
		Some(
			UnboundVariable(
				"wire_d",
				desc="this one is bound on the local end!",
				var_type=Option,
				default=Nothing(),
			)
		),
		BoundVariable("local_d", Some(2), var_type=Option, default=Nothing()),
	),
)


def test_vars():
	assert WiredVariableSet(wired_variables) == WiredVariableSet(wired_variables)
	assert WiredVariableSet(wired_variables) != WiredVariableSet(wired_variables[1:])
	assert WiredVariableSet(wired_variables) != WiredVariableSet(
		reversed(wired_variables)
	)


def test_get_by_local():
	s = WiredVariableSet(wired_variables)

	assert s.get_by_local("local_a") == Some(wv_a)
	assert s.get_by_local("unbound_b") == Some(wv_b)
	assert s.get_by_local("same_c") == Some(wv_c)
	assert s.get_by_local("local_d") == Some(wv_d)

	assert s.get_by_local("wire_a") == Nothing()
	assert s.get_by_local("wire_d") == Nothing()
	assert s.get_by_local("something") == Nothing()


def test_get_by_wire():
	s = WiredVariableSet(wired_variables)

	assert s.get_by_wire("wire_a") == Some(wv_a)
	# b is unwired, so there's no wire name to get it by
	assert s.get_by_wire("same_c") == Some(wv_c)
	assert s.get_by_wire("wire_d") == Some(wv_d)

	assert s.get_by_wire("local_a") == Nothing()
	assert s.get_by_wire("unbound_b") == Nothing()
	assert s.get_by_wire("local_d") == Nothing()
	assert s.get_by_wire("something") == Nothing()


def test_bind_local():
	local_names_to_bind = (
		BoundVariable("local_a", 5, desc="this shouldn't propagate to the vars"),
		BoundVariable("unbound_b", False, desc="this shouldn't propagate to the vars"),
		BoundVariable("same_c", "lovely!", desc="this shouldn't propagate to the vars"),
		BoundVariable(
			"wire_d", Some(1), desc="this shouldn't propagate to the vars"
		),  # this shouldn't do anything
	)

	expected = WiredVariableSet(
		(
			WiredStageVariable(
				Some(BoundVariable("wire_a", 5)),
				BoundVariable(
					"local_a",
					5,
					desc="this is local variable a",
					var_type=int,
					default=0,
				),
			),
			WiredStageVariable(
				Nothing(),
				BoundVariable(
					"unbound_b",
					False,
					desc="this is an unbound local variable",
					var_type=bool,
					default=True,
				),
			),
			WiredStageVariable(
				Some(
					BoundVariable(
						"same_c",
						"lovely!",
						desc="the local and wire variables are the same!",
						var_type=str,
						default="cool!",
					)
				),
				BoundVariable(
					"same_c",
					"lovely!",
					desc="the local and wire variables are the same!",
					var_type=str,
					default="cool!",
				),
			),
			WiredStageVariable(
				Some(
					UnboundVariable(
						"wire_d",
						desc="this one is bound on the local end!",
						var_type=Option,
						default=Nothing(),
					)
				),
				BoundVariable("local_d", Some(2), var_type=Option, default=Nothing()),
			),
		)
	)

	actual = WiredVariableSet(wired_variables).bind_local(local_names_to_bind)

	assert actual == expected


def test_bind_wire():
	wire_names_to_bind = (
		BoundVariable("wire_a", 5, desc="this shouldn't propagate to the vars"),
		BoundVariable(
			"unbound_b", False, desc="this shouldn't propagate to the vars"
		),  # this shouldn't do anything
		BoundVariable("same_c", "lovely!", desc="this shouldn't propagate to the vars"),
		BoundVariable("wire_d", Some(1), desc="this shouldn't propagate to the vars"),
	)

	expected = WiredVariableSet(
		(
			WiredStageVariable(
				Some(BoundVariable("wire_a", 5)),
				BoundVariable(
					"local_a",
					5,
					desc="this is local variable a",
					var_type=int,
					default=0,
				),
			),
			WiredStageVariable(
				Nothing(),
				UnboundVariable(
					"unbound_b",
					desc="this is an unbound local variable",
					var_type=bool,
					default=True,
				),
			),
			WiredStageVariable(
				Some(
					BoundVariable(
						"same_c",
						"lovely!",
						desc="the local and wire variables are the same!",
						var_type=str,
						default="cool!",
					)
				),
				BoundVariable(
					"same_c",
					"lovely!",
					desc="the local and wire variables are the same!",
					var_type=str,
					default="cool!",
				),
			),
			WiredStageVariable(
				Some(
					BoundVariable(
						"wire_d",
						Some(1),
						desc="this one is bound on the local end!",
						var_type=Option,
						default=Nothing(),
					)
				),
				BoundVariable("local_d", Some(1), var_type=Option, default=Nothing()),
			),
		)
	)

	actual = WiredVariableSet(wired_variables).bind_wire(wire_names_to_bind)

	print(f"Expected: {expected}")
	print(f"Actual  : {actual}")

	assert actual == expected

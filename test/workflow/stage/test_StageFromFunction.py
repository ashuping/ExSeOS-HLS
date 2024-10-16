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

from exseos.types.util import TypeCheckWarning
from exseos.types.Option import Some
from exseos.types.Result import Okay, Warn
from exseos.types.Variable import BoundVariable, UnboundVariable, VariableSet
from exseos.workflow.stage.StageFromFunction import (
	make_StageFromFunction,
	ReturnBindingMismatchWarning,
)

import pytest


@pytest.mark.asyncio
async def test_basic_function():
	def fn(x: int) -> int:
		print("[test] calling inner function")
		return 2 * x

	stage = make_StageFromFunction(fn, ("2x",))(UnboundVariable("x"))

	res = await stage.run(VariableSet((BoundVariable("x", 2),)))

	expect = Okay((BoundVariable("2x", 4),))

	print(f"Expected: {expect}")
	print(f"Actual: {res.map(lambda vs: tuple([str(v) for v in vs]))}")

	assert res == expect


@pytest.mark.asyncio
async def test_multi_return():
	def fn(x: int) -> tuple[int, str]:
		print("[test] calling inner function")
		return 2 * x, str(2 * x)

	stage = make_StageFromFunction(fn, ("2x", "str2x"))(UnboundVariable("x"))

	res = await stage.run(VariableSet((BoundVariable("x", 2),)))

	expect = Okay((BoundVariable("2x", 4), BoundVariable("str2x", "4")))

	print(f"Expected: {expect.map(lambda vs: tuple([str(v) for v in vs]))}")
	print(f"Actual: {res.map(lambda vs: tuple([str(v) for v in vs]))}")

	assert res == expect


@pytest.mark.asyncio
async def test_type_mismatch():
	def fn(x: int) -> int:
		print("[test] calling inner function")
		return 2 * x

	stage = make_StageFromFunction(fn, (UnboundVariable("2x", var_type=str),))(
		UnboundVariable("x")
	)

	res = await stage.run(VariableSet((BoundVariable("x", 2),)))

	expect = Warn(
		[
			TypeCheckWarning(
				4,
				str,
				f"(while binding output variable 2x for StageFromFunction_fn_{hash(fn)})",
			)
		],
		(BoundVariable("2x", 4, var_type=str),),
	)

	print(f"Expected: {expect.map(lambda vs: tuple([str(v) for v in vs]))}")
	print(f"Actual  : {res.map(lambda vs: tuple([str(v) for v in vs]))}")

	assert res == expect


@pytest.mark.asyncio
async def test_too_many_returns():
	def fn(x: int) -> int:
		print("[test] calling inner function")
		return 3 * x, 2 * x, x

	stage = make_StageFromFunction(
		fn,
		(
			UnboundVariable("3x"),
			UnboundVariable("2x"),
		),
	)(UnboundVariable("x"))

	res = await stage.run(VariableSet((BoundVariable("x", 2),)))

	expect = Warn(
		[ReturnBindingMismatchWarning(stage, 3, 2)],
		(
			BoundVariable("3x", 6),
			BoundVariable("2x", 4),
		),
	)

	print(f"Expected: {expect.map(lambda vs: tuple([str(v) for v in vs]))}")
	print(f"Actual  : {res.map(lambda vs: tuple([str(v) for v in vs]))}")

	assert res == expect


@pytest.mark.asyncio
async def test_too_few_returns():
	def fn(x: int) -> int:
		print("[test] calling inner function")
		return 3 * x

	stage = make_StageFromFunction(
		fn,
		(
			UnboundVariable("3x"),
			UnboundVariable("2x"),
		),
	)(UnboundVariable("x"))

	res = await stage.run(VariableSet((BoundVariable("x", 2),)))

	expect = Warn(
		[ReturnBindingMismatchWarning(stage, 1, 2)],
		(
			BoundVariable("3x", 6),
			UnboundVariable("2x"),
		),
	)

	print(f"Expected: {expect.map(lambda vs: tuple([str(v) for v in vs]))}")
	print(f"Actual  : {res.map(lambda vs: tuple([str(v) for v in vs]))}")

	assert res == expect


def test_io_types():
	def fn(x: int, y: str, z="test") -> bool:
		return True

	stage_cls = make_StageFromFunction(fn)

	print(f"input_vars: {stage_cls.input_vars}")

	[print(var) for var in stage_cls.input_vars]

	assert stage_cls.input_vars == (
		UnboundVariable("x", Some(int)),
		UnboundVariable("y", Some(str)),
		UnboundVariable("z", default=Some("test")),
	)

	assert stage_cls.output_vars == (UnboundVariable("return", Some(bool)),)


@pytest.mark.asyncio
async def test_side_effecting_function():
	global fn_run_count
	fn_run_count = 0

	def fn():
		global fn_run_count
		fn_run_count += 1

	stage_cls = make_StageFromFunction(fn)

	assert stage_cls.input_vars == ()
	assert stage_cls.output_vars == ()

	assert (await stage_cls().run(VariableSet(()))) == Okay(())
	assert fn_run_count == 1

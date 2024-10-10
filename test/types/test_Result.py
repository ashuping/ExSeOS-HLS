from pytest import raises

from exseos.types.ComparableError import ComparableError
from exseos.types.Result import Okay, Warn, Fail, merge, merge_all, MergeStrategies


def test_is_okay():
	assert Okay(37).is_okay
	assert not Warn([TypeError()], 37).is_okay
	assert not Fail([ArithmeticError()], [TypeError()]).is_okay


def test_is_warn():
	assert not Okay(37).is_warn
	assert Warn([TypeError()], 37).is_warn
	assert not Fail([ArithmeticError()], [TypeError()]).is_warn


def test_is_fail():
	assert not Okay(37).is_fail
	assert not Warn([TypeError()], 37).is_fail
	assert Fail([ArithmeticError()], [TypeError()]).is_fail


def test_val():
	assert Okay(37).val == 37
	assert Warn([TypeError()], "test").val == "test"

	with raises(TypeError):
		Fail([ArithmeticError()], [ArithmeticError()]).val


def test_warnings():
	assert ComparableError.array_encapsulate(
		Warn([ArithmeticError(6)], 37).warnings
	) == [ArithmeticError(6)]
	assert ComparableError.array_encapsulate(
		Fail([SyntaxError()], [ArithmeticError(6)]).warnings
	) == [ArithmeticError(6)]

	with raises(TypeError):
		Okay(37).warnings


def test_errors():
	assert ComparableError.array_encapsulate(
		Fail([SyntaxError()], [ArithmeticError(6)]).errors
	) == [SyntaxError()]

	with raises(TypeError):
		Okay(37).errors

	with raises(TypeError):
		Warn([ArithmeticError(6)], 37).errors


def test_eq():
	assert Okay(37) == Okay(37)
	assert Warn([ArithmeticError(6)], 37) == Warn([ArithmeticError(6)], 37)
	assert Fail([SyntaxError()], [ArithmeticError(6)]) == Fail(
		[SyntaxError()], [ArithmeticError(6)]
	)

	assert Warn([], 37) == Warn([], 37)
	assert Fail([], []) == Fail([], [])

	assert Okay(37) != Okay(36)
	assert Okay(37) != Okay("37")
	assert Okay(37) != 37

	assert Warn([ArithmeticError(6)], 37) != Warn([ArithmeticError(6)], 36)
	assert Warn([ArithmeticError(6)], 37) != Warn([ArithmeticError(6)], "37")
	assert Warn([ArithmeticError(6)], 37) != Warn([SyntaxError(6)], 37)
	assert Warn([ArithmeticError(6)], 37) != Warn([ArithmeticError(5)], 37)
	assert Warn([ArithmeticError(6)], 37) != 37
	assert Warn([], 37) != 37
	assert Warn([ArithmeticError(6)], 37) != ArithmeticError(6)

	assert Fail([SyntaxError("test")], [ArithmeticError(6)]) != Fail(
		[SyntaxError("test")], [ArithmeticError(5)]
	)
	assert Fail([SyntaxError("test")], [ArithmeticError(6)]) != Fail(
		[ArithmeticError(6)], [SyntaxError("test")]
	)
	assert Fail([SyntaxError("test")], [ArithmeticError(6)]) != Fail(
		[SyntaxError("test")], [ArithmeticError(5)]
	)
	assert Fail([SyntaxError("test")], [ArithmeticError(6)]) != Fail(
		[SyntaxError("test")], [ArithmeticError("6")]
	)
	assert Fail([SyntaxError("test")], [ArithmeticError(6)]) != Fail(
		[SyntaxError("test2")], [ArithmeticError(6)]
	)
	assert Fail([SyntaxError("test")], [ArithmeticError(6)]) != SyntaxError("test")
	assert Fail([SyntaxError("test")], [ArithmeticError(6)]) != [SyntaxError("test")]
	assert Fail([SyntaxError("test")], [ArithmeticError(6)]) != "test"
	assert Fail([SyntaxError("test")], [ArithmeticError(6)]) != ArithmeticError(6)
	assert Fail([SyntaxError("test")], [ArithmeticError(6)]) != [ArithmeticError(6)]
	assert Fail([SyntaxError("test")], [ArithmeticError(6)]) != 6

	assert Okay(37) != Warn([ArithmeticError(6)], 37)
	assert Okay(37) != Fail([SyntaxError()], [ArithmeticError(6)])

	assert Warn([ArithmeticError(6)], 37) != Okay(37)
	assert Warn([ArithmeticError(6)], 37) != Warn(
		[ArithmeticError(6), SyntaxError("test")], 37
	)
	assert Warn([ArithmeticError(6)], 37) != Fail([SyntaxError()], [ArithmeticError(6)])

	assert Fail([SyntaxError()], [ArithmeticError(6)]) != Okay(37)
	assert Fail([SyntaxError()], [ArithmeticError(6)]) != Fail([SyntaxError()], [])
	assert Fail([SyntaxError()], [ArithmeticError(6)]) != Fail([], [ArithmeticError(6)])
	assert Fail([SyntaxError()], [ArithmeticError(6)]) != Fail([], [])
	assert Fail([SyntaxError()], [ArithmeticError(6)]) != Warn([ArithmeticError(6)], 37)


def test_okay_rshift():
	assert Okay(37) >> Okay(38) == Okay(38)
	assert Okay(37) >> Okay("test") == Okay("test")
	assert Okay(37) >> Warn([ArithmeticError(6)], 36) == Warn([ArithmeticError(6)], 36)
	assert Okay(37) >> Fail([SyntaxError("test")], [ArithmeticError(6)]) == Fail(
		[SyntaxError("test")], [ArithmeticError(6)]
	)


def test_warning_rshift():
	assert Warn([ArithmeticError(6)], 37) >> Okay(36) == Warn([ArithmeticError(6)], 36)

	assert Warn([ArithmeticError(6)], 37) >> Warn([SyntaxError("test")], 36) == Warn(
		[ArithmeticError(6), SyntaxError("test")], 36
	)

	assert Warn([ArithmeticError(6), ArithmeticError(7)], 36) >> Warn(
		[SyntaxError("test"), TypeError("cool")], 37
	) == Warn(
		[
			ArithmeticError(6),
			ArithmeticError(7),
			SyntaxError("test"),
			TypeError("cool"),
		],
		37,
	)

	assert Warn([ArithmeticError(6)], 37) >> Fail(
		[SyntaxError("test")], [TypeError("cool")]
	) == Fail([SyntaxError("test")], [ArithmeticError(6), TypeError("cool")])


def test_fail_rshift():
	assert Fail([SyntaxError("test")], [ArithmeticError(6)]) >> Okay(36) == Fail(
		[SyntaxError("test")], [ArithmeticError(6)]
	)

	assert Fail([SyntaxError("test")], [ArithmeticError(6)]) >> Warn(
		[TypeError("cool")], 37
	) == Fail([SyntaxError("test")], [ArithmeticError(6), TypeError("cool")])

	assert Fail([SyntaxError("test")], [ArithmeticError(6)]) >> Fail(
		[OSError("wow")], [TypeError("cool")]
	) == Fail(
		[SyntaxError("test"), OSError("wow")], [ArithmeticError(6), TypeError("cool")]
	)

	assert Fail(
		[SyntaxError("test"), SyntaxError("test2")],
		[ArithmeticError(6), ArithmeticError(7)],
	) >> Fail([OSError("wow")], [TypeError("cool")]) == Fail(
		[SyntaxError("test"), SyntaxError("test2"), OSError("wow")],
		[ArithmeticError(6), ArithmeticError(7), TypeError("cool")],
	)


def test_okay_lshift():
	assert Okay(37) << Okay(38) == Okay(37)
	assert Okay(37) << Okay("test") == Okay(37)
	assert Okay(37) << Warn([ArithmeticError(6)], 36) == Warn([ArithmeticError(6)], 37)
	assert Okay(37) << Fail([SyntaxError("test")], [ArithmeticError(6)]) == Fail(
		[SyntaxError("test")], [ArithmeticError(6)]
	)


def test_warning_lshift():
	assert Warn([ArithmeticError(6)], 37) << Okay(36) == Warn([ArithmeticError(6)], 37)

	assert Warn([ArithmeticError(6)], 37) << Warn([SyntaxError("test")], 36) == Warn(
		[ArithmeticError(6), SyntaxError("test")], 37
	)

	assert Warn([ArithmeticError(6), ArithmeticError(7)], 36) << Warn(
		[SyntaxError("test"), TypeError("cool")], 37
	) == Warn(
		[
			ArithmeticError(6),
			ArithmeticError(7),
			SyntaxError("test"),
			TypeError("cool"),
		],
		36,
	)

	assert Warn([ArithmeticError(6)], 37) << Fail(
		[SyntaxError("test")], [TypeError("cool")]
	) == Fail([SyntaxError("test")], [ArithmeticError(6), TypeError("cool")])


def test_fail_lshift():
	assert Fail([SyntaxError("test")], [ArithmeticError(6)]) << Okay(36) == Fail(
		[SyntaxError("test")], [ArithmeticError(6)]
	)

	assert Fail([SyntaxError("test")], [ArithmeticError(6)]) << Warn(
		[TypeError("cool")], 37
	) == Fail([SyntaxError("test")], [ArithmeticError(6), TypeError("cool")])

	assert Fail([SyntaxError("test")], [ArithmeticError(6)]) << Fail(
		[OSError("wow")], [TypeError("cool")]
	) == Fail(
		[SyntaxError("test"), OSError("wow")], [ArithmeticError(6), TypeError("cool")]
	)

	assert Fail(
		[SyntaxError("test"), SyntaxError("test2")],
		[ArithmeticError(6), ArithmeticError(7)],
	) << Fail([OSError("wow")], [TypeError("cool")]) == Fail(
		[SyntaxError("test"), SyntaxError("test2"), OSError("wow")],
		[ArithmeticError(6), ArithmeticError(7), TypeError("cool")],
	)


def test_append_merge():
	assert merge(Okay(1), Okay(2), MergeStrategies.APPEND) == Okay([1, 2])

	assert merge(
		Okay(1), Warn([ArithmeticError(6)], 2), MergeStrategies.APPEND
	) == Warn([ArithmeticError(6)], [1, 2])

	assert merge(
		Okay(1),
		Fail([SyntaxError("test")], [ArithmeticError(6)]),
		MergeStrategies.APPEND,
	) == Fail([SyntaxError("test")], [ArithmeticError(6)])

	assert merge(
		Warn([ArithmeticError(7)], 1),
		Fail([SyntaxError("test")], [ArithmeticError(6)]),
		MergeStrategies.APPEND,
	) == Fail([SyntaxError("test")], [ArithmeticError(7), ArithmeticError(6)])


def test_merge_all():
	rs = [Okay(1), Okay(2), Warn([ArithmeticError(6)], 3), Okay(4)]

	assert merge_all(*rs, fn=MergeStrategies.KEEP_FIRST) == Warn(
		[ArithmeticError(6)], 1
	)

	assert merge_all(*rs, fn=MergeStrategies.KEEP_LAST) == Warn([ArithmeticError(6)], 4)

	assert merge_all(*rs, fn=MergeStrategies.APPEND) == Warn(
		[ArithmeticError(6)], [1, 2, 3, 4]
	)


def test_okay_map():
	assert Okay(37).map(lambda x: f"my {x}") == Okay("my 37")


def test_warning_map():
	assert Warn([ArithmeticError(6)], 37).map(lambda x: f"my {x}") == Warn(
		[ArithmeticError(6)], "my 37"
	)


def test_error_map():
	assert Fail([ArithmeticError(6)], [TypeError("test")]).map(
		lambda x: f"my {x}"
	) == Fail([ArithmeticError(6)], [TypeError("test")])


def test_okay_flatmap():
	assert Okay(37).flat_map(lambda x: Okay(f"my {x}")) == Okay("my 37")

	assert Okay(37).flat_map(lambda x: Warn([ArithmeticError(6)], f"my {x}")) == Warn(
		[ArithmeticError(6)], "my 37"
	)

	assert Okay(37).flat_map(
		lambda x: Fail([TypeError("test")], [ArithmeticError(6)])
	) == Fail([TypeError("test")], [ArithmeticError(6)])


def test_warning_flatmap():
	assert Warn([ArithmeticError(6)], 37).flat_map(lambda x: Okay(f"my {x}")) == Warn(
		[ArithmeticError(6)], "my 37"
	)

	assert Warn([ArithmeticError(6)], 37).flat_map(
		lambda x: Warn([TypeError("test")], f"my {x}")
	) == Warn([ArithmeticError(6), TypeError("test")], "my 37")

	assert Warn([ArithmeticError(6)], 37).flat_map(
		lambda x: Fail([SyntaxError("cool")], [TypeError("test")])
	) == Fail([SyntaxError("cool")], [ArithmeticError(6), TypeError("test")])


def test_error_flatmap():
	assert Fail([SyntaxError("cool")], [TypeError("test")]).flat_map(
		lambda x: Okay(37)
	) == Fail([SyntaxError("cool")], [TypeError("test")])

	assert Fail([SyntaxError("cool")], [TypeError("test")]).flat_map(
		lambda x: Warn([ArithmeticError(6)], 37)
	) == Fail([SyntaxError("cool")], [TypeError("test")])

	assert Fail([SyntaxError("cool")], [TypeError("test")]).flat_map(
		lambda x: Fail([OSError("wow")], [ArithmeticError(6)])
	) == Fail([SyntaxError("cool")], [TypeError("test")])


def test_flatmap_short_circuit_on_error():
	res = (
		Okay(37)
		.flat_map(lambda x: Okay(f"precious {x}"))
		.flat_map(lambda x: Fail([SyntaxError(f"cool {x}")], [TypeError("test")]))
		.flat_map(lambda x: Fail([SyntaxError(f"wow, {x}")], [TypeError("test2")]))
	)

	# print(res)
	# print(Fail([SyntaxError("cool precious 37")], [TypeError("test")]))

	assert res == Fail([SyntaxError("cool precious 37")], [TypeError("test")])


def test_str():
	assert str(Okay(37)) == "Result.Okay[int](37)"
	assert (
		str(Warn([ArithmeticError(6), TypeError("wow")], 37))
		== "Result.Warn[int](37) with the following warnings:\n    > [ArithmeticError] 6\n    > [TypeError] wow\n"
	)
	assert str(Warn([], 37)) == "Result.Warn[int](37) with no warnings"
	assert (
		str(
			Fail(
				[SyntaxError("test"), OSError("awa")],
				[ArithmeticError(6), TypeError("wow")],
			)
		)
		== "Result.Fail with the following warnings:\n    > [ArithmeticError] 6\n    > [TypeError] wow\n and the following errors:\n    > [SyntaxError] test\n    > [OSError] awa\n"
	)
	assert str(Fail([], [])) == "Result.Fail with no warnings and no errors"

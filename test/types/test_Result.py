from pytest import raises

from exseos.types.ComparableError import ComparableError
from exseos.types.Result import Okay, Warning, Error


def test_is_okay():
	assert Okay(37).is_okay
	assert not Warning([TypeError()], 37).is_okay
	assert not Error([ArithmeticError()], [TypeError()]).is_okay


def test_is_warning():
	assert not Okay(37).is_warning
	assert Warning([TypeError()], 37).is_warning
	assert not Error([ArithmeticError()], [TypeError()]).is_warning


def test_is_error():
	assert not Okay(37).is_error
	assert not Warning([TypeError()], 37).is_error
	assert Error([ArithmeticError()], [TypeError()]).is_error


def test_val():
	assert Okay(37).val == 37
	assert Warning([TypeError()], "test").val == "test"

	with raises(TypeError):
		Error([ArithmeticError()], [ArithmeticError()]).val


def test_warnings():
	assert ComparableError.array_encapsulate(
		Warning([ArithmeticError(6)], 37).warnings
	) == [ArithmeticError(6)]
	assert ComparableError.array_encapsulate(
		Error([SyntaxError()], [ArithmeticError(6)]).warnings
	) == [ArithmeticError(6)]

	with raises(TypeError):
		Okay(37).warnings


def test_errors():
	assert ComparableError.array_encapsulate(
		Error([SyntaxError()], [ArithmeticError(6)]).errors
	) == [SyntaxError()]

	with raises(TypeError):
		Okay(37).errors

	with raises(TypeError):
		Warning([ArithmeticError(6)], 37).errors


def test_eq():
	assert Okay(37) == Okay(37)
	assert Warning([ArithmeticError(6)], 37) == Warning([ArithmeticError(6)], 37)
	assert Error([SyntaxError()], [ArithmeticError(6)]) == Error(
		[SyntaxError()], [ArithmeticError(6)]
	)

	assert Warning([], 37) == Warning([], 37)
	assert Error([], []) == Error([], [])

	assert Okay(37) != Okay(36)
	assert Okay(37) != Okay("37")
	assert Okay(37) != 37

	assert Warning([ArithmeticError(6)], 37) != Warning([ArithmeticError(6)], 36)
	assert Warning([ArithmeticError(6)], 37) != Warning([ArithmeticError(6)], "37")
	assert Warning([ArithmeticError(6)], 37) != Warning([SyntaxError(6)], 37)
	assert Warning([ArithmeticError(6)], 37) != Warning([ArithmeticError(5)], 37)
	assert Warning([ArithmeticError(6)], 37) != 37
	assert Warning([], 37) != 37
	assert Warning([ArithmeticError(6)], 37) != ArithmeticError(6)

	assert Error([SyntaxError("test")], [ArithmeticError(6)]) != Error(
		[SyntaxError("test")], [ArithmeticError(5)]
	)
	assert Error([SyntaxError("test")], [ArithmeticError(6)]) != Error(
		[ArithmeticError(6)], [SyntaxError("test")]
	)
	assert Error([SyntaxError("test")], [ArithmeticError(6)]) != Error(
		[SyntaxError("test")], [ArithmeticError(5)]
	)
	assert Error([SyntaxError("test")], [ArithmeticError(6)]) != Error(
		[SyntaxError("test")], [ArithmeticError("6")]
	)
	assert Error([SyntaxError("test")], [ArithmeticError(6)]) != Error(
		[SyntaxError("test2")], [ArithmeticError(6)]
	)
	assert Error([SyntaxError("test")], [ArithmeticError(6)]) != SyntaxError("test")
	assert Error([SyntaxError("test")], [ArithmeticError(6)]) != [SyntaxError("test")]
	assert Error([SyntaxError("test")], [ArithmeticError(6)]) != "test"
	assert Error([SyntaxError("test")], [ArithmeticError(6)]) != ArithmeticError(6)
	assert Error([SyntaxError("test")], [ArithmeticError(6)]) != [ArithmeticError(6)]
	assert Error([SyntaxError("test")], [ArithmeticError(6)]) != 6

	assert Okay(37) != Warning([ArithmeticError(6)], 37)
	assert Okay(37) != Error([SyntaxError()], [ArithmeticError(6)])

	assert Warning([ArithmeticError(6)], 37) != Okay(37)
	assert Warning([ArithmeticError(6)], 37) != Warning(
		[ArithmeticError(6), SyntaxError("test")], 37
	)
	assert Warning([ArithmeticError(6)], 37) != Error(
		[SyntaxError()], [ArithmeticError(6)]
	)

	assert Error([SyntaxError()], [ArithmeticError(6)]) != Okay(37)
	assert Error([SyntaxError()], [ArithmeticError(6)]) != Error([SyntaxError()], [])
	assert Error([SyntaxError()], [ArithmeticError(6)]) != Error(
		[], [ArithmeticError(6)]
	)
	assert Error([SyntaxError()], [ArithmeticError(6)]) != Error([], [])
	assert Error([SyntaxError()], [ArithmeticError(6)]) != Warning(
		[ArithmeticError(6)], 37
	)


def test_okay_rshift():
	assert Okay(37) >> Okay(38) == Okay(38)
	assert Okay(37) >> Okay("test") == Okay("test")
	assert Okay(37) >> Warning([ArithmeticError(6)], 36) == Warning(
		[ArithmeticError(6)], 36
	)
	assert Okay(37) >> Error([SyntaxError("test")], [ArithmeticError(6)]) == Error(
		[SyntaxError("test")], [ArithmeticError(6)]
	)


def test_warning_rshift():
	assert Warning([ArithmeticError(6)], 37) >> Okay(36) == Warning(
		[ArithmeticError(6)], 36
	)

	assert Warning([ArithmeticError(6)], 37) >> Warning(
		[SyntaxError("test")], 36
	) == Warning([ArithmeticError(6), SyntaxError("test")], 36)

	assert Warning([ArithmeticError(6), ArithmeticError(7)], 36) >> Warning(
		[SyntaxError("test"), TypeError("cool")], 37
	) == Warning(
		[
			ArithmeticError(6),
			ArithmeticError(7),
			SyntaxError("test"),
			TypeError("cool"),
		],
		37,
	)

	assert Warning([ArithmeticError(6)], 37) >> Error(
		[SyntaxError("test")], [TypeError("cool")]
	) == Error([SyntaxError("test")], [ArithmeticError(6), TypeError("cool")])


def test_error_rshift():
	assert Error([SyntaxError("test")], [ArithmeticError(6)]) >> Okay(36) == Error(
		[SyntaxError("test")], [ArithmeticError(6)]
	)

	assert Error([SyntaxError("test")], [ArithmeticError(6)]) >> Warning(
		[TypeError("cool")], 37
	) == Error([SyntaxError("test")], [ArithmeticError(6), TypeError("cool")])

	assert Error([SyntaxError("test")], [ArithmeticError(6)]) >> Error(
		[OSError("wow")], [TypeError("cool")]
	) == Error(
		[SyntaxError("test"), OSError("wow")], [ArithmeticError(6), TypeError("cool")]
	)

	assert Error(
		[SyntaxError("test"), SyntaxError("test2")],
		[ArithmeticError(6), ArithmeticError(7)],
	) >> Error([OSError("wow")], [TypeError("cool")]) == Error(
		[SyntaxError("test"), SyntaxError("test2"), OSError("wow")],
		[ArithmeticError(6), ArithmeticError(7), TypeError("cool")],
	)


def test_okay_map():
	assert Okay(37).map(lambda x: f"my {x}") == Okay("my 37")


def test_warning_map():
	assert Warning([ArithmeticError(6)], 37).map(lambda x: f"my {x}") == Warning(
		[ArithmeticError(6)], "my 37"
	)


def test_error_map():
	assert Error([ArithmeticError(6)], [TypeError("test")]).map(
		lambda x: f"my {x}"
	) == Error([ArithmeticError(6)], [TypeError("test")])


def test_okay_flatmap():
	assert Okay(37).flat_map(lambda x: Okay(f"my {x}")) == Okay("my 37")

	assert Okay(37).flat_map(
		lambda x: Warning([ArithmeticError(6)], f"my {x}")
	) == Warning([ArithmeticError(6)], "my 37")

	assert Okay(37).flat_map(
		lambda x: Error([TypeError("test")], [ArithmeticError(6)])
	) == Error([TypeError("test")], [ArithmeticError(6)])


def test_warning_flatmap():
	assert Warning([ArithmeticError(6)], 37).flat_map(
		lambda x: Okay(f"my {x}")
	) == Warning([ArithmeticError(6)], "my 37")

	assert Warning([ArithmeticError(6)], 37).flat_map(
		lambda x: Warning([TypeError("test")], f"my {x}")
	) == Warning([ArithmeticError(6), TypeError("test")], "my 37")

	assert Warning([ArithmeticError(6)], 37).flat_map(
		lambda x: Error([SyntaxError("cool")], [TypeError("test")])
	) == Error([SyntaxError("cool")], [ArithmeticError(6), TypeError("test")])


def test_error_flatmap():
	assert Error([SyntaxError("cool")], [TypeError("test")]).flat_map(
		lambda x: Okay(37)
	) == Error([SyntaxError("cool")], [TypeError("test")])

	assert Error([SyntaxError("cool")], [TypeError("test")]).flat_map(
		lambda x: Warning([ArithmeticError(6)], 37)
	) == Error([SyntaxError("cool")], [TypeError("test")])

	assert Error([SyntaxError("cool")], [TypeError("test")]).flat_map(
		lambda x: Error([OSError("wow")], [ArithmeticError(6)])
	) == Error([SyntaxError("cool")], [TypeError("test")])


def test_flatmap_short_circuit_on_error():
	res = (
		Okay(37)
		.flat_map(lambda x: Okay(f"precious {x}"))
		.flat_map(lambda x: Error([SyntaxError(f"cool {x}")], [TypeError("test")]))
		.flat_map(lambda x: Error([SyntaxError(f"wow, {x}")], [TypeError("test2")]))
	)

	# print(res)
	# print(Error([SyntaxError("cool precious 37")], [TypeError("test")]))

	assert res == Error([SyntaxError("cool precious 37")], [TypeError("test")])


def test_str():
	assert str(Okay(37)) == "Okay[int](37)"
	assert (
		str(Warning([ArithmeticError(6), TypeError("wow")], 37))
		== "Warning[int](37) with the following warnings:\n    > [ArithmeticError] 6\n    > [TypeError] wow\n"
	)
	assert str(Warning([], 37)) == "Warning[int](37) with no warnings"
	assert (
		str(
			Error(
				[SyntaxError("test"), OSError("awa")],
				[ArithmeticError(6), TypeError("wow")],
			)
		)
		== "Error with the following warnings:\n    > [ArithmeticError] 6\n    > [TypeError] wow\n and the following errors:\n    > [SyntaxError] test\n    > [OSError] awa\n"
	)
	assert str(Error([], [])) == "Error with no warnings and no errors"

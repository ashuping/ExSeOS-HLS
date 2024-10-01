from pytest import raises

from exseos.types.Either import Either, Left, Right


def test_is_right():
	assert not Left(12).is_right
	assert Right("str").is_right


def test_val():
	assert Right("str").val == "str"
	with raises(TypeError):
		Left(12).val


def test_lval():
	assert Left(12).lval == 12
	with raises(TypeError):
		Right("str").lval


def test_equals():
	assert Left(12) == Left(12)
	assert Left(12) != Left(13)
	assert Left(12) != Left("12")
	assert Left(12) != 12

	assert Right(12) == Right(12)
	assert Right(12) != Right(13)
	assert Right(12) != Right("12")
	assert Right(12) != 12

	assert Right(12) != Left(12)
	assert Left(12) != Right(12)


def test_str():
	assert str(Left(12)) == "Left[int](12)"
	assert str(Left("test")) == "Left[str](test)"
	assert str(Right(12)) == "Right[int](12)"
	assert str(Right("test")) == "Right[str](test)"


def test_map_right():
	transform = lambda x: f"my {x}"

	assert Right("str").map(transform) == Right("my str")
	assert Right(12).map(transform) == Right("my 12")


def test_map_left():
	transform = lambda x: f"my {x}"

	assert Left("str").map(transform) == Left("str")
	assert Left(12).map(transform) == Left(12)


def test_compound_map_right():
	tf_a = lambda x: f"precious {x}"
	tf_b = lambda x: f"my {x}"

	assert Right("str").map(tf_a).map(tf_b) == Right("my precious str")
	assert Right(12).map(tf_a).map(tf_b) == Right("my precious 12")


def test_compound_map_left():
	tf_a = lambda x: f"precious {x}"
	tf_b = lambda x: f"my {x}"

	assert Left("str").map(tf_a).map(tf_b) == Left("str")
	assert Left(12).map(tf_a).map(tf_b) == Left(12)


def test_flat_map_right_to_right():
	transform = lambda x: Right(f"my {x}")

	assert Right("str").flat_map(transform) == Right("my str")
	assert Right(12).flat_map(transform) == Right("my 12")


def test_flat_map_right_to_left():
	transform = lambda x: Left(f"my {x}")

	assert Right("str").flat_map(transform) == Left("my str")
	assert Right(12).flat_map(transform) == Left("my 12")


def test_flat_map_left_to_left():
	transform = lambda x: Left(f"my {x}")

	assert Left("str").flat_map(transform) == Left("str")
	assert Left(12).flat_map(transform) == Left(12)


def test_flat_map_left_to_right():
	transform = lambda x: Right(f"my {x}")

	assert Left("str").flat_map(transform) == Left("str")
	assert Left(12).flat_map(transform) == Left(12)


def test_exception_comparison():
	# Exceptions use ComparableError's __eq__ operator to allow comparison by
	# value.
	assert Left(TypeError("test")) == Left(TypeError("test"))
	assert Left(TypeError("test")) != Left(TypeError("test2"))
	assert Left(TypeError("test")) != Left(ArithmeticError("test"))

	assert Right(TypeError("test")) == Right(TypeError("test"))
	assert Right(TypeError("test")) != Right(TypeError("test2"))
	assert Right(TypeError("test")) != Right(ArithmeticError("test"))

	assert Right(TypeError("test")) != Left(TypeError("test"))
	assert Left(TypeError("test")) != Right(TypeError("test"))


def test_flat_map_long_chain():
	assert Right("str").flat_map(lambda x: Right(f"precious {x}")).flat_map(
		lambda x: Right(f"my {x}")
	).flat_map(lambda x: Right(f"wow, {x}")) == Right("wow, my precious str")


def test_flat_map_and_map_chain():
	def fn_stoi(x: str) -> Either[Exception, int]:
		try:
			return Right(int(x))
		except Exception as e:
			return Left(e)

	def fn_do_invert(x: int) -> Either[Exception, float]:
		try:
			return Right(1 / x)
		except Exception as e:
			return Left(e)

	def fn_do_stringify(x: float) -> str:
		return f"wow, it's {x:.4}!"

	res = Right("12").flat_map(fn_stoi).flat_map(fn_do_invert).map(fn_do_stringify)

	print(f"Computation result: {res}")
	assert res == Right("wow, it's 0.08333!")


def test_cancelled_chain():
	def fn_stoi(x: str) -> Either[Exception, int]:
		try:
			return Right(int(x))
		except Exception as e:
			return Left(e)

	def fn_do_invert(x: int) -> Either[Exception, float]:
		try:
			return Right(1 / x)
		except Exception as e:
			return Left(e)

	def fn_do_stringify(x: float) -> str:
		return f"wow, it's {x:.4}!"

	res = Right("0").flat_map(fn_stoi).flat_map(fn_do_invert).map(fn_do_stringify)

	assert not res.is_right
	assert res.lval.__class__.__name__ == "ZeroDivisionError"

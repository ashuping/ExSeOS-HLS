from pytest import raises

from modules.types.Option import Option, Nothing, Some

def test_has_val():
	assert not Nothing().has_val
	assert Some(37).has_val
	assert Some("str").has_val
	assert Some(None).has_val

def test_val():
	assert Some(37).val == 37
	assert Some("str").val == "str"
	assert Some(None).val == None

	with raises(TypeError):
		Nothing().val

def test_str():
	assert str(Some(37))     == "Some[int](37)"
	assert str(Some("test")) == "Some[str](test)"
	assert str(Some(None))   == "Some[NoneType](None)"

	assert str(Nothing()) == "Nothing"

def test_eq():
	assert Some(37)     == Some(37)
	assert Some("test") == Some("test")
	assert Some(None)   == Some(None)
	
	assert Some(37)     != Some(36)
	assert Some("test") != Some("tes")
	assert Some(37)     != Some("37")

	assert Some(37)     != Nothing()
	assert Some("test") != Nothing()
	assert Some(None)   != Nothing()

	assert Nothing()    != Some(37)
	assert Nothing()    != Some("test")
	assert Nothing()    != Some(None)

	assert Nothing()    == Nothing()

def test_exc_eq():
	# ExSeOS-H monads use `ComparableError` to enable comparison of Exceptions
	# by value. Exceptions of the same type with the same args are treated as
	# equal for the purpose of comparing monads.
	assert Some(TypeError("test")) == Some(TypeError("test"))
	assert Some(TypeError("test")) != Some(TypeError("test2"))
	assert Some(TypeError("test")) != Some(ArithmeticError("test"))
	assert Some(TypeError("test")) != Nothing()
	assert Nothing()               != Some(TypeError("test"))

def test_map_some():
	transform = lambda x: f"my {x}"

	assert Some(37).map(transform)     == Some("my 37")
	assert Some("test").map(transform) == Some("my test")
	assert Some(None).map(transform)   == Some("my None")

def test_chain_map_some():
	tf_a = lambda x: f"precious {x}"
	tf_b = lambda x: f"my {x}"

	assert Some(37)    .map(tf_a).map(tf_b) == Some("my precious 37")
	assert Some("test").map(tf_a).map(tf_b) == Some("my precious test")
	assert Some(None)  .map(tf_a).map(tf_b) == Some("my precious None")

def test_map_nothing():
	transform = lambda x: f"my {x}"

	assert Nothing().map(transform) == Nothing()

def test_chain_map_nothing():
	tf_a = lambda x: f"precious {x}"
	tf_b = lambda x: f"my {x}"

	assert Nothing().map(tf_a).map(tf_b) == Nothing()

def test_flat_map_some():
	transform = lambda x: Some(f"my {x}")

	assert Some(37).flat_map(transform)     == Some("my 37")
	assert Some("test").flat_map(transform) == Some("my test")
	assert Some(None).flat_map(transform)   == Some("my None")

def test_flat_map_nothing():
	transform = lambda x: Some(f"my {x}")

	assert Nothing().flat_map(transform) == Nothing()

def test_flat_map_and_map_long_chain():
	def tf_stoi(x: str) -> Option[int]:
		try:
			return Some(int(x))
		except Exception as e:
			return Nothing()

	def tf_double(x: int) -> Option[int]:
		return Some(2*x)

	def tf_invert(x: int) -> Option[float]:
		try:
			return Some(1/x)
		except Exception as e:
			return Nothing()
	
	def tf_stringify(x: float) -> str:
		return f"wow, it's {x:.2}"

	assert Some("37") \
		.flat_map(tf_stoi) \
		.flat_map(tf_double) \
		.flat_map(tf_invert) \
		.map(tf_stringify) == Some("wow, it's 0.014")

	assert Some("0") \
		.flat_map(tf_stoi) \
		.flat_map(tf_double) \
		.flat_map(tf_invert) \
		.map(tf_stringify) == Nothing(), \
		"`map` should be skipped, since `tf_invert` returns Nothing()."

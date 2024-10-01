from exseos.types.ComparableError import ComparableError


def test_get_exc():
	x = TypeError("test error")
	assert ComparableError(x).exc == x


def test_encapsulate():
	class CustomException(Exception):
		pass

	class NotAnException:
		pass

	assert isinstance(ComparableError.encapsulate(TypeError()), ComparableError)
	assert isinstance(ComparableError.encapsulate(CustomException()), ComparableError)
	assert isinstance(ComparableError.encapsulate(12), int)
	assert isinstance(ComparableError.encapsulate("test"), str)
	assert isinstance(ComparableError.encapsulate(NotAnException()), NotAnException)


def test_eq():
	assert ComparableError(TypeError("test")) == ComparableError(TypeError("test"))
	assert ComparableError(TypeError("test")) != ComparableError(TypeError("test2"))
	assert ComparableError(TypeError("test")) != ComparableError(
		ArithmeticError("test")
	)
	assert ComparableError(TypeError("test")) != "test"


def test_auto_encapsulate():
	assert ComparableError(TypeError("test")) == TypeError("test")
	assert ComparableError(TypeError("test")) != TypeError("test2")

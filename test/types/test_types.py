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

from abc import ABC

from exseos.types.Result import Okay, Warn, Fail
from exseos.types import (
	type_check,
	common,
	common_t,
	NoCommonTypeError,
	BroadCommonTypeWarning,
)


class TestSuperclass:
	pass


class TestSubclass1(TestSuperclass):
	pass


class TestSubclass2(TestSuperclass):
	pass


class TestUnrelatedClass:
	pass


class TestAbstractClass(ABC):
	pass


class TestUnrelatedAbstract(ABC):
	pass


def test_BroadCommonTypeWarning():
	w = BroadCommonTypeWarning([int, str], object, "test note")

	assert (
		str(w)
		== "Types `int` and `str` only share the broad common type `object`. test note"
	)

	assert w.types == [int, str]
	assert w.common is object
	assert w.note == "test note"


def test_NoCommonTypeError():
	e = NoCommonTypeError([int, str], "test note")

	assert str(e) == "Types `int` and `str` do not share a common type. test note"

	assert e.types == [int, str]
	assert e.note == "test note"


def test_type_check_exact_match():
	sup = TestSuperclass()
	sub1 = TestSubclass1()
	sub2 = TestSubclass2()

	assert type_check(sup, TestSuperclass)
	assert type_check(sub1, TestSubclass1)
	assert type_check(sub2, TestSubclass2)

	assert not type_check(sup, TestUnrelatedClass)


def test_type_check_subclass_match():
	sub1 = TestSubclass1()
	sub2 = TestSubclass2()

	assert type_check(sub1, TestSuperclass)
	assert type_check(sub2, TestSuperclass)

	assert not type_check(sub2, TestSubclass1)
	assert not type_check(sub1, TestUnrelatedClass)


def test_common_t_sibling():
	assert common_t(TestSubclass1, TestSubclass2) == Okay(TestSuperclass)


def test_common_t_parent():
	assert common_t(TestSubclass1, TestSuperclass) == Okay(TestSuperclass)


def test_common_t_child():
	assert common_t(TestSuperclass, TestSubclass2) == Okay(TestSuperclass)


def test_common_t_broad_related():
	assert common_t(TestAbstractClass, TestUnrelatedAbstract) == Warn(
		[BroadCommonTypeWarning([TestAbstractClass, TestUnrelatedAbstract], ABC)], ABC
	)


def test_common_t_unrelated():
	assert common_t(TestSuperclass, TestUnrelatedClass) == Fail(
		[NoCommonTypeError([TestSuperclass, TestUnrelatedClass])]
	)


def test_common():
	# `common` is a wrapper around `common_t`, so we don't need to test it as
	# extensively.

	sup = TestSuperclass()
	sub1 = TestSubclass1()
	sub2 = TestSubclass2()
	unr = TestUnrelatedClass()

	assert common(sup, sub1) == Okay(TestSuperclass)
	assert common(sub2, sup) == Okay(TestSuperclass)
	assert common(sub1, sub2) == Okay(TestSuperclass)
	assert common(sub1, unr) == Fail(
		[NoCommonTypeError([TestSubclass1, TestUnrelatedClass])]
	)

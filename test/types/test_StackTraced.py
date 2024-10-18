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

from exseos.types.StackTraced import StackTraced

from copy import deepcopy
import pytest
from traceback import FrameSummary, format_exception, format_list

test_arg_vals = (1, "a", None, Exception(), False, StackTraced(Exception()))


@pytest.mark.parametrize("val", test_arg_vals)
def test_construct(val):
	to_test = StackTraced(val)
	assert to_test.val == val
	assert isinstance(to_test.stack_trace, tuple)
	for frame in to_test.stack_trace:
		assert isinstance(frame, FrameSummary)


@pytest.mark.parametrize("val", test_arg_vals)
def test_str(val):
	st = StackTraced(val)
	expected = (
		"\n".join(format_list(st.stack_trace))
		+ "\n"
		+ (
			"".join(format_exception(st.val))
			if isinstance(st.val, Exception)
			else f"\n[{type(st.val).__name__}]: {st.val}"
		)
	)

	actual = str(st)

	print(f"Expected: {expected}")
	print(f"Actual  : {actual}")

	assert expected == actual


@pytest.mark.parametrize("val", test_arg_vals)
def test_repr(val):
	assert repr(StackTraced(val)) == f"StackTraced({repr(val)})"


map_fns = (
	(1, lambda x: x + 1),
	("test", lambda x: f"my {x}"),
	(None, lambda x: x),
	(True, lambda x: None),
)


@pytest.mark.parametrize(("val", "fn"), map_fns)
def test_map(val, fn):
	s = StackTraced(val)

	trace = deepcopy(s.stack_trace)

	new = s.map(fn)

	assert new == StackTraced(fn(val))
	assert new.stack_trace == trace


flat_map_fns = (
	(1, lambda x: StackTraced(x + 1)),
	("test", lambda x: StackTraced(f"my {x}")),
	(None, lambda x: StackTraced(x)),
	(True, lambda x: StackTraced(None)),
)


@pytest.mark.parametrize(("val", "fn"), flat_map_fns)
def test_flat_map(val, fn):
	s = StackTraced(val)

	trace = deepcopy(s.stack_trace)

	new = s.flat_map(fn)

	assert new == fn(val)
	assert new.stack_trace != trace

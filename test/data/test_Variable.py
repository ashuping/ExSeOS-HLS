'''
    Chicory ML Workflow Manager
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
'''
from modules.data.Variable import UnboundVariable, BoundVariable
from modules.types.Option import Option, Nothing, Some

def test_is_bound():
	assert BoundVariable('x', 2).is_bound
	assert BoundVariable('x', None).is_bound
	assert not UnboundVariable('x').is_bound

def test_name():
	assert BoundVariable('x', 2).name == 'x'
	assert UnboundVariable('y').name == 'y'
	assert UnboundVariable('multi-word name').name == 'multi-word name'

def test_var_type():
	assert BoundVariable('x', 2, Some(int)).var_type == Some(int)
	assert UnboundVariable('y', Some(str)).var_type == Some(str)

def test_basic_type_inference():
	assert BoundVariable('x', 2).var_type == Some(int)
	assert BoundVariable('x', 2).var_type_inferred == True
	assert BoundVariable('x', 2, Some(int)).var_type_inferred == False
	
	assert UnboundVariable('y', default=Some(2)).var_type == Some(int)
	assert UnboundVariable('y', default=Some(2)).var_type_inferred == True
	assert UnboundVariable('y', Some(int), default=Some(2)).var_type_inferred == False

	assert BoundVariable('x', 2, default=Some(2)).var_type == Some(int)
	assert BoundVariable('x', 2, default=Some(2)).var_type_inferred == True

	assert BoundVariable('x', 2, Some(int), default=Some(2)).var_type == Some(int)
	assert BoundVariable('x', 2, Some(int), default=Some(2)).var_type_inferred == False

def test_explicit_type_overrides_inference():
	assert BoundVariable('x', 2, Some(str), default=Some(2)).var_type == Some(str)
	assert BoundVariable('x', 2, Some(str), default=Some(2)).var_type_inferred == False

def test_type_inference_uses_common_ancestors():
	class TestSuperclass():
		pass

	class TestSubclass1(TestSuperclass):
		pass

	class TestSubclass2(TestSuperclass):
		pass

	# BoundVariables should choose the closest common ancestor of `val` and `default` when performing type inference.
	assert BoundVariable('x', TestSubclass1(), default=Some(TestSubclass2())).var_type == Some(TestSuperclass)

	# Sometimes, the closest common ancestor is `object`.
	assert BoundVariable('x', TestSubclass1(), default=Some(1)).var_type == Some(object)
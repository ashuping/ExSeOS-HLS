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

from enum import Enum

class Strategy(Enum):
	''' Enumeration containing strategies for handling constraint failures.
	'''
	# Fail immediately if the Constraint is not met
	FAIL  = 1 

	# If the Constraint is not met, clamp the failing value to the nearest
	# acceptable one.
	CLAMP = 2 
	
	# If the Constraint is not met, set the failing value to a constant.
	SET   = 3


class Constraint:
	''' Defines a constraint on the experiment. 

		Constraints ensure that a value at a specific stage of the experiment is
		within acceptable parameters. They can also constrain pre-experiment
		operations such as I/O wiring - see `WiringConstraint`

	'''
	pass

class RangeConstraint(Constraint):
	''' Constrains a value to be within a specified range.
	'''
	pass

class EqualsConstraint(Constraint):
	''' Constrains a value to be equal to a specified constant
	'''
	pass

class WiringConstraint(Constraint):
	''' Constrains the automatic wiring system.

		This can be used to override the default wiring for a specific Input or
		Variable.
	'''
	pass
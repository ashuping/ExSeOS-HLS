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

from exseos.experiment.optimizer.GridOptimizer import GridOptimizer
from exseos.experiment.optimizer.Optimizer import OptimizerIteration
from exseos.experiment.optimizer.OptimizerParameter import ContinuousOptimizerParameter
from exseos.experiment.optimizer.OptimizerTarget import TargetMaximize
from exseos.types.Variable import BoundVariable, UnboundVariable, VariableSet


def test_one_param():
	opt = GridOptimizer(
		(ContinuousOptimizerParameter("x", 0, 10),),
		5,
		(TargetMaximize(UnboundVariable("y"), 0, 100),),
	)

	# print(opt.grid)

	assert opt.grid == (
		VariableSet((BoundVariable("x", 0.0),)),
		VariableSet((BoundVariable("x", 2.0),)),
		VariableSet((BoundVariable("x", 4.0),)),
		VariableSet((BoundVariable("x", 6.0),)),
		VariableSet((BoundVariable("x", 8.0),)),
	)

	assert opt.next(2, 2, ()) == (
		VariableSet((BoundVariable("x", 4.0),)),
		VariableSet((BoundVariable("x", 6.0),)),
	)

	ins = (
		VariableSet((BoundVariable("x", 0.0),)),
		VariableSet((BoundVariable("x", 2.0),)),
		VariableSet((BoundVariable("x", 4.0),)),
		VariableSet((BoundVariable("x", 6.0),)),
		VariableSet((BoundVariable("x", 8.0),)),
	)

	outs = (
		VariableSet((BoundVariable("y", 2.1),)),
		VariableSet((BoundVariable("y", 4.6),)),
		VariableSet((BoundVariable("y", 102.1),)),
		VariableSet((BoundVariable("y", -12.11),)),
		VariableSet((BoundVariable("y", 64.8),)),
	)

	hist = [OptimizerIteration(i, o) for i, o in zip(ins, outs)]

	best_2 = (hist[2], hist[4])

	print(str(best_2))
	print(str(opt.get_best(hist, 2)))

	assert opt.get_best(hist, 2) == best_2

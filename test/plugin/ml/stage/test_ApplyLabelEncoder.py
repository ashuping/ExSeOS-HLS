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

from exseos.plugin.ml.stage.ApplyLabelEncoder import ApplyLabelEncoder
from exseos.types.Variable import VariableSet

import numpy as np
import pytest


@pytest.mark.asyncio
async def test_missing_input():
	assert (await ApplyLabelEncoder().run(VariableSet(()))).is_fail


@pytest.mark.asyncio
async def test_basic():
	to_encode = np.array(["a", "b", "c", "d", "e", "a", "a", "c"])
	res = await ApplyLabelEncoder().run(
		VariableSet((ApplyLabelEncoder.input_vars[0].bind(to_encode),))
	)

	assert res.is_okay

	assert len(res.val) == 2
	assert res.val[0] == ApplyLabelEncoder.output_vars[0].bind(
		np.array([0, 1, 2, 3, 4, 0, 0, 2])
	)


@pytest.mark.asyncio
async def test_multi():
	to_encode_A = np.array(["a", "b", "c", "d", "e", "a", "a", "c"])
	to_encode_B = np.array(["c", "a", "a", "c", "b", "e"])
	res = await ApplyLabelEncoder().run(
		VariableSet((ApplyLabelEncoder.input_vars[0].bind(to_encode_A),))
	)

	assert res.is_okay

	assert len(res.val) == 2
	assert res.val[0] == ApplyLabelEncoder.output_vars[0].bind(
		np.array([0, 1, 2, 3, 4, 0, 0, 2])
	)

	res_B = await ApplyLabelEncoder().run(
		VariableSet(
			(
				ApplyLabelEncoder.input_vars[0].bind(to_encode_B),
				ApplyLabelEncoder.input_vars[1].bind(res.val[1].val.val),
			)
		)
	)

	assert res_B.is_okay
	assert len(res_B.val) == 2
	assert res_B.val[0] == ApplyLabelEncoder.output_vars[0].bind(
		np.array([2, 0, 0, 2, 1, 4])
	)


@pytest.mark.asyncio
async def test_exception():
	assert (
		await ApplyLabelEncoder().run(
			VariableSet((ApplyLabelEncoder.input_vars[0].bind(1),))
		)
	).is_fail

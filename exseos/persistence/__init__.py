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

"""
Tools for persisting ``Experiment`` and ``Workflow`` runs and results.
"""

from exseos.types.Result import Result, Okay, Fail

import dill
import gzip
from typing import Any


def serialize(obj: Any) -> Result[Exception, Exception, bytes]:
	try:
		return Okay(dill.dumps(obj))
	except Exception as e:
		return Fail([e])


def deserialize(ser: str) -> Result[Exception, Exception, Any]:
	try:
		return Okay(dill.loads(ser))
	except Exception as e:
		return Fail([e])


def save_to_file(obj: Any, fname: str) -> Result[Exception, Exception, None]:
	def _save(dat: bytes, to: str) -> Result[Exception, Exception, None]:
		try:
			with gzip.open(to, "wb") as f:
				f.write(dat)
		except Exception as e:
			return Fail([e])
		else:
			return Okay(None)

	return serialize(obj).flat_map(lambda ser_dat: _save(ser_dat, fname))


def load_from_file(fname: str) -> Result[Exception, Exception, Any]:
	def _load(fn: str) -> Result[Exception, Exception, str]:
		try:
			with gzip.open(fn, "rb") as f:
				return Okay(f.read())
		except Exception as e:
			return Fail([e])

	return _load(fname).flat_map(lambda dat: deserialize(dat))

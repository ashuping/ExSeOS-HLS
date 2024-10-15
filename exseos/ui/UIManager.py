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
Provides a basic wrapper around core UI functions (prompting the user,
displaying output, logging, etc).
"""

from exseos.types.Result import Result
from exseos.ui.message.UIMessage import UIMessage

from abc import ABC, abstractmethod


class UIManager(ABC):
	@abstractmethod
	async def display(self, message: UIMessage) -> Result[Exception, Exception, any]:
		"""
		Display a message and capture the user's response.

		:param message: The ``UIMessage`` to display
		:returns: A ``Result`` containing data dependent on the ``UIMessage``.
		"""
		...


class UnsupportedMessageError(Exception):
	"""
	Returned when a ``UIManager`` is asked to display a message type it doesn't
	support.
	"""

	def __init__(self, message: UIMessage, manager: UIManager, note: str = ""):
		msg = (
			f"UI Manager {type(manager).__name__} doesn't support "
			+ f"messages of type '{type(message).__name__}'!"
			+ f" {note}"
			if note
			else ""
		)

		super().__init__(msg)

		self.message = message
		self.manager = manager
		self.note = note


class UserCancelledError(Exception):
	"""
	Returned when a prompt sent to a ``UIManager`` is cancelled by the user.
	"""

	def __init__(self, message: UIMessage, manager: UIManager, note: str = ""):
		msg = (
			f"UI Manager {type(manager).__name__}: "
			+ f"message {message} cancelled by user!"
			+ f" {note}"
			if note
			else ""
		)

		super().__init__(msg)

		self.message = message
		self.manager = manager
		self.note = note

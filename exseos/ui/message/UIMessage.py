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
Provides an abstraction over specific classes of UI message.
"""

from exseos.types.Result import Result
from exseos.ui.message.UIResponseType import UIResponseType

from abc import ABC


class UIMessage(ABC):
	"""
	A message that can be sent to the UI Manager to display to the user. May be
	accompanied by a response.
	"""

	pass


class BasicNotice(UIMessage):
	"""
	A simple text notice.
	"""

	__match_args__ = ("text",)

	return_type = None

	def __init__(self, text: str):
		self.__text = text

	@property
	def text(self) -> str:
		return self.__text


class BasicPrompt(UIMessage):
	"""
	A question that can be responded to.
	"""

	__match_args__ = ("response_type", "prompt")

	return_type = any  # response_type

	def __init__(self, response_type: UIResponseType, prompt: str):
		self.__response_type = response_type
		self.__prompt = prompt

	@property
	def response_type(self):
		return self.__response_type

	@property
	def prompt(self):
		return self.__prompt


class ResultMessage(UIMessage):
	"""
	An informative message showing a ``Result``.
	"""

	__match_args__ = ("result",)

	return_type = None

	def __init__(self, result: Result):
		self.__result = result

	@property
	def result(self) -> Result:
		return self.__result


class ResultContinueConfirm(UIMessage):
	"""
	A prompt that informs the user of a ``Result`` and, if the result is not
	``Okay``, asks the user whether they would like to continue.

	The default behavior is as follows:
	  - If the result is ``Okay``, display information but keep going (return
	    True) without user input.
	  - If the result is ``Warn``, display information and ask the user to
	    confirm whether they want to continue.
	  - If the result is ``Fail``, display information but cancel the operation
	    (return False) without user input.

	This behavior can be overridden using ``can_override_warnings`` (default
	``True``) and ``can_override_errors`` (default ``False``).
	"""

	__match_args__ = ("result", "can_override_warnings", "can_override_errors")

	return_type = bool

	def __init__(
		self,
		result: Result,
		can_override_warnings: bool = True,
		can_override_errors: bool = False,
	):
		self.__result = result
		self.__can_override_warnings = can_override_warnings
		self.__can_override_errors = can_override_errors

	@property
	def result(self) -> Result:
		return self.__result

	@property
	def can_override_warnings(self) -> bool:
		return self.__can_override_warnings

	@property
	def can_override_errors(self) -> bool:
		return self.__can_override_errors

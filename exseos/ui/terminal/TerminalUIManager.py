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
A basic TUI interface.
"""

from exseos.types.Result import Result, Okay, Warn, Fail
from exseos.ui.UIManager import UIManager, UnsupportedMessageError, UserCancelledError
from exseos.ui.message.UIMessage import (
	UIMessage,
	BasicNotice,
	BasicPrompt,
	ResultMessage,
	ResultContinueConfirm,
)
import exseos.ui.message.UIResponseType as UIResponseType

import logging

log = logging.getLogger("[UI]")


class TerminalUIManager(UIManager):
	"""
	A basic TUI interface.
	"""

	async def display(self, message: UIMessage) -> Result[Exception, Exception, any]:
		match message:
			case BasicNotice(text):
				log.info(text)
				return Okay(None)
			case BasicPrompt(res_type, prompt):
				return await self._prompt(prompt, res_type, message)
			case ResultMessage(res):
				self._print_result(res)
				return Okay(None)
			case ResultContinueConfirm(res, ovr_warn, ovr_err):
				self._print_result(res)
				match res:
					case Okay(_):
						return Okay(True)
					case Warn(_, _):
						if ovr_warn:
							return await self._prompt(
								"Continue?", UIResponseType.Boolean(), message
							)
						else:
							return Okay(False)
					case Fail(_, _):
						if ovr_err:
							return await self._prompt(
								"Continue?", UIResponseType.Boolean(), message
							)
						else:
							return Okay(False)
			case _:
				return Fail([UnsupportedMessageError(message, self)])

	def _print_result(self, to_print: Result):
		match to_print:
			case Okay(val):
				msg = f"Operation succeeded with result {val}"
				log.info(msg)
			case Warn(_, val):
				msg = (
					"Operation succeeded with warnings. "
					+ f"Result: {val}; Warnings:\n"
					+ "\n\n".join([str(w) for w in to_print.warnings_traced])
				)
				log.warning(msg)
			case Fail(_, _):
				msg = (
					"Operation failed with:\n==== Errors ====\n"
					+ "\n\n".join([str(e) for e in to_print.errors_traced])
					+ "\n\n==== And Warnings ====\n"
					+ "\n\n".join([str(w) for w in to_print.warnings_traced])
				)
				log.error(msg)

	def _prompt_end(self, res_type: UIResponseType.UIResponseType) -> str:
		match res_type:
			case UIResponseType.Integer(range_min, range_max):
				return (
					" [int"
					+ (
						f"(x <= {range_max.val})"
						if range_max.has_val and not range_min.has_val
						else f"(x >= {range_min.val})"
						if range_min.has_val and not range_max.has_val
						else f"({range_min.val} <= x <= {range_max.val})"
						if range_min.has_val and range_max.has_val
						else ""
					)
					+ "]"
				)
			case UIResponseType.Decimal(range_min, range_max):
				return (
					" [decimal"
					+ (
						f"(x <= {range_max.val})"
						if range_max.has_val and not range_min.has_val
						else f"(x >= {range_min.val})"
						if range_min.has_val and not range_max.has_val
						else f"({range_min.val} <= x <= {range_max.val})"
						if range_min.has_val and range_max.has_val
						else ""
					)
					+ "]"
				)
			case UIResponseType.Boolean():
				return " [Y/n]"
			case _:
				return ""

	async def _prompt(
		self, prompt_text: str, res_type: UIResponseType.UIResponseType, msg: UIMessage
	) -> Result[Exception, Exception, any]:
		try:
			while True:
				prompt_end = self._prompt_end(res_type)
				entire_prompt = f"{prompt_text}{prompt_end} >"
				res_raw = input(entire_prompt)

				match res_type.convert(res_raw):
					case Okay(res):
						log.info(f"{entire_prompt} {res_raw}")
						return Okay(res)
					case Fail(errs):
						[print(err) for err in errs]
						continue
					case Warn(warns, res):
						[print(warn) for warn in warns]
						log.info(f"{entire_prompt} {res_raw}")
						return Warn(warns, res)

		except (KeyboardInterrupt, EOFError):
			return Fail([UserCancelledError(msg, self)])

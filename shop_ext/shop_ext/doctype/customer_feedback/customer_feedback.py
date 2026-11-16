# Copyright (c) 2026, David and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class CustomerFeedback(Document):
	def validate(self):
		if (
			not isinstance(self.rating, int)
			or isinstance(self.rating, bool)
			or not (1 <= self.rating <= 5)
		):
			frappe.throw(
				_("Rating must be an integer between 1 and 5."),
				title=_("Invalid Rating"),
			)

		if self.rating < 3:
			if not self.comment or not self.comment.strip():
				frappe.throw(
					_("Comment is required for ratings below 3."),
					title=_("Comment Required"),
				)

import frappe


def low_rating_counts():
	# Intentionally uses frappe.get_all (bypassing user-scoped User Permissions) because this
	# scheduled task aggregates site-wide counts without a user session.
	return frappe.get_all(
		"Customer Feedback",
		fields=["customer", {"COUNT": "name", "as": "count"}],
		filters={"rating": ["<", 3]},
		group_by="customer",
		order_by="customer asc",
	)

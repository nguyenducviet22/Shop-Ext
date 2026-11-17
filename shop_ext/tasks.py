import frappe


def low_rating_counts():
	# Intentionally uses frappe.get_all (bypassing User Permissions) because this
	# daily scheduler task runs in the background as Administrator for site-wide counts.
	return frappe.get_all(
		"Customer Feedback",
		fields=["customer", {"COUNT": "name", "as": "count"}],
		filters={"rating": ["<", 3]},
		group_by="customer",
		order_by="customer asc",
	)

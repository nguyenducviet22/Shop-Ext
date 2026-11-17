import frappe


def low_rating_counts():
	return frappe.get_all(
		"Customer Feedback",
		fields=["customer", {"COUNT": "name", "as": "count"}],
		filters={"rating": ["<", 3]},
		group_by="customer",
		order_by="customer asc",
	)

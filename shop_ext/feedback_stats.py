import frappe


def average_rating_by_customer():
	return frappe.get_list(
		"Customer Feedback",
		fields=[
			"customer",
			{"AVG": "rating", "as": "average_rating"},
			{"COUNT": "name", "as": "review_count"},
		],
		group_by="customer",
		order_by="customer asc",
	)

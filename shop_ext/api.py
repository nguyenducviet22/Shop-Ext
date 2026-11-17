import frappe
from shop_ext.feedback_stats import average_rating_by_customer


@frappe.whitelist(methods=["GET"])
def average_ratings():
	return average_rating_by_customer()

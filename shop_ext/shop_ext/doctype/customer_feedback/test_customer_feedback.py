# Copyright (c) 2026, David and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import flt

from shop_ext.feedback_stats import average_rating_by_customer

EXTRA_TEST_RECORD_DEPENDENCIES = []
IGNORE_TEST_RECORD_DEPENDENCIES = ["Customer", "User"]


class IntegrationTestCustomerFeedback(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		self.reader_email = "test_reader@example.com"
		self.create_customers()
		self.create_reader_user_with_permission()

	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()

	def create_customers(self):
		for name in ("Test Customer", "Other Customer"):
			if not frappe.db.exists("Customer", name):
				doc = frappe.get_doc({
					"doctype": "Customer",
					"customer_name": name,
					"customer_type": "Individual",
				})
				# Avoids mandatory-field validation errors when inserting Customer on a clean site (exact missing field not inspected).
				# Avoids mandatory-field validation errors when inserting Customer on a clean site (exact missing field not inspected).
				doc.flags.ignore_mandatory = True
				doc.insert(ignore_permissions=True)
				if doc.name != name:
					frappe.rename_doc("Customer", doc.name, name, force=True, ignore_permissions=True)

	def create_reader_user_with_permission(self):
		if not frappe.db.exists("User", self.reader_email):
			user = frappe.get_doc({
				"doctype": "User",
				"email": self.reader_email,
				"first_name": "Test Reader",
				"send_welcome_email": 0,
				"roles": [{"role": "Sales User"}],
			})
			user.insert(ignore_permissions=True)
		else:
			user = frappe.get_doc("User", self.reader_email)
			if not any(r.role == "Sales User" for r in user.roles):
				user.add_roles("Sales User")

		if not frappe.db.exists(
			"User Permission",
			{"user": self.reader_email, "allow": "Customer", "for_value": "Test Customer"},
		):
			frappe.get_doc({
				"doctype": "User Permission",
				"user": self.reader_email,
				"allow": "Customer",
				"for_value": "Test Customer",
			}).insert(ignore_permissions=True)

	def test_valid_insert_with_two_child_rows(self):
		doc = frappe.get_doc({
			"doctype": "Customer Feedback",
			"customer": "Test Customer",
			"rating": 4,
			"comment": "Great experience!",
			"follow_up_actions": [
				{"action": "Send thank you note"},
				{"action": "Check product satisfaction"},
			],
		}).insert()

		reloaded = frappe.get_doc("Customer Feedback", doc.name)
		self.assertTrue(reloaded.name.startswith("CF-"))
		self.assertEqual(len(reloaded.follow_up_actions), 2)

	def test_rating_and_comment_boundaries(self):
		for rating, comment in ((1, "Min valid"), (5, "Max valid"), (3, None), (2, "Valid low comment")):
			doc = frappe.get_doc({"doctype": "Customer Feedback", "customer": "Test Customer", "rating": rating, "comment": comment}).insert()
			self.assertEqual(doc.rating, rating)

	def test_non_integer_rating_types_raise(self):
		for bad in ("4", 3.5, True):
			with self.assertRaises(frappe.ValidationError):
				frappe.get_doc({"doctype": "Customer Feedback", "customer": "Test Customer", "rating": bad, "comment": "Bad type"}).insert()

	def test_rating_out_of_range_raises(self):
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc({
				"doctype": "Customer Feedback",
				"customer": "Test Customer",
				"rating": 0,
				"comment": "Invalid rating 0",
			}).insert()

		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc({
				"doctype": "Customer Feedback",
				"customer": "Test Customer",
				"rating": 6,
				"comment": "Invalid rating 6",
			}).insert()

	def test_low_rating_requires_comment(self):
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc({
				"doctype": "Customer Feedback",
				"customer": "Test Customer",
				"rating": 2,
				"comment": None,
			}).insert()

		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc({
				"doctype": "Customer Feedback",
				"customer": "Test Customer",
				"rating": 2,
				"comment": "",
			}).insert()

		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc({
				"doctype": "Customer Feedback",
				"customer": "Test Customer",
				"rating": 2,
				"comment": "   ",
			}).insert()

	def test_average_rating_by_customer_known_data(self):
		frappe.set_user("Administrator")

		frappe.get_doc({
			"doctype": "Customer Feedback",
			"customer": "Test Customer",
			"rating": 4,
			"comment": "Good",
		}).insert()

		frappe.get_doc({
			"doctype": "Customer Feedback",
			"customer": "Test Customer",
			"rating": 2,
			"comment": "Could be better",
		}).insert()

		frappe.get_doc({
			"doctype": "Customer Feedback",
			"customer": "Other Customer",
			"rating": 5,
			"comment": "Excellent",
		}).insert()

		results = average_rating_by_customer()
		stats_by_customer = {r["customer"]: r for r in results}

		self.assertIn("Test Customer", stats_by_customer)
		self.assertEqual(flt(stats_by_customer["Test Customer"]["average_rating"]), 3.0)
		self.assertEqual(stats_by_customer["Test Customer"]["review_count"], 2)

		self.assertIn("Other Customer", stats_by_customer)
		self.assertEqual(flt(stats_by_customer["Other Customer"]["average_rating"]), 5.0)
		self.assertEqual(stats_by_customer["Other Customer"]["review_count"], 1)

	def test_reader_with_user_permission_excludes_other_customer(self):
		frappe.get_doc({
			"doctype": "Customer Feedback",
			"customer": "Test Customer",
			"rating": 4,
			"comment": "Good",
		}).insert()

		frappe.get_doc({
			"doctype": "Customer Feedback",
			"customer": "Other Customer",
			"rating": 5,
			"comment": "Excellent",
		}).insert()

		try:
			frappe.set_user(self.reader_email)
			results = average_rating_by_customer()
			customers = [r["customer"] for r in results]
			self.assertIn("Test Customer", customers)
			self.assertNotIn("Other Customer", customers)
		finally:
			frappe.set_user("Administrator")



	def test_rating_and_comment_boundaries(self):
		for r, c in ((1, "Min"), (5, "Max"), (3, None), (2, "Low")):
			self.assertEqual(frappe.get_doc({"doctype": "Customer Feedback", "customer": "Test Customer", "rating": r, "comment": c}).insert().rating, r)

	def test_non_integer_rating_types_raise(self):
		for bad in ("4", 3.5, True):
			with self.assertRaises(frappe.ValidationError):
				frappe.get_doc({"doctype": "Customer Feedback", "customer": "Test Customer", "rating": bad, "comment": "Bad"}).insert()

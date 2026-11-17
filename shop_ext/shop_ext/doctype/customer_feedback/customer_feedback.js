// Copyright (c) 2026, David and contributors
// For license information, please see license.txt

frappe.ui.form.on("Customer Feedback", {
	refresh(frm) {
		toggle_comment_reqd(frm);

		if (!frm.is_new()) {
			frm.add_custom_button(__("Customer averages"), () => {
				frappe.call({
					method: "shop_ext.api.average_ratings",
					type: "GET",
					callback: (r) => {
						const row = (r.message || []).find((row) => row.customer === frm.doc.customer);
						if (row) {
							frappe.msgprint(
								__("Average Rating: {0}<br>Review Count: {1}", [
									row.average_rating,
									row.review_count,
								])
							);
						} else {
							frappe.msgprint(__("No ratings found for this customer."));
						}
					},
				});
			});
		}
	},

	rating(frm) {
		toggle_comment_reqd(frm);
	},
});

function toggle_comment_reqd(frm) {
	const reqd = frm.doc.rating != null && frm.doc.rating !== "" && frm.doc.rating < 3 ? 1 : 0;
	frm.set_df_property("comment", "reqd", reqd);
}

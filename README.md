# Shop Ext (`shop_ext`)

Custom Frappe Framework v16 extension app providing customer feedback management, follow-up workflows, statistics reporting, and role-based permissions.

---

## 1. Overview

`shop_ext` extends Frappe and ERPNext with comprehensive customer feedback capabilities:
- **`Customer Feedback` DocType**: Primary document capturing feedback linked to `Customer`, with feedback date, integer rating (1–5), customer comment, and confidential internal notes. Automatically named with the series pattern `CF-.YYYY.-.####`.
- **`Feedback Action` Child Table**: Embedded table (`follow_up_actions`) tracking operational action items resulting from feedback, including assignee (`User`), due date, and completion status.
- **Server-Side Validation**: Strict controller-level validation ensuring ratings are integers between 1 and 5, and enforcing mandatory, non-whitespace comments whenever rating is below 3.
- **Client UX**: Real-time form scripting in `customer_feedback.js` dynamically toggling the mandatory state of `comment` based on rating changes, plus a custom "Customer averages" button on saved documents.
- **REST API Endpoint**: Whitelisted GET endpoint `shop_ext.api.average_ratings` providing grouped customer rating averages and review counts.
- **Scheduled Daily Task**: Daily background scheduler task (`shop_ext.tasks.low_rating_counts`) summarizing customers with low ratings (< 3).
- **Role Fixture**: Bundled `Feedback Reviewer` role managed and exported via Frappe's fixture system.

---

## 2. Requirements

- **Frappe Framework**: `version-16` (v16.x)
- **ERPNext**: `version-16` (v16.x)
- **Python**: `>= 3.14` (as defined in `pyproject.toml`)
- **MariaDB**: version requirement unverified

---

## 3. Installation

Run the following commands in your bench directory. Commands not directly executed in this workspace are explicitly marked as `(untested)`:

```bash
# 1. Fetch the application repository on the version-16 branch (untested)
bench get-app <repo-url> --branch version-16

# 2. Create a new site with MariaDB wildcard host login scope (tested)
bench new-site <site> --mariadb-user-host-login-scope='%' --db-root-password <db-root-password> --admin-password <admin-password>

# 3. Install shop_ext on the site (tested)
bench --site <site> install-app shop_ext
```

> [!NOTE]
> `shop_ext/hooks.py` defines `required_apps = ["frappe", "erpnext"]`. Running `bench --site <site> install-app shop_ext` on a fresh site automatically installs `erpnext` first through `required_apps` and then installs `shop_ext` (observed).
> - A newly created site starts with its scheduler disabled (`SystemSettings.enable_scheduler is UNSET` / `Scheduler is disabled`, observed); the daily task requires enabling the scheduler (enable command unverified).

---

## 4. Branching Strategy

The repository uses **`version-16`** as its primary default branch rather than `main` or `master`.

### Justification
- **Frappe Ecosystem Standard**: Frappe Framework, ERPNext, and official ecosystem apps standardize on branch names matching the major release series (`version-14`, `version-15`, `version-16`).
- **Seamless `bench get-app` Resolution**: When running `bench get-app <repo-url>` without explicit branch flags, bench automatically attempts to clone the branch matching the bench's active Frappe major version.
- **Dependency & Compatibility Checks**: Automated deployment environments and CI/CD pipelines use the branch name to validate compatibility constraints against the active Frappe v16 runtime.

---

## 5. Permission Matrix

Permissions for `Customer Feedback` are structured across standard and custom roles:

| Role | Permlevel | Permissions / Capabilities | Scope / Target Fields |
| :--- | :---: | :--- | :--- |
| **System Manager** | `0` | **Full CRUD**: Create, Read, Write, Delete, Export, Print, Email, Report, Share | All Level 0 fields |
| **Sales User** | `0` | **Read / Write / Create**: Create, Read, Write, Export, Print, Email, Report (No Delete) | All Level 0 fields |
| **Sales Manager** | `0` | **Full CRUD**: Create, Read, Write, Delete, Export, Print, Email, Report | All Level 0 fields |
| **Sales Manager** | `1` | **Read / Write**: Read, Write | `internal_note` (Confidential internal remarks) |
| **Feedback Reviewer** | Fixture | Exported role fixture for specialized auditing, reporting, and review workflows | Configured via role permissions |

---

## 6. REST API Endpoint

A GET-only whitelisted REST API endpoint is exposed to query aggregated customer rating statistics.

- **Endpoint**: `/api/method/shop_ext.api.average_ratings`
- **HTTP Method**: `GET` (restricted via `@frappe.whitelist(methods=["GET"])`; guest access is disabled)
- **User Permissions**: Enforced automatically. The endpoint calls `frappe.get_list(...)`, which applies active Frappe `User Permission` rules on `Customer` to restrict returned data to permitted customer records only.

### Example Request

```bash
curl -X GET "https://<site>/api/method/shop_ext.api.average_ratings" \
  -H "Authorization: token <api_key>:<api_secret>" \
  -H "Accept: application/json"
```

### Example Response

```json
{
  "message": [
    {
      "customer": "Test Customer",
      "average_rating": 3.0,
      "review_count": 2
    },
    {
      "customer": "Other Customer",
      "average_rating": 5.0,
      "review_count": 1
    }
  ]
}
```

---

## 7. Client Script, Scheduler Task & Fixtures

### Client-Side Form Logic (`customer_feedback.js`)
- **Mandatory Comment Toggle**:
  `toggle_comment_reqd(frm)` checks if `frm.doc.rating` is set and `< 3`. If true, `frm.set_df_property("comment", "reqd", 1)` marks the comment field mandatory; otherwise, it resets `reqd` to `0`. Called on both `refresh(frm)` and `rating(frm)`.
- **"Customer averages" Action Button**:
  On existing documents (`!frm.is_new()`), adds a custom button:
  ```javascript
  frm.add_custom_button(__("Customer averages"), () => { ... })
  ```
  It queries `shop_ext.api.average_ratings` via `frappe.call` (`type: "GET"`), finds the matching record where `row.customer === frm.doc.customer`, and displays the average rating and review count with `frappe.msgprint(...)` (or a fallback notice if no reviews exist).

### Daily Scheduler Task (`shop_ext.tasks.low_rating_counts`)
- Configured in `hooks.py` under `scheduler_events`:
  ```python
  scheduler_events = {
  	"daily": [
  		"shop_ext.tasks.low_rating_counts",
  	],
  }
  ```
- Executes a single, optimized `frappe.get_all` query:
  ```python
  frappe.get_all(
  	"Customer Feedback",
  	fields=["customer", {"COUNT": "name", "as": "count"}],
  	filters={"rating": ["<", 3]},
  	group_by="customer",
  	order_by="customer asc",
  )
  ```

### Fixtures (`hooks.py`)
- Configured to export the custom `Feedback Reviewer` role:
  ```python
  fixtures = [
  	{
  		"dt": "Role",
  		"filters": [["name", "in", ["Feedback Reviewer"]]],
  	},
  ]
  ```
- Export fixtures to the app directory using `bench --site <site> export-fixtures` (untested).

---

## 8. Running Tests

Integration tests for `Customer Feedback` and `average_rating_by_customer` are implemented in `apps/shop_ext/shop_ext/shop_ext/doctype/customer_feedback/test_customer_feedback.py`.

Enable testing on your target site and run the test suite:

```bash
# 1. Enable test execution on the site (untested)
bench --site <site> set-config allow_tests true

# 2. Run the shop_ext test suite (untested)
bench --site <site> run-tests --app shop_ext
```

### Covered Test Cases
1. `test_valid_insert_with_two_child_rows`: Verifies valid document insertion with `rating=4` and 2 child rows in `follow_up_actions`, asserting naming prefix `CF-` and child row count.
2. `test_rating_out_of_range_raises`: Asserts `frappe.ValidationError` when attempting to insert ratings `0` and `6`.
3. `test_low_rating_requires_comment`: Asserts `frappe.ValidationError` when inserting `rating=2` with `comment=None`, `""`, or whitespace `"   "`.
4. `test_average_rating_by_customer_known_data`: Inserts known test ratings and asserts exact calculated `average_rating` and `review_count` values.
5. `test_reader_with_user_permission_excludes_other_customer`: Switches user to a restricted Sales User with `User Permission` on `"Test Customer"` and asserts that `"Other Customer"` is excluded from `average_rating_by_customer()`.

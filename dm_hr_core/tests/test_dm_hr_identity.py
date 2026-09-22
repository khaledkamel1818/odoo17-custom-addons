# -*- coding: utf-8 -*-
from datetime import date, timedelta

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase

try:
    from psycopg2 import IntegrityError
except ImportError:  # pragma: no cover - psycopg3 fallback
    from psycopg import IntegrityError


class DmHrCoreIdentityTest(TransactionCase):
    """Identity fields, uniqueness, contract validation and expiry cron."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Employee = cls.env["hr.employee"]
        cls.Contract = cls.env["hr.contract"]
        cls.company = cls.env.company
        cls.company_b = cls.env["res.company"].create({
            "name": "Company B",
            "currency_id": cls.env.ref("base.USD").id,
        })

    # ---------------- employee number (auto + unique) ---------------- #
    def test_employee_number_generated_from_sequence(self):
        employee = self.Employee.create({"name": "Employee A"})
        self.assertTrue(employee.employee_number)
        self.assertRegex(employee.employee_number, r"^EMP-\d+$")
        # No GOSI category by default (no hardcoded default value).
        self.assertFalse(employee.gosi_employee_category)
        # The base employee_type field must stay untouched (base default).
        self.assertEqual(employee.employee_type, "employee")
        self.assertEqual(employee.dm_employment_status, "active")

    def test_employee_numbers_are_distinct(self):
        a = self.Employee.create({"name": "A"})
        b = self.Employee.create({"name": "B"})
        self.assertNotEqual(a.employee_number, b.employee_number)

    def test_employee_number_unique_per_company(self):
        a = self.Employee.create({"name": "A"})
        with self.assertRaises(IntegrityError):
            # Keep the expected database error inside its own savepoint.  A
            # full rollback here would remove TransactionCase's savepoint and
            # leave every following test with an aborted transaction.
            with self.cr.savepoint():
                self.Employee.create({
                    "name": "B",
                    "employee_number": a.employee_number,
                    "company_id": self.company.id,
                })

    # ---------------- iqama / national id (per company) ---------------- #
    def test_iqama_unique_per_company(self):
        self.Employee.create({
            "name": "Iqama A", "iqama_no": "DM_TEST_IQAMA_0001",
            "company_id": self.company.id,
        })
        with self.assertRaises(ValidationError):
            self.Employee.create({
                "name": "Iqama B", "iqama_no": "DM_TEST_IQAMA_0001",
                "company_id": self.company.id,
            })

    def test_iqama_allowed_for_different_company(self):
        self.Employee.create({
            "name": "Iqama A", "iqama_no": "DM_TEST_IQAMA_0001",
            "company_id": self.company.id,
        })
        other = self.Employee.create({
            "name": "Iqama B", "iqama_no": "DM_TEST_IQAMA_0001",
            "company_id": self.company_b.id,
        })
        self.assertTrue(other.id)

    # ---------------- contract probation validation ---------------- #
    def test_probation_end_must_not_precede_start(self):
        employee = self.Employee.create({"name": "Contract Emp"})
        with self.assertRaises(ValidationError):
            self.Contract.create({
                "name": "Bad Contract", "employee_id": employee.id,
                "wage": 1000, "date_start": "2026-06-01",
                "probation_end": "2026-05-15", "company_id": self.company.id,
            })

    def test_probation_end_on_or_after_start_is_valid(self):
        employee = self.Employee.create({"name": "Contract Emp"})
        contract = self.Contract.create({
            "name": "Good Contract", "employee_id": employee.id,
            "wage": 1000, "date_start": "2026-06-01",
            "probation_end": "2026-06-15", "company_id": self.company.id,
        })
        self.assertEqual(contract.probation_end, date(2026, 6, 15))

    # ---------------- smart button counters ---------------- #
    def test_dm_contract_count_follows_contracts(self):
        employee = self.Employee.create({"name": "Smart Emp"})
        self.assertEqual(employee.dm_contract_count, 0)
        self.Contract.create({
            "name": "C1", "employee_id": employee.id,
            "wage": 1000, "date_start": "2026-01-01",
            "company_id": self.company.id,
        })
        employee = employee.browse(employee.id)  # force recompute (non-stored)
        self.assertEqual(employee.dm_contract_count, 1)

    # ---------------- expiry alert cron (idempotent) ---------------- #
    def test_expiry_alert_cron_runs_and_does_not_duplicate(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "dm_hr_core.expiry_alert_days", "30")
        employee = self.Employee.create({
            "name": "Expiry Emp", "iqama_no": "DM_TEST_EXP_IQAMA",
            "iqama_expiry_date": (date.today() + timedelta(days=5)).isoformat(),
        })
        self.Contract.create({
            "name": "Expiring Contract", "employee_id": employee.id,
            "wage": 1000, "date_start": date.today().isoformat(),
            "date_end": (date.today() + timedelta(days=10)).isoformat(),
            "company_id": self.company.id,
        })
        runner = self.env["dm.hr.expiry.alert"]
        runner._cron_run()
        summaries = employee.activity_ids.mapped("summary")
        self.assertIn("Iqama / National ID expires soon", summaries)
        self.assertIn("Contract expires soon", summaries)
        before = len(employee.activity_ids)
        runner._cron_run()
        self.assertEqual(len(employee.activity_ids), before)


class DmHrGosiCategoryTest(TransactionCase):
    """GOSI employee category: no default, explicit values, not copied."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Employee = cls.env["hr.employee"]

    def test_no_gosi_category_by_default(self):
        """A new employee has no GOSI category by default."""
        employee = self.Employee.create({"name": "GOSI Default Emp"})
        self.assertFalse(employee.gosi_employee_category)

    def test_gosi_category_saudi_saves(self):
        employee = self.Employee.create(
            {"name": "GOSI Saudi Emp", "gosi_employee_category": "saudi"})
        self.assertEqual(employee.gosi_employee_category, "saudi")

    def test_gosi_category_non_saudi_saves(self):
        employee = self.Employee.create(
            {"name": "GOSI NonSaudi Emp", "gosi_employee_category": "non_saudi"})
        self.assertEqual(employee.gosi_employee_category, "non_saudi")

    def test_copy_does_not_copy_gosi_category(self):
        """Copying an employee must not copy the GOSI category (copy=False)."""
        employee = self.Employee.create(
            {"name": "GOSI Copy Emp", "gosi_employee_category": "saudi"})
        copied = employee.copy()
        self.assertFalse(copied.gosi_employee_category)
        self.assertEqual(employee.gosi_employee_category, "saudi")

    def test_original_employee_type_remains_untouched(self):
        """The base hr employee_type field keeps its standard values."""
        employee = self.Employee.create(
            {"name": "GOSI Type Emp", "gosi_employee_category": "non_saudi"})
        self.assertEqual(employee.employee_type, "employee")
        selection_values = set(
            dict(self.Employee._fields["employee_type"].selection))
        self.assertEqual(
            selection_values,
            {"employee", "student", "trainee", "contractor", "freelance"})

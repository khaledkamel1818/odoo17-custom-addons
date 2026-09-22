# -*- coding: utf-8 -*-
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase


class DmHrCoreModelTest(TransactionCase):
    """Validates model constraints of dm_hr_core (Phase 1)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Company = cls.env["res.company"]
        cls.AllowanceType = cls.env["dm.hr.allowance.type"]
        cls.Scheme = cls.env["dm.hr.social.insurance.scheme"]
        cls.Rate = cls.env["dm.hr.social.insurance.rate"]
        cls.Employee = cls.env["hr.employee"]
        cls.Contract = cls.env["hr.contract"]
        cls.DmContractAllowance = cls.env["dm.hr.contract.allowance"]
        cls.DmEmployeeAllowance = cls.env["dm.hr.employee.allowance"]
        cls.InsurancePolicy = cls.env["dm.hr.insurance.policy"]
        cls.InsuranceProvider = cls.env["dm.hr.insurance.provider"]
        cls.Dependent = cls.env["dm.hr.employee.dependent"]
        cls.Document = cls.env["dm.hr.document"]

        cls.company = cls.env.company
        cls.allowance_fixed = cls.AllowanceType.create({
            "name": "Housing", "code": "HOUSING_TEST",
            "amount_type": "fixed", "schedule": "monthly",
            "company_id": cls.company.id,
        })
        cls.allowance_pct_basic = cls.AllowanceType.create({
            "name": "Transport Percent", "code": "TRANSPORT_PCT_TEST",
            "amount_type": "percentage_of_basic", "schedule": "monthly",
            "company_id": cls.company.id,
        })
        cls.allowance_pct_comp = cls.AllowanceType.create({
            "name": "Bonus Percent", "code": "BONUS_PCT_TEST",
            "amount_type": "percentage_of_component", "schedule": "monthly",
            "company_id": cls.company.id,
        })

        cls.scheme = cls.Scheme.create({
            "name": "GOSI Test", "code": "GOSI_TEST",
            "company_id": cls.company.id,
        })

        cls.employee = cls.Employee.create({"name": "Test Employee", "gosi_employee_category": "saudi"})
        cls.contract = cls.Contract.create({
            "name": "Test Contract", "employee_id": cls.employee.id,
            "wage": 1000, "date_start": "2026-01-01",
            "company_id": cls.company.id,
        })

    # ---- Allowance types ----
    def test_01_allowance_type_requires_code(self):
        with self.assertRaises(ValidationError):
            self.AllowanceType.create({
                "name": "No Code", "code": "   ",
                "amount_type": "fixed", "company_id": self.company.id,
            })

    # ---- Contract allowances ----
    def _contract_allowance_vals(self, **overrides):
        vals = {
            "contract_id": self.contract.id,
            "allowance_type_id": self.allowance_fixed.id,
            "amount": 500,
            "start_date": "2026-01-01", "end_date": "2026-01-31",
        }
        vals.update(overrides)
        return vals

    def test_02_fixed_allowance_requires_positive_amount(self):
        with self.assertRaises(ValidationError):
            self.DmContractAllowance.create(self._contract_allowance_vals(amount=0))

    def test_03_percentage_basic_requires_valid_percent(self):
        with self.assertRaises(ValidationError):
            self.DmContractAllowance.create({
                "contract_id": self.contract.id,
                "allowance_type_id": self.allowance_pct_basic.id,
                "percent": 150, "start_date": "2026-01-01", "end_date": "2026-01-31",
            })

    def test_04_percentage_component_requires_base(self):
        with self.assertRaises(ValidationError):
            self.DmContractAllowance.create({
                "contract_id": self.contract.id,
                "allowance_type_id": self.allowance_pct_comp.id,
                "percent": 10, "start_date": "2026-01-01", "end_date": "2026-01-31",
            })

    def test_05_percentage_component_cannot_reference_itself(self):
        with self.assertRaises(ValidationError):
            self.DmContractAllowance.create({
                "contract_id": self.contract.id,
                "allowance_type_id": self.allowance_pct_comp.id,
                "percent_of_allowance_type_id": self.allowance_pct_comp.id,
                "percent": 10, "start_date": "2026-01-01", "end_date": "2026-01-31",
            })

    def test_06_contract_allowance_overlap_forbidden(self):
        self.DmContractAllowance.create(self._contract_allowance_vals())
        with self.assertRaises(ValidationError):
            self.DmContractAllowance.create(self._contract_allowance_vals())

    # ---- Social insurance rates ----
    def _rate_vals(self, **overrides):
        vals = {
            "scheme_id": self.scheme.id,
            "employee_category": "saudi",
            "effective_from": "2026-01-01", "effective_to": "2026-12-31",
        }
        vals.update(overrides)
        return vals

    def test_07_rate_ratio_bounds(self):
        with self.assertRaises(ValidationError):
            self.Rate.create(self._rate_vals(gosi_employee_ratio=150))

    def test_08_rate_overlap_forbidden(self):
        self.Rate.create(self._rate_vals())
        with self.assertRaises(ValidationError):
            self.Rate.create(self._rate_vals())

    def test_09_employee_allowance_overlap_forbidden(self):
        self.DmEmployeeAllowance.create({
            "employee_id": self.employee.id,
            "allowance_type_id": self.allowance_fixed.id,
            "amount": 500,
            "start_date": "2026-01-01", "end_date": "2026-01-31",
            "company_id": self.company.id,
        })
        with self.assertRaises(ValidationError):
            self.DmEmployeeAllowance.create({
                "employee_id": self.employee.id,
                "allowance_type_id": self.allowance_fixed.id,
                "amount": 500,
                "start_date": "2026-01-01", "end_date": "2026-01-31",
            })

    # ---- Insurance ----
    def test_10_insurance_share_bounds(self):
        provider = self.InsuranceProvider.create({
            "name": "Med Provider", "company_id": self.company.id,
        })
        with self.assertRaises(ValidationError):
            self.InsurancePolicy.create({
                "employee_id": self.employee.id, "provider_id": provider.id,
                "start_date": "2026-01-01", "end_date": "2026-12-31",
                "employee_share_percent": 150,
            })

    def test_11_insurance_policy_overlap_forbidden(self):
        provider = self.InsuranceProvider.create({
            "name": "Med Provider", "company_id": self.company.id,
        })
        base = {
            "employee_id": self.employee.id, "provider_id": provider.id,
            "start_date": "2026-01-01", "end_date": "2026-12-31",
        }
        self.InsurancePolicy.create(base)
        with self.assertRaises(ValidationError):
            self.InsurancePolicy.create(dict(base))


class DmHrMultiCompanySettingsTest(TransactionCase):
    """Proves company-scoped settings do not leak between companies."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env["res.company"].create({
            "name": "Company A",
            "currency_id": cls.env.ref("base.USD").id,
        })
        cls.company_b = cls.env["res.company"].create({
            "name": "Company B",
            "currency_id": cls.env.ref("base.USD").id,
        })
        cls.scheme_a = cls.env["dm.hr.social.insurance.scheme"].create({
            "name": "GOSI A", "code": "GOSI_A_MULTI",
            "company_id": cls.company_a.id,
        })
        cls.scheme_b = cls.env["dm.hr.social.insurance.scheme"].create({
            "name": "GOSI B", "code": "GOSI_B_MULTI",
            "company_id": cls.company_b.id,
        })
        cls.scheme_c = cls.env["dm.hr.social.insurance.scheme"].create({
            "name": "GOSI C", "code": "GOSI_C_MULTI",
            "company_id": cls.company_a.id,
        })

    def test_settings_isolated_between_companies(self):
        settings_model = self.env["res.config.settings"]

        # Configure company A
        settings_model.create({
            "company_id": self.company_a.id,
            "social_insurance_scheme_id": self.scheme_a.id,
        }).execute()
        self.assertEqual(self.company_a.default_social_insurance_scheme_id, self.scheme_a)
        self.assertFalse(self.company_b.default_social_insurance_scheme_id)

        # Configure company B -> must NOT alter A
        settings_model.create({
            "company_id": self.company_b.id,
            "social_insurance_scheme_id": self.scheme_b.id,
        }).execute()
        self.assertEqual(self.company_b.default_social_insurance_scheme_id, self.scheme_b)
        self.assertEqual(self.company_a.default_social_insurance_scheme_id, self.scheme_a)

        # Switch A's scheme -> B stays untouched
        settings_model.create({
            "company_id": self.company_a.id,
            "social_insurance_scheme_id": self.scheme_c.id,
        }).execute()
        self.assertEqual(self.company_a.default_social_insurance_scheme_id, self.scheme_c)
        self.assertEqual(self.company_b.default_social_insurance_scheme_id, self.scheme_b)

    def test_settings_clear_is_local_to_company(self):
        # Set on A, then explicitly clear on A -> B untouched
        settings_model = self.env["res.config.settings"]
        settings_model.create({
            "company_id": self.company_a.id,
            "social_insurance_scheme_id": self.scheme_a.id,
        }).execute()
        settings_model.create({
            "company_id": self.company_b.id,
            "social_insurance_scheme_id": self.scheme_b.id,
        }).execute()

        # Clear A
        settings_model.create({
            "company_id": self.company_a.id,
            "social_insurance_scheme_id": False,
        }).execute()
        self.assertFalse(self.company_a.default_social_insurance_scheme_id)
        self.assertEqual(self.company_b.default_social_insurance_scheme_id, self.scheme_b)

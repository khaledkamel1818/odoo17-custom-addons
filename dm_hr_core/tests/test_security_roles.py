# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase


class DmHrSecurityRolesTest(TransactionCase):
    """HR role matrix: specialized roles, inheritance and security menus."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ref = cls.env.ref

    def test_specialized_hr_groups_exist(self):
        groups = [
            "dm_hr_core.group_dm_hr_line_manager",
            "dm_hr_core.group_dm_hr_leave_officer",
            "dm_hr_core.group_dm_hr_attendance_officer",
            "dm_hr_core.group_dm_hr_document_officer",
        ]
        for xmlid in groups:
            self.assertTrue(self.ref(xmlid), "%s must exist" % xmlid)

    def test_hr_officer_inherits_specialized_roles(self):
        officer = self.ref("dm_hr_core.group_dm_hr_officer")
        implied = officer.implied_ids
        self.assertIn(self.ref("dm_hr_core.group_dm_hr_leave_officer"), implied)
        self.assertIn(self.ref("dm_hr_core.group_dm_hr_attendance_officer"), implied)
        self.assertIn(self.ref("dm_hr_core.group_dm_hr_document_officer"), implied)

    def test_hr_security_menus_exist_for_admin(self):
        self.assertEqual(
            self.ref("dm_hr_core.menu_dm_hr_security_root").groups_id,
            self.ref("dm_hr_core.group_dm_hr_admin"),
        )
        self.assertEqual(
            self.ref("dm_hr_core.menu_dm_hr_security_users").action._name,
            "ir.actions.act_window",
        )
        self.assertEqual(
            self.ref("dm_hr_core.menu_dm_hr_security_groups").action._name,
            "ir.actions.act_window",
        )

    def test_role_acl_intent(self):
        self.assertTrue(
            self.env["dm.hr.document"].with_user(self.ref("base.user_admin"))
            .check_access_rights("create", raise_exception=False)
        )
        self.assertFalse(
            self.env["dm.hr.service.request"].with_user(self.ref("base.public_user"))
            .check_access_rights("read", raise_exception=False)
        )

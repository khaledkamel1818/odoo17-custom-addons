# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import TransactionCase


class DmHrServiceRequestTest(TransactionCase):
    """Employee self-service requests and smart counters."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Employee = cls.env['hr.employee']
        cls.ServiceRequest = cls.env['dm.hr.service.request']
        cls.employee = cls.Employee.create({'name': 'Service Employee'})

    def _request_vals(self, **overrides):
        date_from = fields.Datetime.now()
        vals = {
            'subject': 'Medical permission',
            'request_type_id': self.env.ref('dm_hr_core.service_type_permission').id,
            'employee_id': self.employee.id,
            'date_from': date_from,
            'date_to': date_from + timedelta(hours=2),
        }
        vals.update(overrides)
        return vals

    def test_service_request_sequence_and_duration(self):
        request = self.ServiceRequest.create(self._request_vals())
        self.assertRegex(request.name, r'^HRREQ-\d+$')
        self.assertEqual(request.duration_hours, 2.0)
        self.assertEqual(request.state, 'draft')

    def test_timed_request_requires_valid_range(self):
        with self.assertRaises(ValidationError):
            self.ServiceRequest.create(self._request_vals(date_to=False))
        with self.assertRaises(ValidationError):
            self.ServiceRequest.create(self._request_vals(
                date_to=fields.Datetime.now() - timedelta(hours=1)))

    def test_request_approval_flow_and_employee_counter(self):
        request = self.ServiceRequest.create(self._request_vals())
        self.assertEqual(self.employee.dm_request_count, 1)
        request.action_submit()
        self.assertEqual(request.state, 'submitted')
        request.action_manager_approve()
        self.assertEqual(request.state, 'manager_approved')
        request.action_hr_approve()
        self.assertEqual(request.state, 'approved')
        self.assertTrue(request.approved_on)

    def test_reject_requires_reason(self):
        request = self.ServiceRequest.create(self._request_vals())
        request.action_submit()
        with self.assertRaises(Exception):
            request.action_reject()
        request.rejection_reason = 'Not enough details'
        request.action_reject()
        self.assertEqual(request.state, 'rejected')

    def test_salary_transfer_request_requires_saudi_iban(self):
        type_salary_transfer = self.env.ref('dm_hr_core.service_type_salary_transfer')
        with self.assertRaises(ValidationError):
            self.ServiceRequest.create({
                'subject': 'Salary transfer',
                'request_type_id': type_salary_transfer.id,
                'employee_id': self.employee.id,
                'bank_name': 'Test Bank',
                'iban': 'AE000000000000',
            })
        request = self.ServiceRequest.create({
            'subject': 'Salary transfer',
            'request_type_id': type_salary_transfer.id,
            'employee_id': self.employee.id,
            'bank_name': 'Test Bank',
            'iban': 'SA0000000000000000000000',
        })
        self.assertEqual(request.request_type, 'salary_transfer_certificate')
        self.assertIn('IBAN', request.salary_compliance_note)


class DmHrFlexibleApprovalWorkflowTest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Users = cls.env['res.users'].with_context(no_reset_password=True)
        employee_group = cls.env.ref('dm_hr_core.group_dm_hr_employee')
        officer_group = cls.env.ref('dm_hr_core.group_dm_hr_officer')
        cls.employee_user = Users.create({
            'name': 'Workflow Employee', 'login': 'workflow.employee@test.local', 'email': 'workflow.employee@test.local',
            'groups_id': [(6, 0, [employee_group.id])],
        })
        cls.manager_user = Users.create({
            'name': 'Workflow Manager', 'login': 'workflow.manager@test.local', 'email': 'workflow.manager@test.local',
            'groups_id': [(6, 0, [employee_group.id])],
        })
        cls.hr_user = Users.create({
            'name': 'Workflow HR', 'login': 'workflow.hr@test.local', 'email': 'workflow.hr@test.local',
            'groups_id': [(6, 0, [officer_group.id])],
        })
        cls.manager_employee = cls.env['hr.employee'].create({
            'name': 'Workflow Manager', 'user_id': cls.manager_user.id,
        })
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Workflow Employee', 'user_id': cls.employee_user.id,
            'parent_id': cls.manager_employee.id,
        })
        cls.policy = cls.env['dm.hr.approval.policy'].create({
            'name': 'Permission two-step workflow',
            'company_id': cls.env.company.id,
            'request_type': 'permission',
            'request_type_id': cls.env.ref('dm_hr_core.service_type_permission').id,
            'allow_self_approval': False,
            'step_ids': [
                (0, 0, {'sequence': 10, 'name': 'Direct Manager', 'approver_type': 'manager'}),
                (0, 0, {'sequence': 20, 'name': 'HR Review', 'approver_type': 'hr_officer',
                        'require_comment': True}),
            ],
        })
        now = fields.Datetime.now()
        cls.request = cls.env['dm.hr.service.request'].create({
            'subject': 'Flexible workflow request', 'request_type_id': cls.env.ref('dm_hr_core.service_type_permission').id,
            'employee_id': cls.employee.id, 'date_from': now,
            'date_to': now + timedelta(hours=1),
        })

    def test_complete_configurable_workflow(self):
        self.request.with_user(self.employee_user).action_submit()
        self.assertEqual(self.request.approval_policy_id, self.policy)
        self.assertEqual(len(self.request.approval_item_ids), 2)
        self.assertEqual(self.request.current_approval_label, 'Direct Manager')

        self.request.with_user(self.manager_user).action_approve()
        self.assertEqual(self.request.state, 'manager_approved')
        self.assertEqual(self.request.current_approval_label, 'HR Review')

        with self.assertRaises(UserError):
            self.request.with_user(self.hr_user).action_approve()
        self.request.with_user(self.hr_user).write({'approval_comment': 'Policy verified'})
        self.request.with_user(self.hr_user).action_approve()
        self.assertEqual(self.request.state, 'approved')
        self.assertTrue(self.request.approved_on)
        self.assertEqual(self.request.approval_item_ids.mapped('state'), ['approved', 'approved'])

    def test_wrong_approver_is_blocked(self):
        request = self.request.copy({
            'subject': 'Wrong approver check',
            'date_from': self.request.date_from + timedelta(days=7),
            'date_to': self.request.date_to + timedelta(days=7),
        })
        request.with_user(self.employee_user).action_submit()
        with self.assertRaises(AccessError):
            request.with_user(self.hr_user).action_approve()

    def test_department_approval_step_uses_org_structure(self):
        Users = self.env['res.users'].with_context(no_reset_password=True)
        employee_group = self.env.ref('dm_hr_core.group_dm_hr_employee')
        department_user = Users.create({
            'name': 'Department Approver',
            'login': 'department.approver@test.local',
            'email': 'department.approver@test.local',
            'groups_id': [(6, 0, [employee_group.id])],
        })
        department_approver = self.env['hr.employee'].create({
            'name': 'Department Approver',
            'user_id': department_user.id,
        })
        department = self.env['hr.department'].create({
            'name': 'Operations',
            'dm_approval_manager_id': department_approver.id,
        })
        self.employee.department_id = department
        self.env['dm.hr.approval.policy'].create({
            'name': 'Other request by department',
            'company_id': self.env.company.id,
            'request_type': 'other',
            'request_type_id': self.env.ref('dm_hr_core.service_type_other').id,
            'step_ids': [(0, 0, {
                'sequence': 10,
                'name': 'Department Approval',
                'approver_type': 'department_manager',
            })],
        })
        request = self.env['dm.hr.service.request'].create({
            'subject': 'Department workflow',
            'request_type_id': self.env.ref('dm_hr_core.service_type_other').id,
            'employee_id': self.employee.id,
        })
        request.with_user(self.employee_user).action_submit()
        self.assertEqual(request.current_approval_item_id.approver_user_id, department_user)
        with self.assertRaises(AccessError):
            request.with_user(self.manager_user).action_approve()
        request.with_user(department_user).action_approve()
        self.assertEqual(request.state, 'approved')

    def test_scoped_policy_preview_delegate_and_deadline(self):
        Users = self.env['res.users'].with_context(no_reset_password=True)
        employee_group = self.env.ref('dm_hr_core.group_dm_hr_employee')
        escalation_user = Users.create({
            'name': 'Approval Escalation',
            'login': 'approval.escalation@test.local',
            'email': 'approval.escalation@test.local',
            'groups_id': [(6, 0, [employee_group.id])],
        })
        department_user = Users.create({
            'name': 'Scoped Department Approver',
            'login': 'scoped.department.approver@test.local',
            'email': 'scoped.department.approver@test.local',
            'groups_id': [(6, 0, [employee_group.id])],
        })
        department_approver = self.env['hr.employee'].create({
            'name': 'Scoped Department Approver',
            'user_id': department_user.id,
        })
        department = self.env['hr.department'].create({
            'name': 'Scoped Operations',
            'dm_approval_manager_id': department_approver.id,
        })
        self.employee.department_id = department
        scoped_policy = self.env['dm.hr.approval.policy'].create({
            'name': 'Scoped permission policy',
            'company_id': self.env.company.id,
            'request_type': 'permission',
            'request_type_id': self.env.ref('dm_hr_core.service_type_permission').id,
            'department_id': department.id,
            'priority_filter': '2',
            'escalation_user_id': escalation_user.id,
            'step_ids': [(0, 0, {
                'sequence': 10,
                'name': 'Department SLA Approval',
                'approver_type': 'department_manager',
                'sla_hours': 4,
                'delegate_user_id': self.manager_user.id,
                'instructions': 'راجع سبب الاستئذان والمدة قبل الاعتماد.',
            })],
        })
        later = fields.Datetime.now() + timedelta(days=14)
        request = self.env['dm.hr.service.request'].create({
            'subject': 'Scoped urgent permission',
            'request_type_id': self.env.ref('dm_hr_core.service_type_permission').id,
            'priority': '2',
            'employee_id': self.employee.id,
            'date_from': later,
            'date_to': later + timedelta(hours=1),
        })

        self.assertEqual(request.approval_policy_preview_id, scoped_policy)
        self.assertIn('Department SLA Approval', request.approval_route_preview)
        self.assertIn('مفوّض', request.approval_route_preview)

        request.with_user(self.employee_user).action_submit()
        item = request.current_approval_item_id
        self.assertEqual(request.approval_policy_id, scoped_policy)
        self.assertEqual(item.approver_user_id, department_user)
        self.assertEqual(item.delegate_user_id, self.manager_user)
        self.assertEqual(item.escalation_user_id, escalation_user)
        self.assertTrue(item.deadline)

        request.with_user(self.manager_user).action_approve()
        self.assertEqual(request.state, 'approved')


class DmHrEmployeeOrgStructureTest(TransactionCase):
    def test_employee_org_chain_is_sequential_and_validated(self):
        Branch = self.env['dm.hr.branch']
        Department = self.env['hr.department']
        Employee = self.env['hr.employee']

        branch = Branch.create({
            'name': 'Riyadh Branch',
            'code': 'RYD-ORG-TEST',
            'company_id': self.env.company.id,
        })
        sector = Department.create({
            'name': 'Operations Sector',
            'dm_org_level': 'sector',
            'dm_branch_id': branch.id,
        })
        department = Department.create({
            'name': 'Maintenance Department',
            'dm_org_level': 'department',
            'parent_id': sector.id,
            'dm_branch_id': branch.id,
        })
        section = Department.create({
            'name': 'Electrical Section',
            'dm_org_level': 'section',
            'parent_id': department.id,
            'dm_branch_id': branch.id,
        })
        unit = Department.create({
            'name': 'Field Unit',
            'dm_org_level': 'unit',
            'parent_id': section.id,
            'dm_branch_id': branch.id,
        })
        employee = Employee.create({
            'name': 'Structured Employee',
            'dm_branch_id': branch.id,
            'dm_sector_id': sector.id,
            'dm_department_level_id': department.id,
            'dm_section_id': section.id,
            'dm_unit_id': unit.id,
        })

        self.assertEqual(employee.department_id, unit)

        with self.assertRaises(ValidationError):
            Employee.create({
                'name': 'Invalid Structured Employee',
                'dm_branch_id': branch.id,
                'dm_sector_id': sector.id,
                'dm_department_level_id': department.id,
            })

    def test_employee_cannot_manage_himself(self):
        employee = self.env['hr.employee'].create({'name': 'Self Manager Check'})
        with self.assertRaises(ValidationError):
            employee.parent_id = employee

# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class DmHrBranch(models.Model):
    _name = 'dm.hr.branch'
    _description = 'فرع الشركة'
    _order = 'company_id, sequence, name'
    _check_company_auto = True

    name = fields.Char(string='اسم الفرع', required=True, translate=True)
    code = fields.Char(string='كود الفرع', index=True)
    sequence = fields.Integer(string='الترتيب', default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company',
        string='الشركة',
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    city = fields.Char(string='المدينة')
    address = fields.Char(string='العنوان')
    manager_id = fields.Many2one('hr.employee', string='مدير الفرع')
    employee_count = fields.Integer(string='عدد الموظفين', compute='_compute_employee_count')

    _sql_constraints = [
        ('branch_code_company_uniq', 'unique(code, company_id)', 'كود الفرع يجب أن يكون فريداً داخل الشركة.'),
    ]

    def _compute_employee_count(self):
        Employee = self.env['hr.employee'].sudo()
        for branch in self:
            branch.employee_count = Employee.search_count([('dm_branch_id', '=', branch.id)])

    @api.model
    def dm_org_chart_data(self, company_id=False, branch_id=False, search=False):
        user = self.env.user
        if not user.has_group('dm_hr_core.group_dm_hr_org_chart_user'):
            return {'nodes': [], 'summary': {}, 'filters': {}}

        companies = self.env.companies
        if company_id:
            companies = companies.filtered(lambda company: company.id == int(company_id))
        branches = self.sudo().search([('company_id', 'in', companies.ids)])
        if branch_id:
            branches = branches.filtered(lambda branch: branch.id == int(branch_id))

        Employee = self.env['hr.employee'].sudo()
        Department = self.env['hr.department'].sudo()
        own_employee = user.employee_id or Employee.search([('user_id', '=', user.id)], limit=1)
        is_hr = any([
            user.has_group('dm_hr_core.group_dm_hr_officer'),
            user.has_group('dm_hr_core.group_dm_hr_manager'),
            user.has_group('dm_hr_core.group_dm_hr_admin'),
        ])

        visible_employee_ids = set()
        visible_department_ids = set()
        if is_hr:
            employees = Employee.search([('company_id', 'in', companies.ids)])
            visible_employee_ids.update(employees.ids)
            visible_department_ids.update(Department.search([('company_id', 'in', companies.ids)]).ids)
        elif own_employee:
            visible_employee_ids.add(own_employee.id)
            subordinates = Employee.search([('parent_id', 'child_of', own_employee.id)])
            visible_employee_ids.update(subordinates.ids)
            managed_departments = Department.search(['|', ('manager_id', '=', own_employee.id), ('dm_approval_manager_id', '=', own_employee.id)])
            if managed_departments:
                visible_department_ids.update(Department.search([('id', 'child_of', managed_departments.ids)]).ids)
                visible_employee_ids.update(Employee.search([('department_id', 'child_of', list(visible_department_ids))]).ids)
            for employee in Employee.browse(list(visible_employee_ids)):
                for department in (employee.dm_sector_id | employee.dm_department_level_id | employee.dm_section_id | employee.dm_unit_id | employee.department_id):
                    if department:
                        visible_department_ids.update(Department.search([('id', 'parent_of', department.id)]).ids)

        if search:
            term = search.strip()
            matched_departments = Department.search([('name', 'ilike', term), ('company_id', 'in', companies.ids)])
            matched_employees = Employee.search([
                '&', ('company_id', 'in', companies.ids),
                '|', ('name', 'ilike', term), ('job_id.name', 'ilike', term),
            ])
            visible_department_ids.update(matched_departments.ids)
            visible_employee_ids.update(matched_employees.ids)
            for employee in matched_employees:
                if employee.department_id:
                    visible_department_ids.update(Department.search([('id', 'parent_of', employee.department_id.id)]).ids)
            for department in matched_departments:
                visible_department_ids.update(Department.search(['|', ('id', 'parent_of', department.id), ('id', 'child_of', department.id)]).ids)

        departments = Department.search([('id', 'in', list(visible_department_ids))])
        employees = Employee.search([('id', 'in', list(visible_employee_ids))])
        if branch_id and branches:
            departments = departments.filtered(lambda dep: dep.dm_branch_id in branches)
            employees = employees.filtered(lambda emp: emp.dm_branch_id in branches)

        def employee_payload(employee):
            return {
                'id': employee.id,
                'name': employee.name,
                'job': employee.job_id.name or '',
                'manager': employee.parent_id.name or '',
                'model': 'hr.employee',
                'resId': employee.id,
            }

        employee_by_department = {}
        for employee in employees:
            key = (employee.dm_unit_id or employee.dm_section_id or employee.department_id).id
            employee_by_department.setdefault(key, []).append(employee_payload(employee))

        children_by_parent = {}
        for department in departments:
            children_by_parent.setdefault(department.parent_id.id or 0, []).append(department)

        level_labels = dict(Department._fields['dm_org_level']._description_selection(self.env))

        def department_node(department):
            children = [department_node(child) for child in children_by_parent.get(department.id, [])]
            node_employees = employee_by_department.get(department.id, [])
            manager = department.dm_approval_manager_id or department.manager_id
            return {
                'id': f'department-{department.id}',
                'resId': department.id,
                'model': 'hr.department',
                'name': department.name,
                'level': department.dm_org_level,
                'levelLabel': level_labels.get(department.dm_org_level, ''),
                'manager': manager.name or '',
                'employeeCount': len(node_employees),
                'employees': node_employees,
                'children': children,
            }

        root_nodes = []
        for branch in branches:
            branch_departments = departments.filtered(lambda dep: dep.dm_branch_id == branch and dep.dm_org_level == 'sector')
            if not branch_departments:
                branch_departments = departments.filtered(lambda dep: dep.dm_branch_id == branch and not dep.parent_id)
            branch_employees = employees.filtered(lambda emp: emp.dm_branch_id == branch)
            root_nodes.append({
                'id': f'branch-{branch.id}',
                'resId': branch.id,
                'model': 'dm.hr.branch',
                'name': branch.name,
                'level': 'branch',
                'levelLabel': _('فرع'),
                'manager': branch.manager_id.name or '',
                'employeeCount': len(branch_employees),
                'employees': [],
                'children': [department_node(dep) for dep in branch_departments],
            })
        if not branch_id:
            unassigned_departments = departments.filtered(lambda dep: not dep.dm_branch_id and not dep.parent_id)
            orphan_departments = departments.filtered(
                lambda dep: not dep.dm_branch_id and dep.parent_id and dep.parent_id not in departments
            )
            general_departments = (unassigned_departments | orphan_departments).sorted(
                lambda dep: (dep.dm_approval_level, dep.name or '', dep.id)
            )
            general_employees = employees.filtered(lambda emp: not emp.dm_branch_id)
            if general_departments or general_employees:
                root_nodes.append({
                    'id': 'general-structure',
                    'resId': companies[:1].id if companies else False,
                    'model': 'res.company',
                    'name': _('هيكل عام / بدون فرع'),
                    'level': 'branch',
                    'levelLabel': _('عام'),
                    'manager': '',
                    'employeeCount': len(general_employees),
                    'employees': [
                        employee_payload(employee)
                        for employee in general_employees.filtered(lambda emp: not emp.department_id)
                    ],
                    'children': [department_node(dep) for dep in general_departments],
                })

        summary = {
            'branches': len(branches),
            'sectors': len(departments.filtered(lambda dep: dep.dm_org_level == 'sector')),
            'departments': len(departments.filtered(lambda dep: dep.dm_org_level == 'department')),
            'sections': len(departments.filtered(lambda dep: dep.dm_org_level == 'section')),
            'units': len(departments.filtered(lambda dep: dep.dm_org_level == 'unit')),
            'employees': len(employees),
        }
        return {
            'nodes': root_nodes,
            'summary': summary,
            'filters': {
                'companies': [{'id': company.id, 'name': company.name} for company in self.env.companies],
                'branches': [{'id': branch.id, 'name': branch.name, 'company_id': branch.company_id.id} for branch in self.sudo().search([('company_id', 'in', self.env.companies.ids)])],
            },
        }


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    dm_org_level = fields.Selection(
        [
            ('sector', 'قطاع'),
            ('department', 'إدارة'),
            ('section', 'قسم'),
            ('unit', 'وحدة'),
        ],
        string='المستوى التنظيمي',
        default='department',
        required=True,
        help='استخدم القطاع لتجميع الإدارات، الإدارة للنشاط الرئيسي، القسم للتخصص، والوحدة عند الحاجة فقط.',
    )
    dm_branch_id = fields.Many2one('dm.hr.branch', string='الفرع')
    dm_approval_manager_id = fields.Many2one(
        'hr.employee',
        string='مسؤول موافقات الإدارة',
        help='إذا تم تحديده، يستخدمه محرك الموافقات كمعتمد الإدارة بدلاً من مدير الإدارة القياسي.',
    )
    dm_approval_level = fields.Integer(
        string='مستوى الإدارة',
        default=10,
        help='رقم أقل يعني مستوى أعلى في الهيكل. يستخدم للترتيب والتحليل.',
    )

    @api.constrains('dm_org_level', 'parent_id', 'dm_branch_id')
    def _check_org_hierarchy(self):
        allowed_parent_levels = {
            'sector': {False},
            'department': {False, 'sector'},
            'section': {'department'},
            'unit': {'section'},
        }
        for department in self:
            if department.dm_org_level == 'sector' and not department.dm_branch_id:
                raise ValidationError(_('يجب تحديد الفرع عند إنشاء قطاع.'))
            parent_level = department.parent_id.dm_org_level if department.parent_id else False
            if parent_level not in allowed_parent_levels.get(department.dm_org_level, set()):
                raise ValidationError(_(
                    'تسلسل الهيكل غير صحيح: القطاع بدون أب، الإدارة يمكن أن تكون رئيسية أو تحت قطاع، القسم تحت إدارة، والوحدة تحت قسم.'
                ))
            if department.parent_id and department.parent_id.dm_branch_id and department.dm_branch_id:
                if department.dm_branch_id != department.parent_id.dm_branch_id:
                    raise ValidationError(_('فرع المستوى التنظيمي يجب أن يطابق فرع المستوى الأعلى.'))


class HrJob(models.Model):
    _inherit = 'hr.job'

    dm_approval_role = fields.Selection(
        [
            ('none', 'بدون دور موافقات خاص'),
            ('department_manager', 'مدير إدارة'),
            ('section_manager', 'مدير قسم'),
            ('hr_reviewer', 'مراجع موارد بشرية'),
            ('executive', 'اعتماد تنفيذي'),
        ],
        string='دور الموافقات',
        default='none',
        help='يساعد في اختيار المعتمد تلقائياً حسب الوظيفة داخل نفس الإدارة أو الشركة.',
    )

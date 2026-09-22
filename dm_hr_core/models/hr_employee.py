# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # ------------------------------------------------------------------
    # Identity / DM HR fields (Arabic name, employment status)
    # ------------------------------------------------------------------
    employee_number = fields.Char(
        string='الرقم الوظيفي',
        copy=False,
        index=True,
        tracking=True,
        groups='hr.group_hr_user',
    )
    name_ar = fields.Char(
        string='الاسم بالعربية',
        groups='hr.group_hr_user',
    )
    dm_employment_status = fields.Selection(
        [
            ('active', 'نشط'),
            ('on_leave', 'في إجازة'),
            ('suspended', 'موقوف'),
            ('terminated', 'منتهي الخدمة'),
        ],
        string='حالة التوظيف',
        default='active',
        tracking=True,
        groups='hr.group_hr_user',
    )

    # NOTE: the base ``employee_type`` field (Employee / Student / Trainee /
    # Contractor / Freelancer) is intentionally left untouched by this module.
    # The GOSI category below is the DM-specific nationality classification
    # used later by the social insurance rate engine.
    gosi_employee_category = fields.Selection(
        [('saudi', 'سعودي'), ('non_saudi', 'غير سعودي')],
        string='فئة الموظف في التأمينات',
        copy=False,
        groups='hr.group_hr_user',
        tracking=True,
        help='تصنيف التأمينات حسب الجنسية، ويستخدم لاحقاً في محرك نسب التأمينات.',
    )
    # Identity fields used by the alerts below.
    iqama_no = fields.Char(
        string='الإقامة / الهوية الوطنية',
        groups='hr.group_hr_user',
    )
    iqama_expiry_date = fields.Date(
        string='انتهاء الإقامة / الهوية الوطنية',
        groups='hr.group_hr_user',
    )
    social_security_no = fields.Char(
        string='رقم الاشتراك في التأمينات',
        groups='hr.group_hr_user',
        help='رقم اشتراك الموظف لدى التأمينات الاجتماعية.',
    )
    dm_bank_name = fields.Char(
        string='اسم البنك',
        groups='hr.group_hr_user',
        tracking=True,
    )
    dm_iban = fields.Char(
        string='IBAN',
        groups='hr.group_hr_user',
        tracking=True,
    )
    blood_type = fields.Selection(
        [
            ('O+', 'O+'), ('O-', 'O-'),
            ('A+', 'A+'), ('A-', 'A-'),
            ('B+', 'B+'), ('B-', 'B-'),
            ('AB+', 'AB+'), ('AB-', 'AB-'),
        ],
        string='فصيلة الدم',
        groups='hr.group_hr_user',
    )
    emergency_contact_name = fields.Char(string='جهة اتصال الطوارئ')
    emergency_contact_phone = fields.Char(string='هاتف الطوارئ')
    join_date = fields.Date(string='تاريخ الالتحاق', tracking=True)
    dm_branch_id = fields.Many2one(
        'dm.hr.branch',
        string='الفرع',
        tracking=True,
        groups='hr.group_hr_user',
        help='الفرع المالي/الجغرافي للموظف، مستقل عن الإدارة.',
    )
    dm_sector_id = fields.Many2one(
        'hr.department',
        string='القطاع',
        domain="[('dm_org_level', '=', 'sector')]",
        tracking=True,
        groups='hr.group_hr_user',
    )
    dm_department_level_id = fields.Many2one(
        'hr.department',
        string='الإدارة',
        domain="[('dm_org_level', '=', 'department')]",
        tracking=True,
        groups='hr.group_hr_user',
    )
    dm_section_id = fields.Many2one(
        'hr.department',
        string='القسم',
        domain="[('dm_org_level', '=', 'section')]",
        tracking=True,
        groups='hr.group_hr_user',
    )
    dm_unit_id = fields.Many2one(
        'hr.department',
        string='الوحدة',
        domain="[('dm_org_level', '=', 'unit')]",
        tracking=True,
        groups='hr.group_hr_user',
    )

    dm_dependent_ids = fields.One2many(
        'dm.hr.employee.dependent', 'employee_id', string='المرافقون')
    dm_insurance_policy_ids = fields.One2many(
        'dm.hr.insurance.policy', 'employee_id', string='وثائق التأمين')
    dm_document_ids = fields.One2many(
        'dm.hr.document', 'employee_id', string='المستندات')
    dm_service_request_ids = fields.One2many(
        'dm.hr.service.request', 'employee_id', string='طلبات خدمات الموظف')

    # ------------------------------------------------------------------
    # Smart-button counters (contracts now; attendance/leaves/requests
    # are populated by later dm_hr_* modules, defaulting to 0 here).
    # ------------------------------------------------------------------
    dm_contract_count = fields.Integer(
        string='العقود', compute='_compute_dm_smart_counts')
    dm_attendance_count = fields.Integer(
        string='عدد سجلات الحضور', compute='_compute_dm_smart_counts')
    dm_leave_count = fields.Integer(
        string='عدد الإجازات', compute='_compute_dm_smart_counts')
    dm_request_count = fields.Integer(
        string='عدد الطلبات', compute='_compute_dm_smart_counts')
    dm_task_count = fields.Integer(
        string='المهام', compute='_compute_dm_smart_counts')
    dm_custody_count = fields.Integer(
        string='العهد', compute='_compute_dm_smart_counts')

    @api.depends('contract_ids', 'dm_service_request_ids')
    def _compute_dm_smart_counts(self):
        Attendance = self.env['hr.attendance'].sudo()
        Leave = self.env['hr.leave'].sudo()
        ServiceRequest = self.env['dm.hr.service.request'].sudo()
        Task = self.env['project.task'].sudo()
        Custody = self.env['dm.hr.custody'].sudo()
        for employee in self:
            employee.dm_contract_count = len(employee.contract_ids)
            employee.dm_attendance_count = Attendance.search_count([
                ('employee_id', '=', employee.id),
            ])
            employee.dm_leave_count = Leave.search_count([
                ('employee_id', '=', employee.id),
            ])
            employee.dm_request_count = ServiceRequest.search_count([
                ('employee_id', '=', employee.id),
            ])
            employee.dm_task_count = Task.search_count([
                ('dm_employee_id', '=', employee.id),
            ])
            employee.dm_custody_count = Custody.search_count([
                ('employee_id', '=', employee.id),
            ])

    @api.onchange('dm_branch_id')
    def _onchange_dm_branch_id(self):
        self.dm_sector_id = False
        self.dm_department_level_id = False
        self.dm_section_id = False
        self.dm_unit_id = False
        self.department_id = False

    @api.onchange('dm_sector_id')
    def _onchange_dm_sector_id(self):
        self.dm_department_level_id = False
        self.dm_section_id = False
        self.dm_unit_id = False
        self.department_id = False

    @api.onchange('dm_department_level_id')
    def _onchange_dm_department_level_id(self):
        self.dm_section_id = False
        self.dm_unit_id = False
        self.department_id = False

    @api.onchange('dm_section_id')
    def _onchange_dm_section_id(self):
        self.dm_unit_id = False
        self.department_id = self.dm_section_id

    @api.onchange('dm_unit_id')
    def _onchange_dm_unit_id(self):
        self.department_id = self.dm_unit_id or self.dm_section_id

    def _sync_base_department_from_org(self, vals):
        if 'dm_unit_id' in vals and vals.get('dm_unit_id'):
            vals['department_id'] = vals['dm_unit_id']
        elif 'dm_section_id' in vals and vals.get('dm_section_id') and not vals.get('dm_unit_id'):
            vals['department_id'] = vals['dm_section_id']
        elif any(field in vals for field in ('dm_branch_id', 'dm_sector_id', 'dm_department_level_id')):
            if not vals.get('dm_section_id') and not vals.get('dm_unit_id'):
                vals['department_id'] = False
        return vals

    def _has_org_data(self):
        self.ensure_one()
        return any([
            self.dm_branch_id,
            self.dm_sector_id,
            self.dm_department_level_id,
            self.dm_section_id,
            self.dm_unit_id,
        ])

    # ------------------------------------------------------------------
    # Automatic employee number
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('employee_number'):
                vals['employee_number'] = self.sudo()._get_next_employee_number()
            self._sync_base_department_from_org(vals)
        return super().create(vals_list)

    def write(self, vals):
        vals = dict(vals)
        self._sync_base_department_from_org(vals)
        return super().write(vals)

    @api.model
    def _get_next_employee_number(self):
        """Generate the next unique employee number via a dedicated ir.sequence."""
        number = self.env['ir.sequence'].sudo().next_by_code(
            'dm.hr.employee.number')
        if not number:
            # Fallback: deterministic max-based number if the sequence is missing.
            last = self.search(
                [('employee_number', '!=', False)],
                order='employee_number desc', limit=1)
            try:
                last_num = int(last.employee_number) if last and last.employee_number else 0
            except ValueError:
                last_num = 0
            number = str(last_num + 1)
        return number

    # ------------------------------------------------------------------
    # Uniqueness: employee number and identity per company
    # ------------------------------------------------------------------
    _sql_constraints = [
        (
            'employee_number_company_uniq',
            'UNIQUE(employee_number, company_id)',
            'يجب أن يكون الرقم الوظيفي فريداً داخل الشركة.',
        ),
    ]

    @api.constrains('iqama_no', 'company_id')
    def _check_iqama_unique(self):
        for employee in self:
            if not employee.iqama_no:
                continue
            duplicate = self.sudo().search([
                ('iqama_no', '=', employee.iqama_no),
                ('company_id', '=', employee.company_id.id),
                ('id', '!=', employee.id),
            ], limit=1)
            if duplicate:
                raise ValidationError(_(
                    "الإقامة / الهوية الوطنية '%s' مستخدمة بالفعل لموظف آخر "
                    "داخل هذه الشركة.") % employee.iqama_no)

    @api.constrains('dm_iban')
    def _check_saudi_iban(self):
        for employee in self:
            if employee.dm_iban and not employee.dm_iban.replace(' ', '').upper().startswith('SA'):
                raise ValidationError(_('رقم IBAN السعودي يجب أن يبدأ بـ SA.'))

    @api.constrains(
        'dm_branch_id', 'dm_sector_id', 'dm_department_level_id',
        'dm_section_id', 'dm_unit_id', 'department_id', 'parent_id',
    )
    def _check_dm_employee_org_structure(self):
        for employee in self:
            if employee.parent_id and employee.parent_id == employee:
                raise ValidationError(_('لا يمكن اختيار الموظف مديراً مباشراً لنفسه.'))

            if not employee._has_org_data():
                continue

            missing = []
            if not employee.dm_branch_id:
                missing.append(_('الفرع'))
            if not employee.dm_sector_id:
                missing.append(_('القطاع'))
            if not employee.dm_department_level_id:
                missing.append(_('الإدارة'))
            if not employee.dm_section_id:
                missing.append(_('القسم'))
            if missing:
                raise ValidationError(_('يجب إكمال الربط التنظيمي للموظف: %s.') % '، '.join(missing))

            if employee.dm_sector_id.dm_org_level != 'sector':
                raise ValidationError(_('الحقل "القطاع" يجب أن يحتوي سجلاً من مستوى قطاع فقط.'))
            if employee.dm_sector_id.dm_branch_id != employee.dm_branch_id:
                raise ValidationError(_('القطاع المختار لا يتبع الفرع المحدد.'))
            if employee.dm_department_level_id.dm_org_level != 'department':
                raise ValidationError(_('الحقل "الإدارة" يجب أن يحتوي سجلاً من مستوى إدارة فقط.'))
            if employee.dm_department_level_id.parent_id != employee.dm_sector_id:
                raise ValidationError(_('الإدارة المختارة لا تتبع القطاع المحدد.'))
            if employee.dm_section_id.dm_org_level != 'section':
                raise ValidationError(_('الحقل "القسم" يجب أن يحتوي سجلاً من مستوى قسم فقط.'))
            if employee.dm_section_id.parent_id != employee.dm_department_level_id:
                raise ValidationError(_('القسم المختار لا يتبع الإدارة المحددة.'))
            if employee.dm_unit_id:
                if employee.dm_unit_id.dm_org_level != 'unit':
                    raise ValidationError(_('الحقل "الوحدة" يجب أن يحتوي سجلاً من مستوى وحدة فقط.'))
                if employee.dm_unit_id.parent_id != employee.dm_section_id:
                    raise ValidationError(_('الوحدة المختارة لا تتبع القسم المحدد.'))

            expected_department = employee.dm_unit_id or employee.dm_section_id
            if employee.department_id != expected_department:
                raise ValidationError(_('الإدارة التقنية في Odoo يجب أن تطابق آخر مستوى تنظيمي مختار: الوحدة أو القسم.'))

    # ------------------------------------------------------------------
    # Contract smart action (open the active contract)
    # ------------------------------------------------------------------
    def action_open_contracts(self):
        self.ensure_one()
        return {
            'name': _('العقود'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.contract',
            'view_mode': 'tree,form',
            'domain': [('employee_id', '=', self.id)],
            'context': {'default_employee_id': self.id},
        }

    def action_open_attendances(self):
        self.ensure_one()
        return {
            'name': _('الحضور والانصراف'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.attendance',
            'view_mode': 'tree,form',
            'domain': [('employee_id', '=', self.id)],
            'context': {'default_employee_id': self.id},
        }

    def action_open_leaves(self):
        self.ensure_one()
        return {
            'name': _('الإجازات'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.leave',
            'view_mode': 'tree,form,kanban,calendar,activity',
            'domain': [('employee_id', '=', self.id)],
            'context': {'default_employee_id': self.id},
        }

    def action_open_service_requests(self):
        self.ensure_one()
        return {
            'name': _('طلبات خدمات الموظف'),
            'type': 'ir.actions.act_window',
            'res_model': 'dm.hr.service.request',
            'view_mode': 'kanban,tree,form,activity',
            'domain': [('employee_id', '=', self.id)],
            'context': {'default_employee_id': self.id},
        }

    def action_open_tasks(self):
        self.ensure_one()
        return {
            'name': _('مهام الموظف'),
            'type': 'ir.actions.act_window',
            'res_model': 'project.task',
            'view_mode': 'tree,kanban,form,pivot,graph,calendar,activity',
            'domain': [('dm_employee_id', '=', self.id)],
            'context': {'default_dm_employee_id': self.id},
        }

    def action_open_custodies(self):
        self.ensure_one()
        return {
            'name': _('العهد غير المالية'),
            'type': 'ir.actions.act_window',
            'res_model': 'dm.hr.custody',
            'view_mode': 'tree,form,kanban,activity',
            'domain': [('employee_id', '=', self.id)],
            'context': {'default_employee_id': self.id},
        }

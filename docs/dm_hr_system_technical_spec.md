# النظام المتكامل لموارد البشرية (DM HR System) — المواصفات الفنية

**الإصدار:** **1.1** (مراجعة 1 + قرارات الاعتماد مُدمجة) | **النظام:** Odoo 17 **Community** | **التاريخ:** 2026-08-09
> وثيقة تحليل وتصميم + ملحق تنفيذ. تم اعتماد قرارات التنفيذ (القسم 15) وبدأ تطبيق `dm_hr_core` على الفرع `feature/dm-hr-core` — جاري التهيئة/الاختبار على `dm_hr_test`.

---

## 0. سجل المراجعة — التعديلات الـ15 في الإصدار 1.1

| # | مطلب المراجعة | القرار في 1.1 |
|---|---|---|
| 1 | بدلات مرنة بدل الحقول الثابتة | `dm.hr.allowance.type` + `dm.hr.contract.allowance` + `dm.hr.employee.allowance` (القسم 3.1) |
| 2 | توحيد `gosi_` + مخطط تأميني تاريخي | `dm.hr.social.insurance.scheme` + `.rate`؛ `res.company` تحمل المخطط الافتراضي فقط (3.2) |
| 3 | محرك رواتب Declarative بلا Python/`safe_eval` | `calctype` مغلق من 12 نوعًا + تحقق circular/تكرار/قسمة صفر (3.8) |
| 4 | إعادة تصميم ربط الموافقات | مقارنة الخيارات + النموذج المركزي `dm.approval.request` (3.4) |
| 5 | صلاحيات الموافقات | لا Create/Unlink مباشر على `dm.approval.item` والتحقق داخل Python (5.4) |
| 6 | فصل مجموعات المستخدمين | 10 مجموعات مفصولة؛ المعماري لا يرث `account` (5.1) |
| 7 | فصل الربط المحاسبي | `dm_hr_payroll_account` مستقل يعتمد على `payroll + account` (3.9) |
| 8 | إجازات بدون منطق ثابت + Adapter | أنواع `noupdate` بكود `ANNUAL...`؛ Adapter يحافظ على الحالات الأصلية (3.6) |
| 9 | إثبات `hr.attendance.overtime` + ملكية واحدة | **موجود ومُثبت**؛ مالك النموذج `dm_hr_attendance` (3.5) |
| 10 | فصل تعريف الراتب عن خطاب تحويل الراتب | 3 طلبات مستقلة + `dm.hr.probation.confirmation.request` (3.7) |
| 11 | Workflow موحد | حالات: draft/submitted/under_approval/approved/rejected/cancelled + phases تشغيلية (4) |
| 12 | قابليّة تدقيق الرواتب | snapshot مجمد + مصدر كل سطر + calculation_log + Recompute في draft فقط (3.8) |
| 13 | حماية البيانات الحساسة | مصفوفة RBAC + `groups=` على الحقول + لا sudo عام (5.3) |
| 14 | قاعدة اختبار | مقترح `dm_hr_test` — لا إنشاء بلا موافقة (13) |
| 15 | مخرجات المراجعة | هذه الوثيقة 1.1 + المعمارية/الأمان/الـDoD (الأقسام 2-12) |

### 0.1 القرارات المعتمدة (جلسة الاعتماد 2026-08-09 — ملزمة التنفيذ)
| القرار | المعتمد |
|---|---|
| **(أ) قاعدة الاختبار** | إنشاء `dm_hr_test` مستقلة؛ لا تعديل/حذف لـ `kh1_odoo17`؛ لا استيراد بيانات إنتاج؛ فحص الاسم أولًا؛ الترميز القياسي PostgreSQL/Odoo؛ توثيق أمر الإنشاء ونتيجته |
| **(ب) القيد المحاسبي** | **قيد موحّد واحد لكل Payroll Batch** (`move_id` على الدفعة)؛ كل قسيمة تحتفظ بعلاقة واضحة بالدفعة؛ كل سطر محاسبي يعود إلى Salary Rule ومصدره؛ تجميع الحسابات المتشابهة (حساب/شريك/تحليلي)؛ التفاصيل تبقى في القسيمة دون اسم موظف في القيد المجمّع إلا بالإعداد؛ لا ترحيل مزدوج؛ لا تعديل بعد الترحيل؛ الإلغاء بقيد عكسي لا حذف؛ قابل للتوسعة مستقبلًا نحو "قيد لكل قسيمة" دون تنفيذه الآن |
| **(ج) محرك إجازات** | `use_dm_approval=False` افتراضيًا لكل الأنواع؛ يُفعَّل من `hr.leave.type`؛ معطّل = Workflow Odoo الأصلي دون تغيير؛ مفعّل = DM طبقة موافقة قبل التنفيذ الأصلي النهائي؛ لا تغيير لحالات `hr.leave` ولا كسر للرصيد/التقويم/الاعتمادات؛ لا اعتماد فعلي قبل اكتمال سلسلة DM؛ اختبارات للمسارين معًا |
| **(د) البيانات الافتراضية** | `noupdate="1"` فقط، **بلا أي نسب مالية أو قيم قانونية**؛ 5 بدلات (HOUSING/TRANSPORT/COMMUNICATION/MEAL/OTHER) و4 إجازات (ANNUAL/SICK/UNPAID/EMERGENCY)؛ لا 30 يومًا ولا نسب GOSI ولا مبالغ ولا معدلات إضافي؛ قابلة للتعديل/الأرشفة؛ لا تكرار عند الترقية؛ عامة وتُنسخ لكل شركة عبر إعداد واضح |
| **(هـ) نطاق المرحلة 1** | تنفيذ **`dm_hr_core` فقط** (موظفون/عقود/بدلات/تأمينات/تابعون/مستندات/إعدادات/أمان/قوائم/واجهات/ترجمة/اختبارات core). **لا** تنفيذ: approval/إجازات/حضور/طلبات/رواتب/محاسبة/Portal/Dashboard |

---

## 1. البيئة المعتمدة (نتائج الفحص الفعلي)

| البند | النتيجة |
|---|---|
| Odoo | **17.0 FINAL Community** — لا `enterprise` ولا `ent_*` في addons_path |
| Python / PostgreSQL | 3.12.3 / 16 — القاعدة النشطة: `kh1_odoo17` (الخادم port 8070, `--dev=assets`) |
| لغات مفعّلة | `en_US` فقط → تفعيل `ar_SA` ضمن المرحلة 0 |
| شركات | 3 (US/SAR Saudi + SA Company SAR) → multi-company فعّال |
| مثبّت ذو صلة | `hr`, `mail`, `portal`, `web_hierarchy`, `account`, `l10n_sa`, `web`... |
| متوفر غير مثبّت | `hr_contract`, `hr_attendance`, `hr_holidays`, `hr_holidays_attendance`, `hr_work_entry(_contract)`... |
| Payroll | **غير موجود** في Community (Enterprise حصري) → محرك خاص بنا |

### 1.1 إثبات وجود `hr.attendance.overtime` في Odoo 17 Community (مطلب 9)
فحص فعلي للملفات:
```
/opt/odoo17/odoo/addons/hr_attendance/models/hr_attendance_overtime.py
  class HrAttendanceOvertime(models.Model):
      _name = "hr.attendance.overtime"         # ← مرجع موثّق
      employee_id, company_id(related), date,
      duration ('Extra Hours'), duration_real ('Extra Hours (Real)'), adjustment
      init(): UNIQUE INDEX (employee_id, date) WHERE adjustment IS FALSE
/opt/odoo17/odoo/addons/hr_attendance/models/__init__.py
  from . import hr_attendance_overtime         # ← نعم، مسجّل
/opt/odoo17/odoo/addons/hr_attendance/views/hr_attendance_overtime_view.xml   → tree/search/action
/opt/odoo17/odoo/addons/hr_attendance/controllers/main.py:44                        → kiosk usage
/opt/odoo17/odoo/addons/hr_attendance/tests/test_hr_attendance_overtime.py         → ملف اختبار
```
**النتيجة:** النموذج **موجود** في Community، لذا يجوز `_inherit` عليه، وهو يمثل **سجل الإثبات/الساعات الفعلية** (evidence). يبقى طلب العمل الإضافي والاعتماد نموذجًا جديدًا منفصلًا (3.5).

### 1.2 قاعدة الاختبار (مطلب 14)
- قاعدة `odoo17` الحالية **غير معتمدة** كبيئة نظيفة (تُفحص عند الاستخدام).
- المقترح: قاعدة جديدة باسم **`dm_hr_test`** — **لن أُنشئها أو أحذفها قبل موافقتك الصريحة** (13).

---

## 2. المعمارية المعدّلة (النسخة 1.1)

### 2.1 الموديولات الثمانية
```text
1. dm_hr_core           أساس نماذج HR والبدلات والتأمينات     [لا يعتمد account]
2. dm_hr_approval       محرك الموافقات المركزي               [يعتمد dm_hr_core]
3. dm_hr_attendance     الحضور والورديات والعمل الإضافي      [يعتمد hr_attendance + dm_hr_core + dm_hr_approval]
4. dm_hr_leave          الإجازات + Adapter مع hr_holidays     [hr_holidays + dm_hr_approval + dm_hr_core]
5. dm_hr_requests       الطلبات (تعريف/تحويل/سلف/أذون/انتداب/تثبيت تجربة/عام) [dm_hr_core + dm_hr_approval + portal]
6. dm_hr_payroll        محرك الرواتب القابل للتدقيق          [dm_hr_core + dm_hr_attendance + dm_hr_leave + dm_hr_requests — بدون account]
7. dm_hr_payroll_account تكامل محاسبي (مستقل)                [dm_hr_payroll + account]
8. dm_hr_reports        التقارير والبوابة                    [كل ما سبق — يوفر PDFs/Layout]
```

### 2.2 Dependency Graph المعدّل
```text
                    ┌──────────────────────────────────────────┐
                    │              dm_hr_core                  │
                    └──────────────────────────────────────────┘
                       │            │            │        │
              ┌────────┘            │            │        └──────────────┐
       ┌──────▼──────┐      ┌───────▼────────┐  ┌▼──────────┐    ┌────────▼─────────┐
       │dm_hr_approval│     │dm_hr_attendance │  │dm_hr_leave │   │dm_hr_requests     │
       └──────┬──────┘      └───────┬────────┘  └─────┬──────┘   └────────┬─────────┘
              │                     │                 │                   │
              └─────────────────────┴───────┬─────────┴───────────────────┘
                                    ┌───────▼────────┐      ┌──────────────────────────┐
                                    │  dm_hr_payroll  │──────▶│  dm_hr_payroll_account  │
                                    └───────┬────────┘      │ (payroll + account only) │
                                            │               └──────────────────────────┘
                                     ┌──────▼────────┐
                                     │  dm_hr_reports │
                                     └────────────────┘
```
- **حد مالكي النماذج:** كل نموذج له مالك واحد؛ الوحدات الأعلى لا تُعرّف نماذج نظيرها.
- **العمل الإضافي:** طلبه واعتماده في `dm_hr_attendance` فقط؛ الإدخال المالي الناتج في `dm_hr_payroll` (3.5).
- **المحاسبة:** `account` لا يظهر إلا في `dm_hr_payroll_account` (3.9).

### 2.3 الأسماء/الاصطلاحات
- الحقول بأسماء إنجليزية؛ السلاسل تُترجم عبر `i18n` (عربي/إنجليزي).
- كل النسب/المبالغ الإدارية قابلة للتهيئة؛ **لا قيم ثابتة في الكود** (قاعدة 9).
- بادئة النماذج `dm.` والأكواد كبيرة (ANNUAL, HOUSING, GOSI…).

---

## 3. النماذج والعلاقات المعدّلة

### 3.1 البدلات (مطلب 1) — بدل الحقول الثابتة القديمة `housing/transport/meal/other`

| النموذج | الحقول الأساسية |
|---|---|
| `dm.hr.allowance.type` | `code` (Char، **فريد داخل الشركة**), `name` (translate), `amount_type` (fixed / percentage_of_basic / percentage_of_component), `schedule` (monthly / one_time), `subject_to_gosi` (خاضع للتأمينات), `include_in_net` (يدخل صافي الراتب), `show_on_payslip`, `sequence`, `company_id` (Required), `currency_id`, `active` |
| `dm.hr.contract.allowance` | `contract_id` (M2O hr.contract), `allowance_type_id` (M2O), `amount` (Monetary — للـ fixed), `percent` (Float — للنسبة), `percent_of_allowance_type_id` (M2O — نسبة من مكوّن آخر), `start_date`, `end_date`, `state` (draft/active/expired), `company_id`/`currency_id` (related من العقد), `note` |
| `dm.hr.employee.allowance` (استثنائي بعد موافقة) | `employee_id`, `allowance_type_id`, `amount`, `percent`, `start_date`, `end_date`, `approval_request_id` (M2O → dm.approval.request), `source` (policy/approval), `company_id`, `currency_id`, `active` |

- **رمز/بدل الموظف الاستثنائي** يُنشأ بعد وصول طلب الموافقة إلى `approved` فقط (الربط بـ `approval_request_id` يُضاف في مرحلة `dm_hr_approval`).
- **تحققات:** لا تداخل لفترتين من نفس النوع لنفس العقد؛ `start_date < end_date`؛ `percent` موجب ≤ 100؛ النسبة من مكوّن آخر تمنع الدوران (نوع لا يشير لنفسه).
- إزالة الحقول الثابتة من تصميم `hr.contract`؛ يبقى فيه `allowance_ids` (One2many) فقط.
- قواعد `subject_to_gosi` تُغذّي `dm.hr.social.insurance.rate.subject_allowance_type_ids`.

**البيانات الافتراضية للبدلات (قرار (د)) — تُحمَّل بـ `noupdate="1"` بلا أي قيم مالية:**
`HOUSING` Housing | `TRANSPORT` Transportation | `COMMUNICATION` Communication | `MEAL` Meal | `OTHER` Other
- كلها `amount_type=fixed` (قيمة فارغة تُملأ على الخط)، `schedule=monthly`، `subject_to_gosi=False`، `include_in_net=True`، `show_on_payslip=True` — **قابلة للتعديل/الأرشفة**، وهي `company_id=False` كقوالب عامة ثم تُنسخ لكل شركة عبر إعداد واضح عند الحاجة، بلا تكرار عند الترقية.

### 3.2 التأمينات (مطلب 2) — توحيد `gosi_` + نموذج تاريخي

| النموذج | الحقول الأساسية |
|---|---|
| `dm.hr.social.insurance.scheme` | `name`, `code`, `company_id`, `rate_ids` (One2many), `active`, `default_company_id` (لا يتكرر الافتراضي) |
| `dm.hr.social.insurance.rate` | `scheme_id`, `employee_category` (M2O `hr.employee.category` — جنسية/فئة) أو selection, `gosi_employee_ratio`, `gosi_employer_ratio`, `gosi_sanad_ratio` (أو `additional_component_ratio` + `additional_component_label`), `min_insurable_wage`, `max_insurable_wage` (Monetary), `subject_allowance_type_ids` (M2M إلى `dm.hr.allowance.type`), `effective_from` (Date), `effective_to` (Date), `company_id` |
| `hr.contract` (inherit) | `gosi_insured` (Boolean — **الاسم `gosi_` وليس `gos_`**), `gosi_balance`? (لا — سجل فترات من المخطط), `medical_insurance_policy_id` |
| `res.company` (inherit) | `default_social_insurance_scheme_id` (M2O — **المخطط الافتراضي فقط**)؛ لا حقول نسب مباشرة |
| `res.config.settings` (inherit) | واجهة لاختيار المخطط الافتراضي وإدارة المخططات |

- **منع تداخل الفترات:** قيد ORM/سجل على `dm.hr.social.insurance.rate`: لا يسمح بفترتين متقاطعتين لنفس `(scheme_id, employee_category/selection, company_id)`.
- **الحد الأدنى/الأقصى:** يُطبَّق على الأجر الخاضع (basic + أنواع بدلات `subject_allowance_type_ids`) لحظة احتساب القسيمة.
- عند التغيير لاحقًا تُنشأ فترة جديدة (`effective_from`) ولا تُعدَّل السابقة — أساس "اللقطة المجمدة" للقسائم.

### 3.3 محرك الموافقات — إعادة تصميم الربط (مطلب 4)

**مقارنة الخيارات الثلاثة لربط خطوات الاعتماد بأنواع الطلبات المتعددة:**

| المعيار | (أ) `fields.Reference` | (ب) `res_model` + `res_id` | (ج) نموذج مركزي `dm.approval.request` ✅ |
|---|---|---|---|
| سلامة مرجعية (FK/حذف) | لا FK | لا FK | FK عبر Many2one نحو الطلبات + `approval_request_id` منه |
| Cleanup عند حذف الطلب | يدوي/إشكالي | يدوي | `ondelete='cascade'` + خطاف تلقائي |
| فحص "نموذج مسموح" | يدوي | يدوي | قائمة بيضاء مركزية على `flow_id.model_id` + constraints |
| تقارير/بحث موحّدة | صعبة | متوسطة | **واجهة واحدة** لكل الطلبات + inbox موحّد |
| Record Rules multi-company | صعبة | متوسطة | سهلة (كلها على النموذج المركزي) |
| تسلسل موافقات وسجل | مبعثر | مبعثر | **One2many نظيف** `item_ids` |
| التعقيد | منخفض | منخفض | معتدل (مقبول) |

**القرار:** النموذج المركزي (**ج**).

### 3.4 نماذج `dm_hr_approval`

| النموذج | الحقول/الملاحظات |
|---|---|
| `dm.approval.flow` | `name`, `model_id` (نموذج مقبول للدفق — قائمة بيضاء), `company_id`, `allow_self_approval` (Boolean), `active`, `line_ids` |
| `dm.approval.flow.line` | `sequence`, `approver_type` (manager/department_manager/hr_manager/payroll_manager/role/specific_user), `approver_user_id`, `condition_field`, `condition_operator`, `condition_value`, `mandatory` |
| `dm.approval.request` (**مركزي**) | `res_model` (Char), `res_id` (Integer), `request_name`, `requester_id` (res.users), `employee_id` (hr.employee), `company_id` (Required), `flow_id`, `current_step_id` (M2O dm.approval.item الحالي أو current_sequence), `state` (الحالات العامة §4), `submission_hash` (Char), `submitted_on`, `item_ids` (One2many `dm.approval.item`) |
| `dm.approval.item` | `approval_request_id`, `flow_line_id`, `sequence`, `approver_user_id`, `state` (pending/approved/rejected), `date_done`, `comment`, `action_done_by_id` |
| `dm.approval.mixin` (**abstract**) | `approval_request_id` (M2O → يعطي One2many معكوسة), `state`,… + أساليب استدعاء المحرك |

**قيود وسلامة:**
- `_sql_constraints` على `dm.approval.request`: **UNIQUE(res_model, res_id)**.
- `_check_res_model_allowed`: عند create/update يُقارن `res_model` بمجموعة النماذج المسموحة في `dm.approval.flow` (`model_id`) → رفض عداها.
- **Cleanup:** كل نموذج طلب يطبق الـ mixin يحذف `approval_request_id` تلقائيًا عند حذف السجل (`unlink` → `_cleanup_approval_request()`)، ويُمنع حذف `dm.approval.request` وهو في `under_approval/approved` (السماح بالحذف يُعد خطأ تصميمي).
- **OPTIMISTIC LOCK:** عند `action_submit` يُحسب `submission_hash` من قيم الحقول المؤثرة؛ عند الاعتماد يُقارَن بالحالة الحالية — إن تغيّر الطلب بعد الإرسال، يُرفض الاعتماد وتُطلب إعادة الإرسال ("الطلب لم يتغير بعد الإرسال").
- لا يجوز الربط إلا بنماذج `_approval_res_model_whitelist` (تعرّفها النماذج المنفذة للـmixins: requests/advances/leaves/allowances/overtime…).

### 3.5 الحضور والعمل الإضافي (مطلب 9) — ملكية واحدة وفصل المسؤوليات

**إثبات:** `hr.attendance.overtime` **موجود** في Community (القسم 1.1)؛ نماذجه: `employee_id`, `date`, `duration`, `duration_real`, `adjustment`.

**فصل المفاهيم الأربعة:**

| الكيان | النموذج | المالك |
|---|---|---|
| طلب العمل الإضافي والاعتماد | `dm.hr.overtime.request` (جديد: `employee_id`, `date`, `start_time`, `end_time`, `hours`, `overtime_type` (normal/weekend/holiday), `reason`, عبر `dm.approval.mixin`) | **`dm_hr_attendance`** |
| إثبات الساعات الفعلية (أدلة الحضور) | `hr.attendance.overtime` (**inherit** لإضافة: `request_id` M2O, `verified_state`, `source`, `payslip_processed`) | **`dm_hr_attendance`** |
| النتيجة المعتمدة المجمّعة | `dm.hr.overtime.result` (جديد: `employee_id`, `period`, `hours_normal`, `hours_weekend`, `hours_holiday`, `request_ids`, `state`) | **`dm_hr_attendance`** |
| المدخل المالي الناتج | سطور payslip بقواعد `overtime_hours` (تقرأ المعتمَد فقط) — **لا نموذج جديد في dm_hr_payroll** | **`dm_hr_payroll`** |

- **القاعدة:** لا يُحسب إضافي للقسيمة إلا إذا جاء من `dm.hr.overtime.request` في `approved` ومستندًا إلى سجل إثبات حقيقي (أو إدخال يدوي معتمد من HR لإثبات الاستثناء).
- **dm_hr_requests لا يملك أي نموذج عمل إضافي** (يمنع الازدواجية).
- `hr.attendance.overtime` الأصلي (من الأجهزة/الإدخال اليدوي) يبقى evidence قائمًا بذاته.

### 3.6 الإجازات (مطلب 8) — أنواع افتراضية `noupdate` + Adapter يحافظ على الأصل

**تجنّب المنطق الثابت:**
- لا أسماء حقول سعودية (لا `annual_leaves`)؛ نضيف على `hr.leave.type` (inherit): `code` (Char), `use_dm_approval` (Boolean **افتراضي False — قرار (ج)**), `accrual_policy_id` (M2O).
- **الأنواع الافتراضية (قرار (د))**: فقط 4 أنواع بـ `noupdate="1"`: `ANNUAL` Annual Leave، `SICK` Sick Leave، `UNPAID` Unpaid Leave، `EMERGENCY` Emergency Leave — **بلا أي أيام/أرصدة/قيم**؛ قابلة للتعديل/الأرشفة. الأنواع الأخرى (MATERNITY/HAJJ...) تُنشأ يدويًا عند الحاجة — **لا تُعتبر تطبيقًا تلقائيًا لنظام العمل السعودي**.
- قواعد الرصيد/الاستحقاق: `dm.hr.leave.accrual.policy` (`days_per_year`, `carry_forward_days`, `max_consecutive_days`, قواعد الإنشاء التلقائي) أو الإعدادات — **لا قيمة ثابتة في الحساب**؛ حتى 30 يومًا تصبح قيمة في السياسة.
- **لا تعديل على دورة `hr.leave` الأصلية** (draft→confirm→validate1→validate) عند `use_dm_approval=False`.

**استراتيجية Adapter** (`dm.hr.leave.approval.adapter`):
0. **الافتراضي:** `use_dm_approval = False` لكل الأنواع عند التثبيت (قرار (ج)) — يعمل Workflow Odoo الأصلي 100% دون أي تدخل. التفعيل يدوي لكل `hr.leave.type` عبر الإعداد `use_dm_approval`.
1. عند `use_dm_approval=True`: إنشاء `dm.approval.request` واحد لكل `hr.leave`، و`hr.leave` يظل في حالة `draft`.
2. الاعتماد يجري عبر المحرك فقط؛ عند اكتمال كل الخطوات (approved) يستدعي الـ Adapter **داخل `hr_holidays`** `_action_validate()` — **وهي المسؤولة الوحيدة** عن: تجديد الرصيد والحساب، إنشاء/تأكيد allocation-effect، إنشاء الـ meeting على التقويم، والمتعلقات (activities).
3. عند الرفض يستدعي adapter مسار الرفض الأصلي (`_action_refuse()`) بحيث تبقى الحالات والتاريخ قياسيين.
4. المراسلات/الأنشطة: تُنشأ أنشطة على `hr.leave` عبر `action_submit` الخاص بالمحرك لإخبار الموافق الحالي (mail.activity) قبل أن تلتقطها `hr_holidays` للنشر النهائي.
5. **القيود المؤكدة (قرار (ج)):** لا يمكن لأي إجراء خارج DM أن يُنهي الاعتماد الفعلي قبل اكتمال كل خطوات DM؛ ولا تعديل عنيف لحالات `hr.leave` الأصلية (تظل draft/confirm/refuse/validate1/validate)، ولا كسر للرصيد/Calendar/Allocation.
6. **اختبارات إلزامية:** مسار أصلي (بدون DM) ومسار مخصص (مع DM) — كلاهما في `dm_hr_leave/tests`.

**يُحافظ على:** الأرصدة، allocations، activities، calendar، الحالات الأصلية draft/confirm/refuse/validate1/validate، وكل عمليات Odoo القياسية (استيراد/حساب أيام/بوابة).

### 3.7 طلبات `dm_hr_requests` (مطلب 10) — الفصل بين التعريف والتحويل والتثبيت

| النموذج | الحقول الأساسية | ملاحظات |
|---|---|---|
| `dm.hr.salary.certificate.request` | `certificate_type` (bank/embassy/company/other), `purpose`, `copies`, `fee` (من إعدادات الشركة), `issue_date`, `delivery_state` (issued/delivered), `pdf_attachment` | **تعريف الراتب** — يُولَّد PDF بعد `approved` |
| `dm.hr.salary.assignment.request` | `bank_id` (M2O `res.bank`), `iban` (Char)، `salary_transfer_start_date`, `recipient_entity_id`/`recipient_text`, `letter_type` (new/change/cancel), `reference_no`, `qr_token` / `verification_token`, `issue_date`, `delivery_state`, `pdf_attachment` (عربي/إنجليزي) | **خطاب تثبيت/تحويل راتب** — مستقل كليًا عن التعريف |
| `dm.hr.probation.confirmation.request` | `contract_id`, `evaluation_notes`, `decision` (confirm / prolong / terminate), `new_wage`, `effective_date`, `probation_end` | **تأكيد الموظف بعد فترة التجربة** — نوع ثالث مستقل |
| `dm.hr.advance.request` | `amount`, `currency_id`, `repayment_months`, `installment_amount` (محسوبة), `purpose` | تُغذي `loan_installment` في الرواتب |
| `dm.hr.permission.request` | `date`, `start_time`, `end_time`, `duration_hours`, `permission_type` (personal/medical/family/official) | يُقارن مع الحضور |
| `dm.hr.travel.request` | `destination`, `start_date`, `end_date`, `transport_type`, `accommodation`, `daily_allowance` (من إعدادات), `expense_estimate`, `report_filed` | انتداب/رحلة عمل |
| `dm.hr.general.request` | `subject`, `body`, `attachments` | طلب عام حر |

- جميعها عبر `dm.approval.mixin` + `mail.thread`.
- **لا** يوجد نموذج عمل إضافي هنا (ملكية `dm_hr_attendance`).
- الخطابات (تعريف/تحويل) تحمل `delivery_state` وهي حالة تشغيلية بعد `approved`.

---

### 3.8 محرك الرواتب الآمن والقابل للتدقيق (مطلب 3 + 12)

**`dm.salary.rule` — Declarative بالكامل (لا Python ولا `safe_eval`):**

| الحقل | القيم |
|---|---|
| `code` / `name` | **فريد داخل الشركة** |
| `category` | `allowance / deduction / employer_contribution / employee_contribution / base` |
| `calctype` | `fixed` • `percentage_of_basic` • `percentage_of_component` • `quantity_rate` • `attendance_days` • `overtime_hours` • `unpaid_leave_days` • `social_insurance` • `health_insurance` • `loan_installment` • `manual_input` • `basic` |
| `amount` (fixed) / `percent` / `rate`, `quantity` / `component_rule_id` (M2O dm.salary.rule) / `input_code` | حسب calctype |
| `appear_on_payslip` / `include_in_net` / `employer_only` | أعلام عرض |
| `sequence`, `company_id`, `active` | ترتيب وحصر |

**أنواع المدخلات:** attendance sheet (days/hours) + `overtime_hours` المعتمدة + `unpaid_leave_days` غير المدفوعة + `loan_installment` من سلف معتمدة + `social_insurance` من مخطط GOSI الفعال + `health_insurance` من البوليصة + `manual_input` (إثبات مستندي).

**تحقق (Validation) — تُنفَّذ عند create/write:**
- منع **الاعتماد على النفس** (`component_rule_id != self`).
- منع **الاعتماد الدائري** (فحص كل مسارات الـ graph عند أي تعديل).
- منع **تكرار `code` داخل الشركة** (`_sql_constraints`).
- **صحة الترتيب:** `component_rule_id.sequence < self.sequence` (القاعدة المرجعية تُحسب أولًا).
- **منع القسمة على صفر:** نسبة من مكوّن لا يمكن أن تكون قيمته صفرية عند التنفيذ؛ و`percent` ضمن `(0,100]`.
- **منع حساب مكوّن مرتين:** أنواع احتكارية `(social_insurance, health_insurance, loan_installment, attendance_days, unpaid_leave_days)` لا يجوز تكرارها ضمن نفس `structure_type` — قيد عند التعديل.

**تفاصيل قسيمة الرواتب `dm.payroll.payslip` وقابلية التدقيق:**

| المكوّن | التفصيل |
|---|---|
| `structure_type_id` / `rule_set_version`، `rule_set_hash` | **نسخة/هاش لحزمة القواعد** المستخدمة عند الاحتساب |
| `snapshot` (JSON/سجل) | **لقطة مجمّدة**: أجر العقد، البدلات (أنواع/قيم/نسب)، نسبة GOSI وتأمين صحي الفعالة، الحضور المستخدم — تُحفظ وقت الاحتساب ولا تُحدَّث لاحقًا |
| `calc_base` | الحقول المصدرية (period) لحساب الأيام/الكميات |
| `line_ids` | كل سطر يحمل: `source_type` (rule/allowance/attendance/overtime/leave/loan/insurance/manual), `source_id`, `rule_version`, `quantity`, `rate`, `amount`, `total`, `category`, `sequence` |
| `calculation_log` | سجل تدقيق: مُدخلات/مخرجات/إصدار قواعد + وقت/مستخدم — **بدون بيانات حساسة زائدة** (لا IBAN ولا هوية في السجل) |
| `state` | draft → confirmed → done (posted) → cancelled (فقط قبل الترحيل) |
| Immutability | أي تغيير لاحق في العقد/النسب/البدلات **لا يمس القسائم المؤكدة/done** (لأن المبالغ مخزنة + snapshot) |
| `action_recompute` | **زر في draft فقط**؛ عند confirm تُقفل القيود |
| تقريب | `currency.round()` موحّد يُطبَّق بحسب عملة الشركة على كل مبلغ |
| Idempotency | `_sql_constraints UNIQUE(employee_id, contract_id, period_start, period_end)` + منع إنشاء مكرر في batch |
| `dm.payroll.batch` | `date_start/end`, `slip_ids`, `state`؛ **lock** عند posted (كتابة محظورة)، ترحيل كل القسائم مرة واحدة، إلغاء قبل الترحيل فقط |

**ترتيب الاحتساب:** BASIC → بدلات العقد (dm.hr.contract.allowance) + استثنائية (dm.hr.employee.allowance) → مكونات attendance/overtime/unpaid → خصومات/تابعات → GOSI/تأمين صحي → سلف/loan → صافي.

---

### 3.9 التكامل المحاسبي المنفصل (مطلب 7) — `dm_hr_payroll_account`

> **المبدأ:** `dm_hr_payroll` **لا يعتمد** على `account`؛ كل منطق المحاسبة في موديول تكامل مستقل.

| العنصر | التفصيل |
|---|---|
| الاعتماديات | `['dm_hr_payroll', 'account']` فقط |
| الإعدادات | `journal_id` للرواتب، ربط حسابات لكل نوع (أجور/خصومات/مساهمات صاحب عمل/بدلات…) حسب خريطة الحسابات |
| العلاقة بالقيود | **قيد واحد لكل قسيمة** → `move_id` (M2O إلى `account.move`) يُضاف على payslip **في هذا الموديول فقط** |
| الإنشاء | `action_post()`: ينشئ/يفرض قيدًا متوازنًا (debit=credit) ويغلقه ضد إعادة الترحيل (`move_id مكرر` ممنوع) |
| الإلغاء/العكس | `action_cancel()`/`_reverse_move()` قبل الترحيل أو قيد عكسي بعد الترحيل |
| الصلاحية المحاسبية | منفصلة — مطلوب مستخدم بصلاحية محاسبية (group accounting) + `dm.group_payroll_account` للترحيل (5.1) |
| الاختبارات | توازن القيد، منع الترحيل المزدوج، سلامة العكس، عزل العملة/الشركة |

**القرار (ب) — المعتمد:** قيد موحّد واحد لكل **Payroll Batch** (`move_id` على الدفعة):
- كل قسيمة تحتفظ بـ `payslip_run_id` (الدفعة) + `move_id` إن وُجد (مرجع فقط لعلاقة واضحة).
- كل سطر قيد يحمل مصدره: `salary_rule_id` + `source_type/source_id` من القسيمة.
- تجميع الحسابات المتشابهة داخل القيد (حسب الحساب/الشريك/التحليل)؛ التفاصيل تبقى في القسائم.
- لا اسم موظف في القيد المجمّع افتراضيًا (إعداد اختياري يظهره).
- لا ترحيل مزدوج (قيد فريد على `batch.move_id`)؛ لا تعديل للقسائم بعد ترحيل الدفعة؛ إلغاء الدفعة المنشورة بـ **قيد عكسي** (reversal) لا حذف.
- التصميم قابل للتوسعة نحو "قيد لكل قسيمة" لاحقًا (لا يُنفَّذ في المرحلة الحالية).

---

## 4. العمل الموحّد (Workflow) (مطلب 11)

### 4.1 الحالات العامة (لكل طلب عبر `dm.approval.mixin` / `dm.approval.request.state`)
```text
draft ──Submit──▶ submitted ──▶ under_approval (خطوات الدفق n)
   ▲                                  │
   └── Back_to_draft ◀── (revision) ──┤
                                      ▼
                              approved / rejected / cancelled
```
**التسمية المعتمدة:** الحالات هي فقط `draft, submitted, under_approval, approved, rejected, cancelled` — لا `in_approval` ولا `confirmed` في هذا السياق.

### 4.2 الحالات التشغيلية (بعد `approved` فقط، خاصة بنوع الطلب)
| الطلب | phases بعد approved |
|---|---|
| `dm.hr.advance.request` | `paid → closed` |
| `dm.hr.salary.certificate.request` | `issued → delivered` |
| `dm.hr.salary.assignment.request` | `issued → delivered` |
| `dm.hr.travel.request` | `in_progress → returned → report_filed` |
| `dm.hr.permission.request` | `used` |
| `dm.payroll.payslip` | `posted` (بالاسم `done`) |
| `dm.hr.overtime.result` | `posted` |

### 4.3 خريطة الحالات في النماذج الموروثة
- **`hr.leave`:** تبقى الحالات الأصلية `draft/confirm/refuse/validate1/validate` دون مساس (Adapter §3.6).
- **`hr.attendance.overtime` (inherit):** لا يضيف حالة؛ يظل سجل إثبات.
- **الحضور sheet:** `draft → confirmed → posted` (تشغيلية خاصة).

---

## 5. مصفوفة الأمان المعدّلة (مطلب 5 + 6 + 13)

### 5.1 مجموعات المستخدمين (تحل محل v1.0 — فصل كامل ومراحل إنشاء)
> **مراحل الإنشاء:** مجموعات `approval/الموافقات` و`portal` و`payroll_account` تُنشأ في موديولاتها (dm_hr_approval, dm_hr_requests, dm_hr_payroll_account) بعد توفّر التبعيات (hr_holidays/portal/account). **dm_hr_core ينشئ الآن 6 مجموعات فقط** (صفوفها مميزة بعلامة ★) دون أي ref لموديولات غير مثبتة؛ ويُمدَّد الـ `implied_ids` لاحقًا من الموديولات الأعلى عبر XML update.

| المجموعة | `implied_ids` (وراثة من) | الدور |
|---|---|---|
| `dm.group_employee_portal` | `base.group_portal` | موظف Portal — إنشاء/تتبع طلباته *(مؤجل: dm_hr_requests)* |
| ★ `dm.group_employee` | `base.group_user` | موظف داخلي (بدون صلاحيات HR) |
| `dm.group_approver` | `dm.group_employee` | اعتماد وفق الدفقات *(مؤجل: dm_hr_approval)* |
| ★ `dm.group_hr_officer` | `dm.group_employee` + `hr.group_hr_user` + `resource.group_resource_manager` | مسؤول HR *(يُمَدَّد بـ hr_holidays عند تثبيته)* |
| ★ `dm.group_hr_manager` | `dm.group_hr_officer` + `hr.group_hr_manager` | مدير HR *(يُمَدَّد بـ holidays_manager لاحقًا)* |
| ★ `dm.group_payroll_officer` | `dm.group_employee` | تنفيذ الرواتب (قراءة/احتساب) بلا ترحيل محاسبي |
| ★ `dm.group_payroll_manager` | `dm.group_payroll_officer` + `dm.group_hr_manager` | مراجعة واعتماد رواتب نهائي |
| `dm.group_approval_admin` | `dm.group_approver` | إدارة `dm.approval.flow` والتصنيفات *(مؤجل: dm_hr_approval)* |
| ★ `dm.group_hr_admin` | `dm.group_hr_manager` + `dm.group_payroll_manager` | إعدادات النظام — **لا يرث `account.group_account_manager`** |
| `dm.group_payroll_account` | `dm.group_payroll_officer` | مترحّل المحاسبة *(مؤجل: dm_hr_payroll_account)* |

### 5.2 Access Rights و Record Rules (إعادة صياغة)
- **`dm.approval.item`: الموظف والموافق لا يملكان Create/Unlink إطلاقًا** — الإنشاء حصري من المحرك عبر `_create_approval_items()` محمية؛ القراءة محدودة بالمصادقة (§5.4).
- قاعدة سجلات عامة: `company_id in company_ids + [False]` لكل النماذج الجديدة (نمط hr).
- بوابة الموظف: `employee_id.user_id == user.id` على نماذج الطلبات وكشوفه.
- استثناء: `dm.salary.rule` — قراءة لـ payroll/HR، تعديل فقط لـ `dm.group_hr_admin` + `dm.group_payroll_manager`.

### 5.3 حماية البيانات الحساسة (مطلب 13)
| الفئة | الحماية |
|---|---|
| الراتب (wage/صافي/basics) | حقول `groups="dm.group_payroll_manager, dm.group_hr_manager, dm.group_payroll_officer"` | 
| IBAN / res.partner.bank | `groups="dm.group_payroll_manager, dm.group_hr_manager"` + منع غير الموظفين (مثيل قاعدة hr) |
| الهوية/الإقامة (iqama/identifications) | `groups="hr.group_hr_user"` (عبر hr الأصلي) — الرواتب لا تطبعها |
| التأمين الطبي | `groups="hr.group_hr_user, dm.group_payroll_manager"` |
| قسائم الرواتب | عرض PDF للامتلاك فقط (owner) + HR/Payroll؛ **لا** تظهر في portal إلا لصاحبها |

**قاعدة السودو:** لا `sudo()` عام في حسابات الرواتب. كل عملية تحتاج خدمة داخلية تُنفَّذ عبر **method محدد** يتحقق: `user.has_group(...)` + `record.company_id in user.company_ids` + يكتب سجل `ir.logging` باسم العملية والمستخدم. حسابات القسيمة تعمل في سياق مستخدم يملك `dm.group_payroll_officer` فما فوق.

### 5.4 استراتيجية الاعتماد (مطلب 5 — الأمان داخل Python لا في XML)
`dm.approval.request.action_approve() / action_reject()` تتحقق في كل مرة من:
1. **المصادق هو الموافق الحالي** (`approver_user_id == env.user`).
2. **الخطوة pending** (`item.state == 'pending'`).
3. **الطلب داخل شركات المستخدم** (`company_id in user.company_ids`).
4. **المصادق ليس مقدم الطلب** إلا إذا `flow.allow_self_approval = True`.
5. **الطلب لم يتغيّر بعد الإرسال**: مقارنة `submission_hash` المحسوب لحظة الاعتماد مع المخزّن (optimistic lock §3.4).
6. `state == under_approval` ولا يوجد إلغاء معلق.
- الأزرار في XML تُخفي/تُظهر للراحة فقط؛ **لا تعتمد** على الإخفاء أمانًا.

---

## 6. استراتيجيات التكامل

### 6.1 تكامل الإجازات الأصلية (ملخص Adapter)
- الحالة الأجنبية `hr.leave` = مصدر الحقيقة القانوني للأرصدة؛ المحرك = طبقة «من يقرر».
- عند `use_dm_approval=True`: يوصل المحرك بالموافقة النهائية عبر `_action_validate()` الحصرية؛ عند False لا تدخل dm أصلًا.
- لم تُلمس `validate/validate1` ولا منطق `hr_holidays`؛ الـAdapter **يستدعي** ولا **يستبدل**.

### 6.2 مصادر حساب الرواتب (من أين تأتي المدخلات)
| المدخل | الوسيط | الشرط |
|---|---|---|
| أيام/ساعات عمل | `dm.hr.attendance.sheet` (confirmed) | sheet مؤكد لفترة القسيمة |
| إضافي | `dm.hr.overtime.result` (من طلبات approved + إثبات) | result posted |
| إجازات غير مدفوعة | `hr.leave`/`dm.hr.leave.accrual.policy` | إجازة approved وغير مدفوعة |
| بدلات | `dm.hr.contract.allowance` + `dm.hr.employee.allowance` | نشطة ضمن الفترة |
| GOSI | `dm.hr.social.insurance.rate` الفعال تاريخيًا | فترة فعالة + فئة الموظف |
| تأمين صحي | `dm.hr.insurance.policy` | active في الفترة |
| سلفة/أقساط | `dm.hr.advance.request` (approved) | installments الفترة |

---

## 7. التقارير (محدّثة للمراجعة)

| التقرير | المصدر | الإخراج |
|---|---|---|
| كشف راتب (payslip) | `dm_hr_payroll` | PDF ثنائي اللغة |
| **خطاب تثبيت/تحويل راتب** | `dm_hr_requests` + `dm_hr_reports` | PDF (عربي/إنجليزي) مع QR/token + حالة delivery |
| **تعريف راتب** | `dm_hr_requests` + `dm_hr_reports` | PDF رسمي |
| مسير رواتب شهري | `dm_hr_payroll` + `dm_hr_payroll_account` | XLSX/pivot |
| تقرير الحضور والأرصدة | `dm_hr_attendance`/`dm_hr_leave` | PDF/pivot |
| تكلفة رواتب/لوحة مؤشرات | `dm_hr_reports` | OWL Dashboard |

---

## 8. من الصفر مقابل الوراثة (محدّث)

| البند | القرار |
|---|---|
| `hr.employee` / `hr.contract` / `hr.leave.type` | وراثة (حقول جديدة بأساليب آمنة) |
| `hr.attendance.overtime` | **وراثة** — بعد إثبات وجوده (مطلب 9) |
| `hr.leave`, `hr.leave.allocation` | وراثة + Adapter يحافظ على الأصل |
| طلبات HR الثمانية والخطابات | **من الصفر** |
| `dm.approval.request/flow/item` | **من الصفر** (مركزي) |
| محرك الرواتب | **من الصفر** (declarative) |
| `dm_hr_payroll_account` | **من الصفر** (فصل محاسبي) |
| `doc_signature_module` / `testapp` | لا تعديل (بلا تعارض؛ قاعدة 11) |

---

## 9. المخاطر والتوصيات

1. **لا Payroll مجتمعي** → محرك خاص بنا؛ لا اعتماد على `hr.contract.structure_type_id` (مرجع غير موجود) ولا على قالب `l10n_payroll`.
2. **ازدواجية العقود** (`hr_work_entry`) → الاعتماد على `hr_contract` حاليًا والتصميم غير مرتبط بالمسار.
3. **أخطاء Circular/ترتيب** في القواعد → التحقق الـ declarative عند كل write (§3.8).
4. **إساءة `sudo`** → خدمة داخلية مقيدة + `ir.logging` (§5.3).
5. **ترحيل مزدوج للقيود** → قيود فريدة + lock batch (§3.9).
6. **تعريب** → تفعيل `ar_SA` في المرحلة 0 + ملفات i18n.
7. **قاعدة 9**: لا نسب/بدلات في الكود إطلاقًا.
8. **بيئة التشغيل**: `--dev=assets` => إعادة تحميل assets عند الحاجة؛ قاعدة `kh1_odoo17` كبيرة → اختبار على `dm_hr_test` بعد موافقتك.

---

## 10. خطة الاختبارات الآلية (قاعدة 14 — محدّثة)

**البنية:** `tests/` في كل موديول؛ تُشغَّل على `dm_hr_test` (بعد موافقتك).

| الموديول | الحالات الحرجة |
|---|---|
| `dm_hr_core` | تقاطع عقود، فريدية `code` للبدلات، منع تداخل فترات `dm.hr.social.insurance.rate`، تطبيق min/max insurable، إجبار `company_id`/`currency_id`، صلاحيات الحقول الحساسة |
| `dm_hr_approval` | ترتيب خطوات الدفق، شرط الحد (amount>X)، منع الموظف اعتماد نفسه، **optimistic lock** (تعديل بعد submit يمنع الاعتماد)، cleanup عند حذف الطلب، فحص قائمة النماذج المسموحة، لا Create/Unlink لغير المصنّف |
| `dm_hr_leave` | Adapter: `use_dm_approval=True/False`، حفظ الأرصدة/allocations/calendar بحالات أصلية، مسار validate/validate1 فلا كسر، حساب الرصيد وفق الـ policy (لا قيمة ثابتة) |
| `dm_hr_attendance` | حساب الساعات/الورديات، وراثة `hr.attendance.overtime` (إثبات)، request→evidence→result، عدم احتساب إضافي غير معتمد |
| `dm_hr_requests` | سلفة بأقساط (مجموع = المبلغ)، خطاب تحويل (IBAN/QR/delivery)، تعريف راتب PDF بعد approved، تثبيت تجربة (decision), صلاحية portal للذات فقط |
| `dm_hr_payroll` — **مالي** | payslip = basic+بدلات (fixed/%of basic/%of component)؛ GOSI/Sanad وصاحب العمل من المخطط؛ تأمين صحي؛ خصم إجازة غير مدفوعة؛ overtime بمعدلات العطل؛ قيود declarative (دائرة/تكرار/قسمة صفر/ترتيب)؛ snapshot لا تغيّره تعديلات لاحقة؛ Recompute في draft فقط؛ تقريب `currency.round()`؛ عزل multi-company/currency |
| `dm_hr_payroll_account` | قيد لكل قسيمة: **مجموع مدين = مجموع دائن**، منع الترحيل المزدوج، الإلغاء/العكس، عزل العملة/الشركة، idempotency |
| `dm_hr_reports` | توليد PDFs (قسيمة/تعريف/خطاب تحويل) بلا استثناء، توثيق URIs، تحميل portal مقيّد |

---

## 11. الـ Migrations المتوقعة

| الموديول | Migration 17.0.1.0.0 | ملاحظات الترقية |
|---|---|---|
| `dm_hr_core` | إنشاء الحقول/الجداول + بيانات `noupdate` (أنواع بدلات أولية، مخطط GOSI فارغ) | ترقية لاحقة لا تحذف بيانات؛ تُضاف بالأعمدة الجديدة فقط |
| `dm_hr_approval` | إنشاء `dm.approval.request/item/flow` + قيود UNIQUE | عند ترقية تُعاد قيود الدوائر (خلفية cron تحقق) |
| `dm_hr_attendance` | إنشاء الورديات/النتائج + حقول الوراثة على `hr.attendance.overtime` | لا يمس سجلات الحضور الموجودة |
| `dm_hr_leave` | حقل `code`/`use_dm_approval`/`accrual_policy_id` على `hr.leave.type` + أنواع `noupdate` | يبقى عمل hr_holidays الحالي دون تغيير |
| `dm_hr_requests` | إنشاء 7 نماذج طلبات + دفقات افتراضية | لا صدام مع بيانات سابقة |
| `dm_hr_payroll` | إنشاء الجداول + `UNIQUE(employee, contract, period)` | منع تكرار قسائم؛ يُبقي إصدارات القواعد |
| `dm_hr_payroll_account` | إعدادات الجدول + `move_id` على payslip | عند إزالة الموديول تُنبَّه القيود الموجودة |
| `dm_hr_reports` | تقارير/قوائم/أصول | إعادة تحميل assets عند الترقية (dev=assets) |

- **ترقية الأدوار:** لا تعديل على `hr`/`hr_holidays`/`hr_attendance` الأصلية (قاعدة 1)؛ أي تخصيص عبر الوراثة في موديولات dm فقط.
- **التعريب:** تُسحب ملفات `i18n/*.po` بعد كل موديول وتُدرج في manifest.

---

## 12. Definition of Done لكل موديول

**DoD العام (يطبق على كل موديول قبل اعتباره منجزًا):**
1. `py_compile` ناجح لكل `*.py` + فحص `flake8/ruff` بلا أخطاء حرجة.
2. تثبيت/ترقية نظيفة على `dm_hr_test` (أو قاعدة بديلة بعد موافقتك) **بدون أخطاء** بالسجل.
3. ترقية آمنة على `kh1_odoo17` (نسخة احتياطية قبلها) وسجل بلا `ERROR/CRITICAL`.
4. اختبارات `tests/` كلها خضراء (`--test-enable`).
5. مجموعات/أذونات/قواعد لا تفتح صلاحيات زائدة؛ no `sudo()` عام.
6. ملفات `i18n/ar.po` + `en.po` لكل السلاسل؛ التعريب يعمل.
7. حقول `company_id` + `currency_id` (حيث يلزم) ومتعددة-الشركات مختبرة.
8. التوثيق: سطر إصدار/إصلاح لكل جدول بيانات في الـ migration.

| الموديول | DoD الخاص |
|---|---|
| `dm_hr_core` | بدلات (3 أنواع حساب) + توحيد `gosi_` + خطة GOSI التاريخية بمنع تداخل الفترات + إعدادات res.config.settings |
| `dm_hr_approval` | نموذج مركزي + optimistic lock + قائمة بيضاء للنماذج + لا CRUD مباشر على items + اختبارات أمن |
| `dm_hr_attendance` | ورديات + كشوف شهرية + request→evidence→result + حساب إضافي بالاعتماد فقط |
| `dm_hr_leave` | Adapter يحافظ على الحالات الأصلية + أنواع `noupdate` + accrual policy قابلة للتهيئة |
| `dm_hr_requests` | 7 طلبات + خطابات (تعريف/تحويل) بفصل تام + تثبيت تجربة مستقل + بوابات portal |
| `dm_hr_payroll` | محرك Declarative + كل قيود الدوائر + snapshot + calculation_log + Recompute(draft) + batch lock |
| `dm_hr_payroll_account` | قيود متوازنة لكل قسيمة + منع مزدوج + إلغاء/عكس + صلاحية محاسبية منفصلة |
| `dm_hr_reports` | PDFs ثنائية اللغة + لوحة مؤشرات + تحميل مقيّد في portal |

---

## 13. قاعدة الاختبار (مطلب 14 — معتَمد بقرار (أ) بتاريخ 2026-08-09)

- **المعتمد:** إنشاء قاعدة منفصلة باسم **`dm_hr_test`**.
- **القيود الملزمة:** لا حذف/تعديل لـ `kh1_odoo17`؛ لا استيراد بيانات إنتاج في هذه المرحلة؛ فحص أن الاسم غير مستخدم قبل الإنشاء؛ إنشاء بالترميز القياسي PostgreSQL/Odoo (UTF8, template0, Collate C)؛ توثيق أمر الإنشاء ونتيجته في تقرير المرحلة.
- `dm_hr_test` تُستخدم فقط للتثبيت النظيف والاختبارات الآلية.

---

## 14. مخرجات مراجعة الإصدار 1.1

### 14.1 ما تغيّر عن 1.0 (خلاصة تنفيذية)
- **البدلات:** ثلاثة نماذج مرنة بدل الحقول الثابتة (3.1).
- **التأمينات:** مخطط تاريخي `scheme+rate` موحّد `gosi_` بدل حقول مباشرة (3.2).
- **الموافقات:** نموذج مركزي `dm.approval.request` بدل One2many متعدد النماذج (3.3-3.4) مع optimistic lock.
- **الأمان:** 10 مجموعات مفصولة، لا Create/Unlink على items، تحقق داخل Python، لا `sudo` عام (5).
- **الرواتب:** محرك Declarative بلا safe_eval + قابليّة تدقيق كاملة (3.8).
- **المحاسبة:** موديول تكامل منفصل `dm_hr_payroll_account` (3.9).
- **الإجازات:** أنواع `noupdate` + Adapter غير كاسر للحالات الأصلية (3.6).
- **الطلبات:** فصل تام (تعريف / تحويل بنكي / تثبيت تجربة) (3.7).
- **حالات موحدة:** draft/submitted/under_approval/approved/rejected/cancelled + phases تشغيلية (4).
- **إثبات `hr.attendance.overtime` موجود** في Community (1.1).

### 14.2 ملفات هذه المراجعة
- `/opt/odoo17/custom_addons/docs/dm_hr_system_technical_spec.md` ← **الإصدار 1.1** (مراجعة 1 + قرارات الاعتماد مدمجة).
- تم إنشاء موديول `dm_hr_core` كاملاً على الفرع `feature/dm-hr-core` (نماذج، واجهات، أمان، إعدادات، بيانات افتراضية، ترجمة، اختبارات). جاري التهيئة والاختبار على `dm_hr_test` ضمن المرحلة 1.

### 14.3 القرارات المفتوحة — **حُسمّت بجلسة الاعتماد 2026-08-09 (انظر القسم 0.1)**
| # | القرار | الحسم |
|---|---|---|
| أ | قاعدة الاختبار | ✅ `dm_hr_test` — معتمدة بقيودها |
| ب | القيد المحاسبي | ✅ **قيد موحّد لكل Payroll Batch** (مع دعم مستقبلي "لكل قسيمة") |
| ج | إجازات DM | ✅ `use_dm_approval=False` افتراضيًا، تفعيل يدوي لكل نوع |
| د | البيانات الافتراضية | ✅ 5 بدلات + 4 إجازات `noupdate` بلا أي نسب/قيم |
| هـ | بدء التنفيذ | ✅ `dm_hr_core` — فرع `feature/dm-hr-core`

---

**إصدار التوثيق:** 1.1 — بانتظار اعتمادك للبدء بمرحلة التنفيذ.


---

## 15. ملحق: قرارات التنفيذ المعتمدة — مرحلة 1 (٢٠٢٦-٠٨-٠٩)

دمجت قرارات اعتماد 2026-08-09 مع التصحيحات المعمارية التالية قبل بدء التهيئة على `dm_hr_test`.

| # | العنصر | القرار المعتمد (ملزم) |
|---|---|---|
| 1 | بادئة XML ID للمجموعات | جميع المجموعات تُعرّف في `security/security.xml` بمعرّفات bare (group_*)، لذا المعرّف الخارجي الفعلي = `dm_hr_core.group_*` (اسم وحدة النمط `dm_hr_core` — لا توجد وحدة `dm`). تمّ توحيد `security/ir.model.access.csv` و `groups=` في `views/menus.xml` و `views/res_config_settings_views.xml` على البادئة `dm_hr_core.group_*`. الإشارة `ref('group_*')` داخل `security.xml`/`rules.xml` تبقى محلية وتملحظ صحة. |
| 2 | بيان XML وراثة نموذج العقد | `views/hr_contract_views.xml`: `inherit_id` صحيح إلى `hr_contract.hr_contract_view_form` (معرّف Odoo 17)، مع `xpath //page[@name='information']` و `//form/sheet/notebook` المعتمدين على البنية الأساسية. |
| 3 | إعدادات الشركة المتعددة الشركات | المخطط الافتراضي للتأمين الاجتماعي يُخزن على `res.company.default_social_insurance_scheme_id` (Many2one، ondelete=set null)، ويدخل في `res.config.settings` عبر `related` قابل للتعديل (`readonly=False`). **بدون** `config_parameter`/`ir.config_parameter`. القيم مقيدة لشركة واحدة ولا تتسرب بين الشركات (مثبت اختبارياً). |
| 4 | مخططات التأمين التاريخية | تبقى في نماذج منعزلة (`dm.hr.social.insurance.scheme` + `dm.hr.social.insurance.rate`). تحمل `res.company` فقط `Many2one` للمخطط الافتراضي؛ لا تحمل نسبًا أو معدلات. |
| 5 | نموذج التابع المستقل | أُضيف نموذج `form` لـ `dm.hr.employee.dependent` (`dm_hr_employee_dependent_form`)؛ إصلاح `view_mode` بـ `tree,form` الذي لم يجد `form` من قبل. |
| 6 | عدم استخدام sudo العام | لا `sudo()` عام في منطق الأعمال؛ الوصول عبر مجموعات/قواعد سجلات. اختبار آلي يثبت اختلاف إعدادات الشركة وعدم تسربها بين شركتين. |
| 7 | قاعدة الاختبار | الترقية/الاختبار على `dm_hr_test` فقط؛ `kh1_odoo17` غير ملموسة تمامًا في هذه المرحلة. |
| 8 | ترجمة | استخراج `i18n/dm_hr_core.pot` (قالب) و `i18n/ar.po` (عربي) عبر `--i18n-export=<مسار ملف>` مرة واحدة لكل ملف مع `--modules=dm_hr_core` و `--language=ar_001`. لا تُنشئ `en.po`. كود العربية الفعلي في Odoo 17 هو `ar_001` (من `base/data/res.lang.csv`: `base.lang_ar`). |
| 9 | مراجعة السجلات | لا ERROR/CRITICAL مرتبط بـ `dm_hr_core` في سجل Odoo بعد الترقية. |
| 10 | بادئة المجموعات | تُراجَع تسميات المجموعات لاستخدام البادئة `dm_hr_core.group_dm_hr_*` و `dm_hr_core.group_dm_payroll_*` في `security.xml` + `rules.xml` + `ir.model.access.csv` + `views/menus.xml` + `views/res_config_settings_views.xml` قبل أي تثبيت. |
| 11 | تنظيف Python | حذف `__pycache__` و `*.pyc` من `dm_hr_core` فقط قبل كل تثبيت/اختبار؛ التأكد من وجود `*.pyc` و `__pycache__/` في `.gitignore`. |
| 12 | تحقق الترجمة في Odoo 17 | لا يوجد جدول `ir_translation` في Odoo 17؛ التحقق يتم عبر أعمدة JSONB: `ir_model_fields.field_description->>'ar_001'` و `ir_ui_view.arch_db->>'ar_001'` و `ir_ui_menu.name->>'ar_001'` بالإضافة إلى قراءة الحقول عبر `env[model].with_context(lang='ar_001')`. |


### 15.1 توضيح تنفيذي Odoo 17 — مجموعة الموارد
- صُحّحت `security.xml` لحساب `group_hr_officer`: أزيل `resource.group_resource_manager` لأنه غير موجود في Odoo 17 Community (تم دمج إدارة الموارد في `hr.group_hr_user` منذ إصدار 16). باقي الـ `implied_ids`/`ref()` تستخدم `hr.*` و `base.*` القياسية الصالحة.

### 15.2 السجل التنفيذي للتصحيحات المعمارية (تم تطبيقها قبل التثبيت على `dm_hr_test`)
| # | التصحيح | التفاصيل |
|---|---|---|
| 1 | **إعادة تسمية المجموعات** | جميع المعرّفات الخارجية للمجموعات أصبحت `dm_hr_core.group_dm_hr_employee`، `dm_hr_core.group_dm_hr_officer`، `dm_hr_core.group_dm_hr_manager`، `dm_hr_core.group_dm_hr_admin`، `dm_hr_core.group_dm_payroll_officer`، `dm_hr_core.group_dm_payroll_manager`. تم تحديث `security.xml` + `rules.xml` + `ir.model.access.csv` + `views/menus.xml` + `views/res_config_settings_views.xml`. |
| 2 | **تنظيف Python** | حذف جميع مجلدات `__pycache__` وملفات `*.pyc` من `dm_hr_core` فقط، مع التأكد من وجود `*.pyc` و `__pycache__/` في `.gitignore`. |
| 3 | **كود اللغة العربية** | التأكد من أن الكود الفعلي في Odoo 17 هو `ar_001` (السجل `base.lang_ar` في `res.lang.csv`)، وليس `ar`. خطة الترجme تستخدم `ar_001`. |
| 4 | **آلية التحقق من الترجمة** | Odoo 17 لا يحتوي على جدول `ir_translation`؛ التحقق يتم عبر أعمدة JSONB: `ir_model_fields.field_description->>'ar_001'`، `ir_ui_view.arch_db->>'ar_001'`، `ir_ui_menu.name->>'ar_001'`، بالإضافة إلى قراءة الحقول عبر `env[model].with_context(lang='ar_001')`. |
| 5 | **ترحيل XML IDs** | عند تحديث أسماء المجموعات، تُرحَّل سجلات `ir_model_data` القديمة في `dm_hr_test` فقط إلى الأسماء الجديدة قبل ترقية الموديول، مع بقاء `kh1_odoo17` دون مساس. |

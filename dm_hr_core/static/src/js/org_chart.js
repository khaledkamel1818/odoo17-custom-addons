/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

class DmHrOrgChart extends Component {
    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.state = useState({
            loading: true,
            nodes: [],
            summary: {},
            filters: { companies: [], branches: [] },
            companyId: "",
            branchId: "",
            search: "",
        });
        this.openRecord = this.openRecord.bind(this);
        this.openEmployee = this.openEmployee.bind(this);
        this.searchNow = this.searchNow.bind(this);
        onWillStart(() => this.load());
    }

    async load() {
        this.state.loading = true;
        try {
            const data = await this.orm.call("dm.hr.branch", "dm_org_chart_data", [], {
                company_id: this.state.companyId || false,
                branch_id: this.state.branchId || false,
                search: this.state.search || false,
            });
            this.state.nodes = data.nodes || [];
            this.state.summary = data.summary || {};
            this.state.filters = data.filters || { companies: [], branches: [] };
        } catch (error) {
            this.state.nodes = [];
            this.notification.add(
                "تعذر تحميل الهيكل التنظيمي. تحقق من الصلاحيات أو أعد المحاولة بعد تحديث الصفحة.",
                { type: "danger" }
            );
            throw error;
        } finally {
            this.state.loading = false;
        }
    }

    get flatRows() {
        const rows = [];
        const walk = (node, depth = 0) => {
            rows.push({ ...node, kind: "node", key: node.id, depth });
            for (const employee of node.employees || []) {
                rows.push({ ...employee, kind: "employee", key: `employee-${employee.id}-${node.id}`, depth: depth + 1 });
            }
            for (const child of node.children || []) {
                walk(child, depth + 1);
            }
        };
        for (const node of this.state.nodes || []) {
            walk(node, 0);
        }
        return rows;
    }

    onCompanyChange(ev) {
        this.state.companyId = ev.target.value;
        this.state.branchId = "";
        this.load();
    }

    onBranchChange(ev) {
        this.state.branchId = ev.target.value;
        this.load();
    }

    onSearch(ev) {
        this.state.search = ev.target.value;
    }

    onSearchKeyup(ev) {
        if (ev.key === "Enter") {
            this.load();
        }
    }

    searchNow() {
        this.load();
    }

    _openRecord(model, resId) {
        if (!model || !resId) {
            this.notification.add(
                "لا يمكن فتح هذا العنصر لأن بيانات الرابط غير مكتملة. حدّث الصفحة أو راجع مسؤول النظام.",
                { type: "warning" }
            );
            return;
        }
        window.location.hash = `#id=${Number(resId)}&model=${encodeURIComponent(model)}&view_type=form`;
    }

    openRecord(ev) {
        const target = ev.currentTarget;
        this._openRecord(target.dataset.model, target.dataset.resId);
    }

    openEmployee(ev) {
        const target = ev.currentTarget;
        this._openRecord(target.dataset.model, target.dataset.resId);
    }

    get visibleBranches() {
        if (!this.state.companyId) {
            return this.state.filters.branches || [];
        }
        return (this.state.filters.branches || []).filter(
            (branch) => String(branch.company_id) === String(this.state.companyId)
        );
    }
}

DmHrOrgChart.template = "dm_hr_core.OrgChart";

registry.category("actions").add("dm_hr_core.org_chart_action", DmHrOrgChart);

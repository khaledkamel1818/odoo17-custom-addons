/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Layout } from "@web/search/layout";

export class DmFinanceDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.state = useState({
            loading: true,
            data: {},
        });
        onWillStart(async () => {
            await this.loadDashboard();
        });
    }

    get display() {
        return { controlPanel: {} };
    }

    async loadDashboard() {
        this.state.loading = true;
        try {
            this.state.data = await this.orm.call("dm.finance.dashboard", "get_dashboard_data", []);
        } catch (error) {
            this.notification.add(error.message || "تعذر تحميل لوحة الحسابات.", {
                title: "تنبيه",
                type: "danger",
            });
        } finally {
            this.state.loading = false;
        }
    }

    normalizeAction(action) {
        if (action.type === "ir.actions.act_window" && !Array.isArray(action.views)) {
            const viewModes = (action.view_mode || "tree,form")
                .split(",")
                .map((mode) => mode.trim())
                .filter(Boolean);
            action.views = viewModes.map((mode) => [false, mode]);
        }
        if (!action.context) {
            action.context = {};
        }
        return action;
    }

    async openAction(actionKey) {
        try {
            const action = await this.orm.call("dm.finance.dashboard", "open_action", [actionKey]);
            if (action) {
                await this.action.doAction(this.normalizeAction(action));
            }
        } catch (error) {
            this.notification.add(error.message || "تعذر فتح الإجراء المطلوب.", {
                title: "تنبيه",
                type: "danger",
            });
        }
    }
}

DmFinanceDashboard.template = "dm_finance_dashboard.Dashboard";
DmFinanceDashboard.components = { Layout };

registry.category("actions").add("dm_finance_dashboard.dashboard", DmFinanceDashboard);

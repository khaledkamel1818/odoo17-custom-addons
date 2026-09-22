/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Layout } from "@web/search/layout";

export class DmHrLeaveHub extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.state = useState({ loading: true, data: {} });
        onWillStart(() => this.load());
    }
    get display() { return { controlPanel: {} }; }
    async load() {
        this.state.loading = true;
        try {
            this.state.data = await this.orm.call("dm.hr.leave.hub", "get_data", []);
        } finally {
            this.state.loading = false;
        }
    }
    async open(key) {
        try {
            const action = await this.orm.call("dm.hr.leave.hub", "open_action", [key]);
            await this.action.doAction(action);
        } catch (error) {
            this.notification.add(error.message || "تعذر فتح الإجراء.", { type: "danger", title: "تنبيه" });
        }
    }
}
DmHrLeaveHub.template = "dm_hr_leave_hub.Dashboard";
DmHrLeaveHub.components = { Layout };
registry.category("actions").add("dm_hr_leave_hub.dashboard", DmHrLeaveHub);

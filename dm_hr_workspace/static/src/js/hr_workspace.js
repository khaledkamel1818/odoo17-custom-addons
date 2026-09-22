/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Layout } from "@web/search/layout";

export class DmHrWorkspaceDashboard extends Component {
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
        return {
            controlPanel: {},
        };
    }

    async loadDashboard() {
        this.state.loading = true;
        this.state.data = await this.orm.call("dm.hr.workspace.dashboard", "get_dashboard_data", []);
        this.state.loading = false;
    }

    async openAction(actionKey) {
        try {
            const action = await this.orm.call("dm.hr.workspace.dashboard", "open_action", [actionKey]);
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

    async toggleAttendance() {
        try {
            this.state.loading = true;
            const geoInformation = await this.getGeolocation();
            this.state.data = await this.orm.call(
                "dm.hr.workspace.dashboard", "toggle_attendance", [geoInformation]
            );
            this.notification.add(this.state.data.attendance.state_label, {
                title: "تم تحديث الحضور والانصراف",
                type: "success",
            });
        } catch (error) {
            this.notification.add(error.message || "تعذر تحديث الحضور والانصراف.", {
                title: "تنبيه",
                type: "danger",
            });
        } finally {
            this.state.loading = false;
        }
    }

    async getGeolocation() {
        if (!this.state.data.config.gps_required) {
            return {};
        }
        if (!navigator.geolocation) {
            throw new Error("هذا الجهاز لا يدعم تحديد الموقع GPS.");
        }
        const position = await new Promise((resolve, reject) => {
            navigator.geolocation.getCurrentPosition(resolve, reject, {
                enableHighAccuracy: true,
                timeout: 15000,
                maximumAge: 0,
            });
        });
        return {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            gps_accuracy: position.coords.accuracy,
        };
    }
}

DmHrWorkspaceDashboard.template = "dm_hr_workspace.Dashboard";
DmHrWorkspaceDashboard.components = { Layout };

registry.category("actions").add("dm_hr_workspace.dashboard", DmHrWorkspaceDashboard);

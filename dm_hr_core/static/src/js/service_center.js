/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

class DmHrServiceCenter extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({ loading: true, data: { counts: {}, cards: [] } });
        onWillStart(() => this.load());
    }

    async load() {
        this.state.loading = true;
        this.state.data = await this.orm.call("dm.hr.service.center", "get_dashboard_data", []);
        this.state.loading = false;
    }

    async open(key) {
        const action = await this.orm.call("dm.hr.service.center", "open_action", [key]);
        if (action) {
            await this.action.doAction(action);
        }
    }
}

DmHrServiceCenter.template = "dm_hr_core.ServiceCenter";

registry.category("actions").add("dm_hr_core.service_center_action", DmHrServiceCenter);

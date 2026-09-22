/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

class DmFinanceEnhancementDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            loading: true,
            data: {
                cards: {},
                bank_cards: [],
                recent_moves: [],
                period: {},
                company: {},
                currency: "",
            },
        });
        onWillStart(async () => {
            await this.loadDashboard();
        });
    }

    async loadDashboard() {
        this.state.loading = true;
        this.state.data = await this.orm.call(
            "dm.finance.enhancement.dashboard",
            "get_dashboard_data",
            [{}]
        );
        this.state.loading = false;
    }

    openReport(reportType) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Finance Report",
            res_model: "dm.finance.report.wizard",
            views: [[false, "form"]],
            target: "new",
            context: { default_report_type: reportType },
        });
    }

    openBankReconciliation() {
        this.action.doAction("dm_finance_enhancement.action_dm_finance_bank_reconciliation");
    }

    openChart() {
        this.action.doAction("dm_finance_enhancement.action_dm_finance_enhanced_chart_accounts");
    }
}

DmFinanceEnhancementDashboard.template = "dm_finance_enhancement.FinanceDashboard";

registry.category("actions").add("dm_finance_enhancement.dashboard", DmFinanceEnhancementDashboard);


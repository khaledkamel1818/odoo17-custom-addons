/** @odoo-module **/

import { registry } from "@web/core/registry";

const waitForWebClient = {
    trigger: ".o_web_client",
    run: () => {},
};

registry.category("web_tour.tours").add("dm_hr_ui_workspace_smoke_tour", {
    test: true,
    url: "/web",
    steps: () => [
        waitForWebClient,
        {
            trigger: ".o_app[data-menu-xmlid='dm_hr_core.menu_dm_hr_employee_portal'], .o_app[data-menu-xmlid='dm_hr_core.menu_dm_hr_operations'], .o_menu_sections",
            run: () => {},
        },
    ],
});

registry.category("web_tour.tours").add("dm_hr_ui_service_request_tour", {
    test: true,
    url: "/web#action=dm_hr_core.dm_hr_service_request_action_my",
    steps: () => [
        waitForWebClient,
        {
            trigger: ".o_control_panel, .o_form_view, .o_list_view, .o_kanban_view",
            run: () => {},
        },
    ],
});

registry.category("web_tour.tours").add("dm_hr_ui_attendance_tour", {
    test: true,
    url: "/web#action=dm_hr_core.dm_hr_attendance_records_action",
    steps: () => [
        waitForWebClient,
        {
            trigger: ".o_control_panel, .o_list_view, .o_kanban_view",
            run: () => {},
        },
    ],
});

registry.category("web_tour.tours").add("dm_hr_ui_leave_tour", {
    test: true,
    url: "/web#action=dm_hr_core.dm_hr_leave_action_my",
    steps: () => [
        waitForWebClient,
        {
            trigger: ".o_control_panel, .o_calendar_view, .o_list_view, .o_kanban_view",
            run: () => {},
        },
    ],
});

registry.category("web_tour.tours").add("dm_hr_ui_offboarding_tour", {
    test: true,
    url: "/web#action=dm_hr_offboarding.dm_hr_offboarding_action_my",
    steps: () => [
        waitForWebClient,
        {
            trigger: ".o_control_panel, .o_kanban_view, .o_list_view, .o_form_view",
            run: () => {},
        },
    ],
});

registry.category("web_tour.tours").add("dm_hr_ui_finance_tour", {
    test: true,
    url: "/web#action=dm_hr_core.dm_hr_employee_financial_request_report_action",
    steps: () => [
        waitForWebClient,
        {
            trigger: ".o_control_panel, .o_list_view, .o_pivot, .o_graph_renderer",
            run: () => {},
        },
    ],
});

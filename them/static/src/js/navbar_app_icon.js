/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { session } from "@web/session";
import { NavBar } from "@web/webclient/navbar/navbar";

const svgToDataUrl = (svg) => `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
const fallbackAppsMenuBackground = "linear-gradient(135deg, #0f172a 0%, #10202a 45%, #164e63 100%)";

const applyThemeSettings = () => {
    const background = session.them_apps_menu_background || fallbackAppsMenuBackground;
    document.documentElement.style.setProperty("--them-apps-menu-bg", background);
};

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", applyThemeSettings, { once: true });
} else {
    applyThemeSettings();
}

const iconSvg = {
    hr: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><defs><linearGradient id="a" x1="25" y1="21" x2="99" y2="108" gradientUnits="userSpaceOnUse"><stop stop-color="#34d399"/><stop offset=".55" stop-color="#0d9488"/><stop offset="1" stop-color="#0f766e"/></linearGradient><filter id="s" x="-20%" y="-20%" width="140%" height="150%"><feDropShadow dx="0" dy="4" stdDeviation="4" flood-color="#062f2d" flood-opacity=".3"/></filter></defs><g filter="url(#s)"><circle cx="64" cy="44" r="16" fill="url(#a)"/><path d="M34 92c3-19 15-31 30-31s27 12 30 31" fill="none" stroke="url(#a)" stroke-width="12" stroke-linecap="round"/><path d="M39 102h50" stroke="#164e63" stroke-width="8" stroke-linecap="round"/><circle cx="96" cy="35" r="10" fill="#86efac"/><circle cx="31" cy="38" r="8" fill="#2dd4bf"/></g></svg>`,
    signature: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><defs><linearGradient id="p" x1="31" y1="18" x2="98" y2="113"><stop stop-color="#fff"/><stop offset="1" stop-color="#ede9fe"/></linearGradient><linearGradient id="i" x1="40" y1="72" x2="101" y2="98"><stop stop-color="#a78bfa"/><stop offset=".55" stop-color="#7c3aed"/><stop offset="1" stop-color="#4338ca"/></linearGradient><filter id="s" x="-20%" y="-20%" width="140%" height="150%"><feDropShadow dx="0" dy="4" stdDeviation="4" flood-color="#1e1b4b" flood-opacity=".3"/></filter></defs><g filter="url(#s)"><path d="M36 18h42l21 21v69c0 6-4 10-10 10H36c-6 0-10-4-10-10V28c0-6 4-10 10-10Z" fill="url(#p)"/><path d="M78 18v21h21" fill="#ddd6fe"/><path d="M43 53h30M43 66h22" stroke="#94a3b8" stroke-width="7" stroke-linecap="round"/><path d="M39 91c12-18 22-21 31-11 8 9 16 10 28-7" fill="none" stroke="url(#i)" stroke-width="8" stroke-linecap="round"/><circle cx="91" cy="95" r="11" fill="#22c55e"/><path d="m86 95 4 4 7-8" fill="none" stroke="#fff" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/></g></svg>`,
    sales: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><defs><linearGradient id="a" x1="32" y1="92" x2="98" y2="28"><stop stop-color="#9333ea"/><stop offset=".55" stop-color="#dc2626"/><stop offset="1" stop-color="#f59e0b"/></linearGradient><filter id="s" x="-20%" y="-20%" width="140%" height="150%"><feDropShadow dx="0" dy="4" stdDeviation="4" flood-color="#3b1d08" flood-opacity=".28"/></filter></defs><g filter="url(#s)"><rect x="29" y="68" width="17" height="34" rx="5" fill="#9333ea"/><rect x="55" y="51" width="17" height="51" rx="5" fill="#dc2626"/><rect x="81" y="31" width="17" height="71" rx="5" fill="#d97706"/><path d="M28 105h76" stroke="#334155" stroke-width="8" stroke-linecap="round"/><path d="M29 55c17 1 27-14 41-16 11-2 19 4 28-8" fill="none" stroke="url(#a)" stroke-width="7" stroke-linecap="round"/></g></svg>`,
    contacts: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><defs><linearGradient id="a" x1="29" y1="24" x2="98" y2="104"><stop stop-color="#14b8a6"/><stop offset="1" stop-color="#0f766e"/></linearGradient><filter id="s" x="-20%" y="-20%" width="140%" height="150%"><feDropShadow dx="0" dy="4" stdDeviation="4" flood-color="#0f172a" flood-opacity=".28"/></filter></defs><g filter="url(#s)"><rect x="28" y="24" width="73" height="80" rx="14" fill="url(#a)"/><path d="M93 34v60" stroke="#ef4444" stroke-width="7" stroke-linecap="round"/><circle cx="59" cy="52" r="13" fill="#ccfbf1"/><path d="M39 84c3-13 11-20 20-20s17 7 20 20" fill="#ccfbf1"/><path d="M39 98h39" stroke="#064e3b" stroke-width="7" stroke-linecap="round"/></g></svg>`,
    discuss: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><defs><linearGradient id="a" x1="27" y1="27" x2="98" y2="101"><stop stop-color="#f97316"/><stop offset="1" stop-color="#92400e"/></linearGradient><filter id="s" x="-20%" y="-20%" width="140%" height="150%"><feDropShadow dx="0" dy="4" stdDeviation="4" flood-color="#431407" flood-opacity=".28"/></filter></defs><path filter="url(#s)" d="M30 37c0-9 7-16 16-16h39c9 0 16 7 16 16v25c0 9-7 16-16 16H61l-25 23c-4 4-10 1-9-5l5-22c-2-3-2-7-2-12V37Z" fill="url(#a)"/><path d="M50 47h32M50 62h22" stroke="#ffedd5" stroke-width="8" stroke-linecap="round"/></svg>`,
    invoice: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><defs><linearGradient id="a" x1="30" y1="20" x2="98" y2="111"><stop stop-color="#38bdf8"/><stop offset="1" stop-color="#1d4ed8"/></linearGradient><filter id="s" x="-20%" y="-20%" width="140%" height="150%"><feDropShadow dx="0" dy="4" stdDeviation="4" flood-color="#0f172a" flood-opacity=".3"/></filter></defs><g filter="url(#s)"><path d="M35 18h58v92l-10-7-10 7-10-7-10 7-10-7-8 6V18Z" fill="url(#a)"/><circle cx="64" cy="59" r="18" fill="#bae6fd"/><path d="M64 46v27M56 53c2-4 15-5 17 2 2 8-16 5-15 13 1 6 14 6 18 1" fill="none" stroke="#1d4ed8" stroke-width="6" stroke-linecap="round"/></g></svg>`,
    dashboard: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><defs><linearGradient id="a" x1="28" y1="28" x2="99" y2="100"><stop stop-color="#14b8a6"/><stop offset=".45" stop-color="#2563eb"/><stop offset="1" stop-color="#7c3aed"/></linearGradient><filter id="s" x="-20%" y="-20%" width="140%" height="150%"><feDropShadow dx="0" dy="4" stdDeviation="4" flood-color="#172554" flood-opacity=".28"/></filter></defs><g filter="url(#s)"><rect x="27" y="29" width="28" height="28" rx="7" fill="#7c3aed"/><rect x="65" y="29" width="36" height="18" rx="6" fill="#ef4444"/><rect x="27" y="68" width="39" height="31" rx="8" fill="#0d9488"/><rect x="76" y="59" width="25" height="40" rx="8" fill="#2563eb"/><path d="M34 106h67" stroke="url(#a)" stroke-width="8" stroke-linecap="round"/></g></svg>`,
    link: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><defs><linearGradient id="a" x1="31" y1="33" x2="98" y2="95"><stop stop-color="#f59e0b"/><stop offset=".5" stop-color="#9333ea"/><stop offset="1" stop-color="#7e22ce"/></linearGradient><filter id="s" x="-20%" y="-20%" width="140%" height="150%"><feDropShadow dx="0" dy="4" stdDeviation="4" flood-color="#2e1065" flood-opacity=".3"/></filter></defs><g filter="url(#s)" fill="none" stroke="url(#a)" stroke-width="16" stroke-linecap="round"><path d="M52 82 42 92c-9 9-24-6-15-15l20-20c8-8 18-6 24 1"/><path d="M76 46 86 36c9-9 24 6 15 15L81 71c-8 8-18 6-24-1"/></g></svg>`,
    inventory: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><defs><linearGradient id="a" x1="34" y1="25" x2="96" y2="105"><stop stop-color="#fbbf24"/><stop offset="1" stop-color="#b45309"/></linearGradient><filter id="s" x="-20%" y="-20%" width="140%" height="150%"><feDropShadow dx="0" dy="4" stdDeviation="4" flood-color="#451a03" flood-opacity=".28"/></filter></defs><g filter="url(#s)"><path d="m64 18 43 24v49l-43 24-43-24V42l43-24Z" fill="url(#a)"/><path d="M21 42 64 66l43-24M64 66v49" fill="none" stroke="#fffbeb" stroke-width="7" stroke-linecap="round" opacity=".8"/><path d="m43 31 43 24" stroke="#92400e" stroke-width="7" stroke-linecap="round" opacity=".55"/></g></svg>`,
    calendar: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><defs><linearGradient id="a" x1="28" y1="25" x2="100" y2="105"><stop stop-color="#60a5fa"/><stop offset="1" stop-color="#2563eb"/></linearGradient><filter id="s" x="-20%" y="-20%" width="140%" height="150%"><feDropShadow dx="0" dy="4" stdDeviation="4" flood-color="#172554" flood-opacity=".28"/></filter></defs><g filter="url(#s)"><rect x="25" y="29" width="78" height="78" rx="14" fill="#f8fafc"/><path d="M25 48h78" stroke="url(#a)" stroke-width="16"/><path d="M45 22v17M83 22v17" stroke="#1d4ed8" stroke-width="8" stroke-linecap="round"/><rect x="42" y="65" width="16" height="16" rx="4" fill="#60a5fa"/><rect x="70" y="65" width="16" height="16" rx="4" fill="#22c55e"/></g></svg>`,
    app: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><defs><linearGradient id="a" x1="28" y1="27" x2="100" y2="102"><stop stop-color="#38bdf8"/><stop offset=".5" stop-color="#2563eb"/><stop offset="1" stop-color="#0f172a"/></linearGradient><filter id="s" x="-20%" y="-20%" width="140%" height="150%"><feDropShadow dx="0" dy="4" stdDeviation="4" flood-color="#0f172a" flood-opacity=".28"/></filter></defs><g filter="url(#s)"><rect x="27" y="28" width="74" height="72" rx="17" fill="#eff6ff"/><rect x="39" y="42" width="50" height="12" rx="6" fill="url(#a)"/><rect x="39" y="66" width="21" height="21" rx="6" fill="#22c55e"/><rect x="68" y="66" width="21" height="21" rx="6" fill="#06b6d4"/><path d="M39 100h50" stroke="#1e293b" stroke-width="8" stroke-linecap="round" opacity=".72"/></g></svg>`,
};

const iconDataUrl = Object.fromEntries(Object.entries(iconSvg).map(([key, svg]) => [key, svgToDataUrl(svg)]));

patch(NavBar.prototype, {
    themAppIconSrc(app) {
        applyThemeSettings();
        const expressiveIcon = this.themExpressiveIconSrc(app);
        if (expressiveIcon) {
            return expressiveIcon;
        }
        if (!app.webIconData) {
            return iconDataUrl.app;
        }
        if (app.webIconData.startsWith("data:image")) {
            return app.webIconData;
        }
        const mimetype = app.webIconDataMimetype || (
            app.webIconData.startsWith("P") ? "image/svg+xml" : "image/png"
        );
        return `data:${mimetype};base64,${app.webIconData.replace(/\s/g, "")}`;
    },

    themExpressiveIconSrc(app) {
        const text = `${app.name || ""} ${app.xmlid || ""}`.toLowerCase();

        if (text.includes("dm_hr") || text.includes("hr") || text.includes("employee") || text.includes("الموارد") || text.includes("موظف")) {
            return iconDataUrl.hr;
        }
        if (text.includes("signature") || text.includes("sign") || text.includes("document signature") || text.includes("توقيع")) {
            return iconDataUrl.signature;
        }
        if (text.includes("sale") || text.includes("crm") || text.includes("مبيعات")) {
            return iconDataUrl.sales;
        }
        if (text.includes("invoice") || text.includes("account") || text.includes("الفواتير") || text.includes("محاسبة")) {
            return iconDataUrl.invoice;
        }
        if (text.includes("calendar") || text.includes("event") || text.includes("تقويم")) {
            return iconDataUrl.calendar;
        }
        if (text.includes("contact") || text.includes("partner") || text.includes("جهات") || text.includes("عملاء")) {
            return iconDataUrl.contacts;
        }
        if (text.includes("discuss") || text.includes("mail") || text.includes("chat") || text.includes("مناقشة")) {
            return iconDataUrl.discuss;
        }
        if (text.includes("dashboard") || text.includes("testapp") || text.includes("kh app") || text.includes("لوحة")) {
            return iconDataUrl.dashboard;
        }
        if (text.includes("link")) {
            return iconDataUrl.link;
        }
        if (text.includes("inventory") || text.includes("stock") || text.includes("warehouse") || text.includes("مخزون")) {
            return iconDataUrl.inventory;
        }
        return false;
    },
});

/** @odoo-module **/

/*
 * Lightweight HR navbar enhancer.
 *
 * The styling is enabled only while the user is inside the HR area.  This keeps
 * the visual improvement scoped and avoids changing the experience of other
 * Odoo apps such as Accounting, Sales, or Inventory.
 */

const HR_BRAND_KEYWORDS = [
    "الموارد البشرية",
    "الموظفون",
    "Human Resources",
    "Employees",
    "HR",
];

const HR_HASH_MARKERS = [
    "menu_id=",
    "model=hr.employee",
    "model=hr.contract",
    "model=hr.attendance",
    "model=hr.leave",
    "model=dm.hr.",
];

function isHrNavbarContext() {
    const hash = window.location.hash || "";
    if (HR_HASH_MARKERS.slice(1).some((marker) => hash.includes(marker))) {
        return true;
    }

    const brand = document.querySelector(".o_menu_brand");
    const brandText = brand ? brand.textContent.trim() : "";
    if (HR_BRAND_KEYWORDS.some((keyword) => brandText.includes(keyword))) {
        return true;
    }

    /*
     * Odoo routes sometimes keep only action/menu ids in the hash.  When the
     * current app brand is not yet rendered we avoid guessing; once a brand is
     * present and a menu hash exists, enable the HR visual style because this
     * asset belongs to the HR UI module and is meant to make the HR shell
     * immediately visible to users.
     */
    return Boolean(hash.includes("menu_id=") && brandText);
}

function updateHrNavbarState() {
    document.body.classList.toggle("dm_hr_ui_navbar_active", isHrNavbarContext());
}

function setupHrNavbarObserver() {
    updateHrNavbarState();
    window.addEventListener("hashchange", updateHrNavbarState);
    window.addEventListener("popstate", updateHrNavbarState);
    document.addEventListener("click", () => window.setTimeout(updateHrNavbarState, 80), true);

    const observer = new MutationObserver(updateHrNavbarState);
    observer.observe(document.body, {
        childList: true,
        subtree: true,
        characterData: true,
        attributes: true,
    });

    for (const delay of [100, 300, 800, 1500, 3000]) {
        window.setTimeout(updateHrNavbarState, delay);
    }
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setupHrNavbarObserver, { once: true });
} else {
    setupHrNavbarObserver();
}

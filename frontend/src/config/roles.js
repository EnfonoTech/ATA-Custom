// Batch C: the single place the SPA keeps role labels and logo paths.
// Role keys are stable (they match the server); only the labels changed. Prefer the
// server's own role_label / label strings where a response carries them.

export const ROLE_LABELS = {
	super_admin: "Super Admin",
	department_admin: "Department Admin",
	department_coordinator: "Department Coordinator",
	team_lead: "Team Manager",
	project_lead: "Project Lead",
	team_member: "Project Architect",
	client_customer: "Client Customer",
};

// New names the server also accepts for the two renamed keys.
export const ROLE_KEY_ALIASES = { team_manager: "team_lead", project_architect: "team_member" };

export function roleLabel(key) {
	const k = ROLE_KEY_ALIASES[key] || key;
	return ROLE_LABELS[k] || key || "";
}

// Per-project links (Portal Project Link.link_type), in display order.
export const LINK_TYPES = ["T Server", "Autodesk Server", "ERP"];
export const LINK_LABELS = {
	"T Server": "T Server",
	"Autodesk Server": "Autodesk Server",
	ERP: "ERP",
};
export const LINK_SHORT = { "T Server": "T", "Autodesk Server": "A", ERP: "ERP" };

// Bundled ATA logos. A company_logo set in Portal Project Settings overrides them.
export const LOGOS = {
	horizontal: "/assets/portal_app/images/ata-logo-horizontal.png",
	horizontalWhite: "/assets/portal_app/images/ata-logo-horizontal-white.png",
	stacked: "/assets/portal_app/images/ata-logo-stacked.png",
	stackedWhite: "/assets/portal_app/images/ata-logo-stacked-white.png",
};

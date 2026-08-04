import frappe


def run():
    # ATA Dashboard-ile 8 teams — department name → office + members
    TEAMS = [
        {
            "dept_label": "CD Team 01 — Rey",
            "office": "RIYADH",
            "members": [
                "Reynaldo Pabilona",
                "Dexter Romero",
                "Roderick Garcia",
                "Jovaany Jose",
            ],
        },
        {
            "dept_label": "CD Team 02 — John",
            "office": "MANILA",
            "members": [
                "Jonathan Sadsad",
                "Jio Marco Araullo",
            ],
        },
        {
            "dept_label": "CD Team 03 — Gaius",
            "office": "MANILA",
            "members": [
                "Gaius Kabigting",
                "Don Ardie",
                "Arnel M. Pawa-an",
            ],
        },
        {
            "dept_label": "CD Team 04 — Ana Tendeiro",
            "office": "LISBON",
            "members": [
                "Ana Tendeiro",
                "Katia Tendeiro",
                "Marta Pereira",
                "Martina Darbutaite",
                "Tiago Calais",
                "Pedro Miguel Pimenta",
                "Sergio Calais",
                "Diogo Brito",
                "Bruno Madaleno",
                "Sara Alexandra Albuquerque",
                "Sandro Leite",
            ],
        },
        {
            "dept_label": "CD Team 06 — Tiago Guerreiro",
            "office": "LISBON",
            "members": [
                "Tiago Guerreiro",
                "Rodrigo Silvestre",
                "Ruben Aires",
                "Pedro Cardia",
            ],
        },
        {
            "dept_label": "ID Team 05 — Rita Campino",
            "office": "LISBON",
            "members": [
                "Rita Campino",
                "Vasco Antunes",
                "Joao Novais",
                "Leonor Contreiras",
                "Antonio Pedro",
                "Vera Nunes",
                "Florbela Antunes",
                "Dalva Fernandes",
                "Aleksandr Velgan",
                "Filipa Lindo",
                "Filipa Leite",
            ],
        },
        {
            "dept_label": "LA Team 07 — Luis Peralta",
            "office": "LISBON",
            "members": [
                "Luis Peralta",
            ],
        },
        {
            "dept_label": "Facade Team 09 — Nuno Calado",
            "office": "LISBON",
            "members": [
                "Nuno Calado",
            ],
        },
    ]

    # Get all departments — name (with -E) map cheyyuka
    all_depts = frappe.get_all("Department", fields=["name", "department_name"])
    dept_name_map = {d.department_name: d.name for d in all_depts}

    # Get all employees — employee_name → name map
    all_emps = frappe.get_all("Employee", fields=["name", "employee_name"])
    emp_name_map = {e.employee_name: e.name for e in all_emps}

    print("=== Step 1: Set portal_office on 8 team departments ===")
    for t in TEAMS:
        dept_name = dept_name_map.get(t["dept_label"])
        if dept_name:
            frappe.db.set_value("Department", dept_name, "portal_office", t["office"])
            print(f"  {t['dept_label']} → {t['office']}")
        else:
            print(f"  NOT FOUND: {t['dept_label']}")

    frappe.db.commit()

    print("\n=== Step 2: Assign employees to correct team departments ===")
    for t in TEAMS:
        dept_name = dept_name_map.get(t["dept_label"])
        if not dept_name:
            continue
        for member_name in t["members"]:
            emp_id = emp_name_map.get(member_name)
            if emp_id:
                frappe.db.set_value("Employee", emp_id, "department", dept_name)
                print(f"  {member_name} → {t['dept_label']}")
            else:
                print(f"  NOT FOUND employee: {member_name}")

    frappe.db.commit()

    print("\n=== Step 3: Remove portal_office from group-based departments ===")
    GROUP_DEPTS = [
        "ATA RIYADH HQ",
        "LISBON OFFICE 1",
        "LISBON OFFICE 2 - ID TEAM",
        "LISBON OFFICE 2 - CD TEAM",
        "MANILA OFFICE 01",
        "MANILA OFFICE 02",
        "ATA RIYADH SUPERVISION TEAM",
    ]
    for label in GROUP_DEPTS:
        dept_name = dept_name_map.get(label)
        if dept_name:
            frappe.db.set_value("Department", dept_name, "portal_office", "")
            print(f"  Cleared: {label}")

    frappe.db.commit()
    print("\n=== Done. Portal will now show 8 ATA teams. ===")

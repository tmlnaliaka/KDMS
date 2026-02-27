"""
seed_data.py — Seed Kenya counties, refuge sites and field workers into the DB.
Run ONCE:  python seed_data.py
"""
import asyncio
from database import init_db, execute, fetchone

# All 47 Kenya counties with approximate centroids
COUNTIES = [
    ("Mombasa",     "Coast",           -4.0435, 39.6682),
    ("Kwale",       "Coast",           -4.1735, 39.4522),
    ("Kilifi",      "Coast",           -3.6305, 39.8499),
    ("Tana River",  "Coast",           -1.0183, 39.6544),
    ("Lamu",        "Coast",           -2.1694, 40.9020),
    ("Taita-Taveta","Coast",           -3.3160, 38.4842),
    ("Garissa",     "North Eastern",    -0.4532, 39.6460),
    ("Wajir",       "North Eastern",    1.7474,  40.0573),
    ("Mandera",     "North Eastern",    3.9366,  41.8670),
    ("Marsabit",    "Eastern",          2.3284,  37.9899),
    ("Isiolo",      "Eastern",          0.3545,  37.5820),
    ("Meru",        "Eastern",          0.0460,  37.6490),
    ("Tharaka-Nithi","Eastern",         0.3013,  37.8831),
    ("Embu",        "Eastern",         -0.5300,  37.4580),
    ("Kitui",       "Eastern",         -1.3667,  38.0111),
    ("Machakos",    "Eastern",         -1.5177,  37.2634),
    ("Makueni",     "Eastern",         -1.8039,  37.6241),
    ("Nyandarua",   "Central",         -0.1821,  36.5275),
    ("Nyeri",       "Central",         -0.4170,  36.9509),
    ("Kirinyaga",   "Central",         -0.5636,  37.2823),
    ("Murang'a",    "Central",         -0.7813,  37.0364),
    ("Kiambu",      "Central",         -1.0312,  36.8310),
    ("Turkana",     "Rift Valley",      3.1336,  35.5975),
    ("West Pokot",  "Rift Valley",      1.6210,  35.3873),
    ("Samburu",     "Rift Valley",      1.2166,  36.9985),
    ("Trans-Nzoia", "Rift Valley",      1.0567,  35.0062),
    ("Uasin Gishu", "Rift Valley",      0.5203,  35.2699),
    ("Elgeyo-Marakwet","Rift Valley",   0.7879,  35.5082),
    ("Nandi",       "Rift Valley",      0.1835,  35.1269),
    ("Baringo",     "Rift Valley",      0.4670,  35.9780),
    ("Laikipia",    "Rift Valley",      0.1957,  36.7713),
    ("Nakuru",      "Rift Valley",     -0.3031,  36.0800),
    ("Narok",       "Rift Valley",     -1.0936,  35.8714),
    ("Kajiado",     "Rift Valley",     -1.8522,  36.7820),
    ("Kericho",     "Rift Valley",     -0.3686,  35.2863),
    ("Bomet",       "Rift Valley",     -0.7836,  35.3424),
    ("Kakamega",    "Western",          0.2827,  34.7519),
    ("Vihiga",      "Western",          0.0748,  34.7235),
    ("Bungoma",     "Western",          0.5635,  34.5596),
    ("Busia",       "Western",          0.4607,  34.1116),
    ("Siaya",       "Nyanza",           0.0607,  34.2878),
    ("Kisumu",      "Nyanza",          -0.1022,  34.7617),
    ("Homa Bay",    "Nyanza",          -0.5167,  34.4571),
    ("Migori",      "Nyanza",          -1.0637,  34.4734),
    ("Kisii",       "Nyanza",          -0.6817,  34.7667),
    ("Nyamira",     "Nyanza",          -0.5670,  34.9356),
    ("Nairobi",     "Nairobi",         -1.2921,  36.8219),
]

REFUGE_SITES = [
    ("Mombasa Stadium Camp",   "Mombasa",     -4.0211, 39.6680, 2000, "Stadium"),
    ("Kwale High School Camp", "Kwale",       -4.1735, 39.4500,  800, "School"),
    ("Kilifi District Camp",   "Kilifi",      -3.6300, 39.8500, 1200, "Camp"),
    ("Garissa Evacuation Site","Garissa",     -0.4530, 39.6460, 1500, "Camp"),
    ("Tana River Relief Camp", "Tana River",  -1.0180, 39.6540, 1000, "Camp"),
    ("Turkana IDP Camp",       "Turkana",      3.1330, 35.5970, 3000, "IDP"),
    ("Marsabit Community Hall","Marsabit",     2.3280, 37.9890,  600, "Hall"),
    ("Wajir Red Cross Site",   "Wajir",        1.7470, 40.0570,  900, "Camp"),
    ("Mandera Emergency Site", "Mandera",      3.9360, 41.8660, 1100, "Camp"),
    ("Nairobi Rescue Centre",  "Nairobi",     -1.2920, 36.8200, 5000, "Centre"),
    ("Nakuru Show Ground",     "Nakuru",      -0.3030, 36.0800, 2500, "Show Ground"),
    ("Kisumu Sports Camp",     "Kisumu",      -0.1020, 34.7610, 1800, "Stadium"),
    ("Meru County Camp",       "Meru",         0.0460, 37.6490,  700, "Camp"),
    ("Kitui Safe Zone",        "Kitui",       -1.3660, 38.0110,  800, "Camp"),
    ("Machakos District Camp", "Machakos",    -1.5170, 37.2630, 1000, "Camp"),
    ("Eldoret Rescue Point",   "Uasin Gishu",  0.5200, 35.2690, 1500, "School"),
    ("Kakamega Forest Camp",   "Kakamega",     0.2820, 34.7510,  600, "Camp"),
    ("Kisii Evacuation Hub",   "Kisii",       -0.6810, 34.7660,  900, "Camp"),
    ("Migori Relief Post",     "Migori",      -1.0630, 34.4730,  700, "Post"),
    ("Samburu Pastoralist Site","Samburu",     1.2160, 36.9980,  500, "Camp"),
]

WORKERS = [
    ("Amina Hassan",    "Paramedic",        "+254701000001", "Mombasa"),
    ("Brian Omondi",    "Search & Rescue",  "+254701000002", "Nairobi"),
    ("Carol Wanjiru",   "Medical Officer",  "+254701000003", "Nakuru"),
    ("David Kipchoge",  "Field Coordinator","+254701000004", "Eldoret"),
    ("Eva Achieng",     "Logistics",        "+254701000005", "Kisumu"),
    ("Felix Murithi",   "Paramedic",        "+254701000006", "Meru"),
    ("Grace Kamau",     "Search & Rescue",  "+254701000007", "Nyeri"),
    ("Hassan Abdi",     "Field Coordinator","+254701000008", "Garissa"),
    ("Irene Chelimo",   "Medical Officer",  "+254701000009", "Kericho"),
    ("James Otieno",    "Logistics",        "+254701000010", "Homa Bay"),
    ("Katherine Nduta", "Paramedic",        "+254701000011", "Machakos"),
    ("Liban Duale",     "Field Coordinator","+254701000012", "Wajir"),
    ("Mary Njeri",      "Search & Rescue",  "+254701000013", "Kiambu"),
    ("Noah Sang",       "Medical Officer",  "+254701000014", "Nandi"),
    ("Olivia Chege",    "Logistics",        "+254701000015", "Embu"),
    ("Patrick Lotukoi", "Search & Rescue",  "+254701000016", "Turkana"),
    ("Queen Auma",      "Paramedic",        "+254701000017", "Migori"),
    ("Rashid Omar",     "Field Coordinator","+254701000018", "Mandera"),
    ("Sylvia Maina",    "Medical Officer",  "+254701000019", "Murang'a"),
    ("Tom Kerich",      "Logistics",        "+254701000020", "Baringo"),
]


async def seed():
    await init_db()

    # Counties
    for name, region, lat, lng in COUNTIES:
        existing = await fetchone("SELECT id FROM counties WHERE name=?", (name,))
        if not existing:
            await execute(
                "INSERT INTO counties (name, region, lat, lng, risk_score) VALUES (?,?,?,?,?)",
                (name, region, lat, lng, 0)
            )
    print(f"[SEED] ✅ Seeded {len(COUNTIES)} counties")

    # Refuge sites
    for name, county_name, lat, lng, cap, rtype in REFUGE_SITES:
        row = await fetchone("SELECT id FROM refuge_sites WHERE name=?", (name,))
        if not row:
            county = await fetchone("SELECT id FROM counties WHERE name=?", (county_name,))
            if county:
                await execute(
                    "INSERT INTO refuge_sites (name, county_id, lat, lng, capacity, type) VALUES (?,?,?,?,?,?)",
                    (name, county["id"], lat, lng, cap, rtype)
                )
    print(f"[SEED] ✅ Seeded {len(REFUGE_SITES)} refuge sites")

    # Workers
    for name, role, phone, county_name in WORKERS:
        row = await fetchone("SELECT id FROM workers WHERE name=?", (name,))
        if not row:
            county = await fetchone("SELECT id FROM counties WHERE name=?", (county_name,))
            cid = county["id"] if county else None
            await execute(
                "INSERT INTO workers (name, role, phone, county_id, status) VALUES (?,?,?,?,?)",
                (name, role, phone, cid, "available")
            )
    print(f"[SEED] ✅ Seeded {len(WORKERS)} workers")

    # Sample disasters
    disasters_exist = await fetchone("SELECT id FROM disasters LIMIT 1")
    if not disasters_exist:
        samples = [
            ("Flood",      "High",   "Tana River", -1.0183, 39.6544, 1200, "Flash flooding from river overflow", "auto"),
            ("Wildfire",   "Medium", "Turkana",     3.1336, 35.5975,  340, "Grass fire spreading east",           "nasa_firms"),
            ("Drought",    "High",   "Wajir",       1.7474, 40.0573, 5000, "Severe water shortage, 3rd month",    "auto"),
            ("Earthquake", "Low",    "Nairobi",    -1.2921, 36.8219,   80, "M3.1 tremor felt across city",        "usgs"),
            ("Landslide",  "High",   "Elgeyo-Marakwet", 0.7879, 35.5082, 620, "Heavy rains triggered hillside collapse", "manual"),
        ]
        for dtype, sev, county_name, lat, lng, aff, desc, src in samples:
            county = await fetchone("SELECT id FROM counties WHERE name=?", (county_name,))
            if county:
                await execute(
                    """INSERT INTO disasters (type, severity, county_id, location, lat, lng,
                       affected_people, description, source, status)
                       VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (dtype, sev, county["id"], county_name, lat, lng, aff, desc, src, "active")
                )
        print("[SEED] ✅ Seeded 5 sample disasters")

    print("[SEED] 🎉 All seed data loaded successfully!")


if __name__ == "__main__":
    asyncio.run(seed())

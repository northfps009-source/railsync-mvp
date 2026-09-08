import pandas as pd

# =========================================================
# RailSync AI - Feasible Synthetic Railway Dataset
# =========================================================

# ---------------------------------------------------------
# 20 TRAINS
# ---------------------------------------------------------
# Trains are placed in the daytime operating window.
# This deliberately leaves early-morning time available
# for maintenance while still giving the solver realistic
# train traffic to avoid.
# ---------------------------------------------------------

trains_data = []

train_id = 1

# 8 Rajdhani trains
rajdhani_times = [
    ("A", 600),
    ("B", 630),
    ("C", 660),
    ("A", 720),
    ("B", 750),
    ("C", 780),
    ("A", 840),
    ("B", 870),
]

for section, departure in rajdhani_times:
    trains_data.append({
        "id": f"TRAIN_{train_id:03d}",
        "section": section,
        "departure_min": departure,
        "arrival_min": departure + 60,
        "passengers": 650,
        "priority": "high"
    })
    train_id += 1


# 6 Local trains
local_times = [
    ("C", 900),
    ("A", 930),
    ("B", 960),
    ("C", 990),
    ("A", 1020),
    ("B", 1050),
]

for section, departure in local_times:
    trains_data.append({
        "id": f"TRAIN_{train_id:03d}",
        "section": section,
        "departure_min": departure,
        "arrival_min": departure + 60,
        "passengers": 750,
        "priority": "high"
    })
    train_id += 1


# 4 Goods trains
goods_times = [
    ("C", 1110),
    ("A", 1140),
    ("B", 1170),
    ("C", 1200),
]

for section, departure in goods_times:
    trains_data.append({
        "id": f"TRAIN_{train_id:03d}",
        "section": section,
        "departure_min": departure,
        "arrival_min": departure + 60,
        "passengers": 50,
        "priority": "low"
    })
    train_id += 1


# 2 Mail trains
mail_times = [
    ("A", 1260),
    ("B", 1290),
]

for section, departure in mail_times:
    trains_data.append({
        "id": f"TRAIN_{train_id:03d}",
        "section": section,
        "departure_min": departure,
        "arrival_min": departure + 60,
        "passengers": 350,
        "priority": "medium"
    })
    train_id += 1


# Save trains
trains_df = pd.DataFrame(trains_data)
trains_df.to_csv("trains.csv", index=False)


# ---------------------------------------------------------
# 10 MAINTENANCE BLOCKS
# ---------------------------------------------------------
# Exactly:
# 4 Track Inspections
# 3 Signal Maintenance
# 2 Bridge Checks
# 1 Cable Replacement
#
# All sections are A/B/C.
# ---------------------------------------------------------

blocks_data = [
    {
        "id": "BLOCK_001",
        "section": "A",
        "duration_min": 60,
        "maintenance_type": "Track Inspection"
    },
    {
        "id": "BLOCK_002",
        "section": "A",
        "duration_min": 45,
        "maintenance_type": "Track Inspection"
    },
    {
        "id": "BLOCK_003",
        "section": "B",
        "duration_min": 60,
        "maintenance_type": "Track Inspection"
    },
    {
        "id": "BLOCK_004",
        "section": "C",
        "duration_min": 45,
        "maintenance_type": "Track Inspection"
    },
    {
        "id": "BLOCK_005",
        "section": "A",
        "duration_min": 90,
        "maintenance_type": "Signal Maintenance"
    },
    {
        "id": "BLOCK_006",
        "section": "B",
        "duration_min": 90,
        "maintenance_type": "Signal Maintenance"
    },
    {
        "id": "BLOCK_007",
        "section": "C",
        "duration_min": 90,
        "maintenance_type": "Signal Maintenance"
    },
    {
        "id": "BLOCK_008",
        "section": "B",
        "duration_min": 180,
        "maintenance_type": "Bridge Check"
    },
    {
        "id": "BLOCK_009",
        "section": "C",
        "duration_min": 240,
        "maintenance_type": "Bridge Check"
    },
    {
        "id": "BLOCK_010",
        "section": "C",
        "duration_min": 240,
        "maintenance_type": "Cable Replacement"
    }
]

blocks_df = pd.DataFrame(blocks_data)
blocks_df.to_csv("blocks.csv", index=False)


print(f"Created trains.csv with {len(trains_df)} rows")
print(f"Created blocks.csv with {len(blocks_df)} rows")
print("Synthetic dataset created successfully.")
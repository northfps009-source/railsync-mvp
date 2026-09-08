from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ortools.sat.python import cp_model
import pandas as pd
import uvicorn

app = FastAPI(title="RailSync AI Backend")

# Allow the frontend to communicate with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# LOAD SYNTHETIC RAILWAY DATA
# ---------------------------------------------------------

trains_df = pd.read_csv("trains.csv")
blocks_df = pd.read_csv("blocks.csv")

print(f"✓ Loaded {len(trains_df)} trains from CSV")
print(f"✓ Loaded {len(blocks_df)} blocks from CSV")


# ---------------------------------------------------------
# GET ALL TRAINS
# ---------------------------------------------------------

@app.get("/trains")
def get_trains():
    return trains_df.to_dict(orient="records")


# ---------------------------------------------------------
# GET ALL MAINTENANCE BLOCKS
# ---------------------------------------------------------

@app.get("/blocks")
def get_blocks():
    return blocks_df.to_dict(orient="records")


# ---------------------------------------------------------
# SCHEDULING SOLVER
# ---------------------------------------------------------

@app.post("/schedule")
def create_schedule():

    model = cp_model.CpModel()

    # Railway operating day:
    # 00:00 -> 24:00
    DAY_START = 0
    DAY_END = 1440

    # Peak period:
    # 06:00 -> 22:00
    PEAK_START = 360
    PEAK_END = 1320

    block_starts = {}
    block_ends = {}
    block_intervals = {}

    # -----------------------------------------------------
    # CREATE VARIABLES FOR EACH MAINTENANCE BLOCK
    # -----------------------------------------------------

    for _, block in blocks_df.iterrows():

        block_id = str(block["id"])
        section = str(block["section"])
        duration = int(block["duration_min"])

        start = model.NewIntVar(
            DAY_START,
            DAY_END - duration,
            f"start_{block_id}"
        )

        end = model.NewIntVar(
            DAY_START + duration,
            DAY_END,
            f"end_{block_id}"
        )

        model.Add(end == start + duration)

        interval = model.NewIntervalVar(
            start,
            duration,
            end,
            f"interval_{block_id}"
        )

        block_starts[block_id] = start
        block_ends[block_id] = end
        block_intervals[block_id] = (section, interval)

    # -----------------------------------------------------
    # CREATE TRAIN SAFETY-BUFFER INTERVALS
    #
    # A maintenance block cannot overlap a train's
    # movement window, with a 15-minute safety buffer.
    # -----------------------------------------------------

    sections = set(trains_df["section"].astype(str))

    for section in set(blocks_df["section"].astype(str)):
        section_intervals = []

        # Add maintenance blocks belonging to this section
        for block_id, (block_section, interval) in block_intervals.items():
            if block_section == section:
                section_intervals.append(interval)

        # Add trains belonging to this section
        for _, train in trains_df.iterrows():

            if str(train["section"]) != section:
                continue

            train_start = max(
                DAY_START,
                int(train["departure_min"]) - 15
            )

            train_end = min(
                DAY_END,
                int(train["arrival_min"]) + 15
            )

            # Fixed train interval
            train_interval = model.NewIntervalVar(
                model.NewConstant(train_start),
                train_end - train_start,
                model.NewConstant(train_end),
                f"train_{train['id']}"
            )

            section_intervals.append(train_interval)

        # Nothing on the same section can overlap.
        model.AddNoOverlap(section_intervals)

    # -----------------------------------------------------
    # OBJECTIVE:
    # MINIMIZE MAINTENANCE DURING PEAK HOURS
    # 06:00 -> 22:00
    # -----------------------------------------------------

    peak_overlap_vars = []

    for _, block in blocks_df.iterrows():

        block_id = str(block["id"])
        duration = int(block["duration_min"])

        start = block_starts[block_id]
        end = block_ends[block_id]

        peak_start = model.NewIntVar(
            PEAK_START,
            DAY_END,
            f"peak_start_{block_id}"
        )

        peak_end = model.NewIntVar(
            DAY_START,
            PEAK_END,
            f"peak_end_{block_id}"
        )

        model.AddMaxEquality(
            peak_start,
            [start, PEAK_START]
        )

        model.AddMinEquality(
            peak_end,
            [end, PEAK_END]
        )

        raw_overlap = model.NewIntVar(
            -duration,
            duration,
            f"raw_overlap_{block_id}"
        )

        model.Add(raw_overlap == peak_end - peak_start)

        peak_overlap = model.NewIntVar(
            0,
            duration,
            f"peak_overlap_{block_id}"
        )

        model.AddMaxEquality(
            peak_overlap,
            [raw_overlap, 0]
        )

        peak_overlap_vars.append(peak_overlap)

    # Minimize total maintenance minutes during peak hours
    model.Minimize(sum(peak_overlap_vars))

    # -----------------------------------------------------
    # RUN SOLVER
    # -----------------------------------------------------

    solver = cp_model.CpSolver()

    # Keep demo response fast
    solver.parameters.max_time_in_seconds = 5

    print("→ Running OR-Tools CP-SAT solver...")

    status = solver.Solve(model)

    print(f"→ Solver status: {solver.StatusName(status)}")

    # -----------------------------------------------------
    # HANDLE SOLVER FAILURE
    # -----------------------------------------------------

    if status not in (
        cp_model.OPTIMAL,
        cp_model.FEASIBLE
    ):
        return {
            "status": "INFEASIBLE",
            "message": (
                "No valid maintenance schedule exists "
                "with the current train timings, sections, "
                "durations and safety constraints."
            ),
            "scheduled_blocks": []
        }

    # -----------------------------------------------------
    # BUILD RESULT
    # -----------------------------------------------------

    scheduled_blocks = []

    for _, block in blocks_df.iterrows():

        block_id = str(block["id"])
        section = str(block["section"])

        start_min = solver.Value(block_starts[block_id])
        end_min = solver.Value(block_ends[block_id])

        # Generate human-readable explanation
        if end_min <= PEAK_START:
            reason = "Scheduled before peak traffic hours."
        elif start_min >= PEAK_END:
            reason = "Scheduled after peak traffic hours."
        else:
            reason = (
                "Scheduled in the lowest-impact feasible window "
                "while respecting train safety buffers."
            )

        scheduled_blocks.append({
            "id": block_id,
            "section": section,
            "maintenance_type": str(block["maintenance_type"]),
            "duration_min": int(block["duration_min"]),
            "scheduled_start_min": start_min,
            "scheduled_end_min": end_min,
            "reason": reason
        })

    return {
        "status": "OPTIMAL" if status == cp_model.OPTIMAL else "FEASIBLE",
        "scheduled_blocks": scheduled_blocks
    }


# ---------------------------------------------------------
# ROOT ENDPOINT
# ---------------------------------------------------------

@app.get("/")
def root():
    return {
        "project": "RailSync AI",
        "status": "Backend running",
        "solver": "Google OR-Tools CP-SAT"
    }


# ---------------------------------------------------------
# START SERVER
# ---------------------------------------------------------

if __name__ == "__main__":
    print("========================================")
    print("       RailSync AI Backend")
    print("========================================")
    print("✓ Backend starting...")
    print("✓ Loaded trains from CSV")
    print("✓ Loaded blocks from CSV")
    print("✓ Ready to receive requests")
    print("")
    print("API: http://localhost:8000")
    print("Docs: http://localhost:8000/docs")
    print("========================================")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000
    )
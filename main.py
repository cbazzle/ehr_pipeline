from typing import Optional
from data_generator import db
from fastapi import FastAPI, Query

app = FastAPI(title="Healthcare EHR API")


def paginate(data: list, skip: int, limit: int):
    return data[skip : skip + limit]


@app.get("/patients")
def get_patients(
    skip: int = Query(0, description="Records to skip"),
    limit: int = Query(100, le=1000, description="Max records per page"),
):
    paginated_data = paginate(db["patients"], skip, limit)
    return {
        "metadata": {"skip": skip, "limit": limit, "count": len(paginated_data)},
        "data": paginated_data,
    }


@app.get("/encounters")
def get_encounters(
    patient_id: Optional[int] = Query(None, description="Filter by patient_id"),
    start_date: Optional[str] = Query(
        None, description="ISO format date (YYYY-MM-DD) for incremental loads"
    ),
    skip: int = 0,
    limit: int = 100,
):
    results = db["encounters"]

    if patient_id:
        results = [e for e in results if e["patient_id"] == patient_id]
    if start_date:
        # String comparison works for ISO dates
        results = [e for e in results if e["admission_date"] >= start_date]

    paginated_data = paginate(results, skip, limit)
    return {
        "metadata": {"skip": skip, "limit": limit, "count": len(paginated_data)},
        "data": paginated_data,
    }


@app.get("/observations")
def get_observations(
    encounter_id: Optional[int] = Query(None, description="Filter by encounter_id"),
    observation_type: Optional[str] = Query(None, description="e.g., blood_pressure"),
    skip: int = 0,
    limit: int = 500,
):
    results = db["observations"]

    if encounter_id:
        results = [o for o in results if o["encounter_id"] == encounter_id]
    if observation_type:
        results = [o for o in results if o["type"] == observation_type]

    paginated_data = paginate(results, skip, limit)
    return {
        "metadata": {"skip": skip, "limit": limit, "count": len(paginated_data)},
        "data": paginated_data,
    }

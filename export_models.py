import logging
import pandas as pd
from pathlib import Path
from sqlalchemy import text
from db_setup import get_engine

logger = logging.getLogger("pipeline")

OUTPUT_DIR = "output"

SQL_QUERY_1 = """

SELECT
    patient_id,
    encounter_id,
    admission_date,
    discharge_date,
    prev_discharge_date,
    days_since_last_discharge,
    CASE 
        WHEN days_since_last_discharge <= 30 THEN TRUE
        ELSE FALSE
    END AS readmission_risk
FROM
    (SELECT
        patient_id,
        encounter_id,
        admission_date,
        discharge_date,
        LAG(discharge_date) OVER(
            PARTITION BY patient_id
            ORDER BY admission_date)
        AS prev_discharge_date,
        admission_date - LAG(discharge_date) OVER (
            PARTITION BY patient_id
            ORDER BY admission_date)
        AS days_since_last_discharge
    FROM encounters) dishcarge_calculations
WHERE prev_discharge_date IS NOT NULL
ORDER BY patient_id, admission_date;
"""

SQL_QUERY_2 = """
SELECT 
    encounter_id,
    observation_date,
    type
FROM
    (SELECT
        encounter_id,
        observation_date,
        type,
        ROW_NUMBER() OVER (
            PARTITION BY encounter_id
            ORDER BY observation_date DESC)
        AS recent_observations
    FROM observations) as observation_calculations
WHERE recent_observations = 1
"""

SQL_QUERY_3 = """
SELECT
    e.facility_id,
    COUNT(DISTINCT p.patient_id) AS distinct_patient_count,   
    (SELECT e1.diagnosis_code
        FROM encounters e1
        WHERE e1.facility_id = e.facility_id
        GROUP BY e1.diagnosis_code
        ORDER BY COUNT(*) DESC
        LIMIT 1) AS most_frequent_diagnosis
FROM patients p
INNER JOIN encounters e ON p.patient_id = e.patient_id
GROUP BY e.facility_id
"""

def export_to_parquet(df: pd.DataFrame, filename: str) -> None:
    file_path = Path(OUTPUT_DIR) / filename
    df.to_parquet(file_path, compression='snappy', engine='pyarrow')
    logger.info("Exported | file=%s | rows=%d", file_path, len(df))

def run_query(engine, sql: str) -> pd.DataFrame:
    with engine.connect() as conn:
        df = pd.read_sql(text(sql), conn)
    return df

if __name__ == "__main__":
    logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    level=logging.INFO,
    )
    
    engine = get_engine()
    Path(OUTPUT_DIR).mkdir(exist_ok=True)

    df1 = run_query(engine, SQL_QUERY_1)
    export_to_parquet(df1, "readmission_risk.parquet")

    df2 = run_query(engine, SQL_QUERY_2)
    export_to_parquet(df2, "latest_vitals.parquet")

    df3 = run_query(engine, SQL_QUERY_3)
    export_to_parquet(df3, "facility_diagnosis.parquet")

    

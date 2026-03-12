-- Run with: psql -U postgres -d ehr_pipeline -f analytical_models.sql

-- Model 1: 30-Day Readmission Risk

SELECT
    patient_id,
    encounter_id,
    admission_date,
    discharge_date,
    prev_discharge_date,
    days_since_last_discharge
    CASE 
        WHEN days_since_last_discharge >= 30 THEN TRUE
        ELSE FALSE
    END AS readmission_risk
FROM
    (SELECT
        patient_id,
        encounter_id,
        admission_date,
        discharge_date
        LAG(discharge_date) OVER(
            PARTITION BY patient_id
            ORDER BY admission_date)
        AS prev_discharge_date,
        admission_date - (LAG discharge_date) OVER (
            PARTITION BY patient_id
            ORDER BY admission_date)
        AS days_since_last_discharge
    FROM encounters) dishcarge_caculations
WHERE prev_discharge_date IS NOT NULL
ORDER BY patient_id, admission_date;


-- Model 2: Latest Vitals per Encounter

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


-- Model 3: Facility Diagnosis Aggregation
--Logic: Write a query using `JOIN` and `GROUP BY` to output the total number of distinct 
--patients and the most frequent diagnosis code per `facility_id`.

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

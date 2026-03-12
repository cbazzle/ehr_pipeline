# API Interfaces Specification

**Base URL:** `http://127.0.0.1:8000`
**Response Format:** All endpoints return JSON containing `metadata` (pagination info) and `data` (an array of records).

---

## GET `/patients`

Retrieves core demographic data for patients (Dimension).

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `skip` | int | 0 | Number of records to skip for pagination. |
| `limit` | int | 100 | Maximum records to return (Max: 1000). |

---

## GET `/encounters`

Retrieves hospital admission and discharge records (Fact).

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `patient_id` | int | None | Filter by a specific patient ID. |
| `start_date` | string | None | ISO date (`YYYY-MM-DD`). Use for incremental loading. |
| `skip` | int | 0 | Number of records to skip for pagination. |
| `limit` | int | 100 | Maximum records to return. |

---

## GET `/observations`

Retrieves high-volume clinical readings tied to an encounter (High-Volume Fact).

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `encounter_id` | int | None | Filter by a specific encounter ID. |
| `observation_type`| string | None | Filter by type (`blood_pressure`, `heart_rate`, `temperature_f`).|
| `skip` | int | 0 | Number of records to skip for pagination. |
| `limit` | int | 500 | Maximum records to return. |

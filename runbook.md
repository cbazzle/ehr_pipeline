# EHR Mock API Runbook

**Overview:** A local mock API that dynamically generates patient, encounter, and clinical observation data for ETL pipeline testing.

## Operations

| Action | Command / Shortcut | Notes |
| :--- | :--- | :--- |
| **Start API** | `bash start_api.sh` | Run this from the folder containing the script. It handles all setup automatically. |
| **Stop API** | `Ctrl + C` | Press these keys in the terminal window where the API is running. |
| **View UI** | `http://127.0.0.1:8000/docs` | Interactive Swagger UI. Only available while the API is running. |
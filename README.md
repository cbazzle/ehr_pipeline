# ehr_pipeline
End-to-end pipeline extracting generated data from an API, loading it into PostgreSQL, validating it, modeling with SQL and exporting it to compresssed parquet files.

---

## Setup

Update the settings at the top of `db_setup.py` to match your local PostgreSQL instance:
```python
DB_HOST     = "127.0.0.1"
DB_PORT     = 5432
DB_NAME     = "ehr_pipeline"
DB_USER     = "postgres"
DB_PASSWORD = "your_password"
```

Create the database if it doesn't already exist:
```bash
psql -U postgres -c "CREATE DATABASE ehr_pipeline;"
```

Create the tables:
```bash
python3 db_setup.py
```

---

## Running the Pipeline

**Terminal 1** — Start the API server and keep it running:
```bash
bash start_api.sh
```

**Terminal 2** — Run the pipeline:
```bash
# Activate the virtual environment
source .venv/bin/activate

# Verify the API is responding (optional)
python3 test_api.py

# Run extraction and load pipeline
python3 api_client.py

# Run data validation
python3 validator.py

# Export to parquet
python3 export_models.py
```

---

## Design & Implementation Notes

The pipeline uses Python generators (`yield`) throughout the extraction layer so that API pages are processed one at a time and never fully loaded into memory, keeping space complexity at O(1) relative to total dataset size regardless of how large the API grows. Incremental loading is implemented via a `watermark.txt` file that is only updated on pipeline success, ensuring that failed runs always re-fetch from the last known good state without data loss or duplication. Upserts (`INSERT ... ON CONFLICT DO NOTHING`) are used on all three tables to eliminate duplicate data. Analytical outputs are written as Snappy-compressed Parquet files, which provide columnar storage and significantly faster read performance for downstream analytical queries.

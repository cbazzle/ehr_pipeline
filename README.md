# ehr_pipeline
End-to-end pipeline extracting generated data from an API, loading it into PostgreSQL, validating it, modeling with SQL and exporting it to compresssed parquet files.

## Setup  
Update the settings at the top of db_setup.py to match your local PostgreSQL instance:  
  DB_HOST     = "127.0.0.1"  
  DB_PORT     = 5432  
  DB_NAME     = "ehr_pipeline"  
  DB_USER     = "postgres"  
  DB_PASSWORD = "your_password"  

Create the database if it doesn't already exist:  
  psql -U postgres -c "CREATE DATABASE ehr_pipeline;"  

Create the tables:  
  python3 db_setup.py  

## Running the Pipeline  
Terminal 1: Start the API server and keep it running:  
  bash start_api.sh  

Terminal 2:   
  Run the pipeline:  
    source .venv/bin/activate  
  Verify the API is responding (optional):  
    python3 test_api.py  
  Run extraction and load pipeline:  
    python3 api_client.py  
  Run data validation:  
    python3 validator.py  
  Export to parquet:  
    python3 export_models.py  

  

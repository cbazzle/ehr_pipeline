"""
Phase 2: Database Schema Definition

db_setup.py

Defines and creates the PostgreSQL schemas for:
  - patients   (Dimension table)
  - encounters (Fact table)
  - observations (Fact table)

"""

import logging
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Date,
    Text,
    MetaData,
    Table,
    inspect,
)

# Connection Settings

DB_HOST     = "127.0.0.1"     
DB_PORT     = 5432              
DB_NAME     = "ehr_pipeline"   
DB_USER     = "postgres"       
DB_PASSWORD = "password"             

# --------------------------------------

logger = logging.getLogger("pipeline")


def get_connection_string() -> str:
    """Build the SQLAlchemy PostgreSQL connection string."""
    if DB_PASSWORD:
        return f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return f"postgresql://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def get_engine():
    """Create and return a SQLAlchemy engine."""
    connection_string = get_connection_string()
    engine = create_engine(connection_string, echo=False)
    return engine


metadata = MetaData()


# Dimension Table: patients

patients_table = Table(
    "patients",
    metadata,
    Column("patient_id",  Integer, primary_key=True),
    Column("first_name",  String(100)),
    Column("last_name",   String(100)),
    Column("dob",         Date),
    Column("gender",      String(10)),
    Column("state",       String(2)),
)

# Fact Table: encounters

encounters_table = Table(
    "encounters",
    metadata,
    Column("encounter_id",     Integer, primary_key=True),
    Column("patient_id",       Integer),                    # FK to patients
    Column("admission_date",   Date),
    Column("discharge_date",   Date),
    Column("facility_id",      Integer),
    Column("diagnosis_code",   Text),
)

# Fact Table: observations

observations_table = Table(
    "observations",
    metadata,
    Column("observation_id",   Integer, primary_key=True),
    Column("encounter_id",     Integer),                    # FK to encounters
    Column("observation_date", Date),
    Column("type",             String(50)),
    Column("value",            String(50)),
    Column("unit",             String(20)),
)

# Create tables if they don't exist.

def create_tables(engine) -> None:

    inspector = inspect(engine)
    existing = inspector.get_table_names()

    tables_to_create = [
        ("patients",     patients_table),
        ("encounters",   encounters_table),
        ("observations", observations_table),
    ]

    for name, table in tables_to_create:
        if name in existing:
            logger.info("Table already exists, skipping | table=%s", name)
            print(f"  [SKIP] Table '{name}' already exists.")
        else:
            table.create(engine)
            logger.info("Table created | table=%s", name)
            print(f"  [CREATED] Table '{name}' created successfully.")


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        level=logging.INFO,
    )

    print("\nConnecting to PostgreSQL...")
    try:
        engine = get_engine()
        # Test connection
        with engine.connect() as conn:
            print(f"  [OK] Connected to '{DB_NAME}' at {DB_HOST}:{DB_PORT}\n")

        print("Creating tables...")
        create_tables(engine)
        print("\nSchema setup complete.")

    except Exception as exc:
        print(f"\n  [ERROR] Could not connect to database: {exc}")
        print("  Check your DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD settings.")
        raise

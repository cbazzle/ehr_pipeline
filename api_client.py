import logging
from datetime import datetime, date
from logging.handlers import RotatingFileHandler
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from sqlalchemy.dialects.postgresql import insert as pg_insert

from db_setup import get_engine, patients_table, encounters_table, observations_table



# >>> CONFIGURE: Set these values before running

BASE_URL        = "http://127.0.0.1:8000"  # >>> CONFIGURE: Base URL of your API
LOG_FILE_PATH   = "pipeline.log"            # >>> CONFIGURE: Path for the log file
REQUEST_TIMEOUT = 30                        # >>> CONFIGURE: Seconds before timeout
MAX_RETRIES     = 3                         # >>> CONFIGURE: Max retry attempts
RETRY_BACKOFF   = 1.0                       # >>> CONFIGURE: Seconds between retries
WATERMARK_FILE  = "watermark.txt"          # >>> CONFIGURE: Path to watermark file



# Logging Setup

def setup_logging(log_file: str = LOG_FILE_PATH) -> logging.Logger:
    """
    Configure the root pipeline logger.
    Outputs structured log lines to both a rotating file and the console.
    Log format: TIMESTAMP | LEVEL | MESSAGE
    """
    logger = logging.getLogger("pipeline")
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger



def read_watermark(filepath: str = WATERMARK_FILE) -> str | None:
    logger = logging.getLogger("pipeline")
    path = Path(filepath)

    if not path.exists():
        logger.info("Watermark file not found — full load will run | file=%s", filepath)
        return None

    content = path.read_text().strip()
    if not content:
        logger.info("Watermark file is empty — full load will run | file=%s", filepath)
        return None

    logger.info("Watermark read | last_processed_date=%s", content)
    return content


def write_watermark(run_date: str, filepath: str = WATERMARK_FILE) -> None:
    logger = logging.getLogger("pipeline")
    Path(filepath).write_text(run_date)
    logger.info("Watermark updated | new_watermark=%s | file=%s", run_date, filepath)


# API Client (Phase 1)

class HealthcareAPIClient:
    def __init__(   
        self,
        base_url: str = BASE_URL,
        timeout: int = REQUEST_TIMEOUT,
        max_retries: int = MAX_RETRIES,
        retry_backoff: float = RETRY_BACKOFF,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.logger = logging.getLogger("pipeline")

        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=retry_backoff,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        self.logger.debug(
            "HealthcareAPIClient initialised | base_url=%s | timeout=%ss | max_retries=%d",
            self.base_url, self.timeout, max_retries,
        )

    def _get(self, endpoint: str, params: dict) -> dict:
        """Execute a single GET request and return parsed JSON."""
        url = f"{self.base_url}{endpoint}"
        self.logger.debug("GET %s | params=%s", url, params)

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
        except requests.exceptions.HTTPError as exc:
            self.logger.error(
                "HTTP error | url=%s | status=%s | reason=%s",
                url, exc.response.status_code, exc.response.reason,
            )
            raise
        except requests.exceptions.Timeout:
            self.logger.error("Request timed out | url=%s | timeout=%ss", url, self.timeout)
            raise
        except requests.exceptions.ConnectionError:
            self.logger.error("Connection error | url=%s — is the API server running?", url)
            raise

        return response.json()

    def _paginate(self, endpoint: str, base_params: dict, page_limit: int):
        skip = 0
        total_fetched = 0

        while True:
            params = {**base_params, "skip": skip, "limit": page_limit}
            payload = self._get(endpoint, params)
            records = payload.get("data", [])
            record_count = len(records)

            if record_count == 0:
                self.logger.debug(
                    "Pagination complete | endpoint=%s | total_fetched=%d",
                    endpoint, total_fetched,
                )
                return

            total_fetched += record_count
            self.logger.info(
                "Page fetched | endpoint=%s | skip=%d | records_this_page=%d | total_so_far=%d",
                endpoint, skip, record_count, total_fetched,
            )

            yield records

            if record_count < page_limit:
                self.logger.debug(
                    "Last page detected | endpoint=%s | total_fetched=%d",
                    endpoint, total_fetched,
                )
                return

            skip += record_count

    def fetch_patients(self, page_limit: int = 100):
        """Generator — yields one page of patient demographic records at a time."""
        self.logger.info("Starting extraction | endpoint=/patients")
        yield from self._paginate("/patients", base_params={}, page_limit=page_limit)
        self.logger.info("Extraction complete | endpoint=/patients")

    def fetch_encounters(
        self,
        patient_id: int | None = None,
        start_date: str | None = None,
        page_limit: int = 100,
    ):
        params: dict = {}
        if patient_id is not None:
            params["patient_id"] = patient_id
        if start_date is not None:
            params["start_date"] = start_date

        self.logger.info(
            "Starting extraction | endpoint=/encounters | filters=%s",
            params or "none",
        )
        yield from self._paginate("/encounters", base_params=params, page_limit=page_limit)
        self.logger.info("Extraction complete | endpoint=/encounters")

    def fetch_observations(
        self,
        encounter_id: int | None = None,
        observation_type: str | None = None,
        page_limit: int = 500,
    ):
        """Generator — yields one page of observation records at a time."""
        params: dict = {}
        if encounter_id is not None:
            params["encounter_id"] = encounter_id
        if observation_type is not None:
            params["observation_type"] = observation_type

        self.logger.info(
            "Starting extraction | endpoint=/observations | filters=%s",
            params or "none",
        )
        yield from self._paginate("/observations", base_params=params, page_limit=page_limit)
        self.logger.info("Extraction complete | endpoint=/observations")


# Database Load

def load_patients(engine, pages) -> int:
    logger = logging.getLogger("pipeline")
    total = 0
    with engine.begin() as conn:
        for page in pages:
            if not page:
                continue
            stmt = pg_insert(patients_table).values(page)
            stmt = stmt.on_conflict_do_nothing(index_elements=["patient_id"])
            conn.execute(stmt)
            total += len(page)
            logger.debug("Patients upserted | count=%d", len(page))
    return total


def load_encounters(engine, pages) -> int:
    logger = logging.getLogger("pipeline")
    total = 0
    with engine.begin() as conn:
        for page in pages:
            if not page:
                continue
            stmt = pg_insert(encounters_table).values(page)
            stmt = stmt.on_conflict_do_nothing(index_elements=["encounter_id"])
            conn.execute(stmt)
            total += len(page)
            logger.debug("Encounters upserted | count=%d", len(page))
    return total


def load_observations(engine, pages) -> int:
    logger = logging.getLogger("pipeline")
    total = 0
    with engine.begin() as conn:
        for page in pages:
            if not page:
                continue
            stmt = pg_insert(observations_table).values(page)
            stmt = stmt.on_conflict_do_nothing(index_elements=["observation_id"])
            conn.execute(stmt)
            total += len(page)
            logger.debug("Observations upserted | count=%d", len(page))
    return total


# Entry point — full pipeline run

if __name__ == "__main__":
    logger = setup_logging()

    pipeline_start = datetime.now()
    today = date.today().isoformat()

    logger.info("=" * 60)
    logger.info("Pipeline START | timestamp=%s", pipeline_start.isoformat())
    logger.info("=" * 60)

    engine = get_engine()
    client = HealthcareAPIClient()

    try:
        # --- Patients: full load (dimension table, rarely changes) ---
        patient_total = load_patients(engine, client.fetch_patients())
        logger.info("Patients load finished | total_records=%d", patient_total)

        # --- Encounters: incremental load driven by watermark ---
        watermark = read_watermark()
        if watermark:
            logger.info("Incremental load | fetching encounters since %s", watermark)
        else:
            logger.info("Full load | no watermark found, fetching all encounters")

        encounter_total = load_encounters(
            engine,
            client.fetch_encounters(start_date=watermark)
        )
        logger.info("Encounters load finished | total_records=%d", encounter_total)

        # --- Observations: full load (high-volume fact table) ---
        observation_total = load_observations(engine, client.fetch_observations())
        logger.info("Observations load finished | total_records=%d", observation_total)

        # --- Update watermark only on full success ---
        write_watermark(today)

    except (requests.exceptions.HTTPError,
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError) as exc:
        logger.error("Pipeline aborted due to HTTP error: %s", exc)
        logger.warning("Watermark NOT updated due to pipeline failure.")
        raise

    except Exception as exc:
        logger.error("Pipeline aborted due to unexpected error: %s", exc)
        logger.warning("Watermark NOT updated due to pipeline failure.")
        raise

    finally:
        pipeline_end = datetime.now()
        duration = (pipeline_end - pipeline_start).total_seconds()
        logger.info("=" * 60)
        logger.info(
            "Pipeline END | timestamp=%s | duration=%.2fs",
            pipeline_end.isoformat(), duration,
        )
        logger.info("=" * 60)
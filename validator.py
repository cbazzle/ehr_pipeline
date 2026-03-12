import logging
from collections import Counter

class DataValidator:

    def __init__(self):
        self.logger = logging.getLogger("pipeline")

    def check_duplicates(self, records: list, id_field: str) -> bool:
        counts = Counter(record[id_field] for record in records)
        duplicates = {id_val: count for id_val, count in counts.items() if count > 1}
    
        if duplicates:
            self.logger.error(
                "Duplicate check FAILED | field=%s | duplicate_ids=%s",
                id_field, list(duplicates.keys())
            )
            return False
    
        self.logger.info("Duplicate check PASSED | field=%s | total_records=%d", id_field, len(records))
        return True
    
    def check_referential_integrity(self, encounters: list, patients: list) -> bool:
        # A set is used here instead of a list because checking x in set is much faster than x in list for large datasets   
        patient_ids = {patient["patient_id"] for patient in patients}
        orphaned = [e["encounter_id"] for e in encounters if e["patient_id"] not in patient_ids]

        if orphaned:
            self.logger.error(
                "Referential integrity check FAILED | orphaned_encounter_ids=%s",
                orphaned
            )
            return False

        self.logger.info(
            "Referential integrity check PASSED | encounters=%d | patients=%d",
            len(encounters), len(patients)
        )
        return True

    def check_fan_out(self, before_count: int, after_count: int) -> bool:
        if before_count != after_count:
            self.logger.error(
                "Fan-out check FAILED | before=%d | after=%d",
                before_count, after_count
            )
            return False

        self.logger.info(
            "Fan-out check PASSED | count=%d",
            before_count
        )
        return True
    
#---------------------------------------------
# validator.py TEST

if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        level=logging.INFO,
    )

    # Sample test data
    patients = [
        {"patient_id": 1, "name": "Alice"},
        {"patient_id": 2, "name": "Bob"},
        {"patient_id": 3, "name": "Carol"},
    ]

    encounters = [
        {"encounter_id": 1, "patient_id": 1},
        {"encounter_id": 2, "patient_id": 2},
        {"encounter_id": 3, "patient_id": 3},
    ]

validator = DataValidator()

validator.check_duplicates(patients, "patient_id")
validator.check_duplicates(encounters, "encounter_id")
validator.check_referential_integrity(encounters, patients)
validator.check_fan_out(len(patients), len(patients))
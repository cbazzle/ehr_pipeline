import random
from datetime import timedelta

from faker import Faker

fake = Faker()
Faker.seed(42)
random.seed(42)

db = {"patients": [], "encounters": [], "observations": []}


def generate_data(num_patients: int = 200):
    encounter_id_counter = 1
    observation_id_counter = 1

    # ICD-10 diagnosis codes
    diagnoses = [
        "J01.90 (Acute sinusitis)",
        "I10 (Hypertension)",
        "E11.9 (Type 2 Diabetes)",
        "J45.909 (Asthma)",
    ]
    observation_types = ["heart_rate", "blood_pressure", "temperature_f"]

    for patient_id in range(1, num_patients + 1):
        dob = fake.date_of_birth(minimum_age=18, maximum_age=90)
        db["patients"].append(
            {
                "patient_id": patient_id,
                "first_name": fake.first_name(),
                "last_name": fake.last_name(),
                "dob": dob.isoformat(),
                "gender": random.choice(["M", "F", "Other"]),
                "state": fake.state_abbr(),
            }
        )

        # Generate 1 to 5 Encounters per Patient
        for _ in range(random.randint(1, 5)):
            admission_date = fake.date_between(start_date="-2y", end_date="today")
            # Stay length between 0 (outpatient) and 14 days
            length_of_stay = random.randint(0, 14)
            discharge_date = admission_date + timedelta(days=length_of_stay)

            encounter = {
                "encounter_id": encounter_id_counter,
                "patient_id": patient_id,
                "admission_date": admission_date.isoformat(),
                "discharge_date": discharge_date.isoformat(),
                "facility_id": random.randint(100, 105),
                "diagnosis_code": random.choice(diagnoses),
            }
            db["encounters"].append(encounter)

            # Generate 2 to 10 Observations per Encounter
            for _ in range(random.randint(2, 10)):
                obs_date = admission_date + timedelta(
                    days=random.randint(0, length_of_stay)
                )
                obs_type = random.choice(observation_types)

                # Generate clinical values
                if obs_type == "heart_rate":
                    val = str(random.randint(60, 120))
                    unit = "bpm"
                elif obs_type == "blood_pressure":
                    systolic = random.randint(100, 160)
                    diastolic = random.randint(60, 100)
                    val = f"{systolic}/{diastolic}"
                    unit = "mmHg"
                else:  # temperature_f
                    val = str(round(random.uniform(97.0, 103.0), 1))
                    unit = "F"

                db["observations"].append(
                    {
                        "observation_id": observation_id_counter,
                        "encounter_id": encounter_id_counter,
                        "observation_date": obs_date.isoformat(),
                        "type": obs_type,
                        "value": val,
                        "unit": unit,
                    }
                )
                observation_id_counter += 1

            encounter_id_counter += 1


generate_data()

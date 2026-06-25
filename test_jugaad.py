from jugaad_data.nse import bhavcopy_save, bhavcopy_fo_save
from datetime import date
try:
    # try legacy
    bhavcopy_fo_save(date(2023, 1, 2), "/app")
    print("Legacy downloaded")
    # try new format
    bhavcopy_fo_save(date(2024, 8, 1), "/app")
    print("New downloaded")
except Exception as e:
    print(f"Exception: {e}")

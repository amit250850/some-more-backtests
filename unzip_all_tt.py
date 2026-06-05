import os
import glob
import zipfile
import pandas as pd

# Find all zip files
zips = glob.glob("/app/data/tradingtuitions/**/*.zip", recursive=True)
print(f"Found {len(zips)} zip files.")

os.makedirs("/app/data/tt_raw", exist_ok=True)

for i, z in enumerate(zips):
    try:
        with zipfile.ZipFile(z, 'r') as zip_ref:
            for file_info in zip_ref.infolist():
                if "NIFTY_F1" in file_info.filename or "NIFTY" in file_info.filename:
                    if file_info.filename.endswith('.txt') or file_info.filename.endswith('.csv'):
                        # Read directly from zip to avoid name collision
                        with zip_ref.open(file_info) as f:
                            df = pd.read_csv(f, header=None)
                            # Save with unique name
                            df.to_csv(f"/app/data/tt_raw/nifty_{i}_{os.path.basename(file_info.filename)}.csv", index=False, header=False)
    except Exception as e:
        print(f"Error reading zip {z}: {e}")

print("Extraction complete.")

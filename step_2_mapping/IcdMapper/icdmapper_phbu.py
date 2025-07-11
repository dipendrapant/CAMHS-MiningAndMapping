# Used https://finnkode.helsedirektoratet.no/phbu/chapter
import os
import sys

import mapped_icd_codes as a

parent_dir = os.path.join(os.path.dirname(os.path.abspath("")), os.pardir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
from importall import *

ICDMAPPER = os.getenv("ICDMAPPER")
excel_data = pd.read_excel(ICDMAPPER + "KodelistePHBU2025.xlsx")
kode_to_phbu_map = dict(zip(excel_data["kode"].astype(str), excel_data["phbu_tekst"]))

for key, value in a.mapped_icd_codes.items():
    if value == "Unknown" and key in kode_to_phbu_map:
        a.mapped_icd_codes[key] = kode_to_phbu_map[key]

print("Updated mapped_icd_codes:", a.mapped_icd_codes)

with open("updated_mapped_icd_codes.py", "w") as f:
    f.write("mapped_icd_codes = " + str(a.mapped_icd_codes))

# Project description:
We extract the data, preprocess it and map the records per patient, episode and contacts. And then we do descriptive analysis for the patient demographics profile across axes. Next we find most frequent diagnoses and medication per contact, the comrbities across axes, and map the corresponding observed prescribed medication (based on ATC) per diagnoses categories (based on ICD-10). Based on the preprocessed data the RKBU data analysis application allows users to filter the data by diagnoses codes, medication ATC codes, gender, age slider. Allowing user to view the distribution of demographics, most frequent medication diagnosis , view each individual patient trajectory.  
## Application

The following diagram shows some snapshot of the app:

![Snapshots 1](./RKBUStreamlitApp1.jpg)
![Snapshots 2](./RKBUStreamlitApp2.jpg)

## Setup

1. **Clone the repository** (if using Git):

   ```bash
   git clone https://github.com/dipendrapant/CAMHS-MiningAndMapping
   cd CAMHS-MiningAndMapping
   ```

2. **Create a virtual environment** (recommended):

   - Using `virtualenv`:
     ```bash
     virtualenv venv
     source venv/bin/activate      # On macOS/Linux
     ```
   - Or using Python’s built-in `venv`:
     ```bash
     python3 -m venv venv
     source venv/bin/activate      # On macOS/Linux
     ```

3. **Install dependencies**:

   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

## Usage

Run the application or scripts as needed. For example:

```bash
python /app/appv2.py
```

Adjust the command to match your project’s entry point.


**Project Structure**

```
CAMHS-MiningAndMapping/
├── app/                         # application
│   ├── appv2.py/
├── data/
├── step_1_export/                        # data extract
├── step_2_mapping/                  # clean, map ... data
│   ├── Atcmapper/          # for atc codes
│   ├── IcdMapper           # for icd codes
│   └── all_step_1_load_and_clean_data_opphold_diagnose.ipynb
├── step3/                          # Main analysis
│   ├── Summary/                    # Generate axis wise summary
│   └── all_axis_main_comorbidity_analysis.ipynb
│   └── all_axis_main_comorbidity_analysis.ipynb
│   └── all_axis_rq1_rq3_main_analysis.ipynb
│   └── import_all.py
├── .gitignore
└── readme.md
```

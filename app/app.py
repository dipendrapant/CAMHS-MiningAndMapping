import json
import math
import os
import sys
import warnings

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv
from updated_mapped_icd_codes import mapped_icd_codes

load_dotenv()

warnings.filterwarnings("ignore", category=pd.errors.DtypeWarning)


base = os.getenv("APP_INITIAL_DATA_PATH")
if not base:
    raise RuntimeError("Please set APP_INITIAL_DATA_PATH to your project root")
ATC_JSON_PATH = os.path.join(base, "P4_V5", "app", "atcnavn_code.json")

with open(ATC_JSON_PATH, "r", encoding="utf-8") as f:
    atc_mapping = json.load(f)
atc_map = {code: info.get("atcnavn", "Unknown") for code, info in atc_mapping.items()}


# -------------------------------------------------------------------------------
# File paths
# -------------------------------------------------------------------------------
FIRST_DATA_PATH = base + "/data/patients_axis1_primary_medicated"
AXIS1_DATA_PATH = base + "/P4_V3/data/v2axis1_primary_medicated"
SECOND_DATA_PATH = base + "/data/patients_axis2_primary_medicated"
AXIS2_DATA_PATH = base + "/P4_V3/data/v2axis2_primary_medicated"
THIRD_DATA_PATH = base + "/data/patients_axis3_primary_medicated"
AXIS3_DATA_PATH = base + "/P4_V3/data/v2axis3_primary_medicated"

# -------------------------------------------------------------------------------
# Mapping dictionaries for Summary section
# -------------------------------------------------------------------------------
morrelasj_mapping = {
    0: "Not Specified:0",
    1: "Biologisk mor",
    2: "Biologisk far",
    3: "Adoptivmor",
    4: "Adoptivfar",
    5: "Stemor",
    7: "Fostermor",
    8: "Fosterfar",
    9: "Søsken",
    10: "Annet",
    11: "Ektefelle/Samboer",
    250: "Not Specified:250",
    255: "Not Specified:255",
}
farrelasj_mapping = {
    0: "Not Specified:0",
    1: "Biologisk mor",
    2: "Biologisk far",
    3: "Adoptivmor",
    4: "Adoptivfar",
    5: "Stemor",
    6: "Stefar",
    7: "Fostermor",
    8: "Fosterfar",
    10: "Annet",
    11: "Ektefelle/Samboer",
    23: "Not Specified:23",
    25: "Not Specified:25",
    254: "Not Specified:254",
    255: "Not Specified:255",
}
etnisk_mapping = {
    0: "Not Specified:0",
    1: "Norsk",
    2: "Samisk",
    3: "Nordisk",
    4: "Europeisk",
    5: "Asiatisk",
    6: "Afrikansk",
    7: "Latin-Amerikansk",
    8: "Nord-Amerikansk",
    9: "Australsk",
}
hjemmesprk_mapping = {
    0: "Not Specified:0",
    1: "Norsk",
    2: "Annet hjemmespråk",
    3: "To-språklig",
}
gender_mapping = {0: "Unspecified", 1: "Female", 2: "Male"}


# -------------------------------------------------------------------------------
# Caching data loads
# -------------------------------------------------------------------------------
@st.cache_data
def load_summary_data(path: str) -> pd.DataFrame:
    df = pd.read_parquet(path)
    for col in [
        "atckode",
        "atcnavn",
        "sak_kjonn",
        "morrelasj",
        "farrelasj",
        "etniskmor",
        "etniskfar",
        "hjemmesprk",
    ]:
        if col in df.columns:
            df[col] = df[col].astype("category")
    return df


@st.cache_data
def load_axis1_data(path: str) -> pd.DataFrame:
    cols = [
        "pasient_nr",
        "sak_nr",
        "sak_kjonn",
        "patient_age",
        "sak_igangdato",
        "sak_avsldato",
        "diag_diagnose",
        "diag_akse",
        "diag_hoved",
        "opphold_id",
        "opphold_start_date",
        "opphold_end_date",
        "atckode",
        "atcnavn",
        "patient_diagnose_age",
    ]
    df = pd.read_parquet(path, columns=cols)
    for c in [
        "diag_diagnose",
        "diag_akse",
        "diag_hoved",
        "atckode",
        "atcnavn",
        "sak_kjonn",
    ]:
        if c in df.columns:
            df[c] = df[c].astype("category")
    return df


# -------------------------------------------------------------------------------
# Plotting functions
# -------------------------------------------------------------------------------
@st.cache_data
def plot_patient_trajectory_by_contact(df: pd.DataFrame) -> go.Figure:
    df = df.copy()
    # parse dates
    for d in [
        "opphold_start_date",
        "opphold_end_date",
        "sak_igangdato",
        "sak_avsldato",
    ]:
        df[d] = pd.to_datetime(df[d], errors="coerce")
    # durations and ages
    df["duration_yrs"] = (
        df["opphold_end_date"] - df["opphold_start_date"]
    ).dt.days / 365.0
    df["age_start"] = df["patient_age"] + (
        (df["opphold_start_date"] - df["sak_igangdato"]).dt.days / 365.0
    ).fillna(0)
    df["age_end"] = df["age_start"] + df["duration_yrs"]
    # hover text with mapped ICD
    df["hover"] = df.apply(
        lambda r: (
            f"ID {int(r.pasient_nr)} | Case {int(r.sak_nr)}<br>"
            f"Contact {r.opphold_id}: {r.opphold_start_date.date()}–{r.opphold_end_date.date()}<br>"
            f"ICD {r.diag_diagnose}: {mapped_icd_codes.get(str(r.diag_diagnose),'Unknown')}<br>"
            f"ATC {r.atckode}: {r.atcnavn}"
        ),
        axis=1,
    )
    # Y positioning
    pats = np.sort(df["pasient_nr"].unique())
    ymap = {p: i for i, p in enumerate(pats)}
    df["y"] = df["pasient_nr"].map(ymap)
    # lines
    n = len(df)
    x_line = np.empty(3 * n)
    y_line = np.empty(3 * n)
    x_line[0::3], x_line[1::3], x_line[2::3] = df["age_start"], df["age_end"], np.nan
    y_line[0::3], y_line[1::3], y_line[2::3] = df["y"], df["y"], np.nan
    trace_lines = go.Scatter(
        x=x_line, y=y_line, mode="lines", line=dict(width=4), hoverinfo="skip"
    )
    trace_markers = go.Scatter(
        x=(df["age_start"] + df["age_end"]) / 2,
        y=df["y"],
        mode="markers",
        marker=dict(size=8),
        text=df["hover"],
        hovertemplate="%{text}",
        hoverlabel=dict(align="left"),
    )
    fig = go.Figure([trace_lines, trace_markers])
    fig.update_layout(
        title="Patient Trajectory by Contact",
        xaxis_title="Age (years)",
        yaxis=dict(tickvals=list(ymap.values()), ticktext=[str(int(p)) for p in pats]),
        height=600,
    )
    return fig


# -------------------------------------------------------------------------------
# App UI
# -------------------------------------------------------------------------------
st.set_page_config(page_title="RKBU Data Analytics Tool", layout="wide")
st.title("RKBU Data Analytics Tool")

tabs = st.tabs(
    [
        "Axis 1 Summary",
        "Axis 1 data",
        "Axis 2 Summary",
        "Axis 2 data",
        "Axis 3 Summary",
        "Axis 3 data",
    ]
)


# Axis 1 Summary
def axis_summary(tab, data_path, prefix):
    st.header(f"Summary: Patient Profile Distributions / Pasientprofildistribusjoner")
    df_summary = load_summary_data(data_path)
    with st.expander("Filter Options / Filteralternativer", expanded=False):
        apply_icd = st.checkbox(
            "Apply ICD Filter / Bruk ICD-kodefilter",
            value=True,
            key=f"{prefix}_apply_icd",
        )
        icd_in = None
        if apply_icd:
            codes = sorted(
                {
                    str(c)
                    for c in df_summary.filter(regex="^sak_icd").values.flatten()
                    if pd.notna(c)
                }
            )
            icd_in = st.selectbox(
                "Select ICD Code / Velg ICD-kode:",
                [""] + codes,
                key=f"{prefix}_icd_sbox",
            )
        apply_atc = st.checkbox(
            "Apply ATC Filter / Bruk ATC-kodefilter", key=f"{prefix}_apply_atc"
        )
        atc_in = None
        if apply_atc:
            m = dict(df_summary[["atckode", "atcnavn"]].drop_duplicates().values)
            atc_in = st.selectbox(
                "Select ATC Code / Velg ATC-kode:",
                ["All"] + sorted(m.keys()),
                key=f"{prefix}_atc_sbox",
            )
        apply_gen = st.checkbox(
            "Apply Gender Filter / Bruk kjønnsfilter", key=f"{prefix}_apply_gen"
        )
        gen_val = None
        if apply_gen:
            sel = st.selectbox(
                "Select Gender / Velg kjønn:",
                ["All"] + list(gender_mapping.values()),
                key=f"{prefix}_gen_sbox",
            )
            if sel != "All":
                gen_val = [k for k, v in gender_mapping.items() if v == sel][0]
        apply_age = st.checkbox(
            "Apply Age Filter / Bruk aldersfilter", key=f"{prefix}_apply_age"
        )
        age_rng = None
        if apply_age:
            age_rng = st.slider(
                "Select Age Range / Velg aldersintervall:",
                0.0,
                18.999999,
                (0.0, 18.999999),
                step=0.5,
                key=f"{prefix}_age_sld",
            )
    df2 = df_summary.copy()
    if apply_icd and icd_in:
        df2 = df2[df2.filter(regex="^sak_icd").eq(icd_in).any(axis=1)]
    if apply_atc and atc_in != "All":
        df2 = df2[df2["atckode"] == atc_in]
    if apply_gen and gen_val is not None:
        df2 = df2[df2["sak_kjonn"] == gen_val]
    if apply_age and age_rng:
        df2 = df2[
            (df2["patient_age"] >= age_rng[0]) & (df2["patient_age"] <= age_rng[1])
        ]
    profiles = df2.drop_duplicates(subset=["pasient_nr"]).copy()
    profiles["Gender"] = profiles["sak_kjonn"].cat.rename_categories(gender_mapping)
    profiles["Mother Relationship"] = profiles["morrelasj"].map(morrelasj_mapping)
    profiles["Father Relationship"] = profiles["farrelasj"].map(farrelasj_mapping)
    profiles["Mother Ethnicity"] = profiles["etniskmor"].map(etnisk_mapping)
    profiles["Father Ethnicity"] = profiles["etniskfar"].map(etnisk_mapping)
    profiles["Home Language"] = profiles["hjemmesprk"].map(hjemmesprk_mapping)
    opts = [
        "Age Distribution",
        "Gender Distribution",
        "Mother Relationship",
        "Father Relationship",
        "Mother Ethnicity",
        "Father Ethnicity",
        "Home Language",
    ]
    sel = st.multiselect(
        "Select demographics to display / Velg demografi:",
        opts,
        default=["Age Distribution", "Gender Distribution"],
        key=f"{prefix}_msel",
    )
    if "Age Distribution" in sel:
        st.plotly_chart(
            px.histogram(
                profiles,
                x="patient_age",
                nbins=20,
                title="Age Distribution (Unique Patients)",
            ),
            use_container_width=True,
        )
    if "Gender Distribution" in sel:
        cnt = profiles["Gender"].value_counts().reset_index()
        cnt.columns = ["Gender", "Count"]
        st.plotly_chart(
            px.pie(cnt, names="Gender", values="Count", title="Gender Distribution"),
            use_container_width=True,
        )
    for field, title in [
        ("Mother Relationship", "Mother Relationship Distribution"),
        ("Father Relationship", "Father Relationship Distribution"),
        ("Mother Ethnicity", "Mother Ethnicity Distribution"),
        ("Father Ethnicity", "Father Ethnicity Distribution"),
        ("Home Language", "Home Language Distribution"),
    ]:
        if field in sel:
            cnt = profiles[field].value_counts().reset_index()
            cnt.columns = [field.replace(" ", "_"), "Count"]
            st.plotly_chart(
                px.pie(cnt, names=field.replace(" ", "_"), values="Count", title=title),
                use_container_width=True,
            )


# Axis 1 Summary
with tabs[0]:
    axis_summary(tabs[0], FIRST_DATA_PATH, "axis1_summary")
# Axis 2 Summary
with tabs[2]:
    axis_summary(tabs[2], SECOND_DATA_PATH, "axis2_summary")
# Axis 3 Summary
with tabs[4]:
    axis_summary(tabs[4], THIRD_DATA_PATH, "axis3_summary")


# Generic Analysis Tab
def axis_analysis(tab, load_func, data_path, prefix):
    st.header(f"{prefix} Analysis")
    df1 = load_func(data_path)
    with st.expander("Filter Options", expanded=False):
        apply_icd = st.checkbox(
            "Apply ICD Filter", value=True, key=f"{prefix}_apply_icd"
        )
        icd1 = None
        if apply_icd:
            icds = sorted(df1["diag_diagnose"].cat.categories)
            icd1 = st.selectbox(
                "Select ICD Code", [""] + icds, key=f"{prefix}_icd_sbox"
            )
        apply_atc = st.checkbox("Apply ATC Filter", key=f"{prefix}_apply_atc")
        atc1 = None
        if apply_atc:
            m1 = dict(df1[["atckode", "atcnavn"]].drop_duplicates().values)
            atc1 = st.selectbox(
                "Select ATC Code", ["All"] + sorted(m1.keys()), key=f"{prefix}_atc_sbox"
            )
        apply_gen = st.checkbox("Apply Gender Filter", key=f"{prefix}_apply_gen")
        g1 = None
        if apply_gen:
            sel1 = st.selectbox(
                "Select Gender",
                ["All"] + list(gender_mapping.values()),
                key=f"{prefix}_gen_sbox",
            )
            if sel1 != "All":
                g1 = [k for k, v in gender_mapping.items() if v == sel1][0]
        apply_age = st.checkbox("Apply Age Filter", key=f"{prefix}_apply_age")
        age1 = None
        if apply_age:
            age1 = st.slider(
                "Select Age Range",
                0.0,
                100.0,
                (0.0, 100.0),
                1.0,
                key=f"{prefix}_age_sld",
            )
    df2 = df1.copy()
    if apply_icd and icd1:
        df2 = df2[df2["diag_diagnose"] == icd1]
    if apply_atc and atc1 != "All":
        df2 = df2[df2["atckode"] == atc1]
    if apply_gen and g1 is not None:
        df2 = df2[df2["sak_kjonn"] == g1]
    if apply_age and age1:
        df2 = df2[(df2["patient_age"] >= age1[0]) & (df2["patient_age"] <= age1[1])]
    st.subheader("Patient Overview")
    st.write(
        f"{prefix} Patients: {df2['pasient_nr'].nunique()} | Episodes: {df2['sak_nr'].nunique()} | Contacts: {df2['opphold_id'].nunique()}"
    )
    st.subheader("Distribution of Contacts per Patient")
    dist_df = (
        (df2.groupby("pasient_nr")["opphold_id"].nunique().reset_index(name="n_eps"))
        .groupby("n_eps")
        .size()
        .reset_index(name="n_patients")
    )
    st.plotly_chart(
        px.bar(
            dist_df,
            x="n_eps",
            y="n_patients",
            labels={"n_eps": "Contacts", "n_patients": "Patients"},
            title="Contacts per Patient",
        ),
        use_container_width=True,
    )
    st.subheader("Diagnosis Table")
    diag_counts = (
        df2.groupby(["diag_diagnose", "diag_akse"], observed=True)
        .agg(
            patient_count=("pasient_nr", "nunique"),
            contact_count=("opphold_id", "nunique"),
        )
        .reset_index()
    )
    st.dataframe(diag_counts)
    st.subheader("ATC Table")
    atc_counts = (
        df2.groupby("atckode", observed=True)
        .agg(
            patient_count=("pasient_nr", "nunique"),
            contact_count=("opphold_id", "nunique"),
            ATC_Name=("atcnavn", "first"),
        )
        .reset_index()
    )
    st.dataframe(atc_counts)
    st.subheader("Primary Diagnoses per Contacts")
    prim = df2[df2["diag_hoved"] == "1"][
        ["pasient_nr", "opphold_id", "diag_diagnose"]
    ].copy()
    prim["diag_name"] = prim["diag_diagnose"].astype(str)
    prim_grouped = (
        prim.groupby(["pasient_nr", "opphold_id"])
        .agg(
            diagnoses=("diag_diagnose", lambda x: ", ".join(sorted(set(x)))),
            names=("diag_name", lambda x: ", ".join(sorted(set(x)))),
        )
        .reset_index()
    )
    st.dataframe(prim_grouped)
    st.subheader("Patient Trajectory by Contact")
    required = {
        "pasient_nr",
        "sak_nr",
        "patient_age",
        "sak_igangdato",
        "sak_avsldato",
        "diag_diagnose",
        "diag_akse",
        "diag_hoved",
        "atckode",
        "atcnavn",
        "opphold_id",
        "opphold_start_date",
        "opphold_end_date",
    }
    if not df2.empty and required.issubset(df2.columns):
        pids = sorted(df2["pasient_nr"].unique())
        if f"{prefix}_rand" not in st.session_state or set(
            st.session_state[f"{prefix}_rand"]
        ) != set(pids):
            st.session_state[f"{prefix}_rand"] = list(np.random.permutation(pids))
        page = st.number_input(
            "Page", 1, math.ceil(len(pids) / 20), 1, key=f"{prefix}_page"
        )
        sel = st.session_state[f"{prefix}_rand"][(page - 1) * 20 : page * 20]
        sub = df2[df2["pasient_nr"].isin(sel)]
        st.plotly_chart(
            plot_patient_trajectory_by_contact(sub), use_container_width=True
        )
    else:
        st.write("No trajectory data available.")


# Axis 1 Data
with tabs[1]:
    axis_analysis(tabs[1], load_axis1_data, AXIS1_DATA_PATH, "Axis 1")
# Axis 2 Data
with tabs[3]:
    axis_analysis(tabs[3], load_axis1_data, AXIS2_DATA_PATH, "Axis 2")
# Axis 3 Data
with tabs[5]:
    axis_analysis(tabs[5], load_axis1_data, AXIS3_DATA_PATH, "Axis 3")

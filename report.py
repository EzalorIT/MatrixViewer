import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder
import json
import os

st.set_page_config(layout="wide")
st.title("🧠 Goofball Labs App Usage Matrix Transposer")

FILTER_DIR = "saved_filters"
PAGE_SIZE = 10
DEFAULT_CSV = "output.csv"
DEFAULT_FILTER_FILE = "Default Filter.json"
os.makedirs(FILTER_DIR, exist_ok=True)

st.sidebar.header("📤 Upload CSV File")
uploaded_file = st.sidebar.file_uploader("Upload a large CSV file", type=["csv"])

@st.cache_resource
def load_large_csv(file):
    df = pd.read_csv(file, low_memory=False)
    df.columns = df.columns.str.strip().str.replace("\u200b", "").str.replace("﻿", "")
    return df

try:
    if uploaded_file is not None:
        df_raw = load_large_csv(uploaded_file)
        st.sidebar.success("✅ Uploaded file loaded successfully.")
    else:
        st.sidebar.warning("⚠️ No file uploaded. Using default file.")
        df_raw = load_large_csv(DEFAULT_CSV)
except Exception as e:
    st.error(f"❌ Failed to load CSV: {e}")
    st.stop()

st.sidebar.info(f"📊 {len(df_raw):,} rows")
st.sidebar.info(f"🧠 Memory use: {df_raw.memory_usage(deep=True).sum() / (1024**2):.2f} MB")

if "Name" not in df_raw.columns or "Username" not in df_raw.columns:
    st.error("❌ CSV must contain at least 'Name' and 'Username' columns.")
    st.stop()

user_columns = [
    "Name", "LatestVersion", "Hostname", "Username", "CaughtInProcess", "FileSource",
    "PackagedAppMatch", "PackagedAppMatchScore", "PackagedAppCompatible", "WingetMatchName",
    "WingetMatchScore", "WingetCompatible", "IsNoise", "Category"
]
user_columns = [col for col in user_columns if col in df_raw.columns]

if "clauses" not in st.session_state:
    st.session_state.clauses = [{"logic": "AND", "fields": []}]

# 📂 Filter Management
st.sidebar.header("📂 Filter Management")
saved_files = [f for f in os.listdir(FILTER_DIR) if f.endswith(".json")]

# Auto-load Default Filter
if "clauses_loaded" not in st.session_state and DEFAULT_FILTER_FILE in saved_files:
    try:
        with open(os.path.join(FILTER_DIR, DEFAULT_FILTER_FILE), "r") as f:
            loaded = json.load(f)
            st.session_state.clauses = loaded.get("clauses", [])
            st.session_state.clauses_loaded = True
            st.sidebar.info(f"✅ Loaded default filter: {DEFAULT_FILTER_FILE}")
    except Exception as e:
        st.sidebar.warning(f"⚠️ Failed to load default filter: {e}")

selected_template = st.sidebar.selectbox("📜 Load Saved Filter", ["-- Select --"] + saved_files)
if selected_template != "-- Select --":
    try:
        with open(os.path.join(FILTER_DIR, selected_template), "r") as f:
            loaded = json.load(f)
            st.session_state.clauses = loaded.get("clauses", [])
            st.sidebar.success(f"✅ Loaded {selected_template}")
    except Exception as e:
        st.sidebar.error(f"❌ Failed to load filters: {e}")

custom_name = st.sidebar.text_input("📝 Filter Name to Save", value="my_filters")
if st.sidebar.button("💾 Save Filters"):
    filename = os.path.join(FILTER_DIR, f"{custom_name}.json")
    filters_to_save = {"clauses": st.session_state.get("clauses", [])}
    with open(filename, "w") as f:
        json.dump(filters_to_save, f, indent=2)
    st.sidebar.success(f"✅ Saved as {custom_name}.json")

# 🧩 Clause Builder
st.sidebar.header("🧩 Clause Groups")

if st.sidebar.button("➕ Add Clause Group"):
    st.session_state.clauses.append({"logic": "AND", "fields": []})

for c_idx, clause in enumerate(st.session_state.clauses):
    st.sidebar.markdown(f"---\n**Clause Group {c_idx + 1}**")
    clause["logic"] = st.sidebar.radio(
        f"Combine fields with", ["AND", "OR"],
        index=["AND", "OR"].index(clause["logic"]),
        key=f"clause_logic_{c_idx}"
    )

    new_field = st.sidebar.selectbox("Field", user_columns, key=f"new_field_{c_idx}")
    new_type = st.sidebar.radio("Type", ["Multiselect", "Regex"], key=f"new_type_{c_idx}")

    if new_type == "Multiselect":
        values = sorted(df_raw[new_field].dropna().astype(str).unique())
        new_vals = st.sidebar.multiselect("Values", values, key=f"new_vals_{c_idx}")
    else:
        new_regex = st.sidebar.text_input("Regex", key=f"new_regex_{c_idx}")

    if st.sidebar.button(f"Add Field Filter to Clause {c_idx + 1}", key=f"add_filter_{c_idx}"):
        new_filter = {"field": new_field, "type": new_type}
        if new_type == "Multiselect":
            new_filter["values"] = new_vals
        else:
            new_filter["regex"] = new_regex
        clause["fields"].append(new_filter)

    if clause["fields"]:
        st.sidebar.markdown("Current filters:")
        for f in clause["fields"]:
            val_display = f.get("values") if f["type"] == "Multiselect" else f.get("regex", "")
            st.sidebar.markdown(f"- `{f['field']}` ({f['type']}): {val_display}")

if len(st.session_state.clauses) > 1:
    if st.sidebar.button("➖ Remove Last Clause Group"):
        st.session_state.clauses.pop()

outer_logic = st.sidebar.radio("Combine Clause Groups with", ["AND", "OR"], key="outer_logic")

# 🔍 Apply Filters
clauses = []
for clause in st.session_state.clauses:
    sub_conditions = []
    for f in clause["fields"]:
        field = f.get("field")
        typ = f.get("type")
        if typ == "Multiselect":
            values = f.get("values", [])
            if values:
                sub_conditions.append(df_raw[field].astype(str).isin(values))
        elif typ == "Regex":
            regex = f.get("regex", "")
            if regex:
                sub_conditions.append(df_raw[field].astype(str).str.contains(rf"{regex}", regex=True, na=False))
    if sub_conditions:
        if clause["logic"] == "AND":
            sub_mask = pd.Series(True, index=df_raw.index)
            for cond in sub_conditions:
                sub_mask &= cond
        else:
            sub_mask = pd.Series(False, index=df_raw.index)
            for cond in sub_conditions:
                sub_mask |= cond
        clauses.append(sub_mask)

if clauses:
    if outer_logic == "AND":
        mask = pd.Series(True, index=df_raw.index)
        for c in clauses:
            mask &= c
    else:
        mask = pd.Series(False, index=df_raw.index)
        for c in clauses:
            mask |= c
    df = df_raw[mask]
else:
    df = df_raw.copy()

# 🧾 Pivot Matrix
pivot = pd.crosstab(df["Username"], df["Name"])
matrix = pivot.applymap(lambda x: "Yes" if x > 0 else "No")

# 📄 Column Pagination
if "col_page" not in st.session_state:
    st.session_state.col_page = 0

col_total_pages = (len(matrix.columns) + PAGE_SIZE - 1) // PAGE_SIZE
col1, col2, col3 = st.columns([1, 3, 1])
with col1:
    if st.button("⬅️ Prev Apps") and st.session_state.col_page > 0:
        st.session_state.col_page -= 1
with col3:
    if st.button("Next Apps ➡️") and st.session_state.col_page < col_total_pages - 1:
        st.session_state.col_page += 1

col_start = st.session_state.col_page * PAGE_SIZE
col_end = col_start + PAGE_SIZE
visible_columns = list(matrix.columns[col_start:col_end])
df_view = matrix[visible_columns].copy()
df_view.insert(0, "Username", matrix.index)

# ✅ Enhanced display with total apps
st.markdown(f"**Page {st.session_state.col_page + 1}/{col_total_pages}**")
st.markdown(f"**Showing {len(df_view):,} users and {len(visible_columns)} apps of Total Apps {len(matrix.columns):,}**")

# 📊 AgGrid
gb = GridOptionsBuilder.from_dataframe(df_view)
gb.configure_default_column(filter=True, resizable=True, sortable=True)
gb.configure_column("Username", pinned="left")

AgGrid(
    df_view,
    gridOptions=gb.build(),
    height=700,
    fit_columns_on_grid_load=False,
    enable_enterprise_modules=True
)

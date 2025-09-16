import streamlit as st
import pandas as pd
import sqlite3
from io import BytesIO

st.title("Timesheet Automation Task 1: Timesheets Data Preparation & Feature Engineering")

# Upload 3 CSV/Excel tables
t1 = st.file_uploader("Upload Export file (CSV or Excel)", type=["csv", "xlsx"])
t2 = st.file_uploader("Upload Master data file (CSV or Excel)", type=["csv", "xlsx"])
t3 = st.file_uploader("Upload Mentors file (CSV or Excel)", type=["csv", "xlsx"])

if t1 and t2 and t3:
    # Helper function to load CSV/Excel
    def load_file(f):
        return pd.read_excel(f) if f.name.endswith("xlsx") else pd.read_csv(f)

    # Load all 3 files
    df1, df2, df3 = load_file(t1), load_file(t2), load_file(t3)

    # Create SQLite in-memory DB
    conn = sqlite3.connect(":memory:")
    df1.to_sql("table1", conn, index=False, if_exists="replace")
    df2.to_sql("table2", conn, index=False, if_exists="replace")
    df3.to_sql("table3", conn, index=False, if_exists="replace")

    # SQL Query
    query = """
    WITH base1 AS (
    SELECT
        CONCAT(TRIM("Student first"), ' ', TRIM("Student last")) AS "Student Full Name",
        TRIM("Entry label") AS "Entry Label",
        TRIM("Date") AS "Date",
        CAST(TRIM("Duration in minutes") AS INT) AS "Duration in minutes",
        CAST(TRIM("Duration in hours") AS FLOAT) AS "Duration in hours",
        TRIM("Billable") AS "Billable / Non Billable",
        '' AS "Category",
        TRIM("Logged by") AS "Logged by",
        '' AS "Audit Remark",
        '' AS "TL Remark"
    FROM table1
),
base2 AS (
    SELECT t2."ADEK Applicant ID" AS "PS Number", b1.*
    FROM base1 b1
    LEFT JOIN table2 t2
        ON LOWER(b1."Student Full Name") = LOWER(TRIM(t2."Student Name"))
),
base3 AS (
    SELECT b2.*, t3."Team Lead"
    FROM base2 b2
    LEFT JOIN table3 t3
        ON LOWER(b2."Logged by") = LOWER(t3."Mentor")
),
base4 AS (SELECT
    CASE
        WHEN "Student Full Name" LIKE '%Additional Hour%' THEN 'Administrative Profile'
        ELSE "PS Number"
    END AS "PS Number",
    CASE
        WHEN "Student Full Name" LIKE '%Additional Hour%' THEN 'Non Billable'
        ELSE "Billable / Non Billable"
    END AS "Billable / Non Billable",
    CASE
        WHEN "Student Full Name" LIKE '%Additional Hour%' THEN 'Administrative Task'
        ELSE "Category"
    END AS "Category",
    "Student Full Name",
    "Entry Label",
    "Date",
    "Duration in minutes",
    "Duration in hours",
    "Logged by",
    "Audit Remark",
    "TL Remark",
    "Team Lead"
    FROM base3)

SELECT "PS Number",
"Student Full Name",
"Entry Label",
"Date",
"Duration in minutes",
"Duration in hours",
"Billable / Non Billable",
"Category",
"Logged by",
"Team Lead",
"Audit Remark",
"TL Remark"
FROM base4;

    """

    # Run query
    result_df = pd.read_sql_query(query, conn)

    st.subheader("Transformed Result")
    st.dataframe(result_df)

    # Create Excel file in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        result_df.to_excel(writer, index=False, sheet_name="Data")

    excel_data = output.getvalue()

    # Download button for Excel
    st.download_button(
        label="📥 Download Result as Excel",
        data=excel_data,
        file_name="Task 2 Input.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

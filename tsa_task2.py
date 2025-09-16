import streamlit as st
import pandas as pd
import sqlite3
from io import BytesIO

st.title("Timesheet Automation Task 2: Preliminary Validation & Audit Checks")

# Upload 2 CSV/Excel tables
t1 = st.file_uploader("Upload Task 2 Input file (CSV or Excel)", type=["csv", "xlsx"])
t2 = st.file_uploader("Upload last month's Monthly Progress Report (CSV or Excel)", type=["csv", "xlsx"])

if t1 and t2:
    # Helper function to load CSV/Excel
    def load_file(f):
        return pd.read_excel(f) if f.name.endswith("xlsx") else pd.read_csv(f)

    # Load all 2 files
    df1, df2 = load_file(t1), load_file(t2)

    # Create SQLite in-memory DB
    conn = sqlite3.connect(":memory:")
    df1.to_sql("table1", conn, index=False, if_exists="replace")
    df2.to_sql("table2", conn, index=False, if_exists="replace")

    # SQL Query
    query = """
WITH base1 AS (
        SELECT *
        FROM table1
        WHERE LENGTH("Entry Label") > 0 OR "Duration in minutes" <> 0),
base2 AS (SELECT *
        FROM base1
        WHERE CAST(STRFTIME('%m', "Date") AS INT) = CAST(STRFTIME('%m', DATE('now', '-1 month')) AS INT)),
base3 AS (SELECT *
    FROM base2
    WHERE "Logged by" IN ('Claire Mangrum', 'Dr Fauzia Hasan Siddiqui', 'Dr. Rubi Garcha', 'Allison Houston', 'Erin Nelson', 'Thoywell Hemmings', 'Rakhshan Sharif')
    OR LOWER("Entry Label") NOT LIKE '%timesheet%'),
base4 AS (SELECT "PS Number",
        "Student Full Name",
        "Entry Label",
        "Date",
        "Duration in minutes",
        "Duration in hours",
        "Billable / Non Billable",
        "Category",
        "Logged by",
        "Team Lead",
         CASE WHEN LOWER("Entry Label") LIKE '%june%' 
             OR LOWER("Entry Label") LIKE '%july%' 
             OR LOWER("Entry Label") LIKE '%september%' THEN "Task pertaining to previous or next month will not be paid"
            WHEN "Duration in hours" > 12 THEN "Please rectify the AM/PM Error"
            ELSE "Audit Remark" END AS "Audit Remark",
        "TL Remark"
        FROM base3),
base5 AS (SELECT CASE WHEN "Logged by" IN ('Claire Mangrum', 'Dr Fauzia Hasan Siddiqui', 'Dr. Rubi Garcha', 'Allison Houston', 'Erin Nelson', 'Thoywell Hemmings', 'Rakhshan Sharif') 
        THEN ("Logged by" || ' - Administrative Profile')
        ELSE "PS Number" END AS "PS Number",
        "Student Full Name",
        "Entry Label",
        "Date",
        "Duration in minutes",
        "Duration in hours",
        CASE WHEN LOWER("Entry Label") LIKE '%no show%'
             OR LOWER("Entry Label") LIKE '%ns1%' OR LOWER("Entry Label") LIKE '%ns2%' OR LOWER("Entry Label") LIKE '%ns3%'
             OR LOWER("Entry Label") LIKE '%ns 1%' OR LOWER("Entry Label") LIKE '%ns 2%' OR LOWER("Entry Label") LIKE '%ns 3%' THEN "Non Billable"
            ELSE "Billable / Non Billable" END AS "Billable / Non Billable",
        CASE WHEN LOWER("Entry Label") LIKE '%no show%'
             OR LOWER("Entry Label") LIKE '%ns1%' OR LOWER("Entry Label") LIKE '%ns2%' OR LOWER("Entry Label") LIKE '%ns3%'
             OR LOWER("Entry Label") LIKE '%ns 1%' OR LOWER("Entry Label") LIKE '%ns 2%' OR LOWER("Entry Label") LIKE '%ns 3%' THEN "No Show"
            ELSE "Category" END AS "Category",
        "Logged by",
        "Team Lead",
        CASE WHEN (LOWER("Entry Label") LIKE '%no show%'
             OR LOWER("Entry Label") LIKE '%ns1%' OR LOWER("Entry Label") LIKE '%ns2%' OR LOWER("Entry Label") LIKE '%ns3%'
             OR LOWER("Entry Label") LIKE '%ns 1%' OR LOWER("Entry Label") LIKE '%ns 2%' OR LOWER("Entry Label") LIKE '%ns 3%')
             AND ("Duration in minutes" > 15) THEN "Please adjust the no show time to less than 15 minutes"
            WHEN ("Logged by" NOT IN ('Claire Mangrum', 'Dr Fauzia Hasan Siddiqui', 'Dr. Rubi Garcha', 'Allison Houston', 'Erin Nelson', 'Thoywell Hemmings', 'Rakhshan Sharif') AND LOWER("PS Number") LIKE '%administrative profile%'
             AND ("Entry Label" LIKE '%PS2%' OR "Entry Label" LIKE '%PS3%' OR "Entry Label" LIKE '%PS4%' OR "Entry Label" LIKE '%PS5%')) THEN "Student task booked in admin profile. Please rectify" 
            WHEN DATE("Entry Label") IS NOT NULL THEN "Blank entry - Please delete"
            WHEN LOWER("Entry Label") LIKE '%(date)%' THEN "Dummy entry - Please delete"
            ELSE "Audit Remark" END AS "Audit Remark",
        "TL Remark"
        FROM base4),


base6 AS (SELECT *, 
     SUM("Duration in hours") OVER (PARTITION BY "PS Number") AS hours_summer 
    FROM base5),
base7 AS (SELECT "PS Number",
     "Student Full Name",
     "Entry Label",
      Date,
     "Duration in minutes",
     "Duration in hours",
     "Billable / Non Billable",
      Category,
     "Logged by",
     "Team Lead",
     CASE WHEN "Audit Remark" = "Please rectify the AM/PM Error" 
       THEN "Please rectify the AM/PM Error"
     WHEN hours_summer > 3.5 AND LOWER("PS Number") NOT LIKE '%administrative profile%' AND "Logged by" NOT IN ('Claire Mangrum', 'Dr Fauzia Hasan Siddiqui', 'Dr. Rubi Garcha', 'Allison Houston', 'Erin Nelson', 'Thoywell Hemmings', 'Rakhshan Sharif')
       THEN "Rectify the total time entered for this student"
     ELSE "Audit Remark"
     END AS "Audit Remark",
     "TL Remark"
    FROM base6),
base8 AS (SELECT "PS Number",
     "Student Full Name",
     "Entry Label",
      Date,
     "Duration in minutes",
     "Duration in hours",
     "Billable / Non Billable",
      CASE WHEN (LOWER("Entry Label") NOT LIKE '%no show%'
        AND LOWER("Entry Label") NOT LIKE '%ns1%' AND LOWER("Entry Label") NOT LIKE '%ns2%' AND LOWER("Entry Label") NOT LIKE '%ns3%'
        AND LOWER("Entry Label") NOT LIKE '%ns 1%' AND LOWER("Entry Label") NOT LIKE '%ns 2%' AND LOWER("Entry Label") NOT LIKE '%ns 3%')
        AND LOWER("PS Number") NOT LIKE '%administrative%' THEN 'Student Task'
      ELSE Category END AS Category,
     "Logged by",
     "Team Lead",
      CASE WHEN LOWER("Entry Label") LIKE '%no response%' AND "Duration in minutes" > 0 THEN "Rectify the minutes entered for no response"
      WHEN "Billable / Non Billable" = "Non Billable" AND "Duration in hours" > 0 AND LOWER("PS Number") NOT LIKE '%administrative%' THEN "Please put in Admin Task"
      WHEN "Audit Remark" = "Please adjust the no show time to less than 15 minutes" THEN "Please adjust the no show time to less than 15 minutes"
      WHEN (LOWER("Entry Label") LIKE '%no show%'
             OR LOWER("Entry Label") LIKE '%ns1%' OR LOWER("Entry Label") LIKE '%ns2%' OR LOWER("Entry Label") LIKE '%ns3%'
             OR LOWER("Entry Label") LIKE '%ns 1%' OR LOWER("Entry Label") LIKE '%ns 2%' OR LOWER("Entry Label") LIKE '%ns 3%') 
             AND ("Duration in hours" > 0) THEN "Rectify the hours entered for this no show entry"
      ELSE "Audit Remark" END AS "Audit Remark",
     "TL Remark"
    FROM base7),
base9 AS (SELECT "PS Number",
     "Student Full Name",
     "Entry Label",
      Date,
     "Duration in minutes",
     "Duration in hours",
     CASE WHEN "Billable / Non Billable" NOT IN ("Non Billable") THEN "Billable"
      ELSE "Billable / Non Billable" END AS "Billable / Non Billable",
     CASE WHEN (LOWER("Entry Label") LIKE '%1:1%' OR LOWER("Entry Label") LIKE '%1 to 1%' OR LOWER("Entry Label") LIKE '%1-1%') AND Category NOT IN ("Administrative Task", "No Show") THEN 'Student Session' 
      WHEN LOWER("Entry Label") LIKE '%whatsapp%' AND Category NOT IN ("Administrative Task", "No Show", "Student Session") THEN "Whatsapp Communication"
      ELSE Category END AS Category,
     "Logged by",
     "Team Lead",
     "Audit Remark",
     "TL Remark",
     TRIM(t2."Mentor Name") AS "Mentor Name"
    FROM base8 b8 LEFT JOIN table2 t2 
    ON b8."PS Number" = t2."Student ADEK Application ID")
SELECT "PS Number",
     "Student Full Name",
     "Entry Label",
      Date,
     "Duration in minutes",
     "Duration in hours",
     "Billable / Non Billable",
      Category,
     "Logged by",
     "Team Lead",
     "Audit Remark",
     "TL Remark"
    FROM base9;
    
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
        file_name="Final Output.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )




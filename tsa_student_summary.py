import streamlit as st
import pandas as pd
import sqlite3
from io import BytesIO

st.title("Timesheet Automation Task 4: Consolidated Student Summary")

# Upload 2 CSV/Excel tables
t1 = st.file_uploader("Upload Final Output File (CSV or Excel)", type=["csv", "xlsx"])
t2 = st.file_uploader("Upload Master Data File for Country Mapping (CSV or Excel)", type=["csv", "xlsx"])
t3 = st.file_uploader("Upload Last month's MPR for Student 1:1 Session Mapping (CSV or Excel)", type=["csv", "xlsx"])
t4 = st.file_uploader("Upload Last to last month's MPR for Student 1:1 Session Mapping (CSV or Excel)", type=["csv", "xlsx"])
t5 = st.file_uploader("Upload Mentors File to flag only the part-time mentors (CSV or Excel)", type=["csv", "xlsx"])

if t1 and t2 and t3 and t4 and t5:
    # Helper function to load CSV/Excel
    def load_file(f):
        return pd.read_excel(f) if f.name.endswith("xlsx") else pd.read_csv(f)

    # Load all 2 files
    df1, df2, df3, df4, df5 = load_file(t1), load_file(t2), load_file(t3), load_file(t4), load_file(t5)

    # Create SQLite in-memory DB
    conn = sqlite3.connect(":memory:")
    df1.to_sql("table1", conn, index=False, if_exists="replace")
    df2.to_sql("table2", conn, index=False, if_exists="replace")
    df3.to_sql("table3", conn, index=False, if_exists="replace")
    df4.to_sql("table4", conn, index=False, if_exists="replace")
    df5.to_sql("table5", conn, index=False, if_exists="replace")

    # SQL Query 1
    summary_query1 = """

WITH base1 AS (SELECT "Current Mentor", 
    COUNT(DISTINCT "ADEK Applicant ID") AS "No. of Students" 
    FROM table2
    GROUP BY 1),
base2 AS (SELECT "Logged by",
    "Team Lead",
    SUM(CASE WHEN "Billable / Non Billable" = "Billable" THEN "Duration in hours" ELSE 0 END) OVER (PARTITION BY "Logged by") AS "Billable Hours",
    SUM(CASE WHEN "Billable / Non Billable" = "Non Billable" THEN "Duration in hours" ELSE 0 END) OVER (PARTITION BY "Logged by") AS "Non Billable Hours"
    FROM table1)
SELECT DISTINCT b2."Logged by" AS Mentor,
    t5."Mentor Status",
    b2."Team Lead",
    b1."No. of Students",
    b1."No. of Students"*2.5 AS "Standard Hour / Student (2.5 hours)",
    '' AS "No. of Student Transitioned",
    '' AS "Allocated hours for transition (1.5 hours)",
    '' AS "Total Time",
    "Billable Hours" AS "Billable",
    "Non Billable Hours" AS "Non Billable",
    "Billable Hours" + "Non Billable Hours" AS Total,
    '' AS "Hours to be paid for Aug 2025",
    '' AS "Hours to be paid for July 2025",
    '' AS "Total Payment",
    '' AS "HQ Remark"
    FROM base2 b2 LEFT JOIN base1 b1 
        ON b2."Logged by" = b1."Current Mentor"
                  LEFT JOIN table5 t5
        ON b2."Logged by" = t5."Mentor";

    """

    # SQL Query 2
    student_summary_query2 = """

    WITH base1 AS (SELECT t2."ADEK Applicant ID",
        t2."Student Name",
        t2.Country,
        SUM(t1."Duration in hours") AS "Advising Hours"
    FROM table2 t2 LEFT JOIN table1 t1 
        ON t1."PS Number" = t2."ADEK Applicant ID"
    GROUP BY 1,2,3)
    
    SELECT b1."ADEK Applicant ID",
    b1."Student Name",
    t3."Mentor Name",
    t3."Team Leader Name",
    b1."Country",
    CASE WHEN t3."Date of meeting with student" > t4."Date of meeting with student" THEN t3."Date of meeting with student" ELSE t4."Date of meeting with student" END AS "Last Date of meeting with student",
    CASE WHEN LENGTH(TRIM("Advising Hours")) > 0 THEN "Advising Hours" 
      ELSE 0 END AS "Advising Hours" 
    FROM base1 b1 LEFT JOIN table3 t3
        ON b1."ADEK Applicant ID" = t3."Student ADEK Application ID"
                  LEFT JOIN table4 t4
        ON b1."ADEK Applicant ID" = t4."Student ADEK Application ID";
    
    """

    # Run queries
    result_df1 = pd.read_sql_query(summary_query1, conn)
    result_df2 = pd.read_sql_query(student_summary_query2, conn)

    st.subheader("Transformed Result")
    st.dataframe(result_df1)
    st.dataframe(result_df2)

    # Create Excel file in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        result_df1.to_excel(writer, index=False, sheet_name="Summary")
        result_df2.to_excel(writer, index=False, sheet_name="Student Summary")

    excel_data = output.getvalue()

    # Download button for Excel
    st.download_button(
        label="📥 Download Result as Excel",
        data=excel_data,
        file_name="Payroll File.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

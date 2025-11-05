import streamlit as st
import pandas as pd
import sqlite3
from io import BytesIO

st.title("Timesheet Automation Task 3: Part-Time Mentors Workload Flagging (Exceeding 6 Hours/Day)")

# Upload only 1 file
t1 = st.file_uploader("Upload Final Output file (CSV or Excel)", type=["csv", "xlsx"])
t2 = st.file_uploader("Upload Mentors File to flag only the part-time mentors (CSV or Excel)", type=["csv", "xlsx"])

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

    # SQL Queries
    
    query1 = """
WITH base1 AS (SELECT "Logged by", 
        Date,
        SUM("Duration in minutes") AS "Total minutes",
        SUM("Duration in hours") AS "Total hours"
    FROM table1
    WHERE "Logged by" NOT IN ('Claire Mangrum', 'Dr Fauzia Hasan Siddiqui', 'Dr. Rubi Garcha', 'Allison Houston', 'Erin Nelson', 'Thoywell Hemmings')
    GROUP BY 1,2)
SELECT b1.*, t2."Team Lead",
       CASE WHEN b1."Total hours" > 6 AND b1."Logged by" IN (SELECT Mentor FROM table2 WHERE "Mentor Status" = "Part Time")
       THEN "Part Time Mentor spent more than 6 hours on the students on this day. Please review"
       END AS "HQ Remark"
    FROM base1 b1 LEFT JOIN table2 t2 ON b1."Logged by" = t2.Mentor
    ORDER BY 1,2;

    """

    query2 = """
WITH base1 AS (SELECT "PS Number", 
        COUNT(*) AS "No Show Count"
    FROM table1
      WHERE LOWER("PS Number") NOT LIKE '%administrative profile%'
        AND (LOWER("Entry Label") LIKE '%no show%' OR LOWER("Entry Label") = 'missed meeting'
             OR LOWER("Entry Label") LIKE '%ns1%' OR LOWER("Entry Label") LIKE '%ns2%' OR LOWER("Entry Label") LIKE '%ns3%'
             OR LOWER("Entry Label") LIKE '%ns 1%' OR LOWER("Entry Label") LIKE '%ns 2%' OR LOWER("Entry Label") LIKE '%ns 3%')
    GROUP BY 1)

SELECT *, 
       CASE WHEN "No Show Count" > 2 THEN "No show count for this student > 2. Please rectify the entry as per the SOP." END AS "Audit Remark"
    FROM base1;
    
    """

    # Run query
    result_df1 = pd.read_sql_query(query1, conn)
    result_df2 = pd.read_sql_query(query2, conn)

    st.subheader("Filtered Result")
    st.dataframe(result_df1)
    st.dataframe(result_df2)

    # Create Excel file in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        result_df1.to_excel(writer, index=False, sheet_name="PT Mentors time > 6 hours")
        result_df2.to_excel(writer, index=False, sheet_name="No Show Entries > 2")

    excel_data = output.getvalue()

    # Download button for Excel
    st.download_button(
        label="📥 Download Result as Excel",
        data=excel_data,
        file_name="Mentor Flag more than 6 Hrs and No Show Flag more than 2.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

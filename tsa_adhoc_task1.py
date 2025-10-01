import streamlit as st
import pandas as pd
import sqlite3
from io import BytesIO

st.title("Timesheet Automation Task 3: Mentor Workload Flagging (Exceeding 6 Hours/Day)")

# Upload only 1 file
uploaded_file = st.file_uploader("Upload Final Output file (CSV or Excel)", type=["csv", "xlsx"])

if uploaded_file:
    # Load file
    if uploaded_file.name.endswith("xlsx"):
        df = pd.read_excel(uploaded_file)
    else:
        df = pd.read_csv(uploaded_file)

    # Create SQLite in-memory DB
    conn = sqlite3.connect(":memory:")
    df.to_sql("sharepoint_table", conn, index=False, if_exists="replace")

    # SQL Query
    query = """
WITH base1 AS (SELECT "Logged by", 
        Date,
        SUM("Duration in minutes") AS "Total minutes",
        SUM("Duration in hours") AS "Total hours"
    FROM sharepoint_table
    WHERE "Logged by" NOT IN ('Claire Mangrum', 'Dr Fauzia Hasan Siddiqui', 'Dr. Rubi Garcha', 'Allison Houston', 'Erin Nelson', 'Thoywell Hemmings', 'Rakhshan Sharif')
    GROUP BY 1,2)
SELECT *,
       CASE WHEN "Total hours" > 6 
       THEN "Mentor spent more than 6 hours on the students on this day. Please review"
       END AS "HQ Remark"
    FROM base1
    ORDER BY 1,2;

    """

    # Run query
    result_df = pd.read_sql_query(query, conn)

    st.subheader("Filtered Result")
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
        file_name="Mentor Flagged for > 6 hours.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )



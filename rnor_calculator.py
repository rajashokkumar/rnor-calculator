import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# ---- Helper Functions ----
def fy_range(start_year, end_year):
    return [f"FY {y}-{str(y+1)[-2:]}" for y in range(start_year, end_year+1)]

def is_resident(stay_days):
    return stay_days >= 182

def calc_days_in_india(travel_data, fy_start, fy_end):
    total_days = 0
    for trip in travel_data:
        dep = trip["departure"]
        ret = trip["return"]

        if ret < fy_start or dep > fy_end:
            continue

        actual_return = min(ret, fy_end)
        actual_depart = max(dep, fy_start)

        days_abroad = (actual_return - actual_depart).days
        total_days += max((fy_end - fy_start).days - days_abroad, 0)
    return total_days

def count_non_resident_years(flags):
    return flags.count(False)

# ---- Streamlit UI ----
st.set_page_config(page_title="RNOR Status Calculator", layout="centered")
st.title("🇮🇳 RNOR Status Calculator for Returning NRIs")

st.markdown("""
This tool calculates your **RNOR (Resident but Not Ordinarily Resident)** status for each financial year based on your travel history and return date to India.
""")

st.header("Step 1: Enter Travel History")

with st.form("travel_form"):
    num_trips = st.number_input("Number of international trips (long-term only)", 1, 20, 3)
    travel_data = []

    for i in range(num_trips):
        st.subheader(f"Trip #{i+1}")
        dep = st.date_input(f"Departure from India", key=f"dep_{i}")
        ret = st.date_input(f"Return to India", key=f"ret_{i}")
        if ret <= dep:
            st.error(f"Return date must be after departure for trip #{i+1}")
        travel_data.append({"departure": dep, "return": ret})

    final_return_date = st.date_input("Final return to India (permanently):")

    submit = st.form_submit_button("Check RNOR Eligibility")

if submit:
    st.header("📊 RNOR Status Report")
    start_fy = final_return_date.year - 10
    end_fy = final_return_date.year + 3

    fy_list = fy_range(start_fy, end_fy)
    resident_flags = []
    results = []

    for i, fy in enumerate(fy_list):
        fy_start = datetime(start_fy + i, 4, 1)
        fy_end = datetime(start_fy + i + 1, 3, 31)

        days_in_india = calc_days_in_india(travel_data, fy_start, fy_end)
        resident = is_resident(days_in_india)

        if i >= 1:
            preceding_10 = resident_flags[max(0, i-10):i]
            preceding_7 = resident_flags[max(0, i-7):i]
            nonres_10 = count_non_resident_years(preceding_10)
            stay_7yrs = sum([
                calc_days_in_india(travel_data, 
                    datetime(start_fy + j, 4, 1), 
                    datetime(start_fy + j + 1, 3, 31)
                ) for j in range(max(0, i-7), i)
            ])
        else:
            nonres_10 = "-"
            stay_7yrs = "-"

        rnor = False
        rnor_reason = ""

        if resident:
            if isinstance(nonres_10, int) and nonres_10 >= 9:
                rnor = True
                rnor_reason = f"Non-resident in {nonres_10} of last 10 years"
            elif isinstance(stay_7yrs, int) and stay_7yrs <= 729:
                rnor = True
                rnor_reason = f"Stayed in India only {stay_7yrs} days in last 7 years"

        results.append({
            "Financial Year": fy,
            "Resident": "Yes" if resident else "No",
            "Days in India": days_in_india,
            "RNOR Eligible": "Yes ✅" if rnor else "No ❌",
            "Reason": rnor_reason if rnor else "-"
        })

        resident_flags.append(resident)

    st.dataframe(pd.DataFrame(results))

# ==============================================================================
# NOTICE: This property belongs to Dean Otto
# All rights reserved. Code terminal developed for WBC Polokwane internal branch.
# ==============================================================================

import os
import json
import urllib.parse
import pandas as pd
from datetime import datetime
import streamlit as st

USERS = {
    "dean": {"pin": "15184", "role": "admin", "full_name": "Dean Otto"},
    "sales1": {"pin": "1234", "role": "employee", "full_name": "Dean Otto"},
    "sales2": {"pin": "1234", "role": "employee", "full_name": "Charl"},
    "Adriaan": {"pin": "5555", "role": "manager", "full_name": "Adriaan"}
}

FIXED_OUTDOOR_ZONES = {
    "Outdoor Area 1 (Small)": ["Area 1 - Wash Bay 1", "Area 1 - Wash Bay 2", "Area 1 - Photo Bay"],
    "Outdoor Area 2 (Large)": ["Area 2 - DEKRA 1", "Area 2 - DEKRA 2", "Area 2 - General Overflow"],
    "Area 3 (Sold Cars - Small)": ["Sold Bay S1", "Sold Bay S2", "Sold Bay S3"],
    "Area 4 (Off-Property)": ["Off-Site Transit", "Supplier Holding", "Customer Delivery Pending"]
}

def load_data():
    if os.path.exists("wbc_floor_data.json"):
        with open("wbc_floor_data.json", "r") as f:
            return json.load(f)
    return {
        "vehicles": {},
        "custom_grid": {
            "Row A": [f"Row A (Bay {i})" for i in range(1, 11)],
            "Row B": [f"Row B (Bay {i})" for i in range(1, 11)]
        }
    }

def save_data(data):
    with open("wbc_floor_data.json", "w") as f:
        json.dump(data, f, indent=4)

if "db" not in st.session_state:
    st.session_state.db = load_data()
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_info" not in st.session_state:
    st.session_state.user_info = None

if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align: center;'>🔒 WBC Polokwane Floor Terminal Portal</h2>", unsafe_allow_html=True)
    username = st.text_input("Username").strip()
    pin = st.text_input("PIN", type="password").strip()
    if st.button("Sign In", use_container_width=True):
        if username in USERS and USERS[username]["pin"] == pin:
            st.session_state.logged_in = True
            st.session_state.user_info = USERS[username]
            st.rerun()
        else:
            st.error("Invalid credentials entered.")
    st.stop()

user = st.session_state.user_info
db = st.session_state.db

st.sidebar.title("🎮 Controls")
st.sidebar.write(f"Logged in as: **{user['full_name']}** ({user['role'].upper()})")

menu_options = ["📋 Live Floor Plan Map", "📲 Log / Move Car", "🔍 Quick-Search Tool"]
if user["role"] == "admin":
    menu_options.append("🛠️ Admin Grid Map Setup")
    menu_options.append("⚙️ Admin Database Tools")

choice = st.sidebar.radio("Navigation Viewport", menu_options)

if st.sidebar.button("Sign Out Current User", use_container_width=True):
    st.session_state.logged_in = False
    st.session_state.user_info = None
    st.rerun()

if choice == "📋 Live Floor Plan Map":
    st.title("📋 Live Branch Allocation Grid Map")
    occupied_bays = {v_data["bay"]: s_id for s_id, v_data in db["vehicles"].items()}
    st.subheader("🏢 Indoor Warehouse Grid Lines")
    for row_name, bays in db["custom_grid"].items():
        with st.expander(f"📍 View Layout Structure: {row_name}", expanded=True):
            cols = st.columns(5)
            for idx, bay in enumerate(bays):
                col_target = cols[idx % 5]
                if bay in occupied_bays:
                    sid = occupied_bays[bay]
                    car = db["vehicles"][sid]
                    meta = f" | {car['last_moved_by']}" if user["role"] in ["manager", "admin"] else ""
                    col_target.success(f"**{bay}**\n\n🚗 Stock #{sid}\n\n*{car['make_model']}*{meta}")
                else:
                    col_target.text_area(label=bay, value="[ EMPTY BAY ]", height=100, disabled=True, key=f"empty_{bay}")

    st.subheader("🌤️ External Handling and Overflow Zones")
    out_cols = st.columns(len(FIXED_OUTDOOR_ZONES))
    for idx, (zone_name, bays) in enumerate(FIXED_OUTDOOR_ZONES.items()):
        with out_cols[idx]:
            st.markdown(f"### {zone_name}")
            for bay in bays:
                if bay in occupied_bays:
                    sid = occupied_bays[bay]
                    car = db["vehicles"][sid]
                    st.info(f"🚘 **{bay}**\n\nStock #{sid}: {car['make_model']}\n\n[🔗 Open WBC Link]({car['wbc_url']})")
                else:
                    st.markdown(f"`⬜ {bay}: -- EMPTY --`")

elif choice == "📲 Log / Move Car":
    st.title("📲 Real-Time Location Update Portal")
    all_available_bays = []
    for r_bays in db["custom_grid"].values(): all_available_bays.extend(r_bays)
    for o_bays in FIXED_OUTDOOR_ZONES.values(): all_available_bays.extend(o_bays)
    stock_id = st.text_input("Enter Vehicle Stock ID Reference").strip()
    current_model = ""
    if stock_id in db["vehicles"]:
        current_model = db["vehicles"][stock_id]["make_model"]
        st.warning(f"⚠️ Stock ID #{stock_id} is registered at: **{db['vehicles'][stock_id]['bay']}**")
    make_model = st.text_input("Vehicle Model Specification Details", value=current_model)
    target_bay = st.selectbox("Select Target Destination Bay Alignment", all_available_bays)
    if st.button("Confirm Registry Reallocation", use_container_width=True):
        if not stock_id:
            st.error("Vehicle Stock ID cannot be left blank.")
        else:
            safe_stock = urllib.parse.quote(stock_id)
            safe_bay = urllib.parse.quote(target_bay)
            generated_url = f"https://webuycars.co.za{safe_stock}&bay={safe_bay}"
            db["vehicles"][stock_id] = {
                "make_model": make_model or "Unknown Vehicle Spec",
                "bay": target_bay,
                "last_moved_by": user["full_name"],
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "wbc_url": generated_url
            }
            save_data(db)
            st.success(f"Moved Stock #{stock_id} to **{target_bay}**.")
            st.markdown(f"[🔗 Direct Tracking Link]({generated_url})")

elif choice == "🔍 Quick-Search Tool":
    st.title("🔍 Branch Fleet Search Engine")
    search_query = st.text_input("Type Stock ID number or Model Keyword").strip().lower()
    if search_query:
        matches = False
        for sid, details in db["vehicles"].items():
            if search_query in sid.lower() or search_query in details["make_model"].lower():
                matches = True
                st.markdown(f"### Stock ID: #{sid}")
                st.write(f"🚘 **Model:** {details['make_model']}")
                st.write(f"📍 **Location:** {details['bay']}")
                st.markdown(f"[🔗 Open Link]({details['wbc_url']})")
                st.write("---")
        if not matches:
            st.error("No matches found.")

elif choice == "🛠️ Admin Grid Map Setup" and user["role"] == "admin":
    st.title("🛠️ Physical Layout Allocation System Setup")
    row_name = st.text_input("Enter Row Identifier (e.g., Row C)").strip()
    if row_name:
        if row_name not in db["custom_grid"]:
            if st.button(f"Initialize '{row_name}'"):
                db["custom_grid"][row_name] = []
                save_data(db)
                st.rerun()
        current_bays = db["custom_grid"].get(row_name, [])
        custom_name = st.text_input("Barcode Label ID", value=f"{row_name} (Bay {len(current_bays) + 1})")
        if st.button("Append Grid Unit"):
            db["custom_grid"][row_name].append(custom_name)
            save_data(db)
            st.success(f"Added {custom_name}")
            st.rerun()

elif choice == "⚙️ Admin Database Tools" and user["role"] == "admin":
    st.title("⚙️ Admin Database Tools")
    if st.button("Clear Vehicle Allocation Log"):
        db["vehicles"] = {}
        save_data(db)
        st.success("Cleared vehicle records.")
        st.rerun()

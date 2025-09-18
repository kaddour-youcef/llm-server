import os
import streamlit as st
import httpx
import pandas as pd
from datetime import date, timedelta

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://gateway:8080")

st.set_page_config(page_title="LLM Admin", layout="wide")

if "admin_key" not in st.session_state:
    st.session_state.admin_key = ""


def client():
    return httpx.Client(
        base_url=GATEWAY_URL,
        headers={"x-api-key": st.session_state.admin_key},
        timeout=30.0,
    )


def normalize_rows(rows):
    """Ensure API response is always a list of dicts."""
    if isinstance(rows, dict):
        return [rows]
    return rows or []


st.title("LLM Admin")

with st.sidebar:
    st.subheader("Authentication")
    st.session_state.admin_key = st.text_input("Admin API Key", type="password")
    if st.button("Validate"):
        try:
            r = client().get("/admin/users")
            if r.status_code == 200:
                st.success("Authenticated")
            else:
                st.error("Invalid key")
        except Exception as e:
            st.error(str(e))

tab_users, tab_keys, tab_usage, tab_requests = st.tabs(
    ["Users", "API Keys", "Usage", "Requests"]
)

# ---------------- Users tab ----------------
with tab_users:
    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button("Refresh users"):
            r = client().get("/admin/users")
            if r.status_code == 200:
                users = normalize_rows(r.json())
                st.dataframe(pd.DataFrame(users))
            else:
                st.error(str(r.text))
    with col2:
        st.subheader("Create user")
        name = st.text_input("Name")
        email = st.text_input("Email")
        if st.button("Create"):
            r = client().post("/admin/users", json={"name": name, "email": email or None})
            if r.status_code == 200:
                st.success("User created")
            else:
                st.error(str(r.text))

# ---------------- Keys tab ----------------
with tab_keys:
    st.subheader("Create API Key")
    user_id = st.text_input("User ID")
    name = st.text_input("Key name")
    role = st.selectbox("Role", ["user", "admin"])
    monthly_quota = st.number_input(
        "Monthly token quota (0 = unlimited)", min_value=0, value=0
    )
    daily_req = st.number_input(
        "Daily request quota (0 = unlimited)", min_value=0, value=0
    )
    if st.button("Create key"):
        payload = {
            "user_id": user_id,
            "name": name,
            "role": role,
            "monthly_quota_tokens": None if monthly_quota == 0 else monthly_quota,
            "daily_request_quota": None if daily_req == 0 else daily_req,
        }
        r = client().post("/admin/keys", json=payload)
        if r.status_code == 200:
            st.success("Key created. COPY NOW:")
            st.code(r.json().get("plaintext_key", ""))
        else:
            st.error(str(r.text))

    st.divider()
    st.subheader("List Keys")
    if st.button("Refresh keys"):
        r = client().get("/admin/keys")
        if r.status_code == 200:
            keys = normalize_rows(r.json())
            st.dataframe(pd.DataFrame(keys))
        else:
            st.error(str(r.text))

# ---------------- Usage tab ----------------
with tab_usage:
    st.subheader("Usage")
    today = date.today()
    start = st.date_input("From", today - timedelta(days=30))
    end = st.date_input("To", today)
    key_id = st.text_input("Filter by key_id (optional)")
    params = {"from": str(start), "to": str(end)}
    if key_id:
        params["key_id"] = key_id
    if st.button("Query usage"):
        r = client().get("/admin/usage", params=params)
        if r.status_code == 200:
            data = r.json()
            st.metric("Total Tokens", data.get("totals", {}).get("total_tokens", 0))
            st.metric("Requests", data.get("totals", {}).get("request_count", 0))
            df = pd.DataFrame(data.get("timeseries", []))
            if not df.empty and "day" in df.columns:
                st.line_chart(df.set_index("day")[["total_tokens"]])
        else:
            st.error(str(r.text))

# ---------------- Requests tab ----------------
with tab_requests:
    st.subheader("Recent Requests")
    if st.button("Refresh"):
        r = client().get("/admin/requests")
        if r.status_code == 200:
            rows = normalize_rows(r.json())
            st.dataframe(pd.DataFrame(rows))
        else:
            st.error(str(r.text))


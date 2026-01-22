# Palette's Journal

## 2025-02-20 - Streamlit Dashboard Feedback Patterns
**Learning:** The Streamlit dashboard (`agents/dashboard/app.py`) relied on silent failures for disconnected services (Redis/K8s) and lacked empty states for dataframes.
**Action:** For all future Streamlit tools in this repo, explicitly check connection states *inside* interaction handlers to provide visible error feedback, and wrap `st.dataframe` calls with a check to display a friendly `st.info` message when empty.

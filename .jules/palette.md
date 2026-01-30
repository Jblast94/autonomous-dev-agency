## 2026-01-30 - Streamlit Auto-Refresh Loop
**Learning:** `st.rerun()` inside a checkbox condition creates a tight loop that freezes the browser if no delay is added.
**Action:** Always include `time.sleep(N)` before `st.rerun()` in auto-refresh logic.

## 2026-01-28 - Streamlit Command Inputs and Loops
**Learning:** `st.text_input` is insufficient for code or multi-line commands; `st.text_area` is the preferred UX pattern.
**Action:** Use `st.text_area` for any command/script input fields.

**Learning:** `st.rerun()` in a tight loop (e.g., inside `if checkbox:`) causes browser freezing and high CPU usage.
**Action:** Always include a `time.sleep()` delay before `st.rerun()` in auto-refresh loops.

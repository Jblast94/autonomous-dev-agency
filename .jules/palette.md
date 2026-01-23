## 2026-01-23 - Streamlit Input Limitations
**Learning:** `st.text_input` is insufficient for complex command inputs (like Python scripts or multi-line shell commands), creating friction for power users.
**Action:** Use `st.text_area` for command/script inputs by default, and include validation to prevent accidental empty submissions.

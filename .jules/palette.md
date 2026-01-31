## 2026-01-31 - [Streamlit Input Guidance]
**Learning:** Streamlit `help` parameters render as unobtrusive tooltips (question mark icons), which is perfect for providing context on form fields without cluttering the layout. Also, `st.text_input` is insufficient for code execution inputs; `st.text_area` is essential for multi-line commands.
**Action:** Always verify if an input might accept code or multi-line text and prefer `st.text_area`. Use `help` parameters generously on form inputs to reduce cognitive load.

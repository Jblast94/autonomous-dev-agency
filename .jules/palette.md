## 2026-01-29 - Streamlit Command Input Pattern
**Learning:** Users need multi-line editing for command execution inputs. Single-line inputs (`st.text_input`) feel restrictive for shell/python scripts.
**Action:** Always prefer `st.text_area` with `height` parameter for code/command inputs in Streamlit dashboards.

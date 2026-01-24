## 2024-05-23 - Streamlit Input Patterns
**Learning:** In Streamlit dashboards, `st.text_input` is restrictive for command/code inputs. Users often need to paste multi-line scripts (Python/Shell).
**Action:** Default to `st.text_area` for command inputs in developer-facing dashboards to support richer interactions.

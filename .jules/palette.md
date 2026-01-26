# Palette's UX Journal

## 2024-05-22 - Initial Setup
**Learning:** UX and accessibility improvements require a dedicated space for tracking insights to avoid repetitive fixes without understanding the underlying patterns.
**Action:** Established this journal to track critical learnings.

## 2024-05-22 - Streamlit Input Usability
**Learning:** Single-line text inputs for command execution (like shell scripts) significantly hamper usability and prevent complex task dispatching. Users naturally expect multi-line editing for code/commands.
**Action:** Replace `st.text_input` with `st.text_area` for command inputs and ensure `help` tooltips are provided for context.

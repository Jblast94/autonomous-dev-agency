## 2024-05-22 - Streamlit Accessibility & Verification
**Learning:** Adding the `help` parameter to Streamlit widgets generates a separate button with an aria-label like "Help for [Label]". This improves accessibility but creates ambiguity when testing with Playwright's `get_by_label`, as two elements now match the label text.
**Action:** When verifying Streamlit apps with Playwright, use `get_by_role("textbox", name="Label")` or `get_by_role("button", name="Help for Label")` to distinguish between the input and its help tooltip.

## 2024-05-22 - Command Input UX
**Learning:** Users dispatching shell or python commands often need multi-line support. `st.text_input` confines them to a single line, which is poor UX for code entry.
**Action:** Default to `st.text_area` for command/script inputs to allow multi-line editing and better visibility of content.

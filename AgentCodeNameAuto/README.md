# AgentCodeNameAuto Streamlit App

This Streamlit app reads:
- an Excel file with `Account Number` and `Agent Code`
- a PDF file with account number(s) and error details

It outputs a PDF containing:
- account number(s)
- agent name prefixed with `@` when the agent code is found
- error details
- unmatched accounts listed separately if the agent code is missing

## How to run

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run the app:

```bash
streamlit run AgentCdNmAuto.py
```

3. Upload the Excel and PDF files in the Streamlit interface.

## Notes

- The app uses the built-in agent code-to-name mapping from the provided list.
- Make sure the Excel file contains columns with names that include `Account` and `Agent Code`.
- The PDF parser looks for account numbers with at least 6 digits.

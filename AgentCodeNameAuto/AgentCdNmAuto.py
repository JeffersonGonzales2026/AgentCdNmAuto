import io
import re
from collections import OrderedDict

import pandas as pd
import pdfplumber
import streamlit as st
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

AGENT_CODE_NAME = {
    "PDCI": "Denise Mae",
    "PACR": "Ailyn",
    "PRES": "Rosemarie",
    "PAFP": "Aira Mae",
    "PYDA": "Yumiko",
    "PKPY": "Kaye Ann",
    "PDMU": "Debbie Ruth",
    "PJQB": "Jayson",
    "PMID": "Mika Gay",
    "PRYC": "Rachel",
    "PARB": "Rocel",
    "PRIR": "Rolie",
    "PBRP": "Bryan",
    "PJOH": "John",
    "PSSA": "Sherry Jane",
    "PNBM": "Niña Althea",
    "PBPS": "Pauline Mae",
    "PDUJ": "Joshua",
    "PFJF": "Jorgie",
    "PRFG": "Resley Ann",
    "PFKO": "Kathryn Joy",
    "PPMA": "Angela",
    "PMJR": "Justine Mary",
    "PMKL": "Kyle Andrew",
    "PPDJ": "Joemell",
    "PDRJ": "Juliana Reinalyn Divine",
    "PYAM": "Lyka",
    "PGJY": "Jenny Ann",
    "PAMN": "Ana Marie",
    "PDKZ": "Kimberly Ann",
    "PSMF": "Missy Mae",
    "PASL": "Lance Albert",
    "PSFM": "Fria Mae",
    "PSMC": "Maria Alyzza",
    "POCJ": "Joyce",
    "PACP": "Angelika",
    "PDRM": "Mark Reniel",
    "PSFS": "Fairods",
    "PDSC": "Mary Jean",
    "PMGM": "Marvin",
    "PPMS": "Marvin",
    "PECL": "Erica",
    "DPDD": "Danielle",
    "DSRH": "Sheila",
    "PJOY": "Joyce Ann Leen",
    "PAKP": "Arzel",
    "DPNC": "Nova Crissamaie",
    "DVYR": "Yelody",
    "PRCS": "Ronalyn",
    "PDSL": "Silvester",
    "PMPC": "Carol Anne",
    "PLAP": "Lyka Jane",
    "PDKA": "Kee-R",
    "PPEI": "Emie Jane",
    "PSEA": "Emmalyn",
    "PVJM": "Jesame",
    "PBGP": "Gin Paola",
    "PEZS": "Eddielyn Joy ",
    "PDSM": "Sheila Mae ",
    "PBJL": "James Lester",
    "PAIT": "Ivan Ray",
    "PJRT": "Joan T",
    "PCMJ": "Mark Justin",
    "PDOR": "Raquel",
    "PPMJ": "Joan",
    "PBMI": "Marifi",
    "PIAP": "Ivan",
    "PBPJ": "Jemuel Jiven",
}


def load_account_agent_map(excel_file):
    df = pd.read_excel(excel_file, dtype=str)
    lower_columns = {c.lower().strip(): c for c in df.columns}
    account_col = None
    agent_code_col = None

    for key, orig in lower_columns.items():
        if "account" in key and "number" in key:
            account_col = orig
        if "agent" in key and "code" in key:
            agent_code_col = orig

    if account_col is None or agent_code_col is None:
        raise ValueError(
            "Excel file must contain columns for Account Number and Agent Code."
        )

    mapping = {}
    for _, row in df.iterrows():
        account = str(row.get(account_col, "")).strip()
        agent_code = str(row.get(agent_code_col, "")).strip().upper()
        if account:
            mapping[account] = {
                "agent_code": agent_code,
                "agent_name": AGENT_CODE_NAME.get(agent_code, ""),
            }
    return mapping


def normalize_text(text):
    return re.sub(r"\s+", " ", text).strip()


def parse_pdf_entries(pdf_file):
    with pdfplumber.open(pdf_file) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    lines = [normalize_text(line) for line in text.splitlines() if normalize_text(line)]
    entries = []
    current = None

    for line in lines:
        account_match = re.search(r"\b\d{6,}\b", line)
        if account_match:
            if current:
                entries.append(current)
            account = account_match.group()
            remainder = line[account_match.end():].strip(" :–—-\t")
            current = {"account": account, "details": remainder}
        elif current:
            current["details"] = normalize_text(
                f"{current['details']} {line}" if current["details"] else line
            )
    if current:
        entries.append(current)

    return entries


def group_entries_by_section_and_agent(entries, account_agent_map):
    grouped = OrderedDict()

    for entry in entries:
        section = entry["details"] or "No Section"
        account = entry["account"]
        agent_info = account_agent_map.get(account, {})
        agent_name = agent_info.get("agent_name") or "Unknown"

        if section not in grouped:
            grouped[section] = OrderedDict()
        if agent_name not in grouped[section]:
            grouped[section][agent_name] = []

        grouped[section][agent_name].append(account)

    return grouped


def format_grouped_output(grouped):
    sections = []
    section_items = list(grouped.items())
    for index, (section, agents) in enumerate(section_items):
        lines = [f"### {section}"]
        for agent_name, accounts in agents.items():
            lines.append(f"@{agent_name}")
            lines.extend(f"- {account}" for account in accounts)
            lines.append("")

        if index < len(section_items) - 1:
            lines.append("---")
        sections.append("\n".join(lines).rstrip())

    return "\n\n".join(sections)


def build_result_pdf(entries, account_agent_map):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    style = getSampleStyleSheet()
    normal = style["Normal"]
    heading = style["Heading1"]
    story = [Paragraph("Agent Error Report", heading), Spacer(1, 12)]

    matched = []
    unmatched = []

    for entry in entries:
        account = entry["account"]
        details = entry["details"] or "No error details found."
        agent_info = account_agent_map.get(account, {})
        agent_code = agent_info.get("agent_code", "")
        agent_name = agent_info.get("agent_name", "")

        if agent_code and agent_name:
            matched.append((account, agent_name, details))
        else:
            unmatched.append((account, details))

    if matched:
        story.append(Paragraph("Matched Accounts", style["Heading2"]))
        story.append(Spacer(1, 8))
        for account, name, details in matched:
            story.append(Paragraph(f"<b>{account}</b> - @{name}", normal))
            story.append(Paragraph(details, normal))
            story.append(Spacer(1, 10))
    else:
        story.append(Paragraph("No matched accounts found.", normal))
        story.append(Spacer(1, 10))

    if unmatched:
        story.append(Spacer(1, 12))
        story.append(Paragraph("Unmatched Accounts", style["Heading2"]))
        story.append(Spacer(1, 8))
        for account, details in unmatched:
            story.append(Paragraph(f"<b>{account}</b>", normal))
            story.append(Paragraph(details, normal))
            story.append(Spacer(1, 10))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def main():
    st.title("Agent Code Automation: Excel + PDF to Output PDF")
    st.write(
        "Upload an Excel file containing Account Number and Agent Code, plus a PDF containing Account Number and Error Details. "
        "The app will produce a PDF report with @agent names when an agent code is found."
    )

    excel_file = st.file_uploader("Upload Excel file", type=["xls", "xlsx"] )
    pdf_file = st.file_uploader("Upload PDF file", type=["pdf"] )

    if excel_file and pdf_file:
        try:
            account_agent_map = load_account_agent_map(excel_file)
            entries = parse_pdf_entries(pdf_file)

            if not entries:
                st.warning("No account numbers were found in the uploaded PDF. Please verify the PDF content.")
                return

            grouped = group_entries_by_section_and_agent(entries, account_agent_map)
            grouped_output = format_grouped_output(grouped)

            result_pdf = build_result_pdf(entries, account_agent_map)

            st.success("Result PDF generated successfully.")
            st.download_button(
                label="Download Result PDF",
                data=result_pdf,
                file_name="agent_error_report.pdf",
                mime="application/pdf",
            )
            st.download_button(
                label="Download Grouped Output",
                data=grouped_output,
                file_name="grouped_output.txt",
                mime="text/plain",
            )

            st.write("### Reorganized grouping output")
            st.code(grouped_output, language="markdown")

            sample_table = [
                {
                    "Account Number": item["account"],
                    "Error Details": item["details"],
                    "Agent Code": account_agent_map.get(item["account"], {}).get("agent_code", ""),
                    "Agent Name": account_agent_map.get(item["account"], {}).get("agent_name", ""),
                }
                for item in entries
            ]
            st.write("### Parsed entries preview")
            st.table(sample_table)

        except Exception as error:
            st.error(f"Error processing files: {error}")

    else:
        st.info("Please upload both the Excel file and the PDF file to generate the output PDF.")


if __name__ == "__main__":
    main()

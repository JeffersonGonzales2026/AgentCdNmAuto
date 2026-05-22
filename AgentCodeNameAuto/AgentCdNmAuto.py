import io
import re

import pandas as pd
import pdfplumber
import streamlit as st
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

AGENT_CODE_NAME = {
    "PDCI": "Denise Mae Ilaw",
    "PACR": "Ailyn Palaganas",
    "PRES": "Rosemarie Sanchez",
    "PAFP": "Aira Mae Pecson",
    "PYDA": "Yumiko Alcantara",
    "PKPY": "Kaye Ann Amoguis",
    "PDMU": "Debbie Ruth Ursua",
    "PJQB": "Jayson Aquino",
    "PMID": "Mika Gay De Vera",
    "PRYC": "Rachel Dela Cruz",
    "PARB": "Rocel Amando",
    "PRIR": "Rolie Ricare",
    "PBRP": "Bryan Mandapat",
    "PJOH": "John Munar",
    "PSSA": "Sherry Jane Aquino",
    "PNBM": "Niña Althea Mercado",
    "PBPS": "Pauline Mae Balderas",
    "PDUJ": "Joshua Ursua",
    "PFJF": "Jorgie Ferolino",
    "PRFG": "Resley Ann Garcia",
    "PFKO": "Kathryn Joy Fronda",
    "PPMA": "Angela Daoatin",
    "PMJR": "Justine Mary Rosario",
    "PMKL": "Kyle Andrew Merong",
    "PPDJ": "Joemell Damasco",
    "PDRJ": "Juliana Reinalyn Divine Rodriguez",
    "PYAM": "Lyka Andaya",
    "PGJY": "Jenny Ann Galvez",
    "PAMN": "Ana Marie Nacional",
    "PDKZ": "Kimberly Ann De Leon",
    "PSMF": "Missy Mae Sanchez",
    "PASL": "Lance Albert Salvalleon",
    "PSFM": "Fria Mae Santillan",
    "PSMC": "Maria Alyzza Sampaga",
    "POCJ": "Joyce Mamaradlo",
    "PACP": "Angelika Pernia",
    "PDRM": "Mark Reniel Datuin",
    "PSFS": "Fairods Sinubangan",
    "PDSC": "Mary Jean Delos Santos",
    "PMGM": "Marvin Montemayor",
    "PPMS": "Marvin Padlan",
    "PECL": "Erica Lomboy",
    "DPDD": "Danielle Dalanan",
    "DSRH": "Sheila Hipe",
    "PJOY": "Joyce Ann Leen Robis",
    "PAKP": "Arzel Pili",
    "DPNC": "Nova Crissamaie Pan",
    "DVYR": "Yelody Villarino",
    "PRCS": "Ronalyn Sy",
    "PDSL": "Silvester De Guzman",
    "PMPC": "Carol Anne Patungan",
    "PLAP": "Lyka Jane Pidlaoan",
    "PDKA": "Kee-R Diaz",
    "PPEI": "Emie Jane Prolles",
    "PSEA": "Emmalyn Salinas",
    "PVJM": "Jesame Macaraeg",
    "PBGP": "Gin Paola Balberan",
    "PEZS": "Eddielyn Joy Sarmiento",
    "PDSM": "Sheila Mae Dela Cruz",
    "PBJL": "James Lester Bato",
    "PAIT": "Ivan Ray Alcantara",
    "PJRT": "Joan Tagulao",
    "PCMJ": "Mark Justin Custodio",
    "PDOR": "Raquel Dayog",
    "PPMJ": "Joan Caranto",
    "PBMI": "Marifi Berdolaga",
    "PIAP": "Ivan Padrique",
    "PBPJ": "Jemuel Jiven Pakingan",
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

            result_pdf = build_result_pdf(entries, account_agent_map)

            st.success("Result PDF generated successfully.")
            st.download_button(
                label="Download Result PDF",
                data=result_pdf,
                file_name="agent_error_report.pdf",
                mime="application/pdf",
            )

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

import tkinter as tk
from tkinter import filedialog, messagebox
import pdfplumber
import pandas as pd
import re

root = tk.Tk()
root.withdraw()

file_paths = filedialog.askopenfilenames(
    title="Select PDF files",
    filetypes=[("PDF Files", "*.pdf")]
)

canara_total = 0.0
sbi_total = 0.0


def to_float(val):
    nums = re.findall(r"\d[\d,]*\.\d{2}", str(val))
    return float(nums[-1].replace(",", "")) if nums else 0.0


# =========================
# PROCESS FILES
# =========================
for file in file_paths:
    print(f"\nProcessing: {file}")

    # Detect bank by content, not filename
    is_canara = False
    with pdfplumber.open(file) as pdf:
        first_page_text = pdf.pages[0].extract_text() or ""
        if "Canara" in first_page_text or "CNRB" in first_page_text:
            is_canara = True

    if is_canara:
        # --- CANARA via pdfplumber (same engine, same logic as SBI) ---
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    if not table or len(table) < 2:
                        continue
                    headers = table[0]
                    if not headers or "Credit" not in headers:
                        continue
                    df = pd.DataFrame(table[1:], columns=headers)
                    credit_col = next(
                        (col for col in df.columns if col and "Credit" in str(col)),
                        None
                    )
                    if credit_col:
                        for val in df[credit_col]:
                            v = to_float(val)
                            if v > 0:
                                canara_total += v

    else:
        # --- SBI via pdfplumber ---
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    if not table or len(table) < 2:
                        continue
                    df = pd.DataFrame(table[1:], columns=table[0])
                    credit_col = next(
                        (col for col in df.columns if col and "CREDIT" in str(col).upper()),
                        None
                    )
                    if credit_col:
                        for val in df[credit_col]:
                            sbi_total += to_float(val)

print(f"\nCanara Credits: ₹{canara_total:,.2f}")
print(f"SBI Credits:    ₹{sbi_total:,.2f}")
print(f"TOTAL:          ₹{(canara_total + sbi_total):,.2f}")
input("Press Enter...")

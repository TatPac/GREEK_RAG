print("SCRIPT STARTED")

from pathlib import Path
from pypdf import PdfReader


# --------------------------------------------------
# Folders
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SOURCE_DIR = PROJECT_ROOT / "data" / "corpora" / "raw" / "SBLGNT_pdf"
REPLACE_DIR = PROJECT_ROOT / "data" / "corpora" / "replace"

REPLACE_DIR.mkdir(parents=True, exist_ok=True)

print(f"1")


# --------------------------------------------------
# Convert PDF to TXT
# --------------------------------------------------

def convert_pdf_to_txt(pdf_path, txt_path):

    reader = PdfReader(pdf_path)

    with open(txt_path, "w", encoding="utf-8") as output:

        for page in reader.pages:

            text = page.extract_text()

            if text:
                output.write(text)
                output.write("\n")

    print(f"Converted: {pdf_path.name}")
    print(f"Saved to:    {txt_path}")


# --------------------------------------------------
# Process PDFs
# --------------------------------------------------

for pdf_path in SOURCE_DIR.glob("*.pdf"):

    txt_path = REPLACE_DIR / f"{pdf_path.stem}.txt"

    convert_pdf_to_txt(pdf_path, txt_path)

print(f"2")

print("\nFinished.")
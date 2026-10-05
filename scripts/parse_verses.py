
from pathlib import Path
import json


PROJECT_ROOT = Path(__file__).resolve().parent.parent

READY_DIR = PROJECT_ROOT / "data" / "corpora" / "ready"
PARSED_DIR = PROJECT_ROOT / "data" / "corpora" / "parsed"

def load_corpus(corpus_file):
    with open(corpus_file, "r", encoding="utf-8") as f:
        return json.load(f)

def parse_verses(ready_file): 

    verses =[]

    current_book = None
    page_number = None
    current_chapter = 0
    current_verse = 0
    current_text = []
    Skipping = False
    warnings = []

    with open(ready_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip().isdigit():
                page_number = int(line.strip())
                Skipping = False
                if current_book is None:
                    current_book = next(f).strip()
                continue

            words = line.split()

            for word in words:

                if ":" in word:
                          
                    chapter, verse = word.split(":", 1)
                    if not chapter.isdigit() or not verse.isdigit():
                        continue  
                    chapter = int(chapter)
                    verse = int(verse)

                    if verse == 1 and chapter == current_chapter+1:
                        if chapter > 1:
                            record = {
                                "book": current_book,
                                "chapter": current_chapter,
                                "verse": current_verse,
                                "text": " ".join(current_text).strip(),
                                "page_number": page_number
                            }

                            verses.append(record)
                            current_text = []
                            Skipping = False
                        current_verse = 1
                        current_chapter = chapter
                    else:
                        Skipping = True

                elif word.isdigit():
                    digit = int(word)
                    if current_verse == digit-1:
    
                        record = {
                            "book": current_book,
                            "chapter": current_chapter,
                            "verse": current_verse,
                            "text": " ".join(current_text).strip(),
                            "page_number": page_number
                        }

                        verses.append(record)
                        current_text = []
                        current_verse = digit
                        Skipping = False

                    elif current_verse < digit:
                        warnings.append(f"Unexpected verse number: {digit} at page {page_number}, chapter {current_chapter}, verse {current_verse}")
                        record = {
                            "book": current_book,
                            "chapter": current_chapter,
                            "verse": current_verse,
                            "text": " ".join(current_text).strip(),
                            "page_number": page_number
                        }

                        verses.append(record)
                        current_text = []
                        current_verse = digit



                else:
                    if Skipping:
                        continue
                    current_text.append(word)

    return verses, warnings

def write_jsonl(verses, output_file):
    with open(output_file, "w", encoding="utf-8") as f:
        for record in verses:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def main():

    ready_file = READY_DIR / "61-SBLGNT-Matthew.txt"

    verses, warnings = parse_verses(ready_file)

    output_file = PARSED_DIR / "matthew_test4.jsonl"
    warnings_file = PARSED_DIR / "matthew_test4_warnings.jsonl"

    write_jsonl(verses, output_file)
    write_jsonl(warnings, warnings_file)


if __name__ == "__main__":
    main()
import re
from pathlib import Path
import fitz  # PyMuPDF
import pyttsx3

def extract_text(pdf_path: str) -> str:
    doc = fitz.open(pdf_path)
    return "\n".join(page.get_text("text") for page in doc)

def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"(\w)-\s+(\w)", r"\1\2", text)
    return text.strip()

def chunk_text(text: str, max_chars: int = 1500):
    return [text[i:i + max_chars] for i in range(0, len(text), max_chars)]

def text_to_wav(chunks, out_dir="audio_out", rate=175):
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    engine = pyttsx3.init()
    engine.setProperty("rate", rate)

    for i, chunk in enumerate(chunks, start=1):
        out_file = Path(out_dir) / f"part_{i:03d}.wav"
        engine.save_to_file(chunk, str(out_file))
        engine.runAndWait()
        print(f"Saved: {out_file}")

if __name__ == "__main__":
    pdf_path = "book.pdf"
    raw = extract_text(pdf_path)

    if not raw.strip():
        print("No text found in this PDF (might be scanned).")
        exit()

    cleaned = clean_text(raw)
    chunks = chunk_text(cleaned)
    text_to_wav(chunks)
    print("Done! Check the audio_out folder.")

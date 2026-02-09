import argparse
import re
from pathlib import Path

import fitz  # PyMuPDF
import pyttsx3


def extract_text(pdf_path: Path) -> str:
    doc = fitz.open(str(pdf_path))
    try:
        return "\n".join(page.get_text("text") for page in doc)
    finally:
        doc.close()


def clean_text(text: str) -> str:
    text = text.replace("\u00ad", "")  # soft hyphen (common in PDFs)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"(\w)-\s+(\w)", r"\1\2", text)  # fix hyphenation across line breaks
    return text.strip()


def chunk_by_sentences(text: str, max_chars: int = 1500) -> list[str]:
    # Split on sentence boundaries (simple + effective)
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[str] = []
    buf = ""

    for s in sentences:
        if not s:
            continue
        if len(buf) + len(s) + 1 <= max_chars:
            buf = (buf + " " + s).strip()
        else:
            if buf:
                chunks.append(buf)
            # If a single sentence is huge, fall back to hard chunking
            if len(s) > max_chars:
                for i in range(0, len(s), max_chars):
                    chunks.append(s[i:i + max_chars])
                buf = ""
            else:
                buf = s

    if buf:
        chunks.append(buf)

    return chunks


def text_to_wav(chunks: list[str], out_dir: Path, rate: int = 175) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    engine = pyttsx3.init()
    engine.setProperty("rate", rate)

    # Queue all files first, then run once (faster + cleaner)
    for i, chunk in enumerate(chunks, start=1):
        out_file = out_dir / f"part_{i:03d}.wav"
        engine.save_to_file(chunk, str(out_file))
        print(f"Queued: {out_file}")

    engine.runAndWait()
    print(f"Saved {len(chunks)} file(s) to: {out_dir}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Convert a text-based PDF into WAV audiobook parts.")
    p.add_argument("pdf", nargs="?", default="book.pdf", help="Path to the PDF (default: book.pdf)")
    p.add_argument("--out", default="audio_out", help="Output directory (default: audio_out)")
    p.add_argument("--rate", type=int, default=175, help="Speech rate (default: 175)")
    p.add_argument("--max-chars", type=int, default=1500, help="Max chars per chunk (default: 1500)")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        raise SystemExit(f"Error: PDF not found at: {pdf_path.resolve()}")

    try:
        raw = extract_text(pdf_path)
    except Exception as e:
        raise SystemExit(f"Error: failed to read PDF ({pdf_path.name}): {e}")

    if not raw.strip():
        raise SystemExit("No text found in this PDF (it might be scanned). Try a different PDF.")

    cleaned = clean_text(raw)
    chunks = chunk_by_sentences(cleaned, max_chars=args.max_chars)

    if not chunks:
        raise SystemExit("No usable text chunks produced after cleaning.")

    text_to_wav(chunks, out_dir=Path(args.out), rate=args.rate)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Knowledge Ingestion Script - The "Superhuman Converter" V2

This script ingests PDF, Word, Excel, Image, or text files, chunks them into semantic units,
and prepares them for the Memory Agent.

Usage:
    python scripts/ingest_knowledge.py <file_path> [--url http://localhost:8000/memories]

Requirements:
    pip install pypdf requests python-docx openpyxl pandas pillow pytesseract
"""

import argparse
import json
import os
import sys
from typing import List, Dict

# Lazy imports to avoid startup crash if deps missing
try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    import docx
except ImportError:
    docx = None

try:
    import pandas as pd
except ImportError:
    pd = None

try:
    from PIL import Image
    import pytesseract
except ImportError:
    Image = None
    pytesseract = None

# Configuration
CHUNK_SIZE = 1000  # Characters per chunk
OVERLAP = 100      # Overlap between chunks

def read_pdf(path: str) -> str:
    """Reads text from a PDF file."""
    if PdfReader is None:
        raise ImportError("pypdf is required for PDF ingestion")

    try:
        reader = PdfReader(path)
        full_text = []
        print(f"📖 Reading PDF: {path} ({len(reader.pages)} pages)...")
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                full_text.append(text)
        return "\n".join(full_text)
    except Exception as e:
        print(f"❌ Error reading PDF: {e}")
        sys.exit(1)

def read_docx(path: str) -> str:
    """Reads text from a Word file."""
    if docx is None:
        raise ImportError("python-docx is required for Word ingestion")

    try:
        doc = docx.Document(path)
        print(f"📖 Reading Word Doc: {path} ({len(doc.paragraphs)} paragraphs)...")
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        print(f"❌ Error reading DOCX: {e}")
        sys.exit(1)

def read_xlsx(path: str) -> str:
    """Reads text from an Excel file."""
    if pd is None:
        raise ImportError("pandas and openpyxl are required for Excel ingestion")

    try:
        print(f"📖 Reading Excel: {path}...")
        dfs = pd.read_excel(path, sheet_name=None)
        full_text = []
        for sheet_name, df in dfs.items():
            full_text.append(f"--- Sheet: {sheet_name} ---")
            full_text.append(df.to_string())
        return "\n\n".join(full_text)
    except Exception as e:
        print(f"❌ Error reading Excel: {e}")
        sys.exit(1)

def read_image(path: str) -> str:
    """Reads text from an Image using OCR."""
    if Image is None or pytesseract is None:
        raise ImportError("pillow and pytesseract are required for Image OCR")

    try:
        print(f"👁️ Reading Image (OCR): {path}...")
        img = Image.open(path)
        text = pytesseract.image_to_string(img)
        if not text.strip():
            print("⚠️ Warning: OCR returned empty text.")
        return text
    except Exception as e:
        print(f"❌ Error reading Image: {e}")
        sys.exit(1)

def read_text_file(path: str) -> str:
    """Reads text from a plain text file."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        sys.exit(1)

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> List[str]:
    """Splits text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks

def prepare_payloads(chunks: List[str], filename: str) -> List[Dict]:
    """Prepares JSON payloads for Memory Agent."""
    payloads = []
    base_name = os.path.basename(filename)
    ext = os.path.splitext(filename)[1].lower().replace('.', '')

    for i, chunk in enumerate(chunks):
        payload = {
            "content": chunk,
            "tags": ["ingested", f"{ext}_import", base_name, f"chunk_{i}"]
        }
        payloads.append(payload)
    return payloads

def main():
    parser = argparse.ArgumentParser(description="Ingest knowledge from files into Memory Agent format.")
    parser.add_argument("file", help="Path to the file (PDF, DOCX, XLSX, JPG, PNG, TXT)")
    parser.add_argument("--url", help="Memory Agent API URL (e.g., http://localhost:8001/memories)", default=None)
    parser.add_argument("--dry-run", action="store_true", help="Print payloads without sending", default=False)

    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"❌ File not found: {args.file}")
        sys.exit(1)

    ext = os.path.splitext(args.file)[1].lower()

    # 1. Select Strategy
    if ext == '.pdf':
        content = read_pdf(args.file)
    elif ext == '.docx':
        content = read_docx(args.file)
    elif ext == '.xlsx':
        content = read_xlsx(args.file)
    elif ext in ['.png', '.jpg', '.jpeg']:
        content = read_image(args.file)
    else:
        content = read_text_file(args.file)

    if not content:
        print("⚠️  Warning: No content extracted from file.")
        sys.exit(0)

    print(f"✅ Extracted {len(content)} characters.")

    # 2. Chunk Content
    chunks = chunk_text(content)
    print(f"🧩 Split into {len(chunks)} chunks.")

    # 3. Prepare Payloads
    payloads = prepare_payloads(chunks, args.file)

    # 4. Output or Send
    if args.url and not args.dry_run:
        import httpx
        print(f"🚀 Sending to Memory Agent at {args.url}...")
        success_count = 0
        for p in payloads:
            try:
                response = httpx.post(args.url, json=p)
                if response.status_code == 200:
                    success_count += 1
                    print(f"  - Chunk {p['tags'][-1]} sent ✅")
                else:
                    print(f"  - Chunk {p['tags'][-1]} failed ❌ ({response.status_code})")
            except Exception as e:
                print(f"  - Connection error: {e}")
                break
        print(f"🏁 Completed. Sent {success_count}/{len(payloads)} chunks.")
    else:
        print("\n📦 Generated Payloads (JSON Preview):")
        print(json.dumps(payloads[:3], indent=2, ensure_ascii=False))
        if len(payloads) > 3:
            print(f"... and {len(payloads) - 3} more chunks.")

        # Save to file for inspection
        output_file = f"{args.file}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(payloads, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Full output saved to {output_file}")

if __name__ == "__main__":
    main()

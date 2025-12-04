import io
import pdfplumber
from tika import parser




def parse_pdf(pdf_bytes: bytes) -> str:
"""Try fast extract via pdfplumber; fallback to tika if needed."""
try:
with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
pages = [p.extract_text() or '' for p in pdf.pages]
text = '\n\n'.join(pages).strip()
if len(text) > 200:
return text
except Exception:
pass
# fallback to Tika
parsed = parser.from_buffer(pdf_bytes)
text = parsed.get('content') or ''
return text.strip()

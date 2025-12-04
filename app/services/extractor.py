import re
from typing import Dict, Any




def extract_metadata(text: str) -> Dict[str, Any]:
"""Extract headline fields from RBI circulars / policy PDFs.
This is intentionally simple: headline, circular_no, date, subject, affected_entities
Extend with better NER for production.
"""
out = {
'headline': None,
'circular_no': None,
'date': None,
'subject': None,
'affected_entities': []
}


# Attempt to find 'Circular No. X' patterns
m = re.search(r'Circular\s+No\.?\s*[:#]?\s*(\S+)', text, re.I)
if m:
out['circular_no'] = m.group(1)


# Very naive date search (improve with dateparser)
m = re.search(r'(\d{1,2}\s+\w+\s+\d{4})', text)
if m:
out['date'] = m.group(1)


# Subject line heuristics
m = re.search(r'Subject[:]?(.*)\n', text, re.I)
if m:
out['subject'] = m.group(1).strip()


# Headline: first non-empty line
for line in text.splitlines():
s = line.strip()
if s:
out['headline'] = s
break


# Look for known entity words
for ent in ['NBFC', 'PSP', 'Payment', 'Bank', 'PPI', 'NPCI']:
if re.search(r'\b' + re.escape(ent) + r'\b', text, re.I):
out['affected_entities'].append(ent)


return out

from pathlib import Path
import re
from pypdf import PdfReader
path = Path(r'E:\PROJECTS\RenderX-main\output\pdf\RenderX_Milestone_04_Testing_and_Validation.pdf')
pdf = PdfReader(str(path))
texts = [(page.extract_text() or '') for page in pdf.pages]
text = '\n'.join(texts)
assert len(pdf.pages) == 17, len(pdf.pages)
assert all(len(page.strip()) > 150 for page in texts), [i+1 for i,p in enumerate(texts) if len(p.strip()) <= 150]
figures = [int(n) for n in re.findall(r'Figure\s+(\d+)\.', text)]
tables = [int(n) for n in re.findall(r'Table\s+(\d+)\.', text)]
listings = [int(n) for n in re.findall(r'Listing\s+(\d+)\.', text)]
assert figures == list(range(1,24)), figures
assert tables == list(range(1,19)), tables
assert listings == list(range(1,8)), listings
assert all(abs(float(p.mediabox.width)-595.276) < .5 and abs(float(p.mediabox.height)-841.89) < .5 for p in pdf.pages)
assert not any(x in text for x in ['Declaration', 'Acknowledgement', 'Roll no.'])
dashes = sorted(set(c for c in text if ord(c) in range(0x2010,0x2016) or ord(c)==0x2212))
print('OK pages=17 A4; figures=1-23; tables=1-18; listings=1-7; no blank pages or personal-detail pages')
print('Non-ASCII dash characters:', [f'U+{ord(c):04X}' for c in dashes])
print('Size bytes:', path.stat().st_size)

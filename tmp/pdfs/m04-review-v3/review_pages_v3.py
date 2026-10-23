from pathlib import Path
from PIL import Image, ImageDraw
from pypdf import PdfReader
base = Path(r'E:\PROJECTS\RenderX-main\tmp\pdfs\m04-review-v3')
files = sorted(base.glob('page-*.png'), key=lambda p: int(p.stem.split('-')[-1]))
for start in range(0, len(files), 4):
    thumbs = []
    for path in files[start:start+4]:
        im = Image.open(path).convert('RGB')
        im.thumbnail((390, 555))
        canvas = Image.new('RGB', (410, 585), 'white')
        canvas.paste(im, ((410-im.width)//2, 25))
        ImageDraw.Draw(canvas).text((12, 6), path.stem, fill='#21364b')
        thumbs.append(canvas)
    sheet = Image.new('RGB', (820, 1170), '#d8e1e6')
    for i, im in enumerate(thumbs):
        sheet.paste(im, ((i%2)*410, (i//2)*585))
    out = base / f'contact-{start//4+1}.png'
    sheet.save(out)
    print(out)
pdf = PdfReader(r'E:\PROJECTS\RenderX-main\output\pdf\RenderX_Milestone_04_Testing_and_Validation.pdf')
print('PAGE_COUNT', len(pdf.pages))
for i, page in enumerate(pdf.pages, 1):
    text = (page.extract_text() or '').replace('\n', ' ')
    print(f'{i:02d} chars={len(text):4d} start={text[:115]}')
whole = '\n'.join((p.extract_text() or '') for p in pdf.pages)
for term in ['Declaration', 'Acknowledgement', 'Roll no.', 'F01-F10', 'Fixed (checked)', 'Not measured', 'Figure 23.', 'Figure 8.']:
    print('TERM', repr(term), term in whole)


"""Render the logo marks to PNG, export Figure 1's illustration, copy the PDF, and write authors and contents to meta.json.
The other figures are not rendered: the page uses their SVG from tools/figures/.
python3 tools/prep_assets.py <paper repo, compiled> <site dir> [--with-pdf]
The paper PDF is copied into the site only with --with-pdf: it stays out until the paper is public.
"""
import fitz, json, re, shutil, sys
from pathlib import Path
S = Path(sys.argv[1]); OUT = Path(sys.argv[2]) / 'assets'
WITH_PDF = '--with-pdf' in sys.argv[3:]
for d_ in ('figures', 'logos') + (('paper',) if WITH_PDF else ()):
    (OUT / d_).mkdir(parents=True, exist_ok=True)
dims = {}
# Figure 1's illustration, with its white point moved so that its paper is pure white and it sits on the page without an edge.
pm = fitz.Pixmap(str(S / 'figures/paper/assets/enterprise-cutaway/illustration.png'))
if pm.alpha or pm.n != 3:
    pm = fitz.Pixmap(fitz.csRGB, pm)
table = bytes(min(255, round(v * 255 / 250)) for v in range(256))
fitz.Pixmap(fitz.csRGB, pm.width, pm.height, bytes(pm.samples).translate(table), False).save(OUT / 'figures/cutaway.jpg', jpg_quality=90)
for p in sorted(p for p in (S / 'figures/pdf2/marks').glob('*.pdf') if not p.name.startswith('icon-')):
    d = fitz.open(p); pg = d[0]
    z = 112 / pg.rect.height
    pm = pg.get_pixmap(matrix=fitz.Matrix(z, z)); pm.save(OUT / f'logos/{p.stem}.png'); dims[p.stem] = [pm.width, pm.height]
shutil.copy(S / 'figures/pdf2/boundary-logo.png', OUT / 'logos/boundary.png')
if WITH_PDF:
    shutil.copy(S / 'main.pdf', OUT / 'paper/from-assistants-to-coworkers.pdf')
# authors and affiliations, exactly as in main.tex
tex = (S / 'main.tex').read_text()
authors = [(m.group(1), m.group(2).split(',')) for m in re.finditer(r'\\mbox\{([^\\]+?)\\textsuperscript\{([\d,]+)\}\}', tex)]
affs = [(int(m.group(1)), m.group(2), m.group(3).strip()) for m in re.finditer(r'\\mbox\{\\textsuperscript\{(\d+)\}\\instmark\{([a-z]+)\}([^}]+)\}', tex)]
assert authors and affs
d = fitz.open(S / 'main.pdf')
toc = [[l, t, p] for l, t, p in d.get_toc() if l <= 2]
json.dump({'authors': authors, 'affiliations': affs, 'toc': toc, 'dims': dims, 'pages': d.page_count}, open(Path(__file__).parent / 'meta.json', 'w'), indent=1)
print(len(authors), 'authors;', len(affs), 'affiliations;', len(toc), 'toc entries;', d.page_count, 'pages')
print(authors[:3], affs[:3])

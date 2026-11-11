"""Build index.html from the paper's sources, so the tables, authors, captions and contents match the paper.
python3 tools/build_site.py <paper repo, compiled> <site dir>      (run tools/prep_assets.py first)
"""
import html, json, re, sys
from pathlib import Path
S = Path(sys.argv[1]); OUT = Path(sys.argv[2])
meta = json.load(open(Path(__file__).parent / 'meta.json'))
dims = meta['dims']

def tex(s):
    """Small TeX fragments to HTML."""
    s = s.replace('\\&', '&amp;').replace('--', '–').replace("``", '“').replace("''", '”').replace("'", '’').replace('~', ' ')
    s = re.sub(r'\$\^\\dagger\$', '<sup>†</sup>', s)
    s = re.sub(r'\\textbf\{([^{}]*)\}', r'<strong>\1</strong>', s)
    s = re.sub(r'\\emph\{([^{}]*)\}', r'<em>\1</em>', s)
    return ' '.join(s.split())

def table_block(path, label):
    s = (S / path).read_text()
    return [m.group(0) for m in re.finditer(r'\\begin\{table\*?\}.*?\\end\{table\*?\}', s, re.S) if f'\\label{{{label}}}' in m.group(0)][0]

def cell(c):
    c = c.strip()
    sub = re.search(r'\\newline\\tbsub\{([^{}]*)\}', c)
    if sub:
        c = c.replace(sub.group(0), '')
    items = [tex(i) for i in c.split('\\tbitem')]
    out = ''.join(f'<span class="item">{i}</span>' for i in items) if len(items) > 1 else items[0]
    return out + (f'<span class="sub">{tex(sub.group(1))}</span>' if sub else '')

def rows(block):
    for line in block.split('\n'):
        line = line.strip()
        g = re.match(r'\\tbgroup\{\d+\}\{(.*)\}$', line)
        if g:
            yield 'group', g.group(1)
        elif line.startswith('\\tbrow'):
            body = re.sub(r'\\\\\s*(\\tbgap)?\s*$', '', line[len('\\tbrow'):])
            yield 'row', [c for c in body.split(' & ')]

def logo(c):
    m = re.search(r'\\tbmark\{([^}]+)\}', c)
    w, h = dims[m.group(1)]
    return f'<td class="logo"><img src="assets/logos/{m.group(1)}.png" alt="" width="{w}" height="{h}" loading="lazy"></td>'

# ---- products table
prod = table_block('sections/05-integration.tex', 'tab:products')
prod_rows = []
for kind, r in rows(prod):
    name = r[1]
    prod_rows.append('<tr>' + logo(r[0]) + f'<td class="name">{cell(name)}</td>' + ''.join(f'<td>{cell(c)}</td>' for c in r[2:]) + '</tr>')
PRODUCTS = ('<table class="ptable"><thead><tr><th></th><th>Product</th><th>Reaches data and tools through</th><th>Acts with the rights of</th>'
            '<th>Checked before acting by</th><th>Records</th></tr></thead><tbody>' + ''.join(prod_rows) + '</tbody></table>')

# ---- frameworks: a comparison written for the page (frameworks across the top, one row per question)
itext = ' '.join((S / 'sections/05-integration.tex').read_text().split())
QUESTIONS = re.findall(r'\\emph\{(Enforced limits|Records|Data isolation|Safe updates|Realistic tests)\}: (.*?\?)', itext)
assert [q for q, _ in QUESTIONS] == ['Enforced limits', 'Records', 'Data isolation', 'Safe updates', 'Realistic tests']
FW_LEAD = ['Limits and records are now common.', 'Data isolation is the main gap.', 'No framework covers all five questions.']
for _x in FW_LEAD:
    assert _x in itext, _x
LEVEL = {'\\fwyes': (2, 'built in'), '\\fwpart': (1, 'partly built in, or possible with extra work'),
         '\\fwno': (0, 'not described in the official documentation')}
MARK = {2: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>',
        1: 'Partly', 0: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><path d="M8 12h8"/></svg>'}
fw = table_block('sections/05-integration.tex', 'tab:frameworks')
fws, groups = [], []
for kind, r in rows(fw):
    if kind == 'group':
        groups.append([tex(r), 0])
    else:
        key = re.search(r'\\tbmark\{([^}]+)\}', r[0]).group(1)
        groups[-1][1] += 1
        fws.append((key, tex(r[1]), re.sub(r'<[^>]+>', '', tex(r[1])).rstrip('†'), [LEVEL[c.strip()] for c in r[2:]]))
assert len(prod_rows) == 10 and len(fws) == 9 and [n for _, n in groups] == [5, 4]
_split = groups[0][1]            # the first column of the second group
SP = '<td class="sp"></td>'
_head = ''.join(f'{SP if i == _split else ""}<th scope="col" data-c="{i}"><span class="tile"><img src="assets/logos/{k}.png" alt="" width="{dims[k][0]}" height="{dims[k][1]}" loading="lazy"></span>'
                f'<span class="nm">{name}</span></th>' for i, (k, name, plain, _) in enumerate(fws))
_body = ''
for qi, (q, ask) in enumerate(QUESTIONS):
    cells = ''
    for i, (k, name, plain, lv) in enumerate(fws):
        n, words = lv[qi]
        cells += (f'{SP if i == _split else ""}<td data-c="{i}" data-name="{html.escape(plain)}" class="l{n}">'
                  f'<span class="lvl" role="img" aria-label="{words}" title="{html.escape(plain)}: {words}">{MARK[n]}</span></td>')
    _body += f'<tr><th scope="row"><b>{q}</b><span>{tex(ask[0].upper() + ask[1:])}</span></th>{cells}</tr>'
FRAMEWORKS = ('<table class="compare"><colgroup><col class="q">' + '<col>' * _split + '<col class="sp">' + '<col>' * (len(fws) - _split) + '</colgroup>'
              '<thead><tr class="grp"><td></td>'
              + SP.join(f'<th scope="colgroup" colspan="{n}"><span>{g}</span></th>' for g, n in groups)
              + f'</tr><tr class="who"><td></td>{_head}</tr></thead><tbody>{_body}</tbody></table>')

# ---- authors
AUTHORS = ', '.join(f'<span>{html.escape(n)}<sup>{",".join(a)}</sup></span>' for n, a in meta['authors'])
AFFILS = ''.join(f'<li><sup>{i}</sup><img src="assets/logos/inst-{k}.png" alt="" width="{dims["inst-" + k][0]}" height="{dims["inst-" + k][1]}">{html.escape(n)}</li>'
                 for i, k, n in meta['affiliations'])
def bibname(n):
    n = n.replace(' (Jason)', '')
    parts = n.split()
    last = 'Joty' if n.startswith('Shafiq') else parts[-1]
    first = n[:n.rindex(last)].strip()
    return f'{last}, {first}'
BIB = ('@misc{ma2026assistants,\n  title  = {From Assistants to Coworkers: {AI} Agents in the Enterprise},\n  author = {'
       + ' and '.join(bibname(n) for n, _ in meta['authors']) + '},\n  year   = {2026},\n  note   = {Preprint}\n}')

# ---- text copied from the paper
abstract = (S / 'sections/00-abstract.tex').read_text()
ABSTRACT = tex(abstract)
d = (S / 'sections/02-definitions.tex').read_text()
box = re.search(r'\\begin\{defbox\}(.*?)\\end\{defbox\}', d, re.S).group(1)
clauses = re.search(r'\\textbf\{\(i\)\}(.*?);\s*\\textbf\{\(ii\)\}(.*?);\s*and\s*\\textbf\{\(iii\)\}(.*?)\.\s*\\smallskip', box, re.S)
CLAUSES = [tex(c).strip() for c in clauses.groups()]
STANDING = tex(re.search(r'\\noindent (Some enterprise agents.*?each case\.)', box, re.S).group(1))
cad = re.search(r'\\textbf\{Capability\} is (.*?)\.\s*\\textbf\{Authority\} is (.*?)\.\s*\\textbf\{Delegation\} is (.*?)\.', d, re.S)
CAD = [tex(x) for x in cad.groups()]
b = (S / 'sections/12b-practice-boundary.tex').read_text()
PRINCIPLE = tex(re.search(r'Boundary rests on one principle: \\emph\{(.*?)\}', b, re.S).group(1))


INCLUDED = ['01-introduction', '02-definitions', '03-formal-framework', '04-capabilities', '10-applications-revised2', '05-integration',
            '06-coordination', '06b-agent-organizations', '08-evaluation', '07-risks-governance', '12-challenges', '12b-practice-boundary']

def caption(name):
    """The caption of the figure that includes figures/pdf2/<name>.pdf, copied from the paper."""
    for f in INCLUDED:
        t_ = (S / f'sections/{f}.tex').read_text()
        i = t_.find(f'figures/pdf2/{name}.pdf')
        if i < 0:
            continue
        j = t_.index('\\caption{', i) + len('\\caption{')
        depth, k = 1, j
        while depth:
            depth += {'{': 1, '}': -1}.get(t_[k], 0); k += 1
        c = t_[j:k - 1]
        c = re.sub(r'\s*\(\\Cref\{[^}]*\}\)', '', c)
        c = re.sub(r'\s*All sources are cited in \\Cref\{[^}]*\}\.', '', c)
        assert '\\Cref' not in c and '\\cite' not in c, c
        return tex(c)
    raise KeyError(name)

import fitz
_pdf = fitz.open(S / 'main.pdf')
_caps = {}
for _pg in _pdf:
    for m in re.finditer(r'Figure (\d+): ([^\n]{0,40})', _pg.get_text()):
        _caps[m.group(2)[:24]] = int(m.group(1))

FIGDIR = Path(__file__).parent / 'figures'      # the figures' own SVG, as written by the paper's figure generators

def fig(name, alt, cls=''):
    """A figure set straight into the page as its original SVG: vector, real text in the page's face, no frame."""
    cap = caption(name)
    plain = html.unescape(re.sub(r'<[^>]+>', '', cap))
    num = next(n for k, n in _caps.items() if plain.startswith(k) or plain.replace('’', "'").startswith(k))
    svg = (FIGDIR / f'{name}.svg').read_text()
    m = re.match(r'<svg[^>]*viewBox="0 0 ([\d.]+) ([\d.]+)"[^>]*>', svg)
    body, n = re.subn(r'^<rect width="[\d.]+" height="[\d.]+" fill="#fff"/>', '', svg[m.end():])
    assert n == 1, name                                      # the white sheet is dropped; the page is the ground
    body = re.sub(r'\bid="([^"]+)"', lambda g: f'id="{name}-{g.group(1)}"', body)
    body = re.sub(r'url\(#([^)]+)\)', lambda g: f'url(#{name}-{g.group(1)})', body)
    return (f'<figure class="fig {cls}" data-reveal><div class="fig-scroll" data-zoom tabindex="0" role="button" aria-label="Enlarge figure {num}">'
            f'<svg class="diagram" viewBox="0 0 {m.group(1)} {m.group(2)}" role="img" aria-label="{html.escape(alt)}">{body}</div>'
            f'<figcaption><b>Figure {num}.</b>{cap}</figcaption></figure>')

def cutaway():
    """Figure 1: the illustration as an image, with its labels and leaders as live SVG text."""
    src = (S / 'figures/paper/stack.svg').read_text()
    body = src[src.index('<image'):src.rindex('</svg>')]
    body = re.sub(r'<image id="enterprise-cutaway"([^>]*?)xlink:href="data:image/png;base64,[^"]*"/>',
                  r'<image\1href="assets/figures/cutaway.jpg"/>', body)
    assert 'base64' not in body
    body = body.replace(' font-family="Arial"', '').replace('font-weight="bold"', 'font-weight="800"').replace('font-weight="normal"', 'font-weight="400"')
    return ('<svg class="diagram cutaway-art" viewBox="0 0 600 345" role="img" aria-label="A cutaway drawing of an office. Its rooms stand for capabilities, '
            'integration, coordination and governance, and the street outside for work, firms and markets.">' + body + '</svg>')

ICON = {
 'pdf': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M16 13H8"/><path d="M16 17H8"/><path d="M10 9H8"/></svg>',
 'cpu': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect width="16" height="16" x="4" y="4" rx="2"/><rect width="6" height="6" x="9" y="9" rx="1"/><path d="M15 2v2"/><path d="M15 20v2"/><path d="M2 15h2"/><path d="M2 9h2"/><path d="M20 15h2"/><path d="M20 9h2"/><path d="M9 2v2"/><path d="M9 20v2"/></svg>',
 'key': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2.586 17.414A2 2 0 0 0 2 18.828V21a1 1 0 0 0 1 1h3a1 1 0 0 0 1-1v-1a1 1 0 0 1 1-1h1a1 1 0 0 0 1-1v-1a1 1 0 0 1 1-1h.172a2 2 0 0 0 1.414-.586l.814-.814a6.5 6.5 0 1 0-4-4z"/><circle cx="16.5" cy="7.5" r=".5" fill="currentColor"/></svg>',
 'work': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M16 20V4a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/><rect width="20" height="14" x="2" y="6" rx="2"/></svg>',
}
PDF = 'assets/paper/from-assistants-to-coworkers.pdf'
HAS_PDF = (OUT / PDF).exists()     # the PDF is left out until the paper is public; prep_assets.py --with-pdf adds it
def pdf_link(cls, label, page=''):
    return f'<a class="{cls}" href="{PDF}{page}">{ICON["pdf"]}{label}</a>' if HAS_PDF else ''
import hashlib
def ver(name):
    """Version assets so browsers refresh changed styles, scripts and brand images."""
    return name + '?v=' + hashlib.sha1((OUT / name).read_bytes()).hexdigest()[:8]
# The selected puzzle logo, exported by tools/brand_icon.py and versioned for browser caches.
MARK = f'<span class="mark"><img src="{ver("assets/brand/icon.png")}" alt="" width="256" height="256"></span>'
PROBLEMS = [('Benchmarks as predictors of deployment outcomes', 'A benchmark tells us something about a deployment only if its results predict what happens after the agent is deployed.'),
            ('Combining and passing on authority', 'Access control today checks one request at a time. Agents create cases that such checks miss.'),
            ('Auditing agents', 'To hold an agent accountable, someone outside it must be able to rebuild what it did from evidence they can trust.'),
            ('Self-improvement and recursive self-improvement', 'Agents now change while they are in use. They rewrite their memory, skills, tools, and sometimes their own code.'),
            ('Agents that expand their own authority', 'In enterprises, the means to do so are often close at hand, such as credentials left on the machines that agents run on.'),
            ('Group behavior under broader authority', 'Group behavior matters more as agents receive broader authority and longer-running work.'),
            ('Work, employment, and human authority', 'The first question is whether enterprise agents will replace most employees. So far the evidence points both ways.')]
# every line above is a sentence of Section 10
_ch = ' '.join(re.sub(r'\\citep\{[^}]*\}', '', (S / 'sections/12-challenges.tex').read_text()).split()).replace(' .', '.')
for _t, _s in PROBLEMS:
    for _sent in re.split(r'(?<=\.) ', _s):
        assert _sent in _ch, _sent
ten = [t for l, t, p in meta['toc'] if l == 2 and t.lower() in {x.lower() for x, _ in PROBLEMS}]
assert len(ten) == 7, ten
AUTHORS = ''.join(f'<span data-a="{",".join(a)}">{html.escape(n)}<sup>{",".join(a)}</sup></span>' for n, a in meta['authors'])
AFFILS = ''.join(f'<li data-n="{i}"><b>{i}</b><img src="assets/logos/inst-{k}.png" alt="" width="{dims["inst-" + k][0]}" height="{dims["inst-" + k][1]}">{html.escape(n)}</li>'
                 for i, k, n in meta['affiliations'])


# ---------- parts written for the page in place of paper figures; their words and numbers are checked against the paper ----------
def ico(inner):
    return ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" '
            f'stroke-linejoin="round" aria-hidden="true">{inner}</svg>')

def figure_icons(name):
    """The line icons of one of the paper's figures, in drawing order."""
    return [ico(g) for g in re.findall(r'<g transform="[^"]*" fill="none"[^>]*stroke-linejoin="round">(.*?)</g>', (FIGDIR / f'{name}.svg').read_text(), re.S)]

def figure_text(name):
    return ' '.join(html.unescape(re.sub(r'<[^>]+>', '', x)) for x in re.findall(r'<text[^>]*>(.*?)</text>', (FIGDIR / f'{name}.svg').read_text(), re.S))

def said_in(text, *phrases):
    flat = ' '.join(text.split())
    for ph in phrases:
        assert ' '.join(ph.split()) in flat, ph

def paper_text(path):
    return ' '.join((S / path).read_text().replace('\\%', '%').split())

# -- three limits: each one with the link the evidence does not yet make (the paper's "transfer" figure)
LIMITS = [
    ('Better task performance does not by itself bring knowing when not to act, judgment about context, or safe recovery.',
     'Measured model capability', 'Deployment-specific tests', 'Abstention, privacy and poisoning resistance need separate tests from task skill.', 'Deployment properties'),
    ('Testing the parts does not validate the system built from them.',
     'Individually validated components', 'System-level validation', 'Workflow failures and shared errors require tests of the assembled system.', 'Validated system'),
    ('Benchmark results do not show how an agent performs when work is delegated to it over time.',
     'Benchmark results', 'Organizational evidence', 'Sustained outcomes need evaluation under actual operating conditions.', 'Organizational outcomes'),
]
_abs = ' '.join(abstract.split()).lower()
for _row in LIMITS:
    assert _row[0].lower() in _abs, _row[0]
    said_in(figure_text('transfer'), *_row[1:])
said_in(figure_text('transfer'), 'Existing evidence', 'Validation still required', 'Target claim')
LIMITS_NOTE = 'The broken links mark evidence that deployment claims still need.'
assert LIMITS_NOTE in caption('transfer')
WIRE = ('<span class="wire" aria-hidden="true"><i></i><svg viewBox="0 0 18 16"><path d="M4.5 14.5 8.5 1.5M9.5 14.5 13.5 1.5"/></svg><i></i>'
        '<svg class="tip" viewBox="0 0 8 10"><path d="M0 0 8 5 0 10z"/></svg></span>')
_ti = figure_icons('transfer')                # per row: evidence, claim, validation
assert len(_ti) == 9
def limits():
    out = ''
    for i, (claim, have, test, why, need) in enumerate(LIMITS):
        a, c, b_ = _ti[3 * i: 3 * i + 3]
        out += (f'<div class="card limit"><div class="limit-claim"><span class="numeral">{i + 1}</span><p>{claim}</p></div>'
                f'<div class="chain"><div class="node have">{a}<span>{have}</span></div>'
                f'<div class="gap"><b>{b_}{test}</b>{WIRE}</div>'
                f'<div class="node need">{c}<span>{need}</span></div></div><p class="why">{why}</p></div>')
    return ('<div class="panel limits" data-reveal><div class="limits-head"><span></span><div class="chain"><span>Existing evidence</span>'
            f'<span>Validation still required</span><span>Target claim</span></div></div><div class="cards">{out}</div></div>'
            f'<p class="table-note" data-reveal>{LIMITS_NOTE}</p>')

# -- five threat models (the paper's "threats" figure)
THREATS = [('Outside attacker', 'Hostile content or tools steer the agent', 'harms the firm and its customers'),
           ('Insider misuse', 'A person or the agent reaches beyond a role', 'leaks company data'),
           ('Surveillant employer', 'The firm uses its agents to watch staff', 'harms workers’ privacy'),
           ('Harm to customers', 'The firm’s agent exposes or misjudges people', 'harms customers'),
           ('No adversary', 'Errors, or unsafe goals with no attacker', 'harms anyone the action reaches')]
for _row in THREATS:
    said_in(figure_text('threats'), *_row)
_th = figure_icons('threats')
assert len(_th) == 5
THREATS_CAP = caption('threats')
assert THREATS_CAP.startswith('Five threat models for enterprise agents. ')
def threats():
    cards = ''.join(f'<div class="card threat{" plain" if i == 4 else ""}"><div class="threat-top"><span class="chip">{_th[i]}</span><span class="numeral">{i + 1}</span></div>'
                    f'<h4>{t_}</h4><p>{how}</p><p class="bears">{who}</p></div>' for i, (t_, how, who) in enumerate(THREATS))
    title, rest = THREATS_CAP.split('. ', 1)
    return (f'<div class="block" data-reveal><div class="block-head"><h3>{title}</h3><p>{rest}</p></div>'
            f'<div class="panel"><div class="cards c5">{cards}</div></div></div>')

# -- Boundary results as unit charts: one dot for one conversation, one ring for one attack
btext = paper_text('sections/12b-practice-boundary.tex')
TYPES = [('Compare,', 'then act', 24), ('Act only', 'if eligible', 24), ('Decline when', 'ineligible', 24),
         ('Read three,', 'one foreign', 22), ('Switch target', 'under review', 22)]
# completed conversations per task type, as drawn in the paper's figure (figures/src/build_boundary_figures.py)
MULTISTEP = {
    'GPT-6 Sol': [('Boundary', [24, 24, 24, 22, 21], 'ours'), ('Single-step', [0, 24, 24, 15, 22], 'base'),
                  ('Conventional', [0, 24, 8, 19, 22], 'base'), ('One tool per turn', [0, 19, 24, 2, 22], 'cut')],
    'Gemini 3.8 Flash': [('Boundary', [24, 24, 20, 18, 22], 'ours'), ('Single-step', [0, 24, 24, 16, 17], 'base'),
                         ('Conventional', [1, 24, 11, 22, 17], 'base')],
}
_all = sum(n for *_, n in TYPES)
_g = {n: sum(d) for n, d, _ in MULTISTEP['GPT-6 Sol']}
_f = {n: sum(d) for n, d, _ in MULTISTEP['Gemini 3.8 Flash']}
said_in(btext, f'The multi-step task set has {_all} conversations',
        f'Boundary completes {_g["Boundary"]} of {_all}, the single-step version {_g["Single-step"]}, and the conventional agent {_g["Conventional"]}',
        f'With Gemini 3.8 Flash, the counts are {_f["Boundary"]}, {_f["Single-step"]}, and {_f["Conventional"]}',
        f'Limiting Boundary to one tool call per turn removes the gain ({_g["One tool per turn"]} of {_all})',
        'Boundary solves all 24 cases that require comparing two records before acting, and the other two systems solve none',
        'Boundary gains 36.2 points with GPT-6 Sol (95% confidence interval 30.8 to 41.8) and 28.4 points with Gemini 3.8 Flash')
said_in(figure_text('boundary-multistep'), *[f'{a} {b_}' for a, b_, _ in TYPES], *[n for n, *_ in MULTISTEP['GPT-6 Sol']])
MS_CAP = caption('boundary-multistep')
MS_NOTE = 'In each group, the three systems use the same agent model. The last GPT-6 Sol row is Boundary limited to one tool call per turn.'
assert MS_CAP.startswith('Multi-step tasks by task type. ') and MS_NOTE in MS_CAP

def multistep():
    """A grid of meters: one row for each system, one meter for each task type. One table body for each agent model."""
    head = ''.join(f'<th scope="col">{a}<br>{b_}<small>of {n}</small></th>' for a, b_, n in TYPES)
    bodies = ''
    for k, (model, systems) in enumerate(MULTISTEP.items()):
        rows_ = f'<tr class="model"><th scope="rowgroup" colspan="{len(TYPES) + 2}">{model}</th></tr>'
        for name, done, kind in systems:
            cells = ''.join(f'<td><span class="meter{"" if d else " zero"}" title="{model}, {name}: {d} of {n} completed ({a} {b_})">'
                            f'<span class="track"><i style="--v:{d / n:.4f}"></i></span><b>{d}</b></span></td>' for d, (a, b_, n) in zip(done, TYPES))
            rows_ += f'<tr class="{kind}"><th scope="row">{name}</th>{cells}<td class="tot">{sum(done)}</td></tr>'
        bodies += f'<tbody data-set="{k}">{rows_}</tbody>'
    seg = ''.join(f'<button type="button" data-show="{k}" aria-pressed="{"true" if k == 0 else "false"}">{model}</button>' for k, model in enumerate(MULTISTEP))
    return (f'<div class="chart-head"><h4>{MS_CAP.split(". ")[0]}</h4><div class="seg" role="group" aria-label="Agent model" hidden>{seg}</div></div>'
            f'<div class="chart-scroll"><table class="meters"><colgroup><col class="name">{"<col>" * len(TYPES)}<col class="tot"></colgroup>'
            f'<thead><tr><td></td>{head}<th scope="col" class="tot">All<small>of {_all}</small></th></tr></thead>{bodies}</table></div>')

# 120 conversations with organizations not seen in training, 30 per Service type:
# (Service type, completed by the playbook, by Boundary, carried another organization's sign-off with the playbook, with Boundary).
# A conversation that carries another organization's sign-off does not count as completed, so the two never overlap.
LEARNING = [('Finance', 8, 26, 19, 0), ('Healthcare admin', 3, 28, 25, 0), ('HR', 9, 27, 19, 0), ('Legal', 5, 28, 24, 0)]
_pb, _bd, _pl, _bl = (sum(r[i] for r in LEARNING) for i in (1, 2, 3, 4))
said_in(btext, 'The test set has 120 conversations with 16 organizations never seen in training',
        f'It then completed {_bd} of the 120 new conversations with no foreign sign-off',
        f"completed {_pb} of 120, and {_pl} of its conversations carried another organization's sign-off")
assert _bl == 0 and all(r[1] + r[3] <= 30 and r[2] + r[4] <= 30 for r in LEARNING)
said_in(figure_text('boundary-learning'), 'Finance', 'Healthcare admin', 'HR', 'Legal', 'One global playbook', 'Boundary')
LEARN_CAP = caption('boundary-learning')
assert LEARN_CAP.startswith('Learning across organizations, on the 120 conversations with the 16 organizations not seen in training, 30 per Service type.')
assert LEARN_CAP.endswith('Without learning, none is completed.')

def ring(name, kind, done, leak, total=120):
    arcs = f'<circle class="arc{" soft" if kind == "base" else ""}" cx="60" cy="60" r="52" pathLength="{total}" style="--v:{done}"/>'
    if leak:
        arcs += f'<circle class="arc leak" cx="60" cy="60" r="52" pathLength="{total}" style="--v:{leak - 1.2}" stroke-dashoffset="-{done + 1.2}"/>'
    return (f'<figure class="ring {kind}"><div class="ring-box"><svg viewBox="0 0 120 120" role="img" aria-label="{name}: {done} of {total} completed, {leak} carried another organization’s sign-off">'
            f'<circle class="trk" cx="60" cy="60" r="52"/>{arcs}</svg><div class="ring-n"><b>{done}</b><span>of {total}</span></div></div>'
            f'<figcaption><b>{name}</b><span><i>{leak}</i> carried another organization’s sign-off</span></figcaption></figure>')

def learning():
    """Two rings for the totals, and the counts for each Service type as numbers."""
    head = ''.join(f'<th scope="col">{t_}</th>' for t_, *_ in LEARNING)
    def line(label, i, cls):
        return f'<tr class="{cls}"><th scope="row">{label}</th>' + ''.join(f'<td>{r[i]}</td>' for r in LEARNING) + '</tr>'
    return (f'<div class="chart-head"><h4>{LEARN_CAP.split(",")[0]}</h4></div>'
            f'<div class="rings">{ring("Boundary", "ours", _bd, _bl)}{ring("One global playbook", "base", _pb, _pl)}</div>'
            f'<table class="mini"><thead><tr><th scope="col">Of 30 for each Service type</th>{head}</tr></thead><tbody>'
            f'<tr class="grp"><th scope="rowgroup" colspan="{len(LEARNING) + 1}">Completed</th></tr>'
            + line('Boundary', 2, 'ours') + line('One global playbook', 1, 'base')
            + f'<tr class="grp"><th scope="rowgroup" colspan="{len(LEARNING) + 1}">Carried another organization’s sign-off</th></tr>'
            + line('Boundary', 4, 'ours') + line('One global playbook', 3, 'leak') + '</tbody></table>')

# attacks on the life cycle of authority, read from the paper's table
_auth = table_block('sections/12b-practice-boundary.tex', 'tab:boundary-authority')
_life = _auth[_auth.index('\\tbhead{Lifecycle attack}'):]
ATTACK_HEADS = [tex(h) for h in re.findall(r'\\tbhead\{([^{}]*)\}', _life)][1:4]
assert ATTACK_HEADS == ['Boundary, compromised agent', 'Boundary, model agents', 'Policy only in prompt'], ATTACK_HEADS
ATTACKS = []
for _kind, _r in rows(_life):
    _cells = [re.sub(r'\\(?:tbbest|textbf)\{([^{}]*)\}', r'\1', c).strip() for c in _r]
    ATTACKS.append((tex(_cells[0]), [tuple(int(v) for v in c.split('/')) for c in _cells[1:]]))
assert len(ATTACKS) == 6 and ATTACKS[-1][0] == 'All lifecycle attacks'
for _j in range(3):
    assert tuple(sum(r[1][_j][k] for r in ATTACKS[:5]) for k in (0, 1)) == ATTACKS[-1][1][_j]
assert [x for x in ATTACKS[-1][1]] == [(0, 26), (0, 125), (5, 126)]
ATTACK_NOTE = ('The lifecycle attacks target Boundary with a fully compromised agent and with three model agents (GPT-6 Sol, GPT-6 Luna, Gemini 3.8 Flash). '
               'They also target the same model agents given Boundary’s policy only in their prompt.')
said_in(tex(' '.join(_auth.split())), ATTACK_NOTE)
PROMPT_ONLY = 'An agent given the same policy only in its prompt reused approvals that a suspension had cancelled in 5 of 27 revival attacks.'
said_in(btext, PROMPT_ONLY)

def attacks():
    """A plain table. The two Boundary columns are marked as a band."""
    def cell(j, hit, n):
        return f'<td class="{"b" if j < 2 else ""}{" hit" if hit else ""}"><b>{hit}</b><small>of {n}</small></td>'
    head = ''.join(f'<th scope="col"{" class=b" if j < 2 else ""}>{h}</th>' for j, h in enumerate(ATTACK_HEADS))
    body = ''.join(f'<tr{" class=sum" if name == ATTACKS[-1][0] else ""}><th scope="row">{name}</th>' + ''.join(cell(j, hit, n) for j, (hit, n) in enumerate(cells)) + '</tr>'
                   for name, cells in ATTACKS)
    return (f'<div class="chart-head"><h4>Attacks that reached their goal, out of those tried</h4></div>'
            f'<div class="chart-scroll"><table class="atk"><thead><tr><th scope="col">Lifecycle attack</th>{head}</tr></thead><tbody>{body}</tbody></table></div>')
said_in(tex(' '.join(_auth.split())), 'the number of attacks that reached their goal, out of those tried')

# -- Boundary as a product: the claim, the three objects, the three problems (the paper's design and motivation figures)
bflat = ' '.join((S / 'sections/12b-practice-boundary.tex').read_text().split())
CLAIM, CLAIM_REST = PRINCIPLE.split('. ', 1)
CLAIM = CLAIM[0].upper() + CLAIM[1:] + '.'
BPAGE = next(pg for lvl, title, pg in meta['toc'] if lvl == 1 and title.startswith('Boundary'))
BSEC = [t for l, t, _ in meta['toc'] if l == 1].index(next(t for l, t, _ in meta['toc'] if l == 1 and t.startswith('Boundary'))) + 1
def cap1(x):
    return x[0].upper() + x[1:]
def grab(pattern):
    m = re.search(pattern, bflat)
    assert m, pattern
    return cap1(tex(''.join(m.groups())))
AGENT_IS = grab(r"An \\emph\{Agent\} is (what the vendor ships: the model and harness) \$[^$]*\$(, the vendor's instructions, and the tool capabilities it needs\. It carries no enterprise access\.)")
SERVICE_IS = grab(r"A \\emph\{Service\}, short for Enterprise Service, is (one organization's connector, tools, policy, data, and knowledge\. Each Service declares a type, such as finance or HR, that it shares with other organizations offering the same kind of service\.)")
CONNECTION_IS = grab(r"A \\emph\{Connection\} (binds one exact Agent version to one Service and a chosen subset of its tools\. It becomes active only when a Reviewer approves it\.)")
ALLOWED = 'A tool call is allowed only when the Agent declares the tool, the Service provides it, the Connection enables it, and the current user has permission to use it.'
FIVE = 'Before each tool call, Boundary makes five checks'
SHAPE = 'Three problems in current deployments shape the design'
TESTED = ('We test Boundary in synthetic enterprises built from twelve Service types and 72 organization configurations.',
          "A conversation succeeds only if it reaches the expected business outcome, stays within the user's authority, and ends with a reply that an independent judge accepts.")
said_in(bflat, ALLOWED, FIVE, SHAPE, *TESTED, 'The earlier sections find that many of the hardest problems of enterprise agents lie in the deployment, not in the model.')
_dt = figure_text('boundary-design')
CHECKS = ['active and unchanged', 'tool selected, and allowed for the user', 'identity from the verified user', 'arguments from declared sources',
          'a write runs once, after Reviewer approval']
SCOPES = ['guidance for every deployment', 'guidance for one organization, erased on revocation', 'guidance for every Service of its type']
REVIEWER = 'activates the Connection and approves each write'
SANDBOX = 'allowed calls run in a sandbox'
said_in(_dt, *CHECKS, *SCOPES, REVIEWER, SANDBOX, 'Docker', 'Harbor', 'AgentEnv')
_mt = figure_text('boundary-motivation')
SOLVED = [('The agent holds the grant', 'the Connection holds the grant and checks every call.'),
          ('Shared lessons leak', 'lessons live in the Agent, a Service type, or one Connection.'),
          ('Changes go live untested', 'new versions need approval; new lessons, a promotion check.')]
for _t, _a in SOLVED:
    said_in(_mt, _t, 'Boundary: ' + _a)
_m = re.search(r'Left: (.*?)\. Middle: (.*?)\. Right: (.*?)\.$', caption('boundary-motivation'))
CASES = [cap1(x) + '.' for x in _m.groups()]

def ico16(inner):
    return ('<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.25" stroke-linecap="round" '
            f'stroke-linejoin="round" aria-hidden="true">{inner}</svg>')
_di = [ico16(g) for g in re.findall(r'<g transform="translate\([^"]*" fill="none" stroke="#[0-9A-Fa-f]{6}"[^>]*>(.*?)</g>', (FIGDIR / 'boundary-design.svg').read_text(), re.S)]
assert len(_di) >= 5, len(_di)
I_USER, I_BOT, I_LINK, I_BUILDING, I_BOOK = _di[:5]

def product_flow():
    def obj(cls, icon, name, text, scope, extra=''):
        return (f'<div class="obj {cls}"><h4>{icon}{name}</h4><p>{text}</p>{extra}'
                f'<p class="scope">{I_BOOK}<span>{cap1(scope)}</span></p></div>')
    checks = f'<p class="checks-title">{FIVE}</p><ol class="checks">' + ''.join(f'<li>{cap1(c)}</li>' for c in CHECKS) + '</ol>'
    hop = lambda label: f'<div class="hop"><span>{label}</span><i></i></div>'
    return (f'<div class="flow" data-reveal><div class="flow-reviewer"><b>{I_USER}Reviewer</b><span>{REVIEWER}</span></div>'
            f'<div class="flow-row">{obj("agent", I_BOT, "Agent", AGENT_IS, SCOPES[0])}{hop("tool call")}'
            f'{obj("connection", I_LINK, "Connection", CONNECTION_IS, SCOPES[1], checks)}{hop("allowed")}'
            f'{obj("service", I_BUILDING, "Enterprise Service", SERVICE_IS, SCOPES[2])}</div>'
            f'<p class="flow-sandbox">{cap1(SANDBOX)}<span>Docker</span><span>Harbor</span><span>AgentEnv</span></p></div>')

def product_problems():
    return '<div class="p-cols">' + ''.join(
        f'<div class="p-col" data-reveal><span class="numeral">{i + 1}</span><h4>{t_}</h4><p>{CASES[i]}</p>'
        f'<p class="answer"><b>Boundary</b>{cap1(a_)}</p></div>' for i, (t_, a_) in enumerate(SOLVED)) + '</div>'

page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>From Assistants to Coworkers: AI Agents in the Enterprise</title>
<meta name="description" content="A paper on enterprise agents as deployments: how they are built, connected to company systems, coordinated, evaluated, and governed. With Boundary, an agent framework.">
<meta name="theme-color" content="#1b2e22">
<link rel="icon" href="{ver('assets/favicon.png')}" type="image/png">
<link rel="apple-touch-icon" href="{ver('assets/apple-touch-icon.png')}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Marcellus&family=Marcellus+SC&family=Nunito:ital,wght@0,400;0,600;0,700;0,800;1,400;1,700&display=swap">
<link rel="stylesheet" href="{ver('styles.css')}">
<script>if(!document.hidden&&!/[?&]static/.test(location.search))document.documentElement.classList.add('js')</script>
</head>
<body>

<header class="topbar" id="topbar">
  <div class="wrap">
    <a class="brand" href="#top">{MARK}<span>Enterprise Agent</span></a>
    <nav class="nav" aria-label="Sections">
      <a href="#abstract">Abstract</a>
      <a href="#definition">Definition</a>
      <a href="#findings">Findings</a>
      <a href="#products">Products</a>
      <a href="#problems">Open problems</a>
      <a href="#boundary">Boundary</a>
      <a href="#cite">Cite</a>
    </nav>
    {pdf_link('btn btn-small btn-bar', 'PDF')}
  </div>
</header>

<main id="top">
<div class="hero">
  <div class="hero-ground" id="hero-ground"></div>
  <div class="wrap">
    <h1><span>From Assistants to Coworkers:</span><span>AI Agents in the Enterprise</span></h1>
    <p class="lede">AI agents now read company records, use production tools, and sometimes act without approval for each case. This paper studies them as deployments, not as models.</p>
    <div class="actions">
      {pdf_link('btn btn-light', 'Read the paper')}
      <a class="btn {'btn-ghost' if HAS_PDF else 'btn-light'}" href="#boundary">Boundary framework</a>
      <a class="btn btn-ghost" href="#cite">Cite</a>
    </div>
  </div>
</div>

<div class="opening wrap">
  <figure class="fig cutaway" data-reveal>
    <div class="fig-scroll">{cutaway()}</div>
    <figcaption><b>Figure 1.</b>{caption('stack')}</figcaption>
  </figure>
</div>

<div class="people wrap" id="people">
  <p class="authors">{AUTHORS}</p>
  <ul class="affils">{AFFILS}</ul>
</div>

<section id="abstract" class="rule">
  <div class="wrap split">
    <div class="head" data-reveal><h2>Abstract</h2></div>
    <p class="abstract" data-reveal>{ABSTRACT}</p>
  </div>
</section>

<section id="definition" class="rule">
  <div class="wrap">
    <div class="split">
      <div class="head" data-reveal>
        <span class="where">Section 2</span>
        <h2>The definition of an enterprise agent</h2>
        <p>The definition has three parts, and all three are needed: choice at run time, access to the organization&rsquo;s systems and data, and permission from the organization.</p>
      </div>
      <div class="stack">
        <div class="panel" data-reveal>
          <p class="panel-title">An enterprise agent is a deployed piece of software that</p>
          <div class="cards rows">
            <div class="card"><span class="numeral">i</span><p>{CLAUSES[0]};</p></div>
            <div class="card"><span class="numeral">ii</span><p>{CLAUSES[1]}; and</p></div>
            <div class="card"><span class="numeral">iii</span><p>{CLAUSES[2]}.</p></div>
          </div>
          <p class="panel-note">{STANDING}</p>
        </div>
        <div class="panel" data-reveal>
          <p class="panel-title">Talk about agent &ldquo;autonomy&rdquo; often mixes up three separate decisions</p>
          <div class="cards c3">
            <div class="card icon"><h3>{ICON['cpu']}Capability</h3><p>is {CAD[0]}.</p></div>
            <div class="card icon"><h3>{ICON['key']}Authority</h3><p>is {CAD[1]}.</p></div>
            <div class="card icon"><h3>{ICON['work']}Delegation</h3><p>is {CAD[2]}.</p></div>
          </div>
        </div>
      </div>
    </div>
    <div class="below">{fig('boundary-cases', 'Four deployments checked against the definition. Two are in scope and two are out of scope.')}</div>
  </div>
</section>

<section id="findings">
  <div class="wrap">
    <div class="split">
      <div class="head" data-reveal>
        <span class="where">Across the paper</span>
        <h2>Three limits on what the evidence shows</h2>
        <p>The evidence points to three limits on what can be concluded.</p>
      </div>
      <div class="stack tight">{limits()}</div>
    </div>
  </div>
</section>

<section id="products" class="rule">
  <div class="wrap">
    <div class="split">
      <div class="head" data-reveal>
        <span class="where">Sections 4 and 5</span>
        <h2>Products, frameworks, and standards</h2>
      </div>
      <p class="abstract" data-reveal>With this lens we review how enterprise agents are built, connected to company systems, coordinated, evaluated, and governed, including the products now on the market.</p>
    </div>
    <div class="below stack">
      {fig('river', 'A river of 39 enterprise agent products and standards from November 2023 to October 2026, each with its vendor logo.', 'wide')}
      <div data-reveal>
        <h3 class="table-title">How ten current products connect agents to company systems</h3>
        <div class="table-scroll">{PRODUCTS}</div>
        <p class="table-note">As described in each vendor&rsquo;s own documentation, read 16 October 2026. The entries describe mechanisms the vendors offer. The sources are listed under Table 2 of the paper.</p>
      </div>
      <div data-reveal>
        <div class="block-head"><h3>Agent frameworks on five questions</h3><p>{' '.join(FW_LEAD)}</p></div>
        {FRAMEWORKS}
        <div class="legend">
          <span><span class="lvl l2">{MARK[2]}</span>built in</span>
          <span><span class="lvl l1">{MARK[1]}</span>partly built in, or possible with extra work</span>
          <span><span class="lvl l0">{MARK[0]}</span>not described in the official documentation</span>
        </div>
        <p class="table-note">Judged from each maker&rsquo;s official documentation on 22 October 2026. <sup>†</sup>Some features come from the maker&rsquo;s hosted service rather than the open-source library. Several features are marked experimental or preview.</p>
      </div>
    </div>
  </div>
</section>

<section id="problems" class="rule">
  <div class="wrap">
    <div class="split">
      <div class="head" data-reveal>
        <span class="where">Section 10</span>
        <h2>Open research problems</h2>
        <p>Deployment conventions are forming now. So direct study of real deployments over time is worth more than another autonomy label or overall benchmark score.</p>
      </div>
      <ol class="problems" data-reveal>
        {''.join(f'<li><span class="n">{i}</span><div><h3>{html.escape(t_)}</h3><p>{html.escape(s_)}</p></div></li>' for i, (t_, s_) in enumerate(PROBLEMS, 1))}
      </ol>
    </div>
    <div class="below">{threats()}</div>
  </div>
</section>

<section id="boundary" class="product">
  <div class="wrap">
    <header class="p-hero" data-reveal>
      <div class="p-lockup"><img src="assets/logos/boundary.png" alt="" width="398" height="512"><h2>Boundary</h2></div>
      <p class="p-kicker">An agent framework</p>
      <p class="p-claim">{CLAIM}</p>
      <p class="p-sub">{CLAIM_REST}</p>
      {f'<div class="actions">{pdf_link("btn btn-mint", f"Read Section {BSEC}", f"#page={BPAGE}")}</div>' if HAS_PDF else ''}
    </header>

    <div class="p-part first">
      <div class="p-head" data-reveal>
        <h3>Agent, Service, and Connection</h3>
        <p>{ALLOWED}</p>
      </div>
      {product_flow()}
    </div>

    <div class="p-part">
      <div class="p-head" data-reveal>
        <h3>{SHAPE}</h3>
        <p>The earlier sections find that many of the hardest problems of enterprise agents lie in the deployment, not in the model. Boundary is an agent framework we built to meet these requirements.</p>
      </div>
      {product_problems()}
    </div>

    <div class="p-part">
      <div class="p-head" data-reveal>
        <h3>Results</h3>
        <p>{' '.join(tex(x) for x in TESTED)}</p>
      </div>
      <div class="r-main" data-reveal>
        <div class="rstats">
          <div class="rstat"><b>115 of 116</b><span>multi-step conversations completed with <span class="nb">GPT-6 Sol</span>. A conventional agent with the same model, prompt and tools completed 73.</span></div>
          <div class="rstat"><b>+36.2 points</b><span>over the conventional agent on the same conversations with <span class="nb">GPT-6 Sol</span> (95% confidence interval 30.8 to 41.8), and +28.4 with <span class="nb">Gemini 3.8 Flash</span>.</span></div>
        </div>
        <div class="chart" data-sets>
          {multistep()}
          <p class="chart-note">{MS_NOTE}</p>
        </div>
      </div>
      <div class="r-pair">
        <div class="r-block" data-reveal>
          <div class="rstat"><b>109 of 120</b><span>new conversations completed with no foreign sign-off after two rounds of learning. A single global playbook completed 25, and 87 of its conversations carried another organization&rsquo;s sign-off.</span></div>
          <div class="chart">
            {learning()}
            <p class="chart-note">The 120 conversations are with the 16 organizations not seen in training, 30 per Service type. Without learning, none is completed.</p>
          </div>
        </div>
        <div class="r-block" data-reveal>
          <div class="rstat"><b>0 of 26</b><span>attacks on the life cycle of authority succeeded with a fully compromised agent, and 0 of 125 with three model agents.</span></div>
          <div class="chart">
            {attacks()}
            <p class="chart-note">{ATTACK_NOTE} {PROMPT_ONLY}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>

<section id="cite">
  <div class="wrap split">
    <div class="head" data-reveal><h2>Citation</h2></div>
    <div class="cite" data-reveal>
      <button class="btn btn-light btn-small" type="button" data-copy="bibtex">Copy</button>
      <pre id="bibtex">{html.escape(BIB)}</pre>
    </div>
  </div>
</section>
</main>

<footer>
  <div class="wrap">
    <span class="foot-brand">{MARK}<span class="title">From Assistants to Coworkers</span></span>
    <span>AI Agents in the Enterprise</span>
    {pdf_link('btn btn-ghost btn-small', 'Read the paper')}
  </div>
</footer>

<dialog class="viewer" id="viewer" aria-label="Figure"><div class="viewer-inner"></div></dialog>
<script src="{ver('script.js')}" defer></script>
</body>
</html>
"""
(OUT / 'index.html').write_text(page)
print('index.html', len(page) // 1024, 'KB')

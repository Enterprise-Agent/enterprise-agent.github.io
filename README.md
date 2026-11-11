# From Assistants to Coworkers: website

The website for the paper **From Assistants to Coworkers: AI Agents in the Enterprise** and for **Boundary**, the agent framework described in its Section 11.

It is one static page with no build step and no dependencies: `index.html`, `styles.css`, `script.js` and `assets/`.

## Preview

```sh
python3 -m http.server 8793 --bind 127.0.0.1
```

Open `http://127.0.0.1:8793`. Add `?static` to the address to switch off the entrance and scroll motion, for screenshots.

## Hosting

GitHub Pages serves the site from the `main` branch of this repository, root folder, at `https://enterprise-agent.github.io/`. There is no build step on GitHub: the files in the repository are the site. All links in the page are relative, so the site also works from any other folder or address.

The paper PDF is not part of the site until the paper is public. The page then has no links to it. To add it later, run `tools/prep_assets.py` with `--with-pdf` and build again: the PDF goes to `assets/paper/`, and the build adds the links (in the bar, the title page, the Boundary part and the footer). `assets/paper/` is in `.gitignore`, so it has to be added on purpose.

## Contents of the page

| Part | Source in the paper |
|---|---|
| Title, authors, institutions | `main.tex` |
| Abstract | `sections/00-abstract.tex`, word for word |
| Definition; capability, authority, delegation | Section 2, word for word |
| Three limits | the abstract, each with the evidence, the missing link and the claim of Figure 7 |
| Product table | Table 2, converted from the LaTeX rows |
| Framework comparison | Table 3's marks and the five questions of Section 5, with the frameworks across the top and one row for each question |
| Open research problems | Section 10: subsection titles and sentences from each subsection |
| Threat models | the five threat models of Section 9 |
| Boundary | Section 11, laid out as a product introduction: the principle as the headline, the three objects and five checks, the three problems, the results as three charts |
| Diagrams (Figures 4 and 8) | the figures' own SVG (`tools/figures/*.svg`), set inline: vector, with live text in the page's typeface and no frame |
| Figure 1 | the illustration as an image, with its labels and leaders as live SVG text (`figures/paper/stack.svg`) |
| Captions | the LaTeX |

## Updating after the paper changes

The page is generated, so that nothing is retyped. With a compiled checkout of the paper repository:

```sh
python3 tools/prep_assets.py /path/to/paper .     # logos, the illustration, tools/meta.json (add --with-pdf for the PDF)
python3 tools/build_site.py  /path/to/paper .     # index.html
```

When a figure changes, copy its new `.svg` from the figure generators' output folder into `tools/figures/` first. The paper repository holds only the PDFs of the figures, so the SVG files are kept here.

Six of the paper's figures and two of its tables are not shown as figures or tables. The page builds them in HTML instead, so they read as parts of the page:

| Part of the page | In the paper | What the build checks |
|---|---|---|
| Three limits, each with a broken link | Figure 7 | every phrase is in `tools/figures/transfer.svg`; the three sentences are in the abstract |
| Five threat models | the threat-model figure of Section 9 | every phrase is in `tools/figures/threats.svg` |
| Agent, Connection and Enterprise Service, with the five checks | Figure 18 | the three descriptions are copied from the Design text; the checks and scope lines are in `tools/figures/boundary-design.svg` |
| Three problems and what Boundary does about each | Figure 17 | titles and answers are in `tools/figures/boundary-motivation.svg`; the sentences come from the figure's caption |
| Multi-step tasks: a meter for each system and task type, one agent model at a time | Figure 19 | the totals and the "all 24 cases" result are in the text of Section 11 |
| Learning across organizations: two rings and the counts for each Service type | Figure 20 | the totals are in the text of Section 11 |
| Attacks on the life cycle of authority: a table with the Boundary columns marked | the lower block of the authority table | read from the LaTeX rows; the rows add up to the table's last row |
| Framework comparison | Table 3 | read from the LaTeX rows; the five questions are copied from the text |

The per-task-type counts of Figure 19 and the per-Service-type counts of Figure 20 are not printed in the paper. They are typed into `tools/build_site.py` from the figure generator (`build_boundary_figures.py`), so update them there when the experiments change. The build stops if a checked phrase or number no longer matches the paper.

The selected logo is the sage-green puzzle block with a playful mint E and a mint Agent companion, kept at `tools/brand/enterprise-agent-puzzle.png`. `python3 tools/brand_icon.py .` exports `assets/brand/icon.png` for the bar and footer, `assets/favicon.png`, and `assets/apple-touch-icon.png`. It needs Pillow. The bar and footer show the logo on a white tile. Run the icon exporter before `tools/build_site.py`; the page builder versions the image URLs so browser caches refresh. The former robot source is retained at `tools/brand/enterprise-agent-icon.png` for reference.

Both scripts need PyMuPDF (`pip install pymupdf`). Text that is written for the site only (section headings, the headline results in the Boundary part, chart legends, alt text) lives in `tools/build_site.py`. `styles.css` and `script.js` are edited by hand.

## Design

A deep green title page set in Marcellus SC, then white pages with soft green panels and white cards, the same language as the paper's figures and tables. Body text is Nunito, the paper's own face, and the figures use it too: Nunito's widths are within about 3% of the face the figures were drawn in, so their layout holds. The Boundary part takes its colours from the Boundary mark. Fonts load from Google Fonts with system fallbacks. There is one light theme, because the figures sit directly on a white page. The Boundary part is one dark block laid out as a product introduction. Its three result charts use three forms (meters, rings, a table): mint is Boundary, and orange is a sign-off that reached another organization or an attack that reached its goal.

There are no analytics, cookies or third-party scripts.

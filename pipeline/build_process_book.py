"""Builds the Prototype V1 section of the process book and merges it with the
previous milestone PDFs into one file: Process_Book_Prototype_V1.pdf"""
import json, sys
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle, KeepTogether)
from PIL import Image as PILImage
from pypdf import PdfReader, PdfWriter

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / "img"
S = json.loads((ROOT / "data/summary.json").read_text())
PREV = [Path(p) for p in sys.argv[1:-1]]          # previous milestone PDFs, in order
OUT = Path(sys.argv[-1])
FULLPAGE = Path("/tmp/claude-0/-home-claude/00165de9-0938-54c3-a0f1-5681871aaa25/scratchpad/fullpage_cols.png")

ss = getSampleStyleSheet()
ORANGE = colors.HexColor("#eb6834"); INK = colors.HexColor("#0b0b0b"); GREY = colors.HexColor("#52514e")
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontName="Helvetica-Bold", fontSize=20, textColor=INK, spaceAfter=10)
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontName="Helvetica-Bold", fontSize=14, textColor=INK, spaceBefore=12, spaceAfter=6, keepWithNext=1)
H3 = ParagraphStyle("H3", parent=ss["Heading3"], fontName="Helvetica-Bold", fontSize=11.5, textColor=ORANGE, spaceBefore=8, spaceAfter=4, keepWithNext=1)
B = ParagraphStyle("B", parent=ss["BodyText"], fontName="Times-Roman", fontSize=11, leading=15, spaceAfter=6)
BL = ParagraphStyle("BL", parent=B, leftIndent=14, bulletIndent=4, spaceAfter=3)
CAP = ParagraphStyle("CAP", parent=B, fontSize=9, textColor=GREY, leading=12, alignment=1)
SMALL = ParagraphStyle("SM", parent=B, fontSize=9.5, leading=12)

def P(t, st=B): return Paragraph(t, st)
def bullets(items): return [Paragraph(i, BL, bulletText="•") for i in items]
def img(path, width=6.5 * inch, caption=None, max_h=7.2 * inch):
    w, h = PILImage.open(path).size
    W = width; H = W * h / w
    if H > max_h: H = max_h; W = H * w / h
    out = [Image(str(path), width=W, height=H)]
    if caption: out.append(P(caption, CAP))
    out.append(Spacer(1, 6))
    return out
def table(rows, widths, header=True):
    t = Table([[Paragraph(str(c), SMALL) for c in r] for r in rows], colWidths=widths, repeatRows=1 if header else 0)
    st = [("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c3c2b7")),
          ("VALIGN", (0, 0), (-1, -1), "TOP"),
          ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4)]
    if header: st.append(("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0efec")))
    t.setStyle(TableStyle(st)); return t

band = {b["band"]: b for b in S["by_age_band"]}
story = []

# ---------------- Cover ----------------
story += [Spacer(1, 1.6 * inch),
          P("Process Book", ParagraphStyle("t", parent=H1, fontSize=34, leading=40)),
          P("Talk Back: everyday adult talk and children's speech", ParagraphStyle("t2", parent=H2, fontSize=18, textColor=ORANGE)),
          Spacer(1, 12),
          P("CS171 Final Project · Prototype V1 submission · October 2026"),
          Spacer(1, 18),
          P("<b>Team members who actively worked on this prototype</b>"),
          *bullets(["Arlette Duran", "Hebron Geremew", "Rhys Greenland"]),
          Spacer(1, 18),
          P("<b>Contents</b>"),
          *bullets(["Part A: Previous milestones (topic &amp; questions, sketches, sketch voting, coordinated-view prototypes, "
                    "data storyboard and individual explorations), included unchanged",
                    "Part B: Prototype V1 (this milestone): team, data pipeline, website structure and story, "
                    "two functional D3 visualizations plus the novel 'Echo' view, drafts of three further visualizations, "
                    "interaction design, updated findings, next steps"]),
          Spacer(1, 18),
          P("Data: Bergelson et al. (2023), \"Everyday language input and production in 1,001 children from six continents,\" "
            "<i>PNAS</i> 120(52), doi:10.1073/pnas.2300671120. Public file EL1000_for_reproduce_conf.csv (osf.io/46rcf).", SMALL),
          PageBreak()]

cover_doc = OUT.with_name("_cover.pdf")
SimpleDocTemplate(str(cover_doc), pagesize=letter, leftMargin=inch, rightMargin=inch, topMargin=inch, bottomMargin=inch,
                  title="Process Book - Talk Back", author="Arlette Duran, Hebron Geremew, Rhys Greenland").build(story)

# ---------------- Prototype V1 section ----------------
story = []
story += [P("Part B · Milestone: Prototype V1", H1),
          P("<b>Team members who actively worked on this submission:</b> Arlette Duran, Hebron Geremew, Rhys Greenland."),
          P("This milestone turns our storyboard into a first working website. The data pipeline is complete and runs on the "
            "real Bergelson et al. public dataset. The page follows our Hook → Rising insights → Main message → Takeaway "
            "structure. Three D3 views are live (the brief requires two): child speech by age, the linked adult-talk vs. child-speech "
            "scatter, and our novel <b>Echo</b> view. The remaining views are placeholders on the page and are drafted below."),
          P("Requirement checklist", H2),
          table([["Requirement", "Where"],
                 ["1. Team member documentation", "This page and cover"],
                 ["2. Complete data pipeline (real data)", "§1; code in pipeline/clean_data.py"],
                 ["3. Two functional D3 visualizations", "§3 Vis 1 and Vis 2 (plus Vis 3, the Echo)"],
                 ["4. Drafts of 2–3 more visualizations", "§5 Vis 4, Vis 6, Vis 7 (and Vis 5 recap concept)"],
                 ["5. Website structure / layout", "§2; index.html"],
                 ["6. Clear storytelling", "§2 storyboard-to-page mapping"],
                 ["7. Novel view design", "§4 The Echo (implemented)"],
                 ["8. Updated process book", "Part A (previous milestones) + Part B"]],
                [3.0 * inch, 3.5 * inch])]

# §1 data
story += [P("1. Data pipeline", H2),
          P("Source and acquisition", H3),
          P("The dataset is the public reproduction file from Bergelson et al. (2023), hosted on OSF (osf.io/46rcf, part of "
            "project osf.io/9v2m5). Each row is one day-long LENA recording of a child, with automatic counts of adult "
            "vocalizations per hour (AVC) and child speech-like vocalizations per hour (CVC), plus age, sex, maternal "
            "education, language background, typical-development status and corpus. Our script can re-download the file "
            "(<font face='Courier'>--download</font>); otherwise it reads the copy in <font face='Courier'>data/raw/</font>."),
          P("Cleaning steps (pipeline/clean_data.py)", H3),
          *bullets(["Remove duplicate recordings by .its file ID (none found).",
                    "Keep valid ages (0–48 months), non-negative rates, and recordings with at least 4 hours of audio "
                    f"(7 recordings dropped): <b>2,017 → {S['n_recordings']:,} recordings, {S['n_children']} children, {S['n_corpora']} corpora</b>.",
                    "Rename variables into plain language (e.g. CVCr → child_voc_hr, AVCr → adult_voc_hr).",
                    "Recode flags into labels: sex (Girl/Boy), monolingual/multilingual, typically developing (normative), "
                    "region (North America/Europe vs. rest of world, with 15 missing values filled from the child's corpus), and mother's education (5 levels).",
                    "Derive age bands (0–11, 12–23, 24–35, 36–48 months), within-band quintiles of adult talk, and the number of recordings per child.",
                    "Write <font face='Courier'>data/el1000_clean.csv</font> (loaded by D3) and <font face='Courier'>data/summary.json</font> "
                    "(statistics quoted in the page text, so numbers on the site always match the data)."]),
          P("Cleaned data dictionary", H3),
          table([["Column", "Type", "Meaning"],
                 ["child_id / recording_id", "id", "Anonymized child (corpus_child) and recording file"],
                 ["corpus, region", "categorical", "Research group (fruit code) and broad region"],
                 ["age_mo, age_band", "quant. / ordinal", "Age in months; 12-month bands"],
                 ["adult_voc_hr", "quantitative", "Adult vocalizations per hour heard (our 'adult talk')"],
                 ["child_voc_hr", "quantitative", "Child speech-like vocalizations per hour (our 'child speech')"],
                 ["talk_quintile", "ordinal", "Fifth of adult talk within the child's age band (1 = least)"],
                 ["sex, language_bg, typical", "categorical", "Girl/Boy; Monolingual/Multilingual; typically developing"],
                 ["ses_code, mother_ed", "ordinal", "Maternal education, 1 (less than high school) to 5 (advanced degree)"],
                 ["n_recordings_child", "quantitative", "How many recordings this child has (used for within-child view)"]],
                [1.8 * inch, 1.1 * inch, 3.6 * inch]),
          Spacer(1, 6),
          P("Re-checked numbers", H3),
          P("Re-running every statistic on the cleaned file reproduced the earlier milestone findings: r by age band "
            f"({', '.join(fmt for fmt in [str(band[b]['r']) for b in band])}), the quintile medians, and the within-child "
            f"estimate (r = {S['within_child']['r']}, about {S['within_child']['slope_per100_age_adjusted']:.0f} more child vocalizations/hr per 100 adult, "
            f"age-adjusted). Some recording and child counts in the storyboard (e.g. 2,705 monolingual recordings, 931 children) "
            f"were larger than this file contains, so the site uses the recomputed counts: {S['by_language'][0]['n']:,} monolingual and "
            f"{S['by_language'][1]['n']} multilingual recordings. The less-than-high-school group again looks 'chattiest' in raw "
            f"medians, but it is older (mean {S['by_mother_ed'][0]['mean_age']} months) and "
            f"{S['low_ed_top_corpus']['n']} of its {S['low_ed_top_corpus']['of']} recordings come from one corpus "
            f"({S['low_ed_top_corpus']['corpus']}). Our sandbox had no mixed-model library, so V1 uses a linear "
            "age + age² + adult-talk adjustment. The published mixed models remain the reference for significance claims."),
          PageBreak()]

# §2 website
story += [P("2. Website structure and storytelling", H2),
          P("The page is a single vertical scroll with a sticky section navigation. Each section maps one-to-one onto our storyboard, "
            "and the headline of every section states its takeaway, so a reader who only skims headlines still gets the story."),
          table([["Storyboard beat", "Section on page", "Status in V1"],
                 ["Hook", "\"What matters more for how much a child talks?\" Reader picks Family background or Adult talk, gets feedback, sees dataset scale (731 children, 2,010 recordings).", "Implemented"],
                 ["Rising insight 1: development", "Vis 1: child speech by age", "Implemented (D3)"],
                 ["Rising insight 2: talk ↔ speech", "Vis 2: age-brushed scatter with r/slope readout", "Implemented (D3)"],
                 ["Novel view (supports insight 2)", "Vis 3: The Echo, gap widens with age", "Implemented (D3)"],
                 ["Rising insight 3: what doesn't explain it", "Three summary cards computed from data + Vis 4 placeholder", "Cards live; Vis 4 drafted"],
                 ["Main message", "Dark full-width statement + Vis 5 recap placeholder", "Text done; Vis 5 drafted"],
                 ["Solution / takeaway", "Three action cards (conversation, keep it up, no deficit assumptions) + image placeholder", "Text done; image TBD"],
                 ["Credits", "About the data: citation, measurement caveat, team", "Done"]],
                [1.6 * inch, 3.4 * inch, 1.5 * inch]),
          Spacer(1, 8),
          *img(FULLPAGE, caption="Full page of Prototype V1 in reading order (left → middle → right column)."),
          P("Narrative choices", H3),
          *bullets(["Every causal-sounding sentence was rewritten as an association (\"goes with\", \"tracks\"), and the scatter carries a standing caveat about reverse causation.",
                    "Numbers in the text are bound to summary.json (data-s attributes), so text and charts cannot drift apart.",
                    "Age is introduced first because it is the biggest confound; every later view compares children of similar ages.",
                    "The null-effects section says explicitly that \"no consistent difference\" is not \"identical\", as planned in the storyboard."]),
          PageBreak()]

# §3 vis 1 + 2
story += [P("3. Functional D3 visualizations", H2),
          P("Vis 1 · Child speech by age (rising insight 1)", H3),
          *img(IMG / "proto_vis1_age.png", width=5.6 * inch, caption="Vis 1 as implemented."),
          *bullets(["<b>Data/encoding:</b> each recording is a dot (x = age in months with small fixed jitter, y = child vocalizations/hr), colored with an ordinal blue ramp by age band, the same colors used in every view. A black line shows the rolling median (±1 month) and a shaded band the middle 50%.",
                    "<b>Interaction:</b> a crosshair tooltip gives the median, interquartile range and n at any age. Checkboxes switch to typically developing children only and show/hide the IQR band. Dots animate in and out.",
                    "<b>Why:</b> it sets the baseline that speech roughly doubles from infancy to age 3, and shows the spread at each age that the rest of the story tries to explain."]),
          PageBreak(),
          P("Vis 2 · Adult talk vs. child speech, linked to an age brush (rising insight 2)", H3),
          *img(IMG / "proto_vis2_scatter.png", width=5.4 * inch, caption="Vis 2 with the 36–48 month range selected."),
          *bullets(["<b>Built from:</b> Prototype A from the previous milestone (age histogram + scatter), as our comparison recommended.",
                    "<b>Encoding:</b> x = adult vocalizations/hr, y = child vocalizations/hr, color = age band; dots outside the selected ages fade to grey. An orange regression line fits the selection, and a dashed line shows the all-ages fit for comparison.",
                    f"<b>Interaction:</b> brush across the age histogram or use quick-range buttons. The readout updates n, children, r and the slope per +100 adult vocalizations (e.g. 0–11 mo: r = {band['0–11 mo']['r']}, +{band['0–11 mo']['slope_per100']:.0f}; 36–48 mo: r = {band['36–48 mo']['r']}, +{band['36–48 mo']['slope_per100']:.0f}). Hovering a dot shows a tooltip and draws a path through every recording of that child. There is also a typically-developing toggle.",
                    "<b>Why:</b> it carries the main relationship and lets readers see for themselves that it strengthens with age, instead of taking our word for it."]),
          PageBreak()]

# §4 novel view
story += [P("4. Novel view · The Echo", H2),
          *img(IMG / "proto_vis3_echo.png", width=6.0 * inch, caption="Vis 3, The Echo, as implemented (rank spacing, quintiles shown)."),
          P("Concept", H3),
          P("Our data are audio recordings, so we drew them as audio. Each age band is a mirrored waveform. Recordings are sorted left to right by "
            "how much adult talk they contain. Each thin bar above the axis is the adult talk a child heard (blue), and the bar below it is the child's own "
            "speech (orange), its \"echo\". The blue envelope always rises (it is sorted). The question the reader answers by eye is whether the "
            "orange echo follows it. Orange steps mark the median child speech in each fifth of adult talk."),
          P("Why it is novel and why it works", H3),
          *bullets(["It combines a sorted bar chart, a mirrored (butterfly) layout and a quintile staircase into one waveform glyph, so the visual metaphor matches the recording-based data.",
                    "Small multiples by age make the main message pre-attentive: the orange echo is nearly flat for babies "
                    f"({' → '.join(f'{v:.0f}' for v in band['0–11 mo']['quintile_medians'])}) and steps sharply for 3–4-year-olds "
                    f"({' → '.join(f'{v:.0f}' for v in band['36–48 mo']['quintile_medians'])}, about {band['36–48 mo']['ratio_top_bottom']}× top vs. bottom fifth).",
                    "Every recording stays visible (no summary hides the noise), which keeps us honest about how variable children are."]),
          P("Interactions", H3),
          *bullets(["Hover: highlights a single recording and shows adult talk, child speech, its fifth and that fifth's median.",
                    "Click a band to enlarge it (others shrink) for closer reading; click again to reset.",
                    "Toggle <i>even spacing (rank)</i> vs. <i>true adult-talk scale</i>, which reveals how skewed adult talk is and where recordings cluster.",
                    "Show/hide quintile shading and labels."]),
          P("Alternatives considered and open issues", H3),
          *bullets(["A radial \"day clock\" was rejected because the public file has no hour-by-hour counts.",
                    "A ridgeline of child speech by quintile looked attractive but hid individual recordings.",
                    "Open issues: the 36–48 month band has only 172 recordings, so its steps are noisy (we will add n per fifth). "
                    "The metaphor needs a short legend. We plan an animated intro that 'plays' the waveform left to right."]),
          PageBreak()]

# §5 drafts
story += [P("5. Drafts of visualizations not yet implemented", H2),
          P("These are updated designs drawn from the real cleaned data in a sketch style, so they read as drafts. Each will be built in D3 for V2."),
          P("Vis 4 · \"Same age, same talk\" comparison panels (rising insight 3)", H3),
          *img(IMG / "draft_background_panels.png", width=6.5 * inch),
          *bullets(["Dot + 95% interval of child speech relative to what age and adult talk predict, for sex, language background and mother's education. The dashed zero line means 'no difference'.",
                    "Interaction: a toggle between raw medians (where the less-than-high-school group looks ahead) and adjusted values, so readers watch the apparent gap shrink. Hover shows n and mean age. Clicking a group highlights those children in Vis 2.",
                    "Replaces sketches 4/7, 5 and 14 from earlier milestones and answers questions h, j, l and m."]),
          PageBreak(),
          P("Vis 6 · Same child, different days (supports the main message)", H3),
          *img(IMG / "draft_within_child.png", width=4.6 * inch),
          *bullets([f"Slope chart for children recorded more than once within about 2 months: each line connects the child's lowest-adult-talk day to their highest. In the full within-child analysis ({S['within_child']['children']} children, {S['within_child']['recordings']:,} recordings) r = {S['within_child']['r']}.",
                    "This guards against the claim that the pattern is only about different kinds of families. The draft shows the effect is modest (56 of 92 children go up), which we will state plainly.",
                    "Planned interaction: filter by age band; hover a line to see that child's recordings in Vis 2."]),
          P("Vis 7 · Talk staircase: is there a point of diminishing returns?", H3),
          *img(IMG / "draft_staircase.png", width=6.5 * inch),
          *bullets(["Arlette's insight 1 drawn directly: median child speech per fifth of adult talk, one panel per age band. Babies plateau after the second fifth, while 3–4-year-olds keep climbing.",
                    "May be merged into the Echo as an alternate 'summary' mode instead of a separate chart. We will decide after user testing."]),
          P("Vis 5 · Main-message recap (concept)", H3),
          P("A short scroll-triggered sequence: Vis 1, 2 and 4 shrink into a row of three tiles with one headline number each "
            "(speech roughly doubles by age 3 · r rises from 0.26 to 0.55 · background differences are about 5–20/hr with no consistent direction), leading into the takeaway cards."),
          PageBreak()]

# §6 interaction + next steps
story += [P("6. Interaction design summary", H2),
          table([["View", "Interaction", "Purpose"],
                 ["Hook", "Click a guess → feedback text", "Commit the reader to a prediction (engagement)"],
                 ["Vis 1", "Crosshair tooltip; typical-only toggle; IQR toggle", "Read exact medians; check clinical-risk children aren't driving the trend"],
                 ["Vis 2", "Age brush + quick ranges; live r/slope readout; hover links a child's recordings; typical-only", "Compare same-age children; see link strengthen; show repeated measures"],
                 ["Vis 3 Echo", "Hover a recording; click to enlarge a band; rank vs. value scale; quintile toggle", "Read details; focus; reveal skew in adult talk"],
                 ["Vis 4 (planned)", "Raw ↔ adjusted toggle; click group → highlight in Vis 2", "Watch demographic gaps shrink after adjustment"],
                 ["Vis 6 (planned)", "Age filter; hover line → Vis 2", "Within-child evidence"],
                 ["Nav", "Sticky nav highlights current section", "Orientation in a long scroll"]],
                [1.1 * inch, 2.8 * inch, 2.6 * inch]),
          P("7. Changes since the storyboard", H2),
          *bullets(["Replaced all mock data with the real cleaned dataset; numbers recomputed (see §1).",
                    "Moved the monolingual/multilingual comparison from its own scatter panels (Prototype B) into Vis 4, to keep the main scatter simple for parents and caregivers.",
                    "Added the Echo as our novel view. It visualizes Arlette's 'gap widens with age' insight, which earlier views did not show directly.",
                    "Added the interactive guess to the hook."]),
          P("8. Next steps for Prototype V2", H2),
          *bullets(["Implement Vis 4 and Vis 6 in D3 and link them to Vis 2 (shared selection).",
                    "Add n-per-fifth labels and an animated 'play' intro to the Echo; usability-test the metaphor with 3–5 people outside the class.",
                    "Build the main-message recap (Vis 5) with scroll-triggered transitions; replace the image placeholder.",
                    "Fit the mixed model (child random intercepts, corpus) to confirm the adjusted differences, and add a methods pop-over.",
                    "Accessibility: data-table view for each chart, keyboard access for brush and buttons, and print/forced-colors texture."]),
          P("How to run the code", H3),
          P("<font face='Courier'>python3 pipeline/clean_data.py</font> regenerates the data. From the project folder, "
            "<font face='Courier'>python3 -m http.server</font>, then open http://localhost:8000. D3 v7 is bundled locally in js/lib/.")]

proto_doc = OUT.with_name("_proto.pdf")
def footer(c, d):
    c.setFont("Helvetica", 8); c.setFillColor(GREY)
    c.drawString(inch, 0.55 * inch, "Talk Back · Process Book · Part B: Prototype V1")
    c.drawRightString(letter[0] - inch, 0.55 * inch, f"B-{d.page}")
SimpleDocTemplate(str(proto_doc), pagesize=letter, leftMargin=inch, rightMargin=inch, topMargin=0.8 * inch, bottomMargin=0.85 * inch).build(
    story, onFirstPage=footer, onLaterPages=footer)

# ---------------- merge ----------------
w = PdfWriter()
def add(path, label=None):
    start = len(w.pages)
    for p in PdfReader(str(path)).pages: w.add_page(p)
    if label: w.add_outline_item(label, start)
add(cover_doc, "Cover & contents")
names = ["A1 · Topic, questions, audience (Milestones 1–2)", "A2 · Individual sketches (Milestone 3)",
         "A3 · Sketch voting", "A4 · Coordinated views & two interactive prototypes", "A5 · Data storyboard & individual explorations"]
for p, n in zip(PREV, names): add(p, n)
add(proto_doc, "B · Prototype V1")
w.add_metadata({"/Title": "Process Book - Talk Back (Prototype V1)", "/Author": "Arlette Duran, Hebron Geremew, Rhys Greenland"})
with open(OUT, "wb") as f: w.write(f)
cover_doc.unlink(); proto_doc.unlink()
print("wrote", OUT, len(w.pages), "pages")

# ---------------- shrink embedded images (previous milestones contain large photos) ----------------
w2 = PdfWriter(clone_from=str(OUT))
for page in w2.pages:
    for im in page.images:
        try:
            pil = im.image
            if max(pil.size) > 1600: pil.thumbnail((1600, 1600))
            if pil.mode in ("RGBA", "P", "LA"): pil = pil.convert("RGB")
            im.replace(pil, quality=72)
        except Exception as e:
            print("skip image:", e)
    page.compress_content_streams()
w2.compress_identical_objects(remove_duplicates=True, remove_unreferenced=True)
with open(OUT, "wb") as f: w2.write(f)
print("compressed", OUT, round(OUT.stat().st_size / 1e6, 1), "MB")

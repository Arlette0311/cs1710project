"""Builds the Prototype V3 process book:
cover -> Part A previous milestones (unchanged) -> Part B Prototype V1 -> Part C test session -> Part D Prototype V3.

usage: python3 pipeline/build_process_book_v3.py <V1 process book PDF> <test-session PDF> <output PDF>
(The V1 process book already contains the cover + Part A + Part B; its cover is replaced.)"""
import json, sys
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
from PIL import Image as PILImage
from pypdf import PdfReader, PdfWriter

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / "img" / "v3"
S = json.loads((ROOT / "data/summary.json").read_text())
V1_BOOK, TEST_PDF, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])

ss = getSampleStyleSheet()
ORANGE = colors.HexColor("#eb6834"); INK = colors.HexColor("#14161f"); GREY = colors.HexColor("#4d5060")
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontName="Helvetica-Bold", fontSize=20, textColor=INK, spaceAfter=10)
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontName="Helvetica-Bold", fontSize=14, textColor=INK, spaceBefore=12, spaceAfter=6, keepWithNext=1)
H3 = ParagraphStyle("H3", parent=ss["Heading3"], fontName="Helvetica-Bold", fontSize=11.5, textColor=ORANGE, spaceBefore=8, spaceAfter=4, keepWithNext=1)
B = ParagraphStyle("B", parent=ss["BodyText"], fontName="Times-Roman", fontSize=11, leading=15, spaceAfter=6)
BL = ParagraphStyle("BL", parent=B, leftIndent=14, bulletIndent=4, spaceAfter=3)
CAP = ParagraphStyle("CAP", parent=B, fontSize=9, textColor=GREY, leading=12, alignment=1)
SMALL = ParagraphStyle("SM", parent=B, fontSize=9.5, leading=12)

def P(t, st=B): return Paragraph(t, st)
def bullets(items): return [Paragraph(i, BL, bulletText="•") for i in items]
def img(path, width=6.5 * inch, caption=None, max_h=7.0 * inch):
    w, h = PILImage.open(path).size
    W = width; H = W * h / w
    if H > max_h: H = max_h; W = H * w / h
    out = [Image(str(path), width=W, height=H)]
    if caption: out.append(P(caption, CAP))
    out.append(Spacer(1, 6)); return out
def table(rows, widths):
    t = Table([[Paragraph(str(c), SMALL) for c in r] for r in rows], colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c3c2b7")), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0efec")),
                           ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4)]))
    return t
def side(a, b, cap_a, cap_b, w=3.15 * inch):
    def cell(p, c):
        pw, ph = PILImage.open(p).size
        return [Image(str(p), width=w, height=w * ph / pw), P(c, CAP)]
    t = Table([[cell(a, cap_a), cell(b, cap_b)]], colWidths=[w + 0.1 * inch] * 2)
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")])); return t

band = {b["band"]: b for b in S["by_age_band"]}
r0 = lambda v: int(v + 0.5)   # round half up, like d3.format on the site
gd = S["group_differences"]; mm = S["mixed_model"]
TEAM = ["Arlette Duran", "Hebron Geremew", "Rhys Greenland"]

# ---------------- cover ----------------
cover = [Spacer(1, 1.5 * inch),
         P("Process Book", ParagraphStyle("t", parent=H1, fontSize=34, leading=40)),
         P("Talk Back: everyday adult talk and children's speech", ParagraphStyle("t2", parent=H2, fontSize=18, textColor=ORANGE)),
         Spacer(1, 10), P("CS1710 Final Project · Prototype V3 submission · November 2026"), Spacer(1, 16),
         P("<b>Team members who actively worked on this prototype</b>"), *bullets(TEAM), Spacer(1, 16),
         P("<b>Contents</b>"),
         *bullets(["Part A: Previous milestones (topic, questions and audience; sketches; sketch voting; coordinated-view prototypes; storyboard and individual explorations)",
                   "Part B: Prototype V1 (data pipeline, first website, Vis 1–3 including the novel Echo view, drafts)",
                   "Part C: Week 12 testing (think-aloud notes from two testers and the team's discussion)",
                   "Part D: Prototype V3 (this milestone): responses to testing, redesigned opening, guided story, all seven visualizations implemented, design and next steps"]),
         Spacer(1, 16),
         P("Data: Bergelson et al. (2023), \"Everyday language input and production in 1,001 children from six continents,\" <i>PNAS</i> 120(52), "
           "doi:10.1073/pnas.2300671120. Public file EL1000_for_reproduce_conf.csv (osf.io/46rcf).", SMALL)]
cover_pdf = OUT.with_name("_cover3.pdf")
SimpleDocTemplate(str(cover_pdf), pagesize=letter, leftMargin=inch, rightMargin=inch, topMargin=inch, bottomMargin=inch).build(cover)

# ---------------- Part D ----------------
st = []
st += [P("Part D · Milestone: Prototype V3", H1),
       P(f"<b>Team members who actively worked on this submission:</b> {', '.join(TEAM)}."),
       P("V3 completes the data story. Every chart is now a working, interactive D3 view, the placeholders are gone, and the changes "
         "come straight from our Week 12 think-aloud sessions (Part C). We followed the priority list from our team discussion. "
         "We kept the narrative and the Echo, which both testers liked, and focused on making the experience guided, discoverable and polished."),
       P("Requirement checklist", H2),
       table([["Requirement", "Where"],
              ["1. Team member documentation", "This page and cover"],
              ["2. Complete data pipeline (real data)", "§4; pipeline/clean_data.py (now with bootstrap intervals and a mixed model)"],
              ["3. All visualizations functional and interactive", "§5: seven D3 views, each with hover tooltips and controls"],
              ["4. Website layout fully implemented", "§6; index.html, no placeholders left"],
              ["5. Clear storytelling", "§3 guided chapters; §6 storyboard mapping"],
              ["6. Updated process book", "Parts A–C (previous work) + Part D"],
              ["Incorporate test-session feedback", "§1 and §2"]],
             [2.6 * inch, 3.9 * inch])]

st += [P("1. How we responded to the test session", H2),
       P("Both testers (Rachel Richey and Miles Schwab) understood the main message and named the Echo as the most effective view. "
         "Both were confused by the opening, and both had trouble finding some interactions. The table maps our seven planned revisions "
         "(Part C, \"In order\") to what we built."),
       table([["Priority from testing", "What testers said", "What we changed in V3"],
              ["1. Redesign the opening guess", "Rachel: looked like \"random info boxes\", not answer choices. Miles: \"easy to miss\".",
               "A three-step game card: (1) pick A or B on large lettered answer buttons with hover lift and a \"Click A or B\" cue; "
               "(2) guess a number on a slider; (3) animated bars compare the guess with the real answer and give feedback on both steps."],
              ["2. Make the story more guided", "Miles: don't show later sections until the beginning is done.",
               "The story is locked until the game ends (or the reader skips it). Chapters are numbered 1–6, sections fade in as you scroll, "
               "a progress bar runs under the navigation, and each chapter ends with a \"Next: …\" button that previews the next question."],
              ["3. Clear interaction instructions", "Rachel: list how to interact with the visualizations.",
               "Every chart has a row of \"how to\" chips with icons, e.g. \"Drag across the bar chart to pick an age range\", "
               "\"Hover a dot to connect all recordings of that child\", \"Click any age band to enlarge it\"."],
              ["4. Better legends and tooltips", "Miles: legends and tooltips not fully explained.",
               "Legends now state what a mark means (\"one bar = adult talk in one recording\") and include lines and bands, not just colors. "
               "Tooltips use plain labels (\"Adult sounds heard / hr\") and end with a one-line explanation."],
              ["5. Make Echo expansion discoverable", "Rachel didn't know bands could be enlarged until told.",
               "Each band now has a visible expand button (keyboard accessible), a zoom cursor, a bobbing \"Click a band to enlarge it\" hint "
               "that disappears after first use, and tooltips that say \"Click to enlarge this age band\"."],
              ["6. Visual polish", "\"More images\", \"more fun colors\", \"can be made prettier\".",
               "A navy hero with an original animated illustration (adult and child speech bubbles as sound waves), alternating warm and blue chapter "
               "backgrounds, colored chapter badges, an illustrated conversation in the takeaway, and icon cards. Data colors stay consistent: blue = adult, orange = child, blue ramp = age."],
              ["7. Finish the started visualization", "Team decision: finish what we had begun rather than add many new graphs.",
               "All drafted views are built: Talk staircase (Vis 4), Same child, different days (Vis 5), Background comparison (Vis 6) and the Main-message recap (Vis 7)."]],
             [1.35 * inch, 1.75 * inch, 3.4 * inch]),
       P("Written TF feedback from our check-in with Khadija was not available when we compiled this book, so this part reflects the student think-aloud sessions only.", SMALL),
       PageBreak()]

st += [P("2. The redesigned opening (priority 1)", H2),
       *img(IMG / "game_step1.png", width=4.6 * inch, caption="Step 1: two clearly lettered answer buttons, a progress indicator and a cue."),
       side(IMG / "game_step2.png", IMG / "game_step3.png", "Step 2: guess with a slider.",
            "Step 3: animated reveal with feedback on both answers, then \"Start the story\"."),
       Spacer(1, 6),
       P("The game sets up the story's hook as a real prediction. The reader commits to an answer about family background vs. adult talk, "
         f"then estimates the gap that the Echo later shows: 3- to 4-year-olds in the quietest fifth of homes make about "
         f"{r0(band['36–48 mo']['quintile_medians'][0])} speech sounds per hour, and those in the most talkative fifth about "
         f"{r0(band['36–48 mo']['quintile_medians'][4])}. The numbers come from summary.json, so they always match the charts. "
         "A \"Skip the game\" link keeps the page usable for returning visitors."),
       PageBreak(),
       P("3. A guided, chaptered story (priority 2)", H2),
       *bullets(["<b>Locked until ready:</b> chapters after the hook stay hidden until the game is finished or skipped. Charts are built only then, so they size correctly.",
                 "<b>Numbered chapters:</b> 1 Growing up → 2 Talk &amp; speech → 3 The echo → 4 Diminishing returns? → 5 Same child → 6 Background → Message → Takeaway. The sticky navigation mirrors these, highlights the current chapter, and shows a scroll progress bar.",
                 "<b>Question-led transitions:</b> each chapter ends with a \"Next\" button phrased as the next question (\"Next: is it just different kinds of families?\"), so each finding sets up the next one.",
                 "<b>Scroll reveals:</b> text and charts fade up as they enter the screen (turned off for readers who prefer reduced motion)."]),
       *img(IMG / "fullpage_cols.png", caption="The full V3 page in reading order (four columns, left to right)."),
       PageBreak()]

st += [P("4. Data pipeline updates", H2),
       P(f"The cleaning pipeline from V1 is unchanged ({S['n_recordings']:,} recordings, {S['n_children']} children, {S['n_corpora']} research teams). "
         "We added two analyses to support chapter 6 and replace the simpler adjustment we used in V1:"),
       *bullets(["<b>Raw vs. fair comparison with uncertainty:</b> for each group (sex, language background, five levels of maternal education) we compute its "
                 "difference from the average child, both raw and after removing age, age², adult talk and research team (corpus fixed effects). 95% intervals come "
                 "from a bootstrap that resamples whole children, so repeat recordings of the same child stay together.",
                 "<b>Mixed model</b> (statsmodels): " + mm["formula"] + ". It is shown on the site under \"Methods\"."]),
       table([["Term", "Estimate (child sounds/hr)", "SE", "p"]] +
             [[t["term"], f"{t['estimate']:+.1f}", f"{t['se']:.1f}", "< 0.001" if t["p"] < 0.001 else f"{t['p']:.2f}"] for t in mm["terms"]],
             [3.3 * inch, 1.5 * inch, 0.7 * inch, 0.9 * inch]),
       Spacer(1, 6),
       P("Adult talk (+25.8 per 100 adult vocalizations, close to the paper's ~27) and its interaction with age are clearly non-zero. None of the background terms are. "
         f"The bootstrap tells the same story. The raw advantage of the less-than-high-school group "
         f"({gd['mother_ed'][0]['raw']:+.1f}/hr, 95% {gd['mother_ed'][0]['raw_lo']:.0f} to {gd['mother_ed'][0]['raw_hi']:.0f}) becomes "
         f"{gd['mother_ed'][0]['adj']:+.1f}/hr ({gd['mother_ed'][0]['adj_lo']:.0f} to {gd['mother_ed'][0]['adj_hi']:.0f}) in the fair comparison, and every fair-comparison interval crosses zero."),
       PageBreak()]

# §5 visualizations
st += [P("5. The seven visualizations", H2),
       P("Vis 1 · Growing up (chapter 1), updated", H3),
       *img(IMG / "vis1_age.png", width=5.2 * inch),
       *bullets(["Strip plot of child speech by age with rolling median and middle-50% band. New: how-to chips, a full legend (dot colors, median line, band) and a plain-language subtitle defining \"speech sounds\".",
                 "Interactions: crosshair tooltip at any age; filter to typically developing children; toggle the band."]),
       PageBreak(),
       P("Vis 2 · Talk &amp; speech (chapter 2), updated", H3),
       *img(IMG / "vis2_scatter.png", width=5.4 * inch, caption="36–48 months selected."),
       *bullets(["Age histogram brush linked to the adult-talk vs. child-speech scatter, with live r and slope. New: chips explain dragging, hovering and quick ranges. The legend now includes both trend lines. The readout explains r (\"0 = none, 1 = perfect\").",
                 f"Tooltips describe the recorded day in plain words and say what the black connecting line means. Slope rises from +{band['0–11 mo']['slope_per100']:.0f} (0–11 mo) to +{band['36–48 mo']['slope_per100']:.0f} (36–48 mo) per 100 adult sounds."]),
       PageBreak(),
       P("Vis 3 · The Echo (chapter 3, novel view), updated", H3),
       side(IMG / "vis3_echo.png", IMG / "vis3_echo_expanded.png", "Default view with the 'click to enlarge' hint and expand buttons.", "36–48 months enlarged."),
       *bullets(["Unchanged concept: each age band is a mirrored waveform of real recordings sorted by adult talk, with the child's speech as the orange 'echo' and orange steps for the median of each fifth.",
                 "New for discoverability: visible expand/collapse buttons, a one-time animated hint, zoom cursor, and tooltips ending in \"Click to enlarge this age band\". The legend now explains bars, lines and numbers separately."]),
       PageBreak(),
       P("Vis 4 · The talk staircase (chapter 4), new", H3),
       *img(IMG / "vis4_staircase.png", width=5.6 * inch),
       *bullets(["Answers our original question e (\"is there a point of diminishing returns?\"). Small multiples by age show the median child speech in each fifth of adult talk as a staircase, with the middle half of children as shaded boxes.",
                 f"Babies level off ({' → '.join(f'{r0(v)}' for v in band['0–11 mo']['quintile_medians'])}). 3- to 4-year-olds keep climbing ({' → '.join(f'{r0(v)}' for v in band['36–48 mo']['quintile_medians'])}).",
                 "Interactions: hover a step for adult-talk range, median, IQR and n; show the individual recordings behind each step; switch between a shared and per-age y-scale."]),
       P("Vis 5 · Same child, different days (chapter 5), new", H3),
       *img(IMG / "vis5_samechild.png", width=5.0 * inch),
       *bullets(["Slope chart: each line joins one child's lowest-adult-talk day to their highest. Orange = the child talked more on the busier day, grey = less. The thick line is the median.",
                 f"Addresses the \"different families\" objection, backed by the within-child analysis ({S['within_child']['children']} children, r = {S['within_child']['r']}, about +{S['within_child']['slope_per100_age_adjusted']:.0f} per 100). The readout states plainly that the effect is real but noisy (for example, about 60% of children go up).",
                 "Interactions: slider for the maximum age gap between the two days (0–6 months, to limit age confounding); age-group filter; hover a line for that child's numbers."]),
       PageBreak(),
       P("Vis 6 · Background comparison (chapter 6), new", H3),
       side(IMG / "vis6_background.png", IMG / "vis6_background_adj.png", "Raw averages: some groups differ clearly (orange dots).", "Fair comparison: every interval crosses zero."),
       *bullets(["Dot-and-interval chart of each group's difference from the average child, for sex, language background and maternal education.",
                 "Interactions: a segmented switch (and an \"Animate the switch\" button) moves the dots from raw averages to the fair comparison, so readers watch the gaps shrink. Dots turn orange only when their interval excludes zero. Hover gives n, children, average age and an interpretation. The note under the chart updates with each mode.",
                 "Built from sketches 4/7, 5 and 14 and the V1 draft. It answers questions h, j, l and m."]),
       P("Vis 7 · Main-message recap, new", H3),
       *img(IMG / "vis7_recap.png", width=5.6 * inch),
       *bullets(["Three tiles summarize the story with one headline number and an animated mini chart each: speech roughly doubles from 6 months to 3 years; r rises from "
                 f"{band['0–11 mo']['r']:.2f} to {band['36–48 mo']['r']:.2f}; the largest background gap shrinks from about 43 to about 4 sounds/hr. Each tile links back to its chapter."]),
       PageBreak()]

st += [P("6. Website structure, story and design", H2),
       table([["Storyboard beat", "V3 section", "Visualization / interaction"],
              ["Hook", "Navy hero + 3-step game", "Pick A/B → guess slider → animated reveal"],
              ["Rising insight 1", "Ch. 1 Growing up", "Vis 1 strip plot"],
              ["Rising insight 2", "Ch. 2 Talk & speech; Ch. 3 The echo", "Vis 2 brush + scatter; Vis 3 Echo"],
              ["(supports 2)", "Ch. 4 Diminishing returns?; Ch. 5 Same child", "Vis 4 staircase; Vis 5 slope chart"],
              ["Rising insight 3", "Ch. 6 Background", "Vis 6 raw ↔ fair comparison"],
              ["Main message", "Dark statement + recap", "Vis 7 tiles"],
              ["Solution", "Takeaway", "Illustrated conversation + three action cards"],
              ["Credits & methods", "Footer", "Citation, measurement caveat, mixed-model table, team"]],
             [1.4 * inch, 2.3 * inch, 2.8 * inch]),
       P("Design decisions", H3),
       *bullets(["<b>Color has one meaning everywhere:</b> blue = adult talk, orange = child speech, a light-to-dark blue ramp = age (younger to older). Orange also marks the reader's next action (buttons, chapter badges, how-to chips).",
                 "<b>Imagery:</b> original SVG illustrations drawn for the project (hero speech bubbles with animated sound waves; a conversation in the takeaway) and simple icons. No stock or copyrighted images.",
                 "<b>Typography and layout:</b> one system sans-serif face; headlines state each chapter's finding; text and chart sit side by side on desktop and stack on phones (tested at 390 px wide with no horizontal scrolling).",
                 "<b>Honesty:</b> every causal-sounding sentence is phrased as an association, and chapter 5 and the methods note explain what the data can and cannot show.",
                 "<b>Accessibility:</b> keyboard-focusable buttons (including Echo expand), visible focus rings, reduced-motion support, and text labels that never rely on color alone."]),
       P("7. Remaining work for the final submission (about 5%)", H2),
       *bullets(["Run one more think-aloud with the new opening to confirm it reads as a game.",
                 "Add a data-table view for screen-reader users and finer keyboard control of the age brush.",
                 "Copy-edit the text, add photo credits if we add any photographs, and record the screencast.",
                 "Deploy to GitHub Pages for a public link."]),
       P("How to run", H3),
       P("From the code folder: <font face='Courier'>python3 -m http.server 8000</font>, then open http://localhost:8000. "
         "<font face='Courier'>python3 pipeline/clean_data.py</font> rebuilds the data (the mixed model needs statsmodels).")]

d_pdf = OUT.with_name("_partD.pdf")
def footer(c, d):
    c.setFont("Helvetica", 8); c.setFillColor(GREY)
    c.drawString(inch, 0.55 * inch, "Talk Back · Process Book · Part D: Prototype V3")
    c.drawRightString(letter[0] - inch, 0.55 * inch, f"D-{d.page}")
SimpleDocTemplate(str(d_pdf), pagesize=letter, leftMargin=inch, rightMargin=inch, topMargin=0.8 * inch, bottomMargin=0.85 * inch).build(st, onFirstPage=footer, onLaterPages=footer)

# ---------------- merge ----------------
w = PdfWriter()
def add(reader_pages, label):
    start = len(w.pages)
    for pg in reader_pages: w.add_page(pg)
    w.add_outline_item(label, start)
v1 = PdfReader(str(V1_BOOK)).pages
add(PdfReader(str(cover_pdf)).pages, "Cover & contents")
add(v1[1:24], "A · Previous milestones")
add(v1[24:], "B · Prototype V1")
add(PdfReader(str(TEST_PDF)).pages, "C · Week 12 testing (think-aloud)")
add(PdfReader(str(d_pdf)).pages, "D · Prototype V3")
w.add_metadata({"/Title": "Process Book - Talk Back (Prototype V3)", "/Author": ", ".join(TEAM)})
for page in w.pages:
    for im in page.images:
        try:
            pil = im.image
            if max(pil.size) > 1700: pil.thumbnail((1700, 1700))
            if pil.mode in ("RGBA", "P", "LA"): pil = pil.convert("RGB")
            im.replace(pil, quality=78)
        except Exception as e:
            print("skip image:", e)
    page.compress_content_streams()
w.compress_identical_objects(remove_duplicates=True, remove_unreferenced=True)
with open(OUT, "wb") as f: w.write(f)
cover_pdf.unlink(); d_pdf.unlink()
print("wrote", OUT, len(w.pages), "pages", round(OUT.stat().st_size / 1e6, 1), "MB")

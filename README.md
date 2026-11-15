# Talk Back: Prototype V3

CS1710 final project · Team: Arlette Duran, Hebron Geremew, Rhys Greenland

**Story:** Across a globally diverse sample, the adult talk a child hears goes with how much speech the child
produces, and the link grows stronger with age. Family background (mother's education, sex, mono- or
multilingual) is a much less consistent clue. All claims are correlational.

## Run it

```bash
cd code
python3 -m http.server 8000      # D3 loads CSV/JSON, so a local server is required
# open http://localhost:8000
```

D3 v7.9.0 is bundled in `js/lib/`, so the page needs no internet connection.
If port 8000 is busy (e.g. a teammate's site is running), use 8001 instead.

## Rebuild the data

```bash
pip install pandas numpy statsmodels
python3 pipeline/clean_data.py            # raw CSV -> data/el1000_clean.csv + data/summary.json
python3 pipeline/clean_data.py --download # re-fetch the raw file from OSF first
```

## Story and files

| Chapter | File | What it does |
|---|---|---|
| Hook (3-step game) | `js/story.js` | Pick A/B → guess with a slider → animated reveal; unlocks the story, scroll reveals, progress bar |
| 1 Growing up | `js/vis_age.js` | Child speech by age: strip plot, rolling median, IQR band |
| 2 Talk & speech | `js/vis_scatter.js` | Age-histogram brush linked to the adult-talk vs. child-speech scatter with live r/slope |
| 3 The echo (novel) | `js/vis_echo.js` | Mirrored waveform per age band; click or ⤢ to enlarge |
| 4 Diminishing returns? | `js/vis_staircase.js` | Talk staircase: median child speech per fifth of adult talk |
| 5 Same child | `js/vis_samechild.js` | Slope chart, each child's quiet vs. busy day; age-gap slider |
| 6 Background | `js/vis_background.js` | Raw vs. same-age/same-talk/same-team differences with 95% intervals |
| Message | `js/vis_recap.js` | Three recap tiles with animated mini charts |
| | `js/helpers.js`, `js/main.js` | Shared helpers; data loading and wiring |
| | `css/style.css` | Design tokens and layout |
| | `pipeline/` | Data cleaning, draft images (V1), process-book builders |
| | `img/` | V1 drafts/screenshots and `img/v3/` screenshots for the process book |

## Data

Bergelson, E. et al. (2023). Everyday language input and production in 1,001 children from six continents.
*PNAS* 120(52). doi:10.1073/pnas.2300671120. File `EL1000_for_reproduce_conf.csv`, https://osf.io/46rcf.

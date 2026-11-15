"""
Prototype V1 data pipeline - "Talk Back" (CS171 final project)
Team: Arlette Duran, Hebron Geremew, Rhys Greenland

Source data
-----------
Bergelson, E., Soderstrom, M., Schwarz, I.-C., Rowland, C., Ramirez-Esparza, N.,
Hamrick, L., ... Cristia, A. (2023). Everyday language input and production in
1,001 children from six continents. PNAS 120(52). doi:10.1073/pnas.2300671120

File: EL1000_for_reproduce_conf.csv, OSF project https://osf.io/46rcf
(part of https://osf.io/9v2m5). Metadata: data/raw/46rcf-datacite.json.

Acquisition ("scraping")
------------------------
The file is public on OSF. Run with --download to fetch it again, or place it
in data/raw/ by hand. Our cloud sandbox could not reach osf.io, so we
downloaded it in a browser for this prototype.

Run
---
    python3 pipeline/clean_data.py            # uses data/raw/EL1000_for_reproduce_conf.csv
    python3 pipeline/clean_data.py --download # re-fetch from OSF first

Outputs
-------
    data/el1000_clean.csv   one row per recording, renamed + derived columns (used by D3)
    data/summary.json       pre-computed stats quoted in the narrative text
"""
import argparse
import json
import sys
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "EL1000_for_reproduce_conf.csv"
OUT_CSV = ROOT / "data" / "el1000_clean.csv"
OUT_JSON = ROOT / "data" / "summary.json"
OSF_URL = "https://osf.io/46rcf/download"

# Maternal-education codes, using the 5-level scale described in the paper's supplement.
SES_LABELS = {
    1: "Less than high school",
    2: "High school",
    3: "Some college / vocational",
    4: "College degree",
    5: "Advanced degree",
}
AGE_BANDS = [(0, 12, "0–11 mo"), (12, 24, "12–23 mo"), (24, 36, "24–35 mo"), (36, 49, "36–48 mo")]


def download():
    RAW.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {OSF_URL} ...")
    urllib.request.urlretrieve(OSF_URL, RAW)


def load_raw() -> pd.DataFrame:
    if not RAW.exists():
        sys.exit(f"Missing {RAW}. Download it from https://osf.io/46rcf or run with --download.")
    return pd.read_csv(RAW)


def clean(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()
    n0 = len(df)

    # 1. Drop exact duplicate recordings (same .its file) - defensive; none expected.
    df = df.drop_duplicates(subset="its")

    # 2. Sanity filters: valid ages (2–48 months), non-negative rates, recordings with at least 4 h of audio.
    df = df[(df.age >= 0) & (df.age <= 48)]
    df = df[(df.CVCr >= 0) & (df.AVCr >= 0)]
    df = df[df.rec_h >= 4]

    # 3. Rename to readable names and keep only what the site uses.
    df = df.rename(columns={
        "corp_chi": "child_id",
        "its": "recording_id",
        "CVCr": "child_voc_hr",        # child (speech-like) vocalisations per hour
        "AVCr": "adult_voc_hr",        # adult vocalisations per hour
        "age": "age_mo",
        "rec_h": "rec_hours",
        "ses": "ses_code",
        "CHN_ling_n_prop": "prop_linguistic",
        "CHN_cry_n_prop": "prop_cry",
    })

    # 4. Recode categorical flags into labels.
    df["sex"] = df["sex"].map({"F": "Girl", "M": "Boy"})
    df["language_bg"] = df["monoling"].map({"Y": "Monolingual", "N": "Multilingual"})
    df["typical"] = df["normative"].map({"Y": True, "N": False})
    df["region"] = df["nae"].map({"Y": "North America / Europe", "N": "Rest of world"})
    # 15 recordings have a missing nae flag; every corpus has a single value, so fill from the corpus.
    corpus_region = df.dropna(subset=["region"]).groupby("corpus")["region"].first()
    df["region"] = df["region"].fillna(df["corpus"].map(corpus_region))
    df["mother_ed"] = df["ses_code"].map(SES_LABELS)

    # 5. Derived columns.
    df["age_band"] = pd.cut(df.age_mo, [b[0] for b in AGE_BANDS] + [49], right=False,
                            labels=[b[2] for b in AGE_BANDS]).astype(str)
    # Quintile of adult talk *within each age band* (1 = least talk, 5 = most talk)
    df["talk_quintile"] = (df.groupby("age_band")["adult_voc_hr"]
                             .transform(lambda s: pd.qcut(s.rank(method="first"), 5, labels=False) + 1)
                             .astype(int))
    df["n_recordings_child"] = df.groupby("child_id")["recording_id"].transform("count")

    keep = ["recording_id", "child_id", "corpus", "region", "age_mo", "age_band", "sex",
            "language_bg", "typical", "ses_code", "mother_ed", "adult_voc_hr", "child_voc_hr",
            "talk_quintile", "prop_linguistic", "prop_cry", "rec_hours", "n_recordings_child"]
    df = df[keep].sort_values(["corpus", "child_id", "age_mo"]).reset_index(drop=True)
    for c in ["adult_voc_hr", "child_voc_hr", "prop_linguistic", "prop_cry", "rec_hours"]:
        df[c] = df[c].round(2)
    print(f"Cleaned: {n0} raw rows -> {len(df)} recordings, {df.child_id.nunique()} children, "
          f"{df.corpus.nunique()} corpora")
    return df


def ols_slope(x, y):
    b, a = np.polyfit(x, y, 1)
    return float(b), float(a)


def summarise(df: pd.DataFrame) -> dict:
    r = lambda g: float(np.corrcoef(g.adult_voc_hr, g.child_voc_hr)[0, 1])
    s = {
        "n_recordings": int(len(df)),
        "n_children": int(df.child_id.nunique()),
        "n_corpora": int(df.corpus.nunique()),
        "r_all": round(r(df), 3),
        "slope_per100_all": round(ols_slope(df.adult_voc_hr, df.child_voc_hr)[0] * 100, 1),
    }

    bands = []
    for _, _, lab in AGE_BANDS:
        g = df[df.age_band == lab]
        q = g.groupby("talk_quintile").child_voc_hr.median()
        bands.append({
            "band": lab, "n": int(len(g)), "r": round(r(g), 3),
            "median_child": round(float(g.child_voc_hr.median()), 1),
            "median_adult": round(float(g.adult_voc_hr.median()), 1),
            "slope_per100": round(ols_slope(g.adult_voc_hr, g.child_voc_hr)[0] * 100, 1),
            "quintile_medians": [round(float(v), 1) for v in q.values],
            "gap_top_bottom": round(float(q.iloc[-1] - q.iloc[0]), 1),
            "ratio_top_bottom": round(float(q.iloc[-1] / q.iloc[0]), 2),
        })
    s["by_age_band"] = bands

    def group_stats(col):
        out = []
        for k, g in df.groupby(col):
            out.append({"group": str(k), "n": int(len(g)), "children": int(g.child_id.nunique()),
                        "r": round(r(g), 3),
                        "median_child": round(float(g.child_voc_hr.median()), 1),
                        "median_adult": round(float(g.adult_voc_hr.median()), 1),
                        "mean_age": round(float(g.age_mo.mean()), 1)})
        return out

    s["by_sex"] = group_stats("sex")
    s["by_language"] = group_stats("language_bg")
    s["by_mother_ed"] = sorted(group_stats("mother_ed"),
                               key=lambda d: [v for v in SES_LABELS.values()].index(d["group"]))

    # Age-adjusted comparison: residual child speech after regressing on age (linear + quadratic)
    # and adult talk. Shows how much each demographic group differs once those are held constant.
    X = np.column_stack([np.ones(len(df)), df.age_mo, df.age_mo ** 2, df.adult_voc_hr])
    beta, *_ = np.linalg.lstsq(X, df.child_voc_hr, rcond=None)
    resid = df.child_voc_hr - X @ beta
    adj = {}
    for col in ["sex", "language_bg", "mother_ed"]:
        adj[col] = {str(k): round(float(v), 1) for k, v in resid.groupby(df[col]).mean().items()}
    s["age_talk_adjusted_mean_residual"] = adj

    # Share of the least-educated group coming from its largest corpus (confound check).
    low = df[df.ses_code == 1]
    top_corpus = low.corpus.value_counts()
    s["low_ed_top_corpus"] = {"corpus": top_corpus.index[0], "n": int(top_corpus.iloc[0]),
                              "of": int(len(low))}

    # Within-child: demean each child's adult talk and child speech, then correlate.
    multi = df[df.n_recordings_child > 1].copy()
    for c in ["adult_voc_hr", "child_voc_hr", "age_mo"]:
        multi[c + "_dm"] = multi[c] - multi.groupby("child_id")[c].transform("mean")
    Xw = np.column_stack([multi.adult_voc_hr_dm, multi.age_mo_dm])
    bw, *_ = np.linalg.lstsq(Xw, multi.child_voc_hr_dm, rcond=None)
    s["within_child"] = {
        "children": int(multi.child_id.nunique()), "recordings": int(len(multi)),
        "r": round(float(np.corrcoef(multi.adult_voc_hr_dm, multi.child_voc_hr_dm)[0, 1]), 3),
        "slope_per100_age_adjusted": round(float(bw[0]) * 100, 1),
    }
    s["group_differences"] = group_differences(df)
    s["mixed_model"] = mixed_model(df)
    return s


def group_differences(df: pd.DataFrame, n_boot: int = 400, seed: int = 171) -> dict:
    """For each demographic group: how far its average child speech sits from the overall average,
    (a) raw and (b) after removing age, age^2, adult talk and research group (corpus fixed effects).
    95% intervals come from a bootstrap that resamples whole children (repeat recordings stay together)."""
    rng = np.random.default_rng(seed)
    corp = pd.get_dummies(df.corpus, drop_first=True).to_numpy(float)
    X = np.column_stack([np.ones(len(df)), df.age_mo, df.age_mo ** 2, df.adult_voc_hr, corp])
    y = df.child_voc_hr.to_numpy()

    def stats(idx):
        Xi, yi = X[idx], y[idx]
        beta, *_ = np.linalg.lstsq(Xi, yi, rcond=None)
        resid = yi - Xi @ beta
        sub = df.iloc[idx]
        out = {}
        for col in ["sex", "language_bg", "mother_ed"]:
            raw = sub.child_voc_hr.groupby(sub[col].values).mean() - yi.mean()
            adj = pd.Series(resid).groupby(sub[col].values).mean()
            for g in raw.index:
                out[(col, g, "raw")] = raw[g]
                out[(col, g, "adj")] = adj[g]
        return out

    point = stats(np.arange(len(df)))
    children = df.child_id.unique()
    rows_of = df.groupby("child_id").indices
    boots = []
    for _ in range(n_boot):
        pick = rng.choice(children, len(children), replace=True)
        idx = np.concatenate([rows_of[c] for c in pick])
        boots.append(stats(idx))
    res = {}
    order = {"sex": ["Girl", "Boy"], "language_bg": ["Monolingual", "Multilingual"],
             "mother_ed": list(SES_LABELS.values())}
    for col, groups in order.items():
        res[col] = []
        for g in groups:
            item = {"group": g, "n": int((df[col] == g).sum()),
                    "children": int(df.loc[df[col] == g, "child_id"].nunique()),
                    "mean_age": round(float(df.loc[df[col] == g, "age_mo"].mean()), 1)}
            for kind in ["raw", "adj"]:
                vals = np.array([b.get((col, g, kind), np.nan) for b in boots])
                lo, hi = np.nanpercentile(vals, [2.5, 97.5])
                item[kind] = round(float(point[(col, g, kind)]), 1)
                item[kind + "_lo"] = round(float(lo), 1)
                item[kind + "_hi"] = round(float(hi), 1)
            res[col].append(item)
    return res


def mixed_model(df: pd.DataFrame) -> dict:
    """Linear mixed model in the spirit of the paper: child speech ~ adult talk x age + sex + language
    + mother's education, random intercepts for research group (corpus) and child within corpus."""
    try:
        import statsmodels.formula.api as smf
    except ImportError:
        return {"available": False}
    d = df.copy()
    d["adult100_c"] = (d.adult_voc_hr - d.adult_voc_hr.mean()) / 100
    d["age_c"] = (d.age_mo - d.age_mo.mean()) / 12          # per year
    d["ses_f"] = pd.Categorical(d.ses_code, categories=[4, 1, 2, 3, 5])  # college degree = reference
    m = smf.mixedlm("child_voc_hr ~ adult100_c * age_c + C(sex) + C(language_bg) + ses_f",
                    d, groups="corpus", re_formula="1", vc_formula={"child": "0 + C(child_id)"})
    r = m.fit(method="lbfgs", reml=True)
    names = {"adult100_c": "Adult talk (+100/hr, at mean age)", "age_c": "Age (+1 year)",
             "adult100_c:age_c": "Adult talk x age", "C(sex)[T.Girl]": "Girl (vs. boy)",
             "C(language_bg)[T.Multilingual]": "Multilingual (vs. monolingual)",
             "ses_f[T.1]": "Mother: less than high school (vs. college)", "ses_f[T.2]": "Mother: high school (vs. college)",
             "ses_f[T.3]": "Mother: some college (vs. college)", "ses_f[T.5]": "Mother: advanced degree (vs. college)"}
    terms = []
    for k, lab in names.items():
        if k in r.params.index:
            terms.append({"term": lab, "estimate": round(float(r.params[k]), 1),
                          "se": round(float(r.bse[k]), 1), "p": round(float(r.pvalues[k]), 4)})
    return {"available": True, "n": int(len(d)), "terms": terms,
            "formula": "child voc/hr ~ adult talk x age + sex + language + mother's education + (1 | corpus) + (1 | child)"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--download", action="store_true")
    args = ap.parse_args()
    if args.download:
        download()
    df = clean(load_raw())
    df.to_csv(OUT_CSV, index=False)
    summary = summarise(df)
    OUT_JSON.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"Wrote {OUT_CSV.relative_to(ROOT)} and {OUT_JSON.relative_to(ROOT)}")
    print(json.dumps({k: summary[k] for k in ["n_recordings", "n_children", "r_all", "slope_per100_all"]}))


if __name__ == "__main__":
    main()

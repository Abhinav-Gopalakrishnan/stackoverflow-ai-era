"""Build Member 5's slides (M5-17) and findings text (M5-15) from a finished modelling run.

    python -m src.make_slides                       # reads reports/review1/m5/, writes
                                                    # reports/review1/m5_slides.pptx and m5_findings.md

Every number comes from ``results.json`` and the CSV/PNG files written by
``src.run_models``, so slides, notebook and findings always match. AI-related wording
is "associated with" / "consistent with", never "caused".
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pandas as pd
from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

NAVY, BLUE, GREY, LIGHT = RGBColor(0x1B, 0x2A, 0x49), RGBColor(0x1F, 0x6F, 0xB2), RGBColor(0x55, 0x5B, 0x66), RGBColor(0xEA, 0xF1, 0xF8)
SLIDE_W, SLIDE_H = Inches(13.333), Inches(7.5)
MARGIN = Inches(0.5)

READABLE = {
    "has_error_text": "error text in the question", "code_ratio": "share of code in the body",
    "n_code_blocks": "number of code blocks", "body_length": "body length",
    "title_length": "title length", "account_age_days": "asker account age",
    "new_account": "new asker account", "missing_account_age": "deleted asker account",
    "lagged_tag_volume": "tag volume in the previous 4 weeks",
    "lagged_tag_change": "change in tag volume", "tag_count": "number of tags",
    "other_tags_count": "number of other tags", "hour_posted": "hour posted (UTC)",
    "weekday_posted": "weekday posted", "month_posted": "month posted",
}


def readable(name):
    if name in READABLE:
        return READABLE[name]
    if name.startswith("title_tfidf_svd_"):
        return f"title wording (component {name.rsplit('_', 1)[1]})"
    if name.startswith("tag_"):
        return f"tag {name[4:]}"
    if name.startswith("question_word_"):
        return f"title starts with '{name[14:]}'"
    return name.replace("_", " ")


PRETTY = {"xgboost": "XGBoost", "random forest": "Random Forest", "logistic regression": "Logistic regression",
          "majority class": "Majority class"}


SHORT = {"lagged_tag_volume": "tag volume", "account_age_days": "account age", "code_ratio": "share of code",
         "n_code_blocks": "code blocks", "body_length": "body length", "title_length": "title length",
         "has_error_text": "error text"}


def short(name):
    return SHORT.get(name) or readable(name)


def pretty(model):
    return PRETTY.get(model, model)


def pct(x, digits=0):
    return f"{100 * x:.{digits}f}%"


# ---------------------------------------------------------------- pptx helpers
def _text(slide, left, top, width, height, paragraphs, size=16, color=NAVY, bold=False, align=None):
    box = slide.shapes.add_textbox(left, top, width, height)
    frame = box.text_frame
    frame.word_wrap = True
    for i, para in enumerate(paragraphs if isinstance(paragraphs, list) else [paragraphs]):
        p = frame.paragraphs[0] if i == 0 else frame.add_paragraph()
        run = p.add_run()
        run.text = para
        run.font.size, run.font.bold, run.font.color.rgb, run.font.name = Pt(size), bold, color, "Calibri"
        p.space_after = Pt(6)
        if align:
            p.alignment = align
    return box


def _picture(slide, path, left, top, max_w, max_h):
    w, h = Image.open(path).size
    scale = min(max_w / w, max_h / h)
    width, height = int(w * scale), int(h * scale)
    return slide.shapes.add_picture(str(path), left + (max_w - width) // 2, top, width, height)


def _table(slide, left, top, width, rows, col_widths, size=13, highlight=None, row_height=0.4):
    shape = slide.shapes.add_table(len(rows), len(rows[0]), left, top, width, Inches(row_height) * len(rows))
    table = shape.table
    for row in table.rows:
        row.height = Inches(row_height)
    for j, w in enumerate(col_widths):
        table.columns[j].width = int(width * w / sum(col_widths))
    for i, row in enumerate(rows):
        for j, value in enumerate(row):
            cell = table.cell(i, j)
            cell.text = str(value)
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if j == 0 else PP_ALIGN.CENTER
            f = p.runs[0].font
            f.size, f.name = Pt(size), "Calibri"
            f.bold = i == 0 or (highlight is not None and i == highlight)
            f.color.rgb = RGBColor(255, 255, 255) if i == 0 else NAVY
            cell.fill.solid()
            cell.fill.fore_color.rgb = BLUE if i == 0 else (LIGHT if i == highlight else RGBColor(255, 255, 255))
    return shape


def _slide(prs, title, notes):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _text(slide, MARGIN, Inches(0.3), SLIDE_W - 2 * MARGIN, Inches(1.2), title, size=24, bold=True)
    slide.notes_slide.notes_text_frame.text = notes
    return slide


def _footer(slide, text):
    _text(slide, MARGIN, SLIDE_H - Inches(0.45), SLIDE_W - 2 * MARGIN, Inches(0.35), text, size=10, color=GREY)


# ---------------------------------------------------------------- content
def refresh_rolling(d, R):
    """Rebuild the rolling-origin summary and figure from ``rolling_origin.csv``.

    Adds the share resolved and ROC-AUC next to PR-AUC (PR-AUC depends on how common the
    positive class is), so older result folders get the corrected summary too.
    """
    csv = Path(d) / "rolling_origin.csv"
    if not csv.exists():
        return R
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from src import rolling

    table = pd.read_csv(csv, index_col=0)
    R["rolling"] = {**rolling.summarise_rolling(table), "table": table.reset_index().to_dict("records")}
    fig = rolling.plot_rolling(table)
    fig.savefig(Path(d) / "rolling_origin.png", dpi=130, bbox_inches="tight")
    plt.close(fig)
    (Path(d) / "results.json").write_text(json.dumps(R, indent=2, default=str))
    return R


def _load(res_dir):
    d = Path(res_dir)
    return d, refresh_rolling(d, json.loads((d / "results.json").read_text()))


def _direction(text):
    return text.replace("higher value -> ", "higher: ").replace("more likely resolved", "more often resolved") \
               .replace("less likely resolved", "less often resolved")


def _shap_notes(d):
    """Hand-written reading of the SHAP plots (``shap_notes.txt``, one observation per line), if present."""
    f = Path(d) / "shap_notes.txt"
    return [l.strip() for l in f.read_text().splitlines() if l.strip()] if f.exists() else []


def _trend_lines(roll, sec):
    """Plain statements about the rolling-origin result, with the base rate shown."""
    if not roll:
        return ["Rolling-origin results not available."]
    stable = abs(roll["roc_auc_post"] - roll["roc_auc_pre"]) < 0.02
    lines = [f"Ranking quality is {'stable' if stable else 'different'} across November 2022: mean ROC-AUC "
             f"{roll['roc_auc_pre']:.2f} before, {roll['roc_auc_post']:.2f} after.",
             f"PR-AUC is {roll['pr_auc_pre']:.2f} before and {roll['pr_auc_post']:.2f} after, but the share resolved also moved "
             f"({pct(roll['positive_rate_pre'])} to {pct(roll['positive_rate_post'])}); PR-AUC minus that base rate is "
             f"{roll['pr_auc_lift_pre']:.2f} before and {roll['pr_auc_lift_post']:.2f} after."]
    if sec:
        lines.append(f"Any answer within 7 days (secondary target): ROC-AUC {sec['secondary']['roc_auc']:.2f} vs "
                     f"{sec['main']['roc_auc']:.2f} for an accepted answer.")
    return lines


def build_deck(res_dir, out_path):
    d, R = _load(res_dir)
    val = pd.DataFrame(R["validation"]).set_index("model")
    gain = pd.read_csv(d / "feature_gain.csv", index_col=0)
    chosen, test, roll = R["chosen"], R["test"], R.get("rolling")
    sec = {r["model"].split(":")[0]: r for r in R["secondary"]}
    base = test["positive_rate"]
    prs = Presentation()
    prs.slide_width, prs.slide_height = SLIDE_W, SLIDE_H

    # ---- slide 1: model comparison
    others = val.drop(index=["majority class", chosen["model"]])
    margin = chosen["validation_pr_auc"] - others["pr_auc"].max()
    s1 = _slide(prs,
                f"{pretty(chosen['model'])} scores best, {'only narrowly' if margin < 0.02 else 'clearly'}: validation PR-AUC "
                f"{chosen['validation_pr_auc']:.2f} vs {val.loc['logistic regression', 'pr_auc']:.2f} for logistic regression "
                f"and {val.loc['majority class', 'pr_auc']:.2f} for no skill",
                f"We compared the models on the validation period (Jan to Jun 2025) with the same metrics. The majority-class baseline "
                f"has no skill (PR-AUC equals the share resolved, {val.loc['majority class', 'pr_auc']:.2f}). Logistic regression is the "
                f"interpretable baseline; Random Forest and XGBoost are the advanced models, tuned with time-series folds inside the training "
                f"period only. We select on PR-AUC because it is threshold-free and sensitive to class balance, then tune the decision threshold "
                f"on validation only. The differences between the three real models are small ({val['pr_auc'].drop('majority class').min():.3f} "
                f"to {val['pr_auc'].max():.3f}), so we say gradient boosting is only slightly better. Title text features raise logistic-regression "
                f"PR-AUC from {gain.loc['structured only', 'pr_auc']:.3f} to {gain.loc['structured + title text', 'pr_auc']:.3f}. "
                f"The test period had not been touched at this point.")
    order = ["majority class", "logistic regression", "random forest", "xgboost"]
    cols = ("precision", "recall", "f1", "pr_auc", "roc_auc")
    body = {m: [pretty(m), *(f"{val.loc[m, c]:.3f}" for c in cols)] for m in order}
    m4_file = d / "m4_baseline_val.csv"        # Member 4's baseline, scored by src/m4_baseline_eval.py
    if m4_file.exists():
        m4 = pd.read_csv(m4_file, index_col=0)
        row = m4[m4.index.str.endswith("tuned threshold")].iloc[0]
        body["m4"] = ["Logistic regression (Member 4 features)", *(f"{row[c]:.3f}" for c in cols)]
        order.insert(1, "m4")
    rows = [["Model", "Precision", "Recall", "F1", "PR-AUC", "ROC-AUC"]] + [body[m] for m in order]
    _table(s1, MARGIN, Inches(1.7), Inches(7.4), rows, [3.4, 1, 1, 1, 1, 1], size=14 if len(order) < 5 else 13,
           highlight=order.index(chosen["model"]) + 1)
    _picture(s1, d / "val_pr_roc.png", Inches(8.1), Inches(1.7), Inches(4.8), Inches(2.5))
    dp, df1 = (gain.loc["structured + title text", c] - gain.loc["structured only", c] for c in ("pr_auc", "f1"))
    _text(s1, MARGIN, Inches(4.3), Inches(7.4), Inches(2.6), [
        f"Chosen by highest validation PR-AUC; threshold {chosen['threshold']:.2f}, tuned for F1 on validation only. Share resolved is "
        f"{pct(val.loc['majority class', 'positive_rate'])}, so no-skill PR-AUC is {val.loc['majority class', 'pr_auc']:.2f}.",
        f"Feature gain (logistic regression): title text features change F1 by {df1:+.3f} and PR-AUC by {dp:+.3f}.",
        f"Tuned on time-series folds with a 7-day gap, training period only; XGBoost trees by early stopping on validation ({R['tuning']['xgb'].get('trees_after_early_stopping', 'n/a')} trees).",
    ], size=14)
    _footer(s1, "Validation period: Jan to Jun 2025. 'Resolved' = accepted answer within 7 days is the positive class.")

    # ---- slide 2: test evaluation + SHAP
    top = list(R.get("shap_top", {}))
    drivers = (f"{short(top[0])} and {short(top[1])} matter most" if len(top) > 1 else "see SHAP for the drivers")
    s2 = _slide(prs,
                f"On the untouched test period the model reaches PR-AUC {test['pr_auc']:.2f} (no skill: {base:.2f}) and ROC-AUC "
                f"{test['roc_auc']:.2f}; {drivers}",
                f"The test period (Jul 2025 to Jul 2026, {int(test['n']):,} questions) was evaluated exactly once, after the model, "
                f"hyperparameters and threshold were fixed on earlier data. Precision {test['precision']:.2f}, recall {test['recall']:.2f}, "
                f"F1 {test['f1']:.2f}, PR-AUC {test['pr_auc']:.2f}, ROC-AUC {test['roc_auc']:.2f}. Only {pct(base)} of test questions are "
                f"resolved, so predicting 'resolved' for everything would give precision {base:.2f} and F1 {2 * base / (1 + base):.2f}; the model "
                f"is above that but not by a wide margin. The result is modest and we report it as such. SHAP shows which features move "
                f"the predicted probability; tag volume probably reflects which tag and which period a question belongs to.")
    _table(s2, MARGIN, Inches(1.65), Inches(4.5),
           [["Test metric", "Value"], ["Questions", f"{int(test['n']):,}"], ["Share resolved (no skill)", f"{base:.3f}"],
            ["Precision", f"{test['precision']:.3f}"], ["Recall", f"{test['recall']:.3f}"], ["F1", f"{test['f1']:.3f}"],
            ["PR-AUC", f"{test['pr_auc']:.3f}"], ["ROC-AUC", f"{test['roc_auc']:.3f}"],
            ["Capture rate (20% flagged)", f"{test['capture_rate_20']:.3f}"]], [2.6, 1.2], size=13, row_height=0.34)
    _picture(s2, d / "test_confusion.png", MARGIN, Inches(4.85), Inches(3.0), Inches(2.1))
    if (d / "shap_summary.png").exists():
        _picture(s2, d / "shap_summary.png", Inches(5.3), Inches(1.6), Inches(3.7), Inches(5.3))
    direction = R.get("shap_direction", {})
    notes = [f"{readable(f)}: {_direction(direction.get(f, ''))}" for f in top[:5]]
    shap_notes = _shap_notes(d) or ["Tag volume likely reflects which tag and which period, not the question itself."]
    _text(s2, Inches(9.2), Inches(1.65), Inches(3.7), Inches(5.3),
          ["What the model relies on:"] + notes + ["From the SHAP plots:"] + shap_notes, size=11)
    _footer(s2, "Test period used once, after all tuning. SHAP computed on a random sample of test questions.")

    # ---- slide 3: rolling-origin + business finding
    cap, lift = test["capture_rate_20"], test["lift_20"]
    lines = _trend_lines(roll, sec)
    s3 = _slide(prs,
                f"Flagging the 20% of questions with the lowest predicted resolution catches {pct(cap)} of unresolved ones, "
                f"a {'modest ' if lift < 1.5 else ''}{lift:.1f}x lift over random",
                f"Rolling-origin evaluation trains on everything before each half-year and tests on that half-year, from 2021 H1 to 2026 H1, "
                f"so we can compare before and after November 2022, which the single test period cannot show. " + " ".join(lines) + " "
                f"Business use: a forum manager who can only act on 20% of questions flags the lowest-scoring ones and routes them to experts, "
                f"or prompts askers to add code or error text before posting; the lift is modest, so the score should prioritise, not decide. "
                f"Limits: acceptance is a strict proxy for resolved because it depends on the asker returning; recent data is smaller than the "
                f"sampled early years. We say 'associated with', not 'caused by'.")
    if roll and (d / "rolling_origin.png").exists():
        _picture(s3, d / "rolling_origin.png", MARGIN, Inches(1.65), Inches(7.4), Inches(2.7))
        _text(s3, MARGIN, Inches(4.45), Inches(7.4), Inches(2.5), lines, size=13)
    _text(s3, Inches(8.2), Inches(1.65), Inches(4.6), Inches(1.0), f"{pct(cap)}", size=54, color=BLUE, bold=True)
    _text(s3, Inches(8.2), Inches(2.8), Inches(4.6), Inches(0.7),
          "of unresolved questions are in the lowest-scored 20% (random flagging: 20%)", size=14, color=GREY)
    _text(s3, Inches(8.2), Inches(3.65), Inches(4.6), Inches(3.3), [
        "Act on it: route flagged questions to experts, or prompt askers to add code to their question before posting.",
        "Use the score to prioritise, not to decide: the lift over random flagging is modest.",
        "Limits: an accepted answer within 7 days is a proxy for resolved (it depends on the asker returning); recent data is smaller than the sampled early years.",
        "Results are associated with, not caused by, the platform changes after November 2022.",
    ], size=13)
    _footer(s3, "Rolling-origin: train on all data before each half-year, test on that half-year, 2021 H1 to 2026 H1.")

    prs.save(out_path)
    _check_bounds(prs)
    return out_path


def _check_bounds(prs):
    for i, slide in enumerate(prs.slides, 1):
        for shape in slide.shapes:
            if shape.left < 0 or shape.top < 0 or shape.left + shape.width > prs.slide_width + 1 \
                    or shape.top + shape.height > prs.slide_height + 1:
                raise ValueError(f"slide {i}: shape '{shape.name}' extends outside the slide")


def build_findings(res_dir, out_path):
    """Model findings for the shared findings page (M5-15)."""
    d, R = _load(res_dir)
    t, c = R["test"], R["chosen"]
    sec = {r["model"].split(":")[0]: r for r in R["secondary"]}
    roll = R.get("rolling")
    top = list(R.get("shap_top", {}))
    base = t["positive_rate"]
    lines = [
        "# Model findings (Member 5 section for `initial_findings.md`)",
        "",
        f"**What the model offers a support-forum manager.** {'An' if c['model'][0] in 'aeiou' or c['model'] == 'xgboost' else 'A'} {pretty(c['model'])} model, trained on questions up to December 2024 and "
        f"scored once on {int(t['n']):,} questions from July 2025 to July 2026, ranks questions by their chance of getting an "
        f"accepted answer within 7 days. It is better than no skill but the gain is modest: PR-AUC {t['pr_auc']:.2f} against "
        f"{base:.2f} for a no-skill ranking, ROC-AUC {t['roc_auc']:.2f}.",
        "",
        f"1. **Flagging 20% of questions catches {pct(t['capture_rate_20'])} of the unresolved ones** ({t['lift_20']:.1f} times random "
        f"flagging, which catches 20%). Stakeholder: support-forum manager. Action: use the score to prioritise which questions "
        f"experts see first, not to decide outcomes.",
    ]
    if top:
        direction = R.get("shap_direction", {})
        more = [readable(f) for f in top if "more likely" in direction.get(f, "") and not f.startswith(("lagged_", "title_"))]
        less = [readable(f) for f in top if "less likely" in direction.get(f, "") and not f.startswith(("lagged_", "title_"))]
        sentence = (f"Higher {', '.join(more)} are associated with more accepted answers. " if more else "") + \
                   (f"Higher {', '.join(less)} are associated with fewer. " if less else "")
        lines += [f"2. **The strongest signals are {', '.join(readable(f) for f in top[:3])}.** {sentence}"
                  + " ".join(_shap_notes(d) or ["Tag volume probably reflects which tag and which period a question belongs to, not the question's own quality."])
                  + " Stakeholder: community or product team. Action: prompt askers to add code to their question before posting; "
                    "do not assume error text helps, because it is associated with fewer accepted answers here."]
    if roll:
        lines += [f"3. **The share of resolved questions fell, but the model's ranking quality did not.** The share resolved is "
                  f"{pct(roll['positive_rate_pre'])} in test windows before November 2022 and {pct(roll['positive_rate_post'])} after, "
                  f"while mean ROC-AUC is {roll['roc_auc_pre']:.2f} before and {roll['roc_auc_post']:.2f} after across {roll['windows']} "
                  f"half-year windows. PR-AUC falls from {roll['pr_auc_pre']:.2f} to {roll['pr_auc_post']:.2f}, which follows the lower base rate "
                  f"(PR-AUC minus base rate: {roll['pr_auc_lift_pre']:.2f} before, {roll['pr_auc_lift_post']:.2f} after). The drop in resolution "
                  "is associated with the period around November 2022 but is not proof of cause. Stakeholder: analytics lead. "
                  "Action: track the resolution rate itself over time."]
    lines += [f"4. **The ranking is similar for a second target.** Predicting any answer within 7 days gives ROC-AUC "
              f"{sec['secondary']['roc_auc']:.2f} (accepted answer: {sec['main']['roc_auc']:.2f}); PR-AUC is not comparable because "
              f"{pct(sec['secondary']['positive_rate'])} of questions get an answer within 7 days against {pct(base)} an accepted one.",
              "",
              "**Limits.** An accepted answer within 7 days is a strict proxy for resolved because it depends on the asker returning. "
              "Gains over a no-skill ranking are modest, and the three real models differ only slightly. Recent data (2025 onwards) is "
              "smaller than the sampled early years. Only 13 tags are covered. AI-related statements say 'associated with' or "
              "'consistent with', never 'caused'.",
              ""]
    Path(out_path).write_text("\n".join(lines))
    return out_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="reports/review1/m5")
    ap.add_argument("--slides", default="reports/review1/m5_slides.pptx")
    ap.add_argument("--findings", default="reports/review1/m5_findings.md")
    a = ap.parse_args()
    print("wrote", build_deck(a.results, a.slides))
    print("wrote", build_findings(a.results, a.findings))


if __name__ == "__main__":
    main()

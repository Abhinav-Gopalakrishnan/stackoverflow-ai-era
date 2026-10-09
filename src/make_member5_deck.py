"""Build Member 5's dedicated slides (Adhikkesh) starting after slide 9.

Generates:
    - Member_5_Adhikkesh_Slides.pptx (9 slides, numbered 10 to 18)
    - reports/review1/member5_deck_preview/ (PNG previews of all 9 slides)
"""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from collections import Counter
from pathlib import Path

import pandas as pd

from src import deck_charts as ch
from src.deck_engine import (Deck, Para, check_bounds, check_overflow, contact_sheet, render_previews, save_pptx)

ROOT = Path(__file__).resolve().parents[1]
M5 = ROOT / "reports/review1/m5"
ASSETS = ROOT / "reports/review1/deck_assets"
PARQUET = ROOT / "data/processed/questions_clean_v1.parquet"
INK, MUTED, PANEL, RULE, FAINT = "1F2A37", "4B5563", "F3F4F6", "D1D5DB", "9CA3AF"
NAVY, ORANGE, TEAL, AMBER, SKY = "1D4E89", "C2410C", "0F766E", "B45309", "2A78D6"
LM, CW = 0.6, 12.13

REPO = "github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era"
BOARD = "github.com/users/Abhinav-Gopalakrishnan/projects/3"
NOTEBOOK = REPO + "/blob/main/notebooks/review1_main.ipynb"
DATA_DOC = REPO + "/blob/main/docs/dataset_documentation.md"
KAGGLE = "https://www.kaggle.com/code/abhinavgopalakrishnan/stackoverflow-in-the-ai-era"

TEAM = [
    ("Adhikkesh S K", "Adhikkesh", "CB.SC.U4CSE23101"),
    ("Abhinav Gopalakrishnan", "Abhinav", "CB.SC.U4CSE23201"),
    ("Rishiikesh", "Rishiikesh", "CB.SC.U4CSE23236"),
    ("Akshay Krishna", "Akshay", "CB.SC.U4CSE23403"),
    ("Nishanth Konchada", "Nishanth", "CB.SC.U4CSE23523"),
]


def P(*runs, size=13, after=6, color=INK, bullet=False, head=False, align="l", track=0.0):
    out = []
    for r in runs:
        out.append((r, False, color) if isinstance(r, str) else (r[0], r[1], r[2] if len(r) > 2 else color))
    return Para(out, size, align, bullet, after, head=head, track=track)


def lines(items, size=13, after=6, bullet=False, color=INK):
    return [P(t, size=size, after=after, bullet=bullet, color=color) if isinstance(t, str) else t for t in items]


def panel(s, x, y, w, h):
    s.rect(x, y, w, h, PANEL, radius=0.05)


def label(s, x, y, w, text):
    s.text(x, y, w, 0.3, text.upper(), size=11, bold=True, color=NAVY, track=1.5)


def block(s, x, y, w, h, title, body, size=13):
    panel(s, x, y, w, h)
    s.text(x + 0.25, y + 0.15, w - 0.5, 0.3, title, size=14, bold=True, color=NAVY, head=True)
    s.text(x + 0.25, y + 0.55, w - 0.5, h - 0.65, body if not isinstance(body, str) else P(body, size=size, after=0), size=size)


def title(s, text, n):
    s.text(LM, 0.4, CW, 0.8, text, size=28, bold=True, head=True)
    s.text(LM, 7.0, 6, 0.3, "Stack Overflow in the AI Era", size=10, color=FAINT)
    s.text(12.33, 7.0, 0.4, 0.3, str(n), size=10, color=FAINT, align="r")


def takeaway(s, lab, text, y, size=13):
    s.text(LM, y, CW, 0.6, P((lab + " ", True, ORANGE), (text, False), size=size, after=0))


def table(s, x, y, widths, rows, row_h=0.45, size=12, head_h=0.42, aligns=None, bold_first=True, highlight=None):
    total = sum(widths)
    cx = [x]
    for wd in widths[:-1]:
        cx.append(cx[-1] + wd)
    yy = y
    for i, row in enumerate(rows):
        hh = head_h if i == 0 else row_h
        if i == 0:
            s.rect(x, yy, total, hh, PANEL)
        elif highlight is not None and i == highlight:
            s.rect(x, yy, total, hh, "FDE8DC")
        for j, cell in enumerate(row):
            al = aligns[j] if aligns else ("l" if j == 0 else "c")
            if "\n" in str(cell):
                parts = [P((ln, k == 0 or i == 0), size=size, after=0, align=al, color=INK if k == 0 else MUTED)
                         for k, ln in enumerate(str(cell).split("\n"))]
                s.text(cx[j] + 0.1, yy, widths[j] - 0.2, hh, parts, size=size, valign="m")
            else:
                s.text(cx[j] + 0.1, yy, widths[j] - 0.2, hh, str(cell), size=size, valign="m", align=al,
                       bold=(i == 0) or (bold_first and j == 0))
        yy += hh
        s.line(x, yy, x + total, yy, RULE, 0.75)
    return yy


def derived_accuracy(precision, recall, positive_rate):
    if precision == 0 or recall == 0:
        return 1 - positive_rate
    tp = recall * positive_rate
    fp = tp / precision - tp
    return tp + (1 - positive_rate) - fp


def when(date):
    return pd.Timestamp(date).strftime("%-d %b")


def build(tmp: Path):
    d = Deck("FFFFFF")
    R = json.loads((M5 / "results.json").read_text())
    val = pd.read_csv(M5 / "model_comparison_val.csv", index_col=0)
    m4 = pd.read_csv(M5 / "m4_baseline_val.csv", index_col=0)
    base = m4[m4.index.str.endswith("tuned threshold")].iloc[0]
    test, roll = R["test"], R["rolling"]
    sec = pd.read_csv(M5 / "secondary_target.csv", index_col=0)
    snap = json.loads((ASSETS / "board_snapshot.json").read_text())
    
    # Start slide numbering from 10 (since slides 1-9 precede this in the team deck)
    n = [9]

    def new(name, notes=""):
        n[0] += 1
        s = d.slide(notes)
        title(s, name, n[0])
        return s

    # Slide 10: Predictive Model Development
    s = new("Predictive Model Development",
            "Binary classification with a chronological split. XGBoost is chosen on validation PR-AUC.")
    w3 = (CW - 0.6) / 3
    block(s, LM, 1.45, w3, 1.7, "Prediction task", "Binary classification: will a new question get an accepted answer within 7 days?", 12.5)
    block(s, LM + w3 + 0.3, 1.45, w3, 1.7, "Model(s)", "Majority-class baseline, logistic regression (baseline), random forest and XGBoost.", 12.5)
    block(s, LM + 2 * (w3 + 0.3), 1.45, w3, 1.7, "Model selection",
          f"Highest validation PR-AUC: XGBoost {val.loc['xgboost', 'pr_auc']:.3f}, random forest {val.loc['random forest', 'pr_auc']:.3f}, logistic regression {val.loc['logistic regression', 'pr_auc']:.3f}.", 12.5)
    block(s, LM, 3.3, 6.0, 1.7, "Data split",
          "Chronological. Train Jan 2019 to Dec 2024: 248,294 rows (85%). Validation Jan to Jun 2025: 28,132 (10%). Test Jul 2025 to Jul 2026: 16,695 (6%). The test period is scored once.", 12.5)
    block(s, 6.9, 3.3, 5.83, 1.7, "Model settings",
          f"Random forest: 472 trees, depth 16. XGBoost: learning rate 0.029, depth 5, {R['tuning']['xgb']['trees_after_early_stopping']} trees by early stopping. "
          f"Randomized search on time-series folds with a 7-day gap. Threshold {R['chosen']['threshold']:.2f}, chosen on validation.", 12.5)
    img = ch.split_timeline(PARQUET, tmp / "split.png", (12.0, 1.7))
    s.image(img, LM, 5.15, CW, 1.65)

    # Slide 11: Model Evaluation and Result Interpretation: Results
    s = new("Model Evaluation and Result Interpretation: Results",
            "Validation comparison of all models and the single test evaluation of XGBoost. Accuracy is derived from precision, recall and the share resolved.")
    rows = [["Model (validation)", "Accuracy", "Precision", "Recall", "F1", "PR-AUC", "ROC-AUC"]]
    for key, name in [("majority class", "Majority class"), ("m4", "Logistic regression (baseline)"), ("logistic regression", "Logistic regression"),
                      ("random forest", "Random forest"), ("xgboost", "XGBoost")]:
        r = base if key == "m4" else val.loc[key]
        pos = float(val.loc["majority class", "positive_rate"])
        rows.append([name, f"{derived_accuracy(r['precision'], r['recall'], pos):.3f}"] + [f"{r[c]:.3f}" for c in ("precision", "recall", "f1", "pr_auc", "roc_auc")])
    tn, fp, fn, tp = 5020, 6719, 1134, 3822
    rows.append(["XGBoost on the test period", f"{(tn + tp) / (tn + fp + fn + tp):.3f}", f"{test['precision']:.3f}", f"{test['recall']:.3f}", f"{test['f1']:.3f}",
                 f"{test['pr_auc']:.3f}", f"{test['roc_auc']:.3f}"])
    yb = table(s, LM, 1.5, [3.2, 1.0, 1.0, 0.9, 0.8, 0.95, 1.0], rows, row_h=0.5, size=12, highlight=6)
    s.text(LM, yb + 0.2, 8.8, 1.9, lines([
        f"Share resolved: {val.loc['majority class', 'positive_rate'] * 100:.0f}% in validation and {test['positive_rate'] * 100:.0f}% in the test period, so a no-skill ranking has PR-AUC {val.loc['majority class', 'pr_auc']:.3f} and {test['positive_rate']:.3f}.",
        "Baseline row uses the threshold tuned on validation. At the default 0.5 it scores accuracy 0.640, precision 0.423, recall 0.160. Always guessing 'unresolved' gives accuracy 0.659.",
        "Regression metrics (R², MAE, MSE, RMSE) do not apply: this is a classification task."], 12.5, 6, bullet=True))
    s.text(9.7, 1.4, 3.0, 0.3, "Test confusion matrix", size=12, bold=True, color=MUTED)
    s.image(M5 / "test_confusion.png", 9.55, 1.75, 3.2, 3.2)

    # Slide 12: Model Evaluation and Result Interpretation: Interpretation
    s = new("Model Evaluation and Result Interpretation: Interpretation",
            "SHAP shows what drives the predictions. Strengths: ranks questions above chance and stays stable across November 2022. Limits: the gain is modest.")
    s.image(M5 / "shap_summary.png", LM, 1.4, 3.9, 5.3)
    block(s, 4.8, 1.5, 3.9, 5.2, "Strengths", lines([
        f"Ranks questions above chance on the untouched test period: ROC-AUC {test['roc_auc']:.3f} (chance 0.5), PR-AUC {test['pr_auc']:.3f} (no skill {test['positive_rate']:.3f}).",
        f"Ranking quality holds across November 2022 (ROC-AUC {roll['roc_auc_pre']:.2f} before, {roll['roc_auc_post']:.2f} after).",
        f"Works for 'any answer in 7 days' too (ROC-AUC {sec.iloc[1]['roc_auc']:.3f}).",
        "Drivers agree with the logistic regression: new accounts and error text go with fewer accepted answers, code with more."], 12.5, 7, bullet=True))
    block(s, 8.9, 1.5, 3.83, 5.2, "Limitations", lines([
        "The gain over no skill is modest, and the three real models differ by about 0.01.",
        "An accepted answer depends on the asker coming back, so it is a proxy for resolved.",
        "Tag volume stands in for the period and tag mix, not for the question.",
        "13 tags only, and recent data is smaller than the sampled early years.",
        "Results are associated with, not caused by, the platform changes."], 12.5, 7, bullet=True))

    # Slide 13: Model Evaluation and Result Interpretation: Business findings
    s = new("Model Evaluation and Result Interpretation: Business findings",
            "Flagging the lowest 20 percent of predicted resolution catches 24 percent of the unresolved questions. Resolution fell while ranking quality did not.")
    w4 = (CW - 0.9) / 4
    findings = [("Prioritise", f"Flag the 20% of questions with the lowest predicted resolution: it catches {test['capture_rate_20'] * 100:.0f}% of the unresolved ones, against 20% by chance."),
                ("Ask for code", "More code goes with more accepted answers. Error text and brand-new accounts go with fewer."),
                ("Watch the rate", f"Resolution fell from {roll['positive_rate_pre'] * 100:.0f}% to {roll['positive_rate_post'] * 100:.0f}% while ranking quality stayed flat. Track the rate itself."),
                ("Refresh the model", "Behaviour shifts over time, so retrain regularly and keep scoring on the newest months.")]
    for i, (head, text) in enumerate(findings):
        block(s, LM + i * (w4 + 0.3), 1.5, w4, 2.3, head, text, 12.5)
    img = ch.rolling_chart(M5 / "rolling_origin.csv", tmp / "roll.png", (12.0, 2.9))
    s.text(LM, 3.95, CW, 0.3, "Train on everything before each half-year, test on that half-year (2021 H1 to 2026 H1)", size=12, bold=True, color=MUTED)
    s.image(img, LM, 4.25, CW, 2.6)

    # Slide 14: Project Tracking and Progress
    s = new("Project Tracking and Progress",
            "One GitHub Projects board with five stages. Each task has an assignee and a status. Due dates are not set on the board.")
    label(s, LM, 1.45, 4.6, "Tool and board link")
    s.text(LM, 1.78, 4.6, 0.7, [P("GitHub Projects", size=12.5, after=1), P(BOARD, size=11, color=MUTED, after=0)])
    label(s, LM, 2.6, 4.6, "Stages")
    s.text(LM, 2.93, 4.6, 0.7, "Backlog, To Do, In Progress, Review/Testing, Completed", size=12.5)
    label(s, LM, 3.75, 4.6, "Evidence")
    s.text(LM, 4.08, 4.6, 1.5, lines(["Code and tests: src/, tests/", "Data and documentation: data/processed, docs/", "Notebooks: notebooks/",
                                      "Charts and reports: reports/review1/"], 12, 3, bullet=True))
    label(s, 5.5, 1.45, 7.2, "Tasks")
    pick = ["Core API request function", "Weekly question counts", "Enrichment script", "Both targets", "Question volume trends", "Time to answer",
            "Split module and verification", "Baseline model", "Evaluation module", "Feature spec and leakage review"]
    by_title = {t["title"]: t for t in snap["tasks"]}
    trows = [["Task", "Assignee", "Status", "Closed"]]
    for t in pick:
        x = by_title[t]
        trows.append([t, x["assignee"], x["status"], when(x["closed"]) if x["closed"] else "-"])
    table(s, 5.5, 1.78, [3.1, 1.2, 1.7, 1.23], trows, row_h=0.34, size=11, head_h=0.36, aligns=["l", "l", "l", "l"], bold_first=False)
    created, closed = Counter(i["created"] for i in snap["issue_dates"]), Counter(i["closed"] for i in snap["issue_dates"] if i["closed"])
    notes = {"2026-10-01": "board and repository set up", "2026-10-02": "API client, key and enrichment design",
             "2026-10-03": "collection, enrichment and cleaning finished, cleaned dataset ready", "2026-10-04": "EDA, features, models, evaluation and findings"}
    label(s, LM, 5.65, 6, "Activity history")
    days = sorted(created)
    cwd = CW / len(days)
    for i, day in enumerate(days):
        s.text(LM + i * cwd, 5.98, cwd - 0.15, 0.9, [P((when(day) + " 2026", True, NAVY), size=12, after=2),
                                                    P(f"{created[day]} tasks opened, {closed.get(day, 0)} closed", size=11, color=MUTED, after=1),
                                                    P(notes.get(day, ""), size=11, after=0)])

    # Slide 15: Individual Contributions
    s = new("Individual Contributions",
            "Tasks on the GitHub Projects board by assignee: how many were assigned, completed, and still open or in review.")
    did = {"Adhikkesh": "Models, evaluation and findings: XGBoost and random forest, SHAP, before-and-after check, error analysis.",
           "Abhinav": "Data collection: API client, sampling, 309,179 questions, weekly counts, Data Explorer check, dataset documentation.",
           "Rishiikesh": "Enrichment and cleaning: answer and asker details, clean table, both 7-day outcomes, sampling robustness.",
           "Akshay": "Problem and EDA: problem statement, event list, EDA charts, statistical checks, findings page.",
           "Nishanth": "Split and features: time-based split, feature pipeline, leakage check, logistic regression baseline."}
    crow = [["Member", "What they did", "Tasks assigned", "Completed", "Open or in review"]]
    for full, short, reg in TEAM:
        mine = [t for t in snap["tasks"] if t["assignee"] == short]
        done = sum(t["status"] == "Completed" for t in mine)
        crow.append([f"{full}\n{reg}", did[short], len(mine), done, len(mine) - done])
    table(s, LM, 1.5, [3.0, 5.4, 1.2, 1.2, 1.33], crow, row_h=0.85, size=12, head_h=0.5, aligns=["l", "l", "c", "c", "c"])
    takeaway(s, "Source:", "the GitHub Projects board, counted by assignee as of 4 October 2026.", 6.4, size=12)

    # Slide 16: Review 2 Plan
    s = new("Review 2 Plan",
            "Topics people still ask about, forecasts by technology, and a stronger model.")
    plans = [("Topics and complexity", ["Mine question text to find what developers still ask humans.", "Check whether question complexity changed around AI adoption."]),
             ("Forecast activity by technology", ["Forecast weekly volume per tag from the complete counts.", "Find which tags keep declining and which stay stable, and how support should change."]),
             ("A stronger prediction model", ["Add asker-history features if they can be used without leakage.", "Make the error-text feature case-insensitive and calibrate the scores.", "Use one shared feature pipeline and save the final model."])]
    cw3 = (CW - 0.6) / 3
    for i, (head, items) in enumerate(plans):
        panel(s, LM + i * (cw3 + 0.3), 1.5, cw3, 4.6)
        s.text(LM + i * (cw3 + 0.3) + 0.3, 1.75, cw3 - 0.6, 0.8, head, size=18, bold=True, head=True, color=NAVY)
        s.text(LM + i * (cw3 + 0.3) + 0.3, 2.7, cw3 - 0.6, 3.3, lines(items, 14, 10, bullet=True))

    # Slide 17: Submissions
    s = new("Submissions", "Links to the notebook, the data documentation and the project board.")
    rows = [("Kaggle Notebook", KAGGLE or "link to be added"), ("Data Documentation", DATA_DOC), ("Board", BOARD)]
    for i, (name, link) in enumerate(rows):
        y = 1.6 + i * 1.5
        s.text(LM, y, 0.9, 0.6, f"{i + 1:02d}", size=30, bold=True, head=True, color=NAVY)
        s.text(LM + 1.0, y + 0.02, 5, 0.45, name, size=20, bold=True)
        s.text(LM + 1.0, y + 0.55, CW - 1.0, 0.5, link, size=13, color=MUTED if KAGGLE or name != "Kaggle Notebook" else ORANGE)
        s.line(LM, y + 1.25, LM + CW, y + 1.25, RULE, 0.75)
    s.text(LM, 6.2, CW, 0.5, "The notebook is also on GitHub: " + NOTEBOOK, size=11.5, color=MUTED)

    # Slide 18: Thank you
    n[0] += 1
    s = d.slide("Thank you. We are happy to take questions.")
    s.text(0.6, 1.6, 7.5, 1.0, "Thank you!", size=48, bold=True, head=True)
    s.text(0.6, 3.0, 7, 0.4, "Questions?", size=18, color=MUTED)
    s.text(0.6, 4.3, 6.4, 1.9, [P((nm, True), ("     " + reg, False, MUTED), size=13, after=3) for nm, _, reg in TEAM])
    img = ch.weekly_volume(ROOT / "data/processed/weekly_counts.csv", tmp / "end.png", (5.4, 3.8), events=False)
    s.image(img, 7.6, 1.5, 5.4, 3.8)
    
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "Member_5_Adhikkesh_Slides.pptx"))
    ap.add_argument("--preview", action="store_true")
    a = ap.parse_args()
    tmp = Path(tempfile.mkdtemp(prefix="m5_deck_"))
    try:
        d = build(tmp)
        out = Path(a.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        save_pptx(d, out)
        print(f"wrote {out}  ({len(d.slides)} slides)")
        if a.preview:
            pdir = ROOT / "reports/review1/member5_deck_preview"
            pdir.mkdir(parents=True, exist_ok=True)
            files = render_previews(d, pdir)
            contact_sheet(files, pdir / "contact_sheet.png", cols=3)
            print(f"previews written to {pdir}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()

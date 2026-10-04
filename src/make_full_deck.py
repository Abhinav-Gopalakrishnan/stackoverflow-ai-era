"""Build the full Review 1 deck (all five members) from the repository's results.

    python -m src.make_full_deck            # writes "BA Final Project - Review 1 - Full.pptx" in the repo root
    python -m src.make_full_deck --preview  # also writes slide PNGs and a contact sheet to reports/review1/deck_preview/

The look follows the team's earlier SNA case-study deck: white slides, light-grey panels, a small
navy section tag, Cambria headings and big numbers, Calibri body text, and a "What it means" line
at the bottom of most slides. Every number is read from files in the repo (``data/processed``,
``reports/review1/m5``) or taken from the members' own write-ups (``reports/review1/*_slides.md``,
``notebooks/03_eda.ipynb``).
"""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path

import pandas as pd

from src import deck_charts as ch
from src.deck_engine import (Deck, Para, check_bounds, check_overflow, contact_sheet, render_previews, save_pptx,
                             text_height)

ROOT = Path(__file__).resolve().parents[1]
M5 = ROOT / "reports/review1/m5"
INK, MUTED, PANEL, RULE, FAINT = "1F2A37", "4B5563", "F3F4F6", "D1D5DB", "9CA3AF"
NAVY, ORANGE, TEAL, AMBER, PURPLE, SKY = "1D4E89", "C2410C", "0F766E", "B45309", "6D28D9", "2A78D6"
LM, CW, TOP = 0.6, 12.13, 1.75
REPO_URL = "github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era"
BOARD_URL = "github.com/users/Abhinav-Gopalakrishnan/projects/3"

TEAM = [("Adhikkesh S K", "CB.SC.U4CSE23101"), ("Abhinav Gopalakrishnan", "CB.SC.U4CSE23201"), ("Rishiikesh", "CB.SC.U4CSE23236"),
        ("Akshay Krishna", "CB.SC.U4CSE23403"), ("Nishanth Konchada", "CB.SC.U4CSE23523")]
PARQUET = ROOT / "data/processed/questions_clean_v1.parquet"

TAG_COUNTS = {"python": 84574, "javascript": 56600, "java": 33716, "reactjs": 25276, "android": 22616, "r": 17963,
              "powerbi": 16401, "sql": 13967, "pandas": 13447, "excel": 8052, "fastapi": 7290, "docker": 6743,
              "openai-api": 2534}


# ---------------------------------------------------------------- building blocks
def P(*runs, size=13.5, after=6, color=INK, bullet=False, head=False, align="l"):
    """A paragraph from strings or ``(text, bold[, color])`` runs."""
    out = []
    for r in runs:
        if isinstance(r, str):
            out.append((r, False, color))
        else:
            out.append((r[0], r[1], r[2] if len(r) > 2 else color))
    return Para(out, size, align, bullet, after, head=head)


def lines(items, size=13.5, after=7, color=INK, bullet=False):
    return [P(t, size=size, after=after, color=color, bullet=bullet) if isinstance(t, str) else t for t in items]


def panel(s, x, y, w, h):
    s.rect(x, y, w, h, PANEL, radius=0.05)


def bignum(s, x, y, w, text, color=NAVY, size=30, h=0.6):
    s.text(x, y, w, h, text, size=size, color=color, bold=True, head=True)


def stat_panel(s, x, y, w, h, num, label, desc=None, color=NAVY, size=30):
    panel(s, x, y, w, h)
    bignum(s, x + 0.3, y + 0.15, w - 0.6, num, color, size)
    s.text(x + 0.3, y + 0.15 + size / 72 * 1.5, w - 0.6, 0.3, label, size=13, bold=True)
    if desc:
        s.text(x + 0.3, y + 0.15 + size / 72 * 1.5 + 0.35, w - 0.6, h - size / 72 * 1.5 - 0.65, desc, size=11.5, color=MUTED)


def mini_stat(s, x, y, w, h, num, label, color=NAVY, size=26):
    panel(s, x, y, w, h)
    s.text(x + 0.25, y + 0.1, w - 0.5, h * 0.5, num, size=size, color=color, bold=True, head=True, valign="m")
    s.text(x + 0.25, y + h * 0.55, w - 0.5, h * 0.42, label, size=11.5, color=MUTED)


def takeaway(s, label, text, y=6.3, size=13.5):
    s.text(LM, y, CW, 0.6, P((label + " ", True, ORANGE), (text, False), size=size, after=0))


def header(s, tag, title, n, who):
    s.text(LM, 0.34, 9, 0.3, tag.upper(), size=11, color=NAVY, bold=True, track=2)
    s.text(LM, 0.66, CW, 1.0, title, size=28, bold=True, head=True)
    s.text(LM, 7.0, 6, 0.3, "Stack Overflow in the AI Era", size=10, color=FAINT)
    s.text(12.33, 7.0, 0.4, 0.3, str(n), size=10, color=FAINT, align="r")


def table(s, x, y, widths, rows, row_h=0.5, size=12.5, head_h=0.45, aligns=None, bold_first=True):
    """Light table: grey header row, thin rules between rows. Returns the bottom edge."""
    total = sum(widths)
    cx = [x]
    for wd in widths[:-1]:
        cx.append(cx[-1] + wd)
    yy = y
    for i, row in enumerate(rows):
        hh = head_h if i == 0 else row_h
        if i == 0:
            s.rect(x, yy, total, hh, PANEL)
        for j, cell in enumerate(row):
            al = aligns[j] if aligns else ("l" if j == 0 else "c")
            s.text(cx[j] + 0.12, yy, widths[j] - 0.24, hh, str(cell), size=size, valign="m", align=al,
                   bold=(i == 0) or (bold_first and j == 0))
        yy += hh
        s.line(x, yy, x + total, yy, RULE, 0.75)
    return yy


def numbered(s, x, y, items, step=0.95, w=6.8):
    """The 01, 02, ... list used on the overview slide."""
    for i, (title, text) in enumerate(items):
        yy = y + i * step
        s.text(x, yy, 0.9, 0.6, f"{i + 1:02d}", size=30, bold=True, head=True, color=NAVY)
        s.text(x + 0.95, yy + 0.02, w, 0.35, title, size=17, bold=True)
        s.text(x + 0.95, yy + 0.38, w, 0.5, text, size=13.5, color=MUTED)


# ---------------------------------------------------------------- content
def build(tmp: Path):
    d = Deck("FFFFFF")
    R = json.loads((M5 / "results.json").read_text())
    val = pd.read_csv(M5 / "model_comparison_val.csv", index_col=0)
    m4 = pd.read_csv(M5 / "m4_baseline_val.csv", index_col=0)
    m4row = m4[m4.index.str.endswith("tuned threshold")].iloc[0]
    test, roll = R["test"], R["rolling"]
    sec = pd.read_csv(M5 / "secondary_target.csv", index_col=0)
    gain = pd.read_csv(M5 / "feature_gain.csv", index_col=0)
    pp = ch.pre_post(ROOT / "data/processed/monthly_tag_tables.csv")
    n = [0]

    def new(tag, title, who, notes=""):
        n[0] += 1
        s = d.slide(notes)
        header(s, tag, title, n[0], who)
        return s

    # ---- 1 title ---------------------------------------------------------------------------
    n[0] += 1
    s = d.slide("Good morning. We are Team 7. Our project asks one practical question about Stack Overflow in the age of AI coding assistants: "
                "can we tell, when a question is posted, whether it will get an accepted answer within a week?")
    s.text(0.6, 1.15, 6.4, 0.3, "TEAM 7  ·  23CSE452 BUSINESS ANALYTICS  ·  REVIEW 1", size=12, bold=True, color=NAVY, track=1.5)
    s.text(0.6, 1.6, 5.9, 2.5, "Which Stack Overflow questions still get an answer in the age of AI?", size=36, bold=True, head=True, after=0)
    s.text(0.6, 4.2, 5.9, 0.8, "A prediction study on 309,179 questions, 2019 to 2026", size=16, color=MUTED)
    s.text(0.6, 4.95, 6.2, 1.9, [P((n_, True), ("     " + r_, False, MUTED), size=13, after=3) for n_, r_ in TEAM])
    img = ch.weekly_volume(ROOT / "data/processed/weekly_counts.csv", tmp / "weekly_title.png", (6.1, 4.3), events=False)
    s.image(img, 6.9, 1.0, 6.1, 4.6)
    s.text(6.9, 5.75, 6.0, 0.5, "Questions per week on Stack Overflow, 2019 to 2026 (complete counts from the Stack Exchange API)", size=10.5, color=MUTED)

    # ---- 2 plan -----------------------------------------------------------------------------
    s = new("01  /  The plan", "Five stages, one pipeline, one question", "Team 7",
            "Our work follows the data: collect it, clean it, explore it, prepare features and a baseline, then build and test the stronger models. "
            "We present the problem first, then the data, what the data shows, and the models.")
    numbered(s, LM, TOP + 0.0, [
        ("Collect", "309,179 questions pulled from the Stack Exchange API, across 13 tags."),
        ("Clean", "302,026 clean rows, each with two 7-day outcomes."),
        ("Explore", "What the data says about resolution before and after late 2022."),
        ("Prepare", "A time-based split, features that cannot leak, and a baseline."),
        ("Predict", "Stronger models, tested once on the newest period.")], step=0.9, w=6.8)
    panel(s, 8.55, TOP, 4.18, 3.7)
    s.text(8.85, TOP + 0.25, 3.6, 0.4, "The question", size=18, bold=True, head=True)
    s.text(8.85, TOP + 0.8, 3.6, 3.5, [P("Will a newly posted question get an accepted answer within 7 days?", size=14, after=10),
                                       P("If we can tell early, a forum team can send the hardest questions to an expert first.", size=13.5, color=MUTED, after=10),
                                       P("We also look at what changed after ChatGPT launched, without claiming it was the cause.", size=13.5, color=MUTED, after=0)])
    takeaway(s, "Order of the talk:", "the problem, the data, what the data shows, then the models.", y=6.5)

    # ---- 3 problem: decline -----------------------------------------------------------------
    s = new("01  /  The problem", "Stack Overflow lost about nine in ten questions in three years", "",
            "Stack Overflow used to be where every developer went with a question. Checked against the Stack Exchange Data Explorer, the site received about "
            "1.3 million questions in 2022 and about 109 thousand in 2025. The fall starts around the time Copilot became available and ChatGPT launched. "
            "We describe the timing of events; we do not claim they caused it.")
    img = ch.weekly_volume(ROOT / "data/processed/weekly_counts.csv", tmp / "weekly.png", (7.8, 4.2))
    s.text(LM, TOP, 7.8, 0.3, "Questions per week, 2019 to 2026", size=12, bold=True, color=MUTED)
    s.image(img, LM, TOP + 0.35, 7.8, 4.15)
    stat_panel(s, 8.75, TOP, 3.98, 1.9, "1.34M → 109K", "questions a year, 2022 vs 2025", "A fall of 92%, checked against Stack Exchange Data Explorer.", NAVY, 28)
    panel(s, 8.75, TOP + 2.1, 3.98, 2.4)
    s.text(9.05, TOP + 2.25, 3.4, 2.2, [P(("Four events sit around the break", True), size=14, after=6),
                                       P(("Jun 2022  ", True, NAVY), "GitHub Copilot opens to all developers", size=12.5, after=3),
                                       P(("30 Nov 2022  ", True, NAVY), "ChatGPT launches", size=12.5, after=3),
                                       P(("Dec 2022  ", True, NAVY), "Stack Overflow bans ChatGPT answers", size=12.5, after=3),
                                       P(("Jun 2023  ", True, NAVY), "Moderators go on strike", size=12.5, after=0)])
    takeaway(s, "What it means:", "the timing fits the arrival of AI tools, but we only describe timing. We do not claim cause.", y=6.45)

    # ---- 4 problem: question ----------------------------------------------------------------
    s = new("01  /  The problem", "So we asked: will a new question get an accepted answer?", "",
            "A forum manager cannot read every new question. If we can estimate which ones are likely to stay unresolved, experts can look at those first. "
            "We predict whether a question gets an accepted answer within seven days, and we check our conclusions against a second, easier outcome: any answer within seven days.")
    cw3 = (CW - 2 * 0.3) / 3
    cols = [("The problem", ["Activity on developer Q&A sites has dropped since AI coding assistants spread.",
                            "Managers cannot see which questions still need a human expert, or which are likely to go unanswered.",
                            "We study how resolution changed and whether we can predict it."]),
            ("The prediction", [P(("Main outcome: ", True, NAVY), "an accepted answer within 7 days. 41% of questions get one.", size=15, after=10),
                                P(("Check outcome: ", True, NAVY), "any answer within 7 days. 75% do.", size=15, after=10),
                                P(("One rule: ", True, NAVY), "only what is known when the question is posted may be used.", size=15, after=0)]),
            ("Who would use it", ["Forum managers send risky questions to experts.", "Product teams track how resolution shifts.",
                                  "Developer relations teams see which technologies lose community help."])]
    for i, (title, items) in enumerate(cols):
        x = LM + i * (cw3 + 0.3)
        panel(s, x, TOP, cw3, 4.0)
        s.text(x + 0.3, TOP + 0.22, cw3 - 0.6, 0.4, title, size=18, bold=True, head=True, color=NAVY)
        s.text(x + 0.3, TOP + 0.85, cw3 - 0.6, 3.05, lines(items, 15, 10))
    takeaway(s, "Our research question:", "which question characteristics predict an accepted answer within 7 days, and how did resolution change around November 2022?", y=6.0)

    # ---- 5 collection -----------------------------------------------------------------------
    who = ""
    s = new("02  /  Data collection", "We collected 309,179 questions from the official API", who,
            "Everything comes from the public Stack Exchange API, version 2.3. We built a collection client that waits half a second between calls, obeys the API's "
            "back-off requests, retries failures with longer waits and saves every raw response. During collection we found that the API sometimes says there are no more "
            "pages when there are. Probing one extra page recovered more than 3,600 missing questions. User IDs are hashed with a secret salt the moment they arrive.")
    heads = [("1.  Ask the API", NAVY, ["One registered key, API version 2.3.", "Half a second between calls.", "Obey the API's back-off requests and retry failures with longer waits.", "Save every raw response."]),
             ("2.  Fix what broke", TEAL, ["The API sometimes says there are no more pages when there are.", "We probe one extra page. That recovered 3,222 reactjs and 393 docker questions.", "Every call goes into an audit log: 19,306 calls."]),
             ("3.  Protect people", ORANGE, ["User IDs are hashed with SHA-256 and a secret salt as they arrive.", "Raw IDs and names are never stored.", "Content is CC BY-SA 4.0, so slides show titles only, with links."])]
    cw3 = (CW - 2 * 0.3) / 3
    for i, (title, color, items) in enumerate(heads):
        x = LM + i * (cw3 + 0.3)
        s.rect(x, TOP, cw3, 0.6, color)
        s.text(x + 0.25, TOP, cw3 - 0.5, 0.6, title, size=17, bold=True, color="FFFFFF", valign="m")
        panel(s, x, TOP + 0.75, cw3, 3.0)
        s.text(x + 0.25, TOP + 0.95, cw3 - 0.5, 2.7, lines(items, 14.5, 9))
    takeaway(s, "In numbers:", "309,179 questions, 13 tags, 2,800 days (January 2019 to August 2026), 19,306 logged API calls.", y=5.95)

    # ---- 6 sampling -------------------------------------------------------------------------
    s = new("02  /  Data collection", "Two sampled days a month before 2025, every day after", who,
            "Collecting all four million questions would have exceeded the API limits, so before 2025 we sampled one random weekday and one random weekend day per tag "
            "and month, and gave each question a weight that restores the real mix of days. From January 2025 volume is low enough to collect everything. "
            "The chart shows the sampling rate jumping from about seven percent to one hundred percent.")
    panel(s, LM, TOP, 4.7, 4.45)
    s.text(LM + 0.3, TOP + 0.2, 4.1, 4.1, [P(("2019 to 2024", True, NAVY), size=16, after=3),
                                          P("One random weekday and one random weekend day per tag and month (seed 42).", size=13.5, after=7),
                                          P("Each question gets a weight: ", ("days of that type in the month divided by days sampled.", True), size=13.5, after=7),
                                          P("Example: a month with 22 weekdays and 8 weekend days. One sampled weekday stands for 22 days of questions, one sampled weekend day for 8.", size=12, color=MUTED, after=12),
                                          P(("2025 to 2026", True, NAVY), size=16, after=3),
                                          P("Every question is collected, so the weight is 1.", size=13.5, after=0)])
    s.image(ROOT / "reports/review1/deck_assets/eda_sampling.png", 5.5, TOP, 7.23, 4.45)
    takeaway(s, "What it means:", "the sample is cheap but safe. Yearly volume estimated from it is within about 2% of the complete counts.", y=6.4)

    # ---- 7 tags -----------------------------------------------------------------------------
    s = new("02  /  The dataset", "Python and JavaScript make up almost half of the 13 tags", who,
            "We chose popular and varied tags: general-purpose languages, data tools, frameworks, and one AI tag, openai-api, as a contrast. That tag's history only starts in 2023, "
            "so it shows topic and volume contrast, nothing more. Alongside the sampled records we collected the complete weekly question counts for every tag and for the whole site.")
    img = ch.tag_bars(TAG_COUNTS, tmp / "tags.png", (6.7, 4.1))
    s.text(LM, TOP, 6.6, 0.3, "Collected questions per tag", size=12, bold=True, color=MUTED)
    s.image(img, LM, TOP + 0.3, 6.7, 4.1)
    stat_panel(s, 7.7, TOP, 5.03, 2.0, "5,600", "weekly counts", "14 series (13 tags and the whole site) over 400 weeks, with no missing weeks. They drive every volume chart.", NAVY)
    stat_panel(s, 7.7, TOP + 2.2, 5.03, 2.0, "46%", "of rows are Python or JavaScript", "openai-api is our AI contrast tag. Its history starts in 2023, so we use it only for contrast.", ORANGE)
    takeaway(s, "Why these tags:", "they are popular and varied, so the results are not about one language.", y=6.5)

    # ---- 8 verification ---------------------------------------------------------------------
    s = new("02  /  Verification", "Our counts match Stack Exchange's own tool to within 0.01%", who,
            "To be sure the population counts are right, we checked them against Stack Exchange Data Explorer queries. The monthly sums match within 0.01 percent. "
            "These verified figures are the only headline numbers we use: a peak of about 207 thousand questions in March 2014, 1.34 million in 2022, 109 thousand in 2025 and 1,442 in July 2026.")
    w2 = (CW - 0.3) / 2
    for i, (num, label, desc, color) in enumerate([("207,204", "questions in March 2014", "The all-time monthly peak.", AMBER),
                                                   ("1,336,266", "questions in 2022", "The last full year before ChatGPT.", NAVY),
                                                   ("108,981", "questions in 2025", "A fall of 91.8% from 2022.", ORANGE),
                                                   ("1,442", "questions in July 2026", "99.3% below the 2014 peak.", ORANGE)]):
        stat_panel(s, LM + (i % 2) * (w2 + 0.3), TOP + (i // 2) * 2.1, w2, 1.95, num, label, desc, color)
    takeaway(s, "How we checked:", "we queried Stack Exchange Data Explorer for several tags and compared its monthly totals with our weekly counts. They agree within 0.01%. These are the only headline numbers we quote.", y=6.1)

    # ---- 9 cleaning steps -------------------------------------------------------------------
    who = ""
    s = new("03  /  Cleaning", "Five cleaning steps turned raw records into one clean table", who,
            "We first fetched the answer and asker details we were missing: over eight thousand batched API calls, none failed, with user IDs hashed straight away. Then five cleaning steps: "
            "merge and remove duplicates, convert timestamps, split the HTML into text and code, handle missing values, and check for invalid or extreme posts.")
    steps = [("Merge", "7,147 questions carried two selected tags. We kept one row for each."),
             ("Timestamps", "Converted to UTC and checked: no answer before its question, nothing outside the window."),
             ("Split the HTML", "Plain text and code are separated. We count code blocks and flag error text."),
             ("Missing values", "No accepted answer means target 0. Deleted askers get a flag and an imputed age."),
             ("Invalid posts", "Empty, mostly non-English or spam posts are removed. Very long bodies are capped.")]
    cw5 = (CW - 4 * 0.2) / 5
    for i, (title, text) in enumerate(steps):
        x = LM + i * (cw5 + 0.2)
        panel(s, x, TOP, cw5, 2.75)
        bignum(s, x + 0.2, TOP + 0.12, 1.0, f"{i + 1}", NAVY, 28)
        s.text(x + 0.2, TOP + 0.75, cw5 - 0.4, 0.4, title, size=15, bold=True)
        s.text(x + 0.2, TOP + 1.2, cw5 - 0.4, 1.5, text, size=12.5, color=MUTED)
    w3 = (CW - 0.6) / 3
    for i, (num, label) in enumerate([("302,032", "rows joined with answers and asker details"), ("8,462", "enrichment API calls, none failed"),
                                      ("220,943", "asker records, IDs hashed on arrival")]):
        mini_stat(s, LM + i * (w3 + 0.3), TOP + 3.0, w3, 1.05, num, label)
    takeaway(s, "Where to look:", "src/cleaning.py and notebooks/02_cleaning.ipynb. Every step records what it changed, so the before and after numbers come from the code.", y=6.1)

    # ---- 10 decisions -----------------------------------------------------------------------
    s = new("03  /  Cleaning", "We kept every unresolved question, because they are the point", who,
            "The key rule: no row is removed because of its outcome. A question without an accepted answer is a real result, so it gets target zero rather than being dropped. "
            "The only imputation is the asker's account age, using the median from before 2025 so nothing from the test period leaks in, and a flag keeps the imputed rows visible.")
    table(s, LM, TOP, [3.5, 3.9, 4.73], [
        ["What we found", "What we did", "Why"],
        ["171,932 questions with no accepted answer", "Gave them target 0 instead of dropping them", "It is a real outcome. Dropping them would remove every unresolved question."],
        ["6,319 deleted askers (2.1%) with no account date", "Used the median age before 2025 (543 days) and added a flag", "Only training-period data, so nothing leaks from later."],
        ["7,147 questions with two selected tags", "Kept one row and the smaller sampling weight", "The more cautious estimate of how many real questions it stands for."],
        ["303 extremely long bodies", "Capped them at the 99.9th percentile", "Keeps the question without letting it dominate."],
        ["6 mostly non-English posts", "Removed them", "Nothing to model. Decided without looking at the outcome."]],
          row_h=0.78, size=12.5, aligns=["l", "l", "l"])
    takeaway(s, "Also:", "the raw HTML body is not in the shared table (316 MB is over GitHub's file limit). plain_body and code_text are kept.", y=6.35)

    # ---- 11 targets -------------------------------------------------------------------------
    s = new("03  /  Targets", "41% of questions get an accepted answer within a week", who,
            "From 309,179 collected rows, merging duplicates leaves 302,032 and removing six invalid posts leaves 302,026. Our main outcome, an accepted answer within 168 hours, is positive for "
            "41 percent of questions. The secondary outcome, any answer within a week, is 75 percent. Among questions that were answered, 54 percent also got an accepted answer. "
            "We drop questions younger than 30 days so every label has had time to form; none were that recent.")
    s.text(LM, TOP - 0.05, 5.4, 0.3, "Before and after cleaning", size=12, bold=True, color=MUTED)
    table(s, LM, TOP + 0.3, [3.6, 1.7], [["Step", "Rows"], ["Rows collected", "309,179"], ["After merging duplicates", "302,032"],
                                          ["After removing invalid posts", "302,026"], ["Immature labels dropped", "0"]],
          row_h=0.52, size=13, aligns=["l", "r"])
    s.text(LM, TOP + 3.3, 5.3, 0.9, "The newest question is 33 days old, so every label has had at least 30 days to form.", size=12.5, color=MUTED)
    img = ch.class_balance(PARQUET, tmp / "classbalance.png", (6.4, 3.7))
    s.text(6.65, TOP - 0.05, 6.0, 0.3, "The outcomes we predict", size=12, bold=True, color=MUTED)
    s.image(img, 6.65, TOP + 0.3, 6.1, 3.7)
    takeaway(s, "What it means:", "the main outcome is the minority, so we judge models with PR-AUC and the share resolved, not with accuracy.", y=6.2)

    # ---- 12 robustness ----------------------------------------------------------------------
    s = new("03  /  Robustness", "The sample does not bend the trends, but it has limits", who,
            "Sampling is a risk, so we tested it. Yearly volumes estimated from the sample are within about two percent of the complete counts. A second random seed changes the overall resolution "
            "rate by only a quarter of a percentage point. The limits: monthly estimates from the sample are noisy, so every volume chart uses the complete weekly counts, and a few small tags have thin months.")
    w3 = (CW - 0.6) / 3
    for i, (num, label, desc, color) in enumerate([("about 2%", "gap in yearly volume", "Between the sampled estimate and the complete counts.", TEAL),
                                                   ("0.2-0.3 pts", "change with a second seed", "In the overall resolved rate for sql and excel.", TEAL),
                                                   ("137 of 1,168", "thin tag-months", "Fewer than 30 sampled questions each, so they are flagged and greyed out.", AMBER)]):
        stat_panel(s, LM + i * (w3 + 0.3), TOP, w3, 2.2, num, label, desc, color)
    panel(s, LM, TOP + 2.45, CW, 1.75)
    s.text(LM + 0.3, TOP + 2.6, CW - 0.6, 1.5, lines([
        "Monthly volume from the sample is noisy (mean error 7.1%), so volume charts use the complete weekly counts.",
        "Weighted and unweighted yearly rates differ by under 1 percentage point, but weights are still used for every monthly rate.",
        "A target of 0 mixes 'no good answer' with 'the asker never came back to accept'. We treat that as a limit of using acceptance."], 13.5, 7, bullet=True))
    takeaway(s, "What it means:", "trends are safe to read from the weekly counts and weighted monthly rates, and the limits are written down.", y=6.4)

    # ---- 13 EDA trends ----------------------------------------------------------------------
    who = ""
    s = new("04  /  What the data shows", "Since late 2022 fewer questions get resolved, and answers come slower", who,
            "Before November 2022 about 44 percent of questions were resolved within a week. Since then it is about 36 percent. The share that get any answer also dropped, from 77 to 71 percent, "
            "and the median time to an accepted answer grew from under an hour to close to three hours. We say these changes are associated with that period; we cannot show cause.")
    a, b = pp["resolved_rate_7d"], pp["answered_rate_7d"]
    g, h = pp["accepted_given_answered"], pp["median_hours_to_accept"]
    img1 = ch.rates_trend(ROOT / "data/processed/monthly_tag_tables.csv", tmp / "rates.png", (6.1, 3.2))
    img2 = ch.hours_trend(ROOT / "data/processed/monthly_tag_tables.csv", tmp / "hours.png", (5.9, 3.2))
    s.text(LM, TOP - 0.05, 6.0, 0.3, "Share of questions resolved or answered within 7 days", size=12, bold=True, color=MUTED)
    s.image(img1, LM, TOP + 0.25, 6.1, 3.2)
    s.text(6.95, TOP - 0.05, 5.7, 0.3, "Median time to an answer (hours)", size=12, bold=True, color=MUTED)
    s.image(img2, 6.95, TOP + 0.25, 5.8, 3.2)
    tw = (CW - 0.6) / 4
    for i, (num, label, color) in enumerate([(f"{a[0] * 100:.0f}% → {a[1] * 100:.0f}%", "resolved within 7 days", NAVY), (f"{b[0] * 100:.0f}% → {b[1] * 100:.0f}%", "answered at all", SKY),
                                             (f"{g[0] * 100:.0f}% → {g[1] * 100:.0f}%", "accepted, given answered", AMBER), (f"{h[0]:.1f} h → {h[1]:.1f} h", "median time to accepted answer", ORANGE)]):
        mini_stat(s, LM + i * (tw + 0.2), 5.75, tw, 1.05, num, label, color, 24)
    s.text(LM, 5.45, CW, 0.28, "Before → after November 2022 (averages weighted by estimated questions)", size=11.5, bold=True, color=MUTED)

    # ---- 14 EDA characteristics -------------------------------------------------------------
    s = new("04  /  What the data shows", "Code helps a question; error text and brand-new accounts do not", who,
            "These are the question characteristics that move resolution. Questions with code blocks are resolved about 43 percent of the time against 32 percent without. Error text and long "
            "bodies go with lower resolution, and accounts under a week old resolve about 33 percent against 42 percent for established askers. All of these are known when the question is posted, "
            "so they can be used as features.")
    img = ch.characteristics(ROOT / "data/processed/questions_clean_v1.parquet", tmp / "chars.png", (12.0, 3.7))
    s.text(LM, TOP - 0.05, 9, 0.3, "Share of questions resolved within 7 days, by question characteristic", size=12, bold=True, color=MUTED)
    s.image(img, LM, TOP + 0.25, CW, 3.7)
    w3 = (CW - 0.6) / 3
    for i, (title, text) in enumerate([("Code blocks", "43% are resolved with code and 32% without."), ("Shorter is better", "Resolution falls steadily as the body gets longer."),
                                       ("Trust takes time", "Accounts under 7 days: 33%. After a week it levels off near 42%.")]):
        x = LM + i * (w3 + 0.3)
        panel(s, x, 5.85, w3, 1.0)
        s.text(x + 0.25, 5.85, w3 - 0.5, 1.0, [P((title, True, NAVY), size=13, after=2), P(text, size=12.5, after=0)], valign="m")

    # ---- 14b hour by weekday ----------------------------------------------------------------
    s = new("04  /  What the data shows", "Resolution varies by only about nine points across the week", who,
            "This heatmap shows the share of questions resolved within a week for every hour of every weekday, in UTC. The highest cell is late Saturday at 47 percent and the lowest are around 38 percent. "
            "The whole grid spans about nine points, so timing is a weak signal. We keep hour and weekday as features but do not expect them to drive the predictions.")
    s.image(ROOT / "reports/review1/deck_assets/eda_hour_weekday_heatmap.png", LM, TOP, 8.6, 3.98)
    panel(s, 9.45, TOP, 3.28, 3.98)
    s.text(9.7, TOP + 0.2, 2.8, 3.6, [P(("What the grid shows", True, NAVY), size=15, after=7, head=True),
                                     P("The highest cell is late Saturday UTC, at 47.2%.", size=13, after=7),
                                     P("The lowest cells are near 38%, for example Friday 06:00 UTC.", size=13, after=7),
                                     P("The whole grid spans about nine points.", size=13, after=0)])
    takeaway(s, "What it means:", "timing is a weak signal. We keep hour and weekday as features, but we do not expect them to drive the predictions.", y=6.05)

    # ---- 15 EDA insights --------------------------------------------------------------------
    s = new("04  /  What the data shows", "Five findings from the EDA became features", who,
            "The exploration did not stay in the notebook. Each of the top five insights became a feature we used: structure of the question, account maturity, timing, volume shifts "
            "and the tags. Statistical tests agree that every feature is related to the outcome, but the effects are small, so we should not expect a very accurate model.")
    table(s, LM, TOP, [2.7, 4.2, 5.23], [["Finding", "What the EDA showed", "Feature it became"],
                                         ["Question structure", "Code blocks, error text and body length matter", "code_ratio, n_code_blocks, has_error_text, body_length"],
                                         ["Account maturity", "New accounts resolve less often", "new_account, account_age_days"],
                                         ["Timing", "Weekend and time-of-day patterns", "hour, weekday and month posted"],
                                         ["Volume collapse", "Questions fell about 90% after late 2022", "tag volume in the past 4 weeks"],
                                         ["Tags", "Resolution differs by technology", "one column per selected tag"]],
          row_h=0.62, size=13, aligns=["l", "l", "l"])
    takeaway(s, "One exclusion:", "answer_count has the strongest link to the outcome, yet it is only known after the question has been answered, so it is a leak and we do not use it.", y=5.85, size=13.5)

    # ---- 15b correlations -------------------------------------------------------------------
    s = new("04  /  What the data shows", "Most features are only weakly related to the outcome", who,
            "This is the Spearman correlation between the numeric features and the two outcomes. Code blocks, account age and body length are all close to zero. Answer count has the strongest link to the outcome, "
            "but it only exists after the question has been answered, so it is a leak and not a usable feature. Statistical tests agree that every feature is related to the outcome, but the effects are small.")
    s.image(ROOT / "reports/review1/deck_assets/eda_spearman_heatmap.png", LM, TOP - 0.05, 5.6, 4.5)
    panel(s, 6.6, TOP, 6.13, 4.4)
    s.text(6.9, TOP + 0.2, 5.55, 4.0, [P(("Reading the heatmap", True, NAVY), size=16, after=8, head=True)] + lines([
        "Code blocks (0.08), account age (0.04) and body length (-0.05) are all close to zero.",
        "answer_count has the strongest link (0.33), but it is only known after the question is answered, so it is a leak.",
        "The two outcomes are linked (0.48): answered questions are more likely to be accepted.",
        "Tests give p < 0.001 for every feature, but the effects are small (Cramér's V below 0.11)."], 13.5, 8, bullet=True))
    takeaway(s, "What it means:", "no single feature predicts resolution well, so we should expect a modest model.", y=6.35)

    # ---- 16 split ---------------------------------------------------------------------------
    s = new("05  /  Features and baseline", "We test on the future, never on the past", who,
            "A random split would let the model learn from 2024 to predict 2023, which no real system could do. So training is January 2019 to December 2024, validation is the first half of 2025, "
            "and the test period is July 2025 to July 2026. Notice the share of resolved questions falls from 42 to 30 percent across the three periods: the outcome itself drifts, which makes the test hard.")
    img = ch.split_timeline(PARQUET, tmp / "split.png", (12.0, 2.7))
    s.text(LM, TOP - 0.05, CW, 0.3, "Share of questions resolved within 7 days, by month, with the three periods", size=12, bold=True, color=MUTED)
    s.image(img, LM, TOP + 0.25, CW, 2.7)
    w3 = (CW - 0.6) / 3
    for i, (name, dates, rows, color) in enumerate([("Train", "Jan 2019 to Dec 2024", "256,810 questions, 42.3% resolved", NAVY),
                                                    ("Validation", "Jan to Jun 2025", "28,132 questions, 34.1% resolved", SKY),
                                                    ("Test", "Jul 2025 to Jul 2026", "16,695 questions, 29.7% resolved", ORANGE)]):
        x = LM + i * (w3 + 0.3)
        panel(s, x, TOP + 3.1, w3, 1.0)
        s.text(x + 0.25, TOP + 3.1, w3 - 0.5, 1.0, [P((name + ":  ", True, color), dates, size=13.5, after=2), P(rows, size=12.5, color=MUTED, after=0)], valign="m")
    takeaway(s, "Why not a random split?", "it would let the model peek at the future, and behaviour changed in late 2022. Inside the training period we use time-series folds: always train on the past and validate on the next block.", y=6.05)

    # ---- 17 features ------------------------------------------------------------------------
    s = new("05  /  Features and baseline", "The model only sees what exists when a question is posted", who,
            "The feature specification lists every candidate feature with its formula and whether it is available at posting time. On the other side is a forbidden list: score, views, answer count, "
            "closed status and similar fields only exist after the question has been out for a while. The post-AI flag and 'first question' are excluded on purpose too.")
    cw2 = (CW - 0.3) / 2
    panel(s, LM, TOP, cw2, 4.35)
    s.text(LM + 0.3, TOP + 0.2, cw2 - 0.6, 4.0, [P(("Allowed", True, TEAL), size=17, after=7, head=True)] + lines([
        "Question text: title and body length, code blocks, code share, error text, question word", "Tags: how many, and one column per selected tag",
        "Asker: account age, new-account flag, missing-age flag", "Timing: hour, weekday and month posted (UTC)",
        "Volume: tag volume in the 4 weeks before the posting week", "Title wording, reduced with TF-IDF and SVD"], 13.5, 7))
    panel(s, LM + cw2 + 0.3, TOP, cw2, 4.35)
    s.text(LM + cw2 + 0.6, TOP + 0.2, cw2 - 0.6, 4.0, [P(("Never allowed", True, ORANGE), size=17, after=7, head=True)] + lines([
        "score, views, answer count, is_answered", "closed status and comments", "current reputation", "post_ai flag: constant in the test period, kept for analysis only",
        "first_question: unreliable with sampled data", "anything that contains the outcome, such as the time of the accepted answer"], 13.5, 7))
    takeaway(s, "Rule of thumb:", "if it did not exist at the moment of posting, the model may not use it.", y=6.35)

    # ---- 18 checks --------------------------------------------------------------------------
    s = new("05  /  Features and baseline", "The checks found one real problem and no leaks", who,
            "We ran a correlation and variance-inflation check on the features. No leaky variables were found. The check did catch the dummy variable trap: one-hot encoding the leading question word "
            "made the columns perfectly collinear, with a variance inflation factor above ten to the fifteenth. Dropping one category removes it.")
    w3 = (CW - 0.6) / 3
    for i, (num, label, desc, color) in enumerate([("0", "leaky variables", "None of score, views or accepted-answer fields reached the feature set.", TEAL),
                                                   ("VIF > 1e15", "perfect collinearity", "Caused by one-hot encoding the question word. Fixed by dropping one category.", ORANGE),
                                                   ("0.07 / -0.05", "strongest linear links", "Code blocks and error text. Every honest feature is weakly related to the outcome.", NAVY)]):
        stat_panel(s, LM + i * (w3 + 0.3), TOP, w3, 2.45, num, label, desc, color)
    panel(s, LM, TOP + 2.7, CW, 1.6)
    s.text(LM + 0.3, TOP + 2.85, CW - 0.6, 1.4, lines(["The two outcomes correlate at 0.48, as expected: answered questions are more likely to be accepted.",
                                                      "Dummy variable trap: keep one fewer one-hot column per categorical feature (the baseline drops 'none')."], 13.5, 8, bullet=True))
    takeaway(s, "What it means:", "weak correlations mean a very accurate model is not realistic, so we judge by how much we beat guessing.", y=6.2)

    # ---- 19 baseline ------------------------------------------------------------------------
    s = new("05  /  Features and baseline", "The baseline is 64% accurate, yet barely beats guessing", who,
            "The baseline is a plain logistic regression on the structured features. Accuracy 64 percent sounds acceptable, but only 34 percent of validation questions are resolved, so always predicting "
            "'unresolved' is right 66 percent of the time. On a fairer metric, precision-recall AUC, the baseline scores 0.394 against 0.341 for no skill. That is the floor the advanced models have to beat.")
    img = ch.baseline_bars(tmp / "baseline.png", (5.8, 3.7), 0.6396, 1 - float(val.loc["majority class", "positive_rate"]), float(m4row["pr_auc"]), float(val.loc["majority class", "pr_auc"]))
    s.text(LM, TOP - 0.05, 5.8, 0.3, "Baseline vs simple guessing (validation period)", size=12, bold=True, color=MUTED)
    s.image(img, LM, TOP + 0.3, 5.8, 3.7)
    for i, (num, label) in enumerate([("0.640", "accuracy"), ("0.423", "precision"), ("0.160", "recall"), ("0.579", "ROC-AUC")]):
        mini_stat(s, 6.9 + (i % 2) * 3.0, TOP + (i // 2) * 1.3, 2.83, 1.15, num, label, NAVY, 28)
    panel(s, 6.9, TOP + 2.7, 5.83, 1.45)
    s.text(7.15, TOP + 2.7, 5.35, 1.45, [P("Accuracy is below always guessing 'unresolved' (about 0.66).", size=13, after=5),
                                        P("Recall of 0.16 means it misses most resolved questions at the default threshold.", size=13, after=0)], valign="m")
    takeaway(s, "What it means:", "this is the floor. The advanced models have to beat PR-AUC 0.394 and accuracy alone tells us nothing.", y=6.2)

    # ---- 20 models setup --------------------------------------------------------------------
    who = ""
    s = new("06  /  Models and findings", "We finished the feature set and trained three kinds of model", who,
            "My part starts where the baseline stopped. I added the remaining features from the specification: tag volume in the four weeks before the posting week, tag columns, and title wording "
            "reduced with SVD. Preprocessing sits inside the model pipeline, so it is refit on training data only in every fold. Random forest and XGBoost are tuned on date-based folds that leave a "
            "seven-day gap, because a label is only known a week after posting.")
    heads = [("1.  Features", NAVY, ["30 inputs, all known at posting time.", "A guard rejects any outcome field.", f"Title wording adds {gain.loc['structured + title text', 'pr_auc'] - gain.loc['structured only', 'pr_auc']:+.3f} PR-AUC."]),
             ("2.  Models", TEAL, ["Logistic regression, random forest and XGBoost.", "Class weights, and scale_pos_weight for XGBoost.", f"XGBoost trees chosen by early stopping ({R['tuning']['xgb']['trees_after_early_stopping']} trees)."]),
             ("3.  Rules", ORANGE, ["Tuning on date-based folds with a 7-day gap.", "Threshold chosen on validation only.", "Test period scored once."])]
    cw3 = (CW - 2 * 0.3) / 3
    for i, (title, color, items) in enumerate(heads):
        x = LM + i * (cw3 + 0.3)
        s.rect(x, TOP, cw3, 0.6, color)
        s.text(x + 0.25, TOP, cw3 - 0.5, 0.6, title, size=17, bold=True, color="FFFFFF", valign="m")
        panel(s, x, TOP + 0.75, cw3, 2.35)
        s.text(x + 0.25, TOP + 0.95, cw3 - 0.5, 2.1, lines(items, 13.5, 8))
    panel(s, LM, TOP + 3.3, CW, 1.1)
    s.text(LM + 0.3, TOP + 3.3, CW - 0.6, 1.1, P(("Added to the baseline's features: ", True, NAVY), "tag volume from the complete weekly counts (past weeks only), body length, new-account and missing-age flags, "
                                              "one column per tag, and title wording (TF-IDF reduced to 100 components, fitted on training data only).", size=13, after=0), valign="m")
    takeaway(s, "Where it ran:", "on Google Colab with a T4 GPU for XGBoost. All code and tests are in the repository.", y=6.35)

    # ---- 21 comparison ----------------------------------------------------------------------
    s = new("06  /  Models and findings", "XGBoost wins, but only just", who,
            "On the validation period, the three real models are close. Logistic regression gets 0.471 precision-recall AUC, random forest 0.473 and XGBoost 0.482, against 0.341 for no skill and 0.394 "
            "for the baseline. XGBoost is chosen because it has the highest value on the threshold-free metric, and its decision threshold is tuned on validation only. "
            "The summary: gradient boosting is only slightly better than a well-built linear model.")
    order = [("majority class", "Majority class"), ("m4", "Logistic regression (baseline)"), ("logistic regression", "Logistic regression"), ("random forest", "Random forest"), ("xgboost", "XGBoost")]
    rows = [["Model", "Precision", "Recall", "F1", "PR-AUC", "ROC-AUC"]]
    for key, label in order:
        r = m4row if key == "m4" else val.loc[key]
        rows.append([label] + [f"{r[c]:.3f}" for c in ("precision", "recall", "f1", "pr_auc", "roc_auc")])
    s.rect(LM, TOP + 0.45 + 4 * 0.55, 8.4, 0.55, "FDE8DC")        # highlight the chosen model's row
    yb = table(s, LM, TOP, [3.3, 1.15, 1.0, 0.8, 1.0, 1.15], rows, row_h=0.55, size=13)
    s.text(LM, yb + 0.2, 8.4, 0.9, [P(f"The share resolved in validation is {val.loc['majority class', 'positive_rate'] * 100:.0f}%, so a no-skill ranking has PR-AUC {val.loc['majority class', 'pr_auc']:.3f}.", size=13, after=5),
                                    P(f"We chose XGBoost with threshold {R['chosen']['threshold']:.2f}, tuned for F1 on validation only.", size=13, after=0)])
    img = ch.val_models_bars(tmp / "valbars.png", (4.0, 3.9), [("No skill", float(val.loc["majority class", "pr_auc"])), ("Baseline", float(m4row["pr_auc"])), ("Logistic", float(val.loc["logistic regression", "pr_auc"])),
                                                                ("Random\nforest", float(val.loc["random forest", "pr_auc"])), ("XGBoost", float(val.loc["xgboost", "pr_auc"]))], None)
    s.text(9.15, TOP - 0.05, 3.6, 0.3, "Validation PR-AUC", size=12, bold=True, color=MUTED)
    s.image(img, 9.05, TOP + 0.25, 3.7, 3.9)
    takeaway(s, "What it means:", "the three real models differ by about 0.01. The gain over the baseline comes mostly from better features, not from a fancier model.", y=6.3)

    # ---- 22 test ----------------------------------------------------------------------------
    s = new("06  /  Models and findings", "On the test period the model beats guessing, but not by much", who,
            "The test period, July 2025 to July 2026, was scored exactly once, after the model and threshold were fixed on earlier data. A lock file stops a second run. The model reaches 0.43 precision-recall AUC "
            "where a no-skill ranking gets 0.30, and 0.655 ROC-AUC. If a manager flags the 20 percent of questions with the lowest predicted resolution, 24 percent of the unresolved ones are in that group, against 20 percent by chance.")
    w3 = 2.65
    stat_panel(s, LM, TOP, w3, 1.85, f"{test['pr_auc']:.3f}", "PR-AUC", f"A no-skill ranking scores {test['positive_rate']:.3f}.", NAVY, 28)
    stat_panel(s, LM + w3 + 0.2, TOP, w3, 1.85, f"{test['roc_auc']:.3f}", "ROC-AUC", "No skill is 0.500.", SKY, 28)
    stat_panel(s, LM + 2 * (w3 + 0.2), TOP, w3, 1.85, f"{test['capture_rate_20'] * 100:.1f}%", "of unresolved caught", "By flagging the lowest 20%. Chance: 20%.", ORANGE, 28)
    table(s, LM, TOP + 2.05, [2.4, 1.3, 4.2], [["Metric", "Value", "Meaning"], ["Precision", f"{test['precision']:.3f}", "of questions predicted resolved, the share that were"],
                                              ["Recall", f"{test['recall']:.3f}", "of resolved questions, the share we found"], ["F1", f"{test['f1']:.3f}", "balance of the two at the chosen threshold"],
                                              ["Questions scored", f"{int(test['n']):,}", f"{test['positive_rate'] * 100:.1f}% of them resolved"]], row_h=0.45, size=12.5, aligns=["l", "c", "l"])
    s.text(9.05, TOP - 0.05, 3.7, 0.3, "Test confusion matrix", size=12, bold=True, color=MUTED)
    s.image(M5 / "test_confusion.png", 8.95, TOP + 0.3, 3.8, 3.5)
    takeaway(s, "What it means:", "the model finds most resolved questions (recall 0.77) but flags many unresolved ones too (precision 0.36). It helps prioritise; it cannot decide.", y=6.3)

    # ---- 22b curves -------------------------------------------------------------------------
    s = new("06  /  Models and findings", "On the curves, the three real models are hard to tell apart", who,
            "These are the precision-recall and ROC curves for all four models on the validation period. The curves for the three real models lie close together and above the no-skill line, "
            "which is why the differences in the table are small. The no-skill line sits at the share of resolved questions for precision-recall and on the diagonal for ROC.")
    s.text(LM, TOP - 0.05, 9, 0.3, "Validation period, all models", size=12, bold=True, color=MUTED)
    s.image(M5 / "val_pr_roc.png", LM, TOP + 0.25, 9.1, 3.65)
    panel(s, 9.95, TOP, 2.78, 4.0)
    s.text(10.2, TOP + 0.2, 2.3, 3.6, [P(("How to read them", True, NAVY), size=14, after=7, head=True),
                                      P("Precision-recall: how many flagged questions are really resolved, as we flag more.", size=12.5, after=7),
                                      P("ROC: how well questions are ranked, at any threshold. The diagonal is chance.", size=12.5, after=0)])
    takeaway(s, "What it means:", "the three real models are hard to tell apart, and all of them sit well below a perfect curve.", y=6.1)

    # ---- 23 SHAP ----------------------------------------------------------------------------
    s = new("06  /  Models and findings", "Account age, code and the tag's recent volume drive the predictions", who,
            "SHAP shows how much each feature pushes a question towards resolved or unresolved. Brand-new accounts and questions with no code are the least often resolved. Error text, longer titles and longer "
            "bodies go with fewer accepted answers in the test period. Tag volume stays in one narrow, low range in the test period, so it stands in for the period and tag mix and not for the question itself. "
            "The logistic regression coefficients agree on error text and new accounts.")
    s.image(M5 / "shap_summary.png", LM, TOP - 0.05, 3.9, 4.5)
    notes = [t.strip() for t in (M5 / "shap_notes.txt").read_text().splitlines() if t.strip()]
    panel(s, 4.9, TOP, 7.83, 4.45)
    s.text(5.2, TOP + 0.2, 7.25, 4.1, [P(("How to read the SHAP plot", True, NAVY), size=16, after=7, head=True)] + lines(notes, 13, 7, bullet=True))
    takeaway(s, "Cross-check:", "the plain logistic regression gives the same signs for error text and new accounts, and for the pandas, r and sql tags (more resolved) against python and android (fewer).", y=6.4, size=13)

    # ---- 24 rolling-origin ------------------------------------------------------------------
    s = new("06  /  Models and findings", "Ranking quality held up after November 2022; the resolution rate fell", who,
            "The single test period is entirely after November 2022, so it cannot show what changed. Rolling-origin evaluation can: for each half-year we train on everything before it and test on that half-year. "
            "Precision-recall AUC falls from 0.56 to 0.47, but so does the share of resolved questions, from 42 to 33 percent, and PR-AUC depends on that share. ROC-AUC stays flat at 0.64 to 0.65 and PR-AUC minus "
            "the no-skill level is the same before and after. So the model's skill did not change; what changed is how often questions are resolved.")
    img = ch.rolling_chart(M5 / "rolling_origin.csv", tmp / "roll.png", (12.0, 3.4))
    s.text(LM, TOP - 0.05, CW, 0.3, "Train on everything before each half-year, test on that half-year (2021 H1 to 2026 H1)", size=12, bold=True, color=MUTED)
    s.image(img, LM, TOP + 0.25, CW, 3.4)
    tw = (CW - 0.6) / 4
    s.text(LM, 5.45, CW, 0.28, "Before → after November 2022 (mean over the half-year windows)", size=11.5, bold=True, color=MUTED)
    for i, (num, label, color) in enumerate([(f"{roll['roc_auc_pre']:.2f} → {roll['roc_auc_post']:.2f}", "mean ROC-AUC", TEAL), (f"{roll['pr_auc_pre']:.2f} → {roll['pr_auc_post']:.2f}", "mean PR-AUC", NAVY),
                                             (f"{roll['positive_rate_pre'] * 100:.0f}% → {roll['positive_rate_post'] * 100:.0f}%", "share resolved", ORANGE),
                                             (f"{roll['pr_auc_lift_pre']:.2f} → {roll['pr_auc_lift_post']:.2f}", "PR-AUC minus no skill", PURPLE)]):
        mini_stat(s, LM + i * (tw + 0.2), 5.78, tw, 1.05, num, label, color, 24)

    # ---- 25 secondary target ----------------------------------------------------------------
    s = new("06  /  Models and findings", "The same model ranks 'any answer in 7 days' about as well", who,
            "Acceptance depends on the asker coming back, so we repeated the analysis for the easier outcome: any answer within seven days. The model ranks that outcome about as well, with ROC-AUC 0.667 against 0.655. "
            "We compare ROC-AUC because the two outcomes have very different base rates, 71 percent against 30 percent. The top features differ in a sensible way: body length matters more for getting any answer, "
            "account age and code for getting an accepted one.")
    s_main, s_sec = sec.iloc[0], sec.iloc[1]
    table(s, LM, TOP, [4.6, 2.3, 2.3], [["Test period", "Accepted answer", "Any answer"],
                                       ["Share of questions positive", f"{s_main['positive_rate'] * 100:.1f}%", f"{s_sec['positive_rate'] * 100:.1f}%"],
                                       ["PR-AUC", f"{s_main['pr_auc']:.3f}", f"{s_sec['pr_auc']:.3f}"], ["ROC-AUC", f"{s_main['roc_auc']:.3f}", f"{s_sec['roc_auc']:.3f}"],
                                       ["Capture rate (lowest 20% flagged)", f"{s_main['capture_rate_20'] * 100:.1f}%", f"{s_sec['capture_rate_20'] * 100:.1f}%"]], row_h=0.62, size=13.5, head_h=0.55)
    panel(s, 10.0, TOP, 2.73, 3.65)
    s.text(10.25, TOP + 0.2, 2.25, 3.3, [P(("Top features", True, NAVY), size=14, after=7), P(("Accepted answer", True), size=12.5, after=2),
                                        P("tag volume, account age, code share, code blocks", size=12.5, color=MUTED, after=9), P(("Any answer", True), size=12.5, after=2),
                                        P("body length, tag volume, title wording, code blocks", size=12.5, color=MUTED, after=0)])
    takeaway(s, "What it means:", "PR-AUC is not comparable across the two outcomes because their base rates differ, so ROC-AUC is the fair comparison. For 'any answer', the best F1 threshold flags almost everything, so we do not use F1 there.", y=5.7, size=13)

    # ---- 26 error analysis ------------------------------------------------------------------
    s = new("06  /  Models and findings", "The model's confident mistakes are mostly about the asker", who,
            "To understand the mistakes, I took the 30 most confident errors, 15 false positives and 15 false negatives, and read each question. Most false positives were answered, often within minutes, but the asker "
            "never accepted an answer, which nothing known at posting time can predict. Most false negatives came from accounts created the same day that returned and got an accepted answer within hours. "
            "One miss came from a feature limit: the error-text pattern is case sensitive.")
    items = [("Answered but not accepted", 10, "fp"), ("No answer received", 4, "fp"), ("Accepted just after day 7", 1, "fp"), ("New asker account", 8, "fn"), ("No code block", 2, "fn"),
             ("Android tag + error text", 2, "fn"), ("Long body + error text", 1, "fn"), ("Error text not detected", 1, "fn"), ("High-visibility question", 1, "fn")]
    img = ch.reason_bars(items, tmp / "reasons.png", (6.4, 3.8))
    s.text(LM, TOP - 0.05, 6.4, 0.3, "Main reason for each of the 30 confident errors", size=12, bold=True, color=MUTED)
    s.image(img, LM, TOP + 0.25, 6.4, 3.8)
    s.oval(LM + 0.2, TOP + 4.2, 0.16, 0.16, ORANGE)
    s.text(LM + 0.45, TOP + 4.12, 2.3, 0.3, "false positives", size=11.5, color=MUTED)
    s.oval(LM + 2.6, TOP + 4.2, 0.16, 0.16, NAVY)
    s.text(LM + 2.85, TOP + 4.12, 2.3, 0.3, "false negatives", size=11.5, color=MUTED)
    panel(s, 7.3, TOP, 5.43, 4.45)
    s.text(7.6, TOP + 0.2, 4.85, 4.1, [P(("What it tells us", True, NAVY), size=16, after=8, head=True)] + lines([
        "Acceptance depends on the asker, which the model cannot see at posting time.", "New askers who do come back are resolved fast: 7 of 8 within 4 hours.",
        "The error-text pattern is case sensitive, so one miss was a feature gap.", "A question's visibility (41,576 views for one) is not known at posting time."], 13.5, 8, bullet=True))
    takeaway(s, "How we did it:", "each question was read at its link. Only titles are shared, and each links to the original (CC BY-SA 4.0).", y=6.4)

    # ---- 27 business ------------------------------------------------------------------------
    s = new("06  /  Models and findings", "How a forum manager could use the model", who,
            "The model is useful for prioritising, not deciding. Flagging the lowest-scored fifth of questions catches 24 percent of the unresolved ones against 20 percent by chance. Askers who add code and who have established "
            "accounts are resolved more often. The resolution rate itself has fallen, so it should be tracked. Limits: acceptance is only a proxy for resolved, recent data is smaller than the sampled early years, and we say "
            "'associated with', never 'caused by'.")
    cards = [("Prioritise", NAVY, f"Flag the 20% of questions with the lowest predicted resolution. It catches {test['capture_rate_20'] * 100:.0f}% of the unresolved ones, against 20% by chance."),
             ("Ask for code", TEAL, "More code goes with more accepted answers. Do not assume error text helps: it goes with fewer."),
             ("Watch the rate", ORANGE, f"Resolution fell from about {roll['positive_rate_pre'] * 100:.0f}% to {roll['positive_rate_post'] * 100:.0f}% while ranking quality stayed flat. Track the rate itself."),
             ("Keep it fresh", AMBER, "Behaviour shifts over time. Refresh the model regularly and keep scoring on the newest months.")]
    cw4 = (CW - 3 * 0.25) / 4
    for i, (title, color, text) in enumerate(cards):
        x = LM + i * (cw4 + 0.25)
        panel(s, x, TOP, cw4, 2.55)
        s.text(x + 0.25, TOP + 0.2, cw4 - 0.5, 0.4, title, size=17, bold=True, head=True, color=color)
        s.text(x + 0.25, TOP + 0.75, cw4 - 0.5, 1.75, text, size=14)
    panel(s, LM, TOP + 2.8, CW, 1.7)
    s.text(LM + 0.3, TOP + 2.95, CW - 0.6, 1.5, [P(("Limits", True, ORANGE), size=14, after=4)] + lines([
        "An accepted answer within 7 days is a strict proxy for resolved: it depends on the asker coming back.",
        "The gain over a no-skill ranking is modest, and the three real models differ only slightly.",
        "Recent data (2025 onwards) is smaller than the sampled early years, only 13 tags are covered, and we say 'associated with', never 'caused by'."], 13, 5, bullet=True))

    # ---- 28 how we worked -------------------------------------------------------------------
    s = new("07  /  How we worked", "We worked from one shared board and one repository", "",
            "Everything was planned on one GitHub Projects board and built in one repository. Each piece of work had an owner and a stage, changes were reviewed by a partner before they were merged, "
            "and the notebooks and scripts rebuild every result.")
    heads = [("1.  Plan", NAVY, ["Every task had an owner, a stage and a place for evidence.", "Stages ran from Backlog and To Do through In Progress and Review/Testing to Completed.", "Delays were raised early so work could be reassigned."]),
             ("2.  Build", TEAL, ["One branch for each piece of work.", "Commit messages start with the number of the task they belong to.", "A partner reviews each change before it is merged."]),
             ("3.  Reproduce", ORANGE, ["Notebooks and scripts rebuild every table and chart.", "The cleaned dataset is too large for GitHub and is shared on the team drive.", "Tests cover the collection, cleaning, feature and evaluation code."])]
    cw3 = (CW - 2 * 0.3) / 3
    for i, (title, color, items) in enumerate(heads):
        x = LM + i * (cw3 + 0.3)
        s.rect(x, TOP, cw3, 0.6, color)
        s.text(x + 0.25, TOP, cw3 - 0.5, 0.6, title, size=17, bold=True, color="FFFFFF", valign="m")
        panel(s, x, TOP + 0.75, cw3, 2.75)
        s.text(x + 0.25, TOP + 0.95, cw3 - 0.5, 2.5, lines(items, 14, 10))
    takeaway(s, "What it means:", "anyone can trace a result back to the code that made it and to the person who reviewed it.", y=5.85)

    # ---- 29 contributions -------------------------------------------------------------------
    s = new("07  /  How we worked", "What each of us did", "",
            "Each of us led one stage of the pipeline and reviewed a partner's work, so everyone has seen the code they depend on. The individual contribution summaries link every claim to its evidence.")
    who_did = [
        ("Adhikkesh S K", TEAM[0][1], "Built and tested the prediction models. Completed the feature set with tag volume and title wording, trained logistic regression, random forest and XGBoost, tuned them on time-based folds, scored the test period once, and explained the results with SHAP, a before-and-after check around November 2022, a second outcome and an error analysis."),
        ("Abhinav Gopalakrishnan", TEAM[1][1], "Built the data foundation. Wrote the API collection client, designed the sampling, collected the questions and the complete weekly counts, checked them against Stack Exchange Data Explorer, and wrote the dataset documentation and the combined notebook."),
        ("Rishiikesh", TEAM[2][1], "Enriched and cleaned the data. Fetched answer and asker details, merged and cleaned everything into one table, built both 7-day outcomes, and tested how far the sampling could bend the results."),
        ("Akshay Krishna", TEAM[3][1], "Framed the problem and explored the data. Wrote the problem statement and research question, built the event timeline, made the charts and statistical checks on resolution, and turned the findings into suggestions for the features."),
        ("Nishanth Konchada", TEAM[4][1], "Prepared the ground for modelling. Built the time-based split and validation folds, the feature pipeline, the leakage and multicollinearity checks, and the logistic regression baseline.")]
    rowh = 0.92
    for i, (nm, reg, text) in enumerate(who_did):
        yy = TOP + i * rowh
        s.text(LM, yy, 3.0, rowh - 0.08, [P((nm, True), size=14, after=2), P(reg, size=11.5, color=MUTED, after=0)], valign="m")
        s.text(LM + 3.2, yy, CW - 3.2, rowh - 0.08, text, size=12.5, valign="m")
        s.line(LM, yy + rowh - 0.04, LM + CW, yy + rowh - 0.04, RULE, 0.75)
    takeaway(s, "Together:", "each of us led one stage and reviewed a partner's work, so everyone has seen the code they depend on.", y=6.45)

    # ---- 30 next steps ----------------------------------------------------------------------
    s = new("08  /  What comes next", "Review 2: topics, technology forecasts and a stronger model", "Team 7",
            "For Review 2 we move from whether a question gets resolved to what people still ask and which technologies keep declining. On the modelling side, the error analysis tells us what to improve: asker history, "
            "a better error-text feature, and calibration of the scores.")
    cw3 = (CW - 2 * 0.3) / 3
    for i, (title, color, items) in enumerate([
            ("Topics and complexity", NAVY, ["Topic modelling on titles: which topics do developers still bring to a human community?", "Did question complexity change around AI adoption?"]),
            ("Technology forecasts", TEAL, ["Forecast weekly volume per tag from the complete counts.", "Which tags keep declining and which stay stable? How should support change?"]),
            ("A stronger model", ORANGE, ["Asker-history features, if we can get them without leakage.", "A case-insensitive error-text feature, and calibrated scores.", "One shared feature pipeline, and a saved final model."])]):
        x = LM + i * (cw3 + 0.3)
        s.rect(x, TOP, cw3, 0.6, color)
        s.text(x + 0.25, TOP, cw3 - 0.5, 0.6, title, size=17, bold=True, color="FFFFFF", valign="m")
        panel(s, x, TOP + 0.75, cw3, 3.4)
        s.text(x + 0.25, TOP + 0.95, cw3 - 0.5, 3.1, lines(items, 14, 10))
    takeaway(s, "In short:", "Review 1 answered 'can we predict resolution'. Review 2 asks 'what do people still ask, and where is it going'.", y=6.2)

    # ---- 31 submissions ---------------------------------------------------------------------
    s = new("08  /  Submissions", "Everything is in one repository and can be re-run", "Team 7",
            "All deliverables are in the repository: the notebooks, the data documentation, the board and the code with its tests. The cleaned dataset is too large for GitHub and is shared on the team drive; "
            "the notebooks and scripts say exactly how to rebuild every result.")
    rows = [("Notebooks", "01_collection, 02_cleaning, 03_eda, 04_features, 05_models, 06_evaluation, and the combined review1_main", "notebooks/"),
            ("Data documentation", "dataset_documentation, data_dictionary, sampling_limitations, problem_statement", "docs/"),
            ("Project board", "owners, stages, evidence and history for every task", "GitHub Projects"),
            ("Reports", "contribution summaries, viva questions, model results and figures", "reports/review1/")]
    for i, (title, detail, where) in enumerate(rows):
        yy = TOP + i * 1.05
        s.text(LM, yy, 0.9, 0.6, f"{i + 1:02d}", size=30, bold=True, head=True, color=NAVY)
        s.text(LM + 0.95, yy + 0.02, 3.2, 0.35, title, size=17, bold=True)
        s.text(LM + 0.95, yy + 0.4, 8.3, 0.5, detail, size=13.5, color=MUTED)
        s.text(LM + 10.3, yy + 0.08, 1.83, 0.4, where, size=13, bold=True, color=NAVY, align="r")
    takeaway(s, "Repository:", REPO_URL, y=6.3)

    # ---- 32 thank you -----------------------------------------------------------------------
    n[0] += 1
    s = d.slide("Thank you. We are happy to take questions on any part of the pipeline.")
    s.text(0.6, 1.6, 7.5, 1.0, "Thank you  ·  Questions?", size=40, bold=True, head=True)
    s.text(0.6, 2.8, 7.0, 1.0, "Which Stack Overflow questions still get an answer in the age of AI?", size=16, color=MUTED)
    s.text(0.6, 3.6, 7.0, 0.8, [P(("Repository  ", True, NAVY), REPO_URL, size=12.5, after=5), P(("Board  ", True, NAVY), BOARD_URL, size=12.5, after=0)])
    s.text(0.6, 4.7, 6.2, 1.9, [P((n_, True), ("     " + r_, False, MUTED), size=13, after=3) for n_, r_ in TEAM])
    img = ch.weekly_volume(ROOT / "data/processed/weekly_counts.csv", tmp / "weekly_end.png", (5.4, 3.8), events=False)
    s.image(img, 7.6, 1.5, 5.4, 3.8)
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "BA Final Project - Review 1 - Full.pptx"))
    ap.add_argument("--preview", action="store_true")
    a = ap.parse_args()
    tmp = Path(tempfile.mkdtemp(prefix="deck_"))
    try:
        deck = build(tmp)
        for item in check_overflow(deck):
            print("OVERFLOW  slide %d  %r  needs %.2f in, has %.2f in" % item)
        for item in check_bounds(deck):
            print("OUT OF BOUNDS", item)
        if a.preview:
            files = render_previews(deck, ROOT / "reports/review1/deck_preview")
            contact_sheet(files, ROOT / "reports/review1/deck_preview/contact_sheet.png")
        save_pptx(deck, a.out)
        print(f"wrote {a.out}  ({len(deck.slides)} slides)")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()

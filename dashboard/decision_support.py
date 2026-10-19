"""Deterministic pilot suggestions from saved evidence, with explicit scope.

These rules do not predict intervention benefits or infer causality. They keep
within-tag topic evidence separate from global topic shares.
"""

import math


def _finite(value):
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def format_count(value):
    """Keep small fractional forecast medians visible instead of rounding to zero."""
    if not _finite(value):
        return "unavailable"
    value = float(value)
    return f"{value:,.2f}" if 0 < abs(value) < 10 else f"{value:,.1f}"


def tag_pilots(row):
    """Return tag-specific actions, evidence, owners and prospective KPIs."""
    tag = str(row["tag"])
    change = row.get("change_26w_pct")
    rising = str(row.get("rising_topics", ""))
    if rising.lower() in {"nan", "none", ""}:
        rising = "No rising topic is available in the saved comparison."
    scope = str(row.get("topic_evidence_scope", "weighted within-tag comparison"))
    if not _finite(change):
        forecast = "The last observed weekly count is zero, so percentage change is undefined."
        action = f"Monitor absolute {tag} question counts and inspect source posts before changing support capacity."
        kpi = "Weekly question counts, active questions and first-answer delay. Review against a fixed rolling baseline."
    elif float(change) < -40:
        forecast = f"The validation-selected model projects {float(change):+.1f}% at week 26 versus the last observed week."
        action = f"Trial a shared expert rota for {tag}, while preserving coverage for unanswered questions. Measure workload before reallocating staff."
        kpi = "Expert minutes per answered question, unanswered backlog and first-answer delay versus a contemporaneous control rota."
    elif float(change) < -10:
        forecast = f"The validation-selected model projects {float(change):+.1f}% at week 26 versus the last observed week."
        action = f"Pilot focused expert sessions for {tag}; compare queue outcomes before expanding the schedule."
        kpi = "First-answer delay and seven-day resolution proxy versus a contemporaneous control queue."
    else:
        forecast = f"The validation-selected model projects {float(change):+.1f}% at week 26 versus the last observed week."
        action = f"Retain {tag} coverage and trial an overflow queue before increasing capacity."
        kpi = "Queue size and first-answer delay versus the existing support schedule."
    pilots = [{
        "title": f"{tag}: support scheduling pilot",
        "stakeholder": "developer-forum managers",
        "evidence": f"{forecast} Rising topic candidates: {rising}",
        "action": action,
        "kpi": kpi,
        "scope": scope,
        "caveat": "Forecasts describe question volume, not staff workload. Intervals under-cover in backtests. Topic names are automatic and need inspection.",
    }, {
        "title": f"{tag}: documentation pilot",
        "stakeholder": "DevRel teams",
        "evidence": f"{forecast} Rising topic candidates: {rising}",
        "action": f"Inspect linked {tag} posts in the rising topics, then trial one guide with reproducible, version-specific examples.",
        "kpi": "Guide use and repeat-question share under controlled exposure. Measure resolution proxy as a secondary outcome.",
        "scope": scope,
        "caveat": "Relative topic-share growth does not prove greater absolute demand or a documentation gap. This pilot has no measured benefit yet.",
    }]
    pre, post = row.get("resolved_rate_pre"), row.get("resolved_rate_post")
    if _finite(pre) and _finite(post):
        delta = (float(post) - float(pre)) * 100
        evidence = f"Weighted seven-day resolution proxy: {float(pre)*100:.1f}% before versus {float(post)*100:.1f}% after ({delta:+.1f} pp)."
        pilots.append({
            "title": f"{tag}: question-template pilot",
            "stakeholder": "Q&A platform product team",
            "evidence": f"{evidence} {forecast}",
            "action": f"Test optional {tag} prompts for a minimal example, expected behaviour and version details using random assignment.",
            "kpi": "Question completion and seven-day resolution proxy versus the current form, with first-answer delay as a secondary KPI.",
            "scope": f"Weighted {tag} question sample, fixed pre/post periods; weekly forecasts use separate API counts.",
            "caveat": "This proxy uses the creation time of the answer that is accepted in the collected record. Acceptance-event time is unavailable. Tone scores must not gate users.",
        })
    return pilots

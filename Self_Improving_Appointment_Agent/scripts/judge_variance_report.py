"""Tabulate the `clarity` verdicts from results/judge_variance/ (re-judged copies of saved transcripts) next to the
original judgment, and flag cited turns that come BEFORE the patient stated the preference being cited.
Reads files only; no model calls.   python scripts/judge_variance_report.py > results/judge_variance/report.md
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VAR = ROOT / "results" / "judge_variance"
TERMS = ["afternoon", "morning", "next week", "evening", "friday", "monday"]
SRC = {"v1_reschedule_happy": "baseline_v1", "v2_reschedule_happy": "candidate_v2",
       "v1_reschedule_race": "baseline_v1_heldout", "v2_reschedule_race": "candidate_v2_heldout",
       "v1_book_happy": "baseline_v1", "v2_book_happy": "candidate_v2"}


def first_patient_turn(turns, term):
    for t in turns:
        if term in t["patient"].lower():
            return t["turn"]
    return None


def clarity(rec):
    j = rec.get("judge")
    return (j["items"]["clarity"] if j else None)


def flag(rec, item):
    """Return a note if the cited turn precedes the patient's statement of a term the reason mentions."""
    if not item:
        return ""
    cited = [int(x) for x in re.findall(r"T(\d+)", item["reason"])]
    if not cited:
        return ""
    notes = []
    for term in TERMS:
        if term in item["reason"].lower():
            when = first_patient_turn(rec["turns"], term)
            if when is not None and when > min(cited):
                notes.append(f"cites T{min(cited)} but patient first says '{term}' at T{when}")
    return "; ".join(notes)


def main():
    out = ["# Judge variance: `clarity` item on re-judged saved transcripts", "",
           "orig = verdict stored with the original run. r1..r3 = three re-judgments of the same transcript (same "
           "Qwen judge, rubric v2). `-` = not yet judged (quota). FLAG = the reason cites a turn before the patient "
           "stated the preference it cites.", ""]
    flagged, pass_reasons = [], []
    for label, src in SRC.items():
        out += [f"## {label}", "", "| transcript | orig | r1 | r2 | r3 | cited turn(s) / flags |", "|---|---|---|---|---|---|"]
        for f in sorted((ROOT / "results" / src / "runs").glob(f"{label.split('_', 1)[1]}__s*.json")):
            orig = json.loads(f.read_text(encoding="utf-8"))
            cells, notes = [clarity_cell(clarity(orig))], []
            n0 = flag(orig, clarity(orig))
            if n0:
                notes.append(f"orig: {n0}"); flagged.append((label, orig["sample"], "orig", n0))
            for k in (1, 2, 3):
                p = VAR / f"rep{k}" / label / "runs" / f"{orig['scenario']}__s{1000 * k + orig['sample']}.json"
                if not p.exists():
                    cells.append("-"); continue
                rec = json.loads(p.read_text(encoding="utf-8"))
                item = clarity(rec)
                if item is None:
                    cells.append("-"); continue
                cells.append(clarity_cell(item))
                cited = re.findall(r"T\d+", item["reason"])
                if item["verdict"] == "fail":
                    notes.append(f"r{k}: {','.join(cited) or 'no turn'}")
                n = flag(rec, item)
                if n:
                    notes.append(f"**FLAG r{k}**: {n}"); flagged.append((label, orig["sample"], f"r{k}", n))
                if item["verdict"] != "fail":
                    pass_reasons.append((label, orig["sample"], f"r{k}", item))
            out.append(f"| {label} s{orig['sample']} | " + " | ".join(cells) + f" | {'; '.join(notes) or '-'} |")
        out.append("")
    out += ["## Flags (cited turn before the preference was stated)", ""]
    out += [f"- {l} s{s} {w}: {n}" for l, s, w, n in flagged] or ["- none"]
    out += ["", "## clarity = pass/na whose reason reads like a failure (manual review; keyword screen)", ""]
    bad = re.compile(r"\b(despite|ignor|confus|delay|only|instead|failed to|did not|didn't|not offer)", re.I)
    hits = [(l, s, w, i) for l, s, w, i in pass_reasons if bad.search(i["reason"])]
    out += [f"- {l} s{s} {w}: clarity={i['verdict']}: \"{i['reason']}\"" for l, s, w, i in hits] or ["- none"]
    for label, src in SRC.items():       # same screen on the original judgments
        for f in sorted((ROOT / "results" / src / "runs").glob(f"{label.split('_', 1)[1]}__s*.json")):
            o = json.loads(f.read_text(encoding="utf-8")); i = clarity(o)
            if i and i["verdict"] != "fail" and bad.search(i["reason"]):
                out.append(f"- {label} s{o['sample']} orig: clarity={i['verdict']}: \"{i['reason']}\"")
    print("\n".join(out))


def clarity_cell(item):
    return "-" if not item else item["verdict"]


if __name__ == "__main__":
    main()

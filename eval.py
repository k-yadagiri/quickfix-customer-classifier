"""Evaluate the running API on quickfix_messages.csv.

Usage (API must be running):
    python eval.py                                  # local API on http://localhost:8000
    python eval.py --url https://your-app.example   # deployed API
    python eval.py --out EVAL_before.md             # keep a separate report per prompt version

It sends every message to POST /classify, compares with the correct labels, prints a
summary and writes:
    - a Markdown report (default EVAL_run.md) to copy into EVAL.md
    - a CSV with every row (default eval_results.csv)
"""
import argparse
import csv
import datetime
import platform
import sys

import httpx

LANGUAGES = ("english", "tenglish", "telugu")
FIELDS = ("intent", "category", "urgency")


def load_rows(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def pct(correct, total):
    return f"{correct}/{total} ({100 * correct / total:.1f}%)" if total else "n/a"


def md_cell(text):
    return str(text).replace("|", "\\|").replace("\n", " ")


def main():
    # Windows consoles often cannot print Telugu unless forced to UTF-8.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--csv", default="data/quickfix_messages.csv")
    parser.add_argument("--out", default="EVAL_run.md", help="Markdown report file")
    parser.add_argument("--results", default="eval_results.csv", help="per-message CSV file")
    parser.add_argument("--timeout", type=float, default=300, help="seconds per request")
    args = parser.parse_args()
    base = args.url.rstrip("/")

    rows = load_rows(args.csv)
    client = httpx.Client(timeout=args.timeout)

    try:
        model = client.get(f"{base}/health").json().get("model", "unknown")
    except Exception as exc:
        sys.exit(f"Cannot reach the API at {base}: {exc}\nStart it first: uvicorn app.main:app")

    print(f"Evaluating {len(rows)} messages on model '{model}' via {base}\n")

    results = []
    for row in rows:
        entry = {**row, "got": None, "error": None, "response_ms": None, "invalid_attempts": 0, "needs_review": False}
        try:
            resp = client.post(f"{base}/classify", json={"message": row["message"]})
            if resp.status_code == 200:
                data = resp.json()
                entry.update(
                    got={k: data[k] for k in FIELDS},
                    response_ms=data["response_ms"],
                    invalid_attempts=data.get("invalid_attempts", 0),
                    needs_review=data["needs_review"],
                    summary=data["summary"],
                )
            else:
                entry["error"] = f"HTTP {resp.status_code}: {resp.text[:120]}"
        except Exception as exc:  # network problem etc. - keep going
            entry["error"] = str(exc)[:120]
        results.append(entry)

        if entry["got"]:
            ok = all(entry["got"][k] == row[k] for k in FIELDS)
            print(f"[{row['id']:>2}] {'OK   ' if ok else 'WRONG'} {entry['response_ms']:>6} ms  {row['message'][:60]}")
        else:
            print(f"[{row['id']:>2}] ERROR {entry['error']}")

    # ------------------------------------------------------------ metrics
    def accuracy(subset, field):
        correct = sum(1 for r in subset if r["got"] and r["got"][field] == r[field])
        return pct(correct, len(subset))

    def all_three(subset):
        correct = sum(1 for r in subset if r["got"] and all(r["got"][k] == r[k] for k in FIELDS))
        return pct(correct, len(subset))

    groups = [("Overall", results)] + [(lang.capitalize(), [r for r in results if r["language"] == lang]) for lang in LANGUAGES]

    times = [r["response_ms"] for r in results if r["response_ms"] is not None]
    slowest = max((r for r in results if r["response_ms"] is not None), key=lambda r: r["response_ms"], default=None)
    invalid_msgs = sum(1 for r in results if r["invalid_attempts"] > 0)
    invalid_total = sum(r["invalid_attempts"] for r in results)
    review = sum(1 for r in results if r["needs_review"])
    errors = [r for r in results if r["error"]]
    wrong = [r for r in results if r["got"] and any(r["got"][k] != r[k] for k in FIELDS)]

    # ------------------------------------------------------------ report
    lines = [
        "# Evaluation run",
        "",
        f"- Date: {datetime.datetime.now():%Y-%m-%d %H:%M}",
        f"- Model: `{model}`",
        f"- API: {base}",
        f"- Messages: {len(results)}",
        f"- Machine (auto): {platform.system()} {platform.release()}, {platform.processor() or platform.machine()}",
        "- Laptop RAM / GPU: **<fill in by hand>**",
        "",
        "## Accuracy",
        "",
        "| Group | Intent | Category | Urgency | All three correct |",
        "|---|---|---|---|---|",
    ]
    for name, subset in groups:
        lines.append(
            f"| {name} ({len(subset)}) | {accuracy(subset, 'intent')} | {accuracy(subset, 'category')} "
            f"| {accuracy(subset, 'urgency')} | {all_three(subset)} |"
        )

    lines += ["", "## Speed and reliability", ""]
    if times:
        lines.append(f"- Average response time: {sum(times) / len(times):.0f} ms")
        lines.append(f"- Slowest response: {slowest['response_ms']} ms (message {slowest['id']})")
    lines += [
        f"- Messages where the model's first answer was invalid (before retry): {invalid_msgs} "
        f"({invalid_total} invalid answers in total)",
        f"- Messages that ended with `needs_review = true` (fallback used): {review}",
        f"- Requests that failed (HTTP/network error): {len(errors)}",
        "",
        "## Wrong answers",
        "",
    ]
    if wrong or errors:
        lines += [
            "| ID | Lang | Message | Expected (intent / category / urgency) | Got (intent / category / urgency) | Why (fill in) |",
            "|---|---|---|---|---|---|",
        ]
        for r in wrong:
            exp = " / ".join(r[k] for k in FIELDS)
            got = " / ".join(
                f"**{r['got'][k]}**" if r["got"][k] != r[k] else r["got"][k] for k in FIELDS
            )
            lines.append(f"| {r['id']} | {r['language']} | {md_cell(r['message'])} | {exp} | {got} | TODO |")
        for r in errors:
            exp = " / ".join(r[k] for k in FIELDS)
            lines.append(f"| {r['id']} | {r['language']} | {md_cell(r['message'])} | {exp} | ERROR: {md_cell(r['error'])} | TODO |")
    else:
        lines.append("No wrong answers.")

    report = "\n".join(lines) + "\n"
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(report)

    with open(args.results, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["id", "language", "message", "exp_intent", "exp_category", "exp_urgency",
             "got_intent", "got_category", "got_urgency", "needs_review", "invalid_attempts",
             "response_ms", "error"]
        )
        for r in results:
            g = r["got"] or {}
            writer.writerow(
                [r["id"], r["language"], r["message"], r["intent"], r["category"], r["urgency"],
                 g.get("intent", ""), g.get("category", ""), g.get("urgency", ""),
                 r["needs_review"], r["invalid_attempts"], r["response_ms"] or "", r["error"] or ""]
            )

    print("\n" + report)
    print(f"Saved report to {args.out} and per-message results to {args.results}")


if __name__ == "__main__":
    main()

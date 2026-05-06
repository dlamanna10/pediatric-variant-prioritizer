"""Build a self-contained HTML dashboard from the prioritized variant CSV."""

from __future__ import annotations

import argparse
import csv
import html
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "results" / "prioritized_variants.csv"
OUTPUT = ROOT / "dashboard" / "index.html"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a self-contained HTML dashboard from a ranked CSV."
    )
    parser.add_argument(
        "--input",
        default=str(INPUT),
        help="Prioritized variant CSV to visualize",
    )
    parser.add_argument(
        "--output",
        default=str(OUTPUT),
        help="Output HTML dashboard path",
    )
    parser.add_argument(
        "--predictions",
        help="Optional baseline ML prediction CSV to merge by variant_key",
    )
    parser.add_argument(
        "--model-metrics",
        help="Optional baseline model JSON with training metrics",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    rows = read_rows(input_path)
    if args.predictions:
        rows = merge_predictions(rows, read_rows(Path(args.predictions)))
    model_metrics = read_model_metrics(Path(args.model_metrics)) if args.model_metrics else {}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_dashboard(rows, model_metrics), encoding="utf-8")
    print(f"Wrote {output_path}")


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def merge_predictions(
    rows: list[dict[str, str]],
    predictions: list[dict[str, str]],
) -> list[dict[str, str]]:
    predictions_by_key = {
        row["variant_key"]: row
        for row in predictions
    }
    merged: list[dict[str, str]] = []
    for row in rows:
        combined = dict(row)
        prediction = predictions_by_key.get(row["variant_key"], {})
        combined["ml_probability"] = prediction.get("predicted_probability", "")
        combined["ml_predicted_label"] = prediction.get("predicted_label", "")
        combined["ml_candidate_label"] = prediction.get("candidate_label", "")
        merged.append(combined)
    return merged


def read_model_metrics(path: Path) -> dict[str, float]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {
        "training_accuracy": float(payload.get("training_accuracy", 0.0)),
        "leave_one_out_accuracy": float(payload.get("leave_one_out_accuracy", 0.0)),
    }


def render_dashboard(
    rows: list[dict[str, str]],
    model_metrics: dict[str, float] | None = None,
) -> str:
    payload = json.dumps(rows, indent=2)
    top = rows[0] if rows else {}
    max_score = max((float(row["score"]) for row in rows), default=0.0)
    variant_count = len(rows)
    phenotype_matches = sum(
        len([term for term in row["matched_hpo_terms"].split("|") if term])
        for row in rows
    )
    ml_rows = [
        row
        for row in rows
        if row.get("ml_probability")
    ]
    ml_count = len(ml_rows)
    max_ml_probability = max(
        (float(row["ml_probability"]) for row in ml_rows),
        default=0.0,
    )
    ml_summary_value = f"{max_ml_probability:.3f}" if ml_rows else "Not run"
    ml_summary_note = (
        f"{ml_count} variants with baseline ML predictions"
        if ml_rows
        else "Pass --predictions to display model output"
    )
    model_metrics = model_metrics or {}
    model_metric_value = (
        f"{model_metrics['leave_one_out_accuracy']:.3f}"
        if "leave_one_out_accuracy" in model_metrics
        else "Not run"
    )
    model_metric_note = (
        f"training accuracy {model_metrics['training_accuracy']:.3f}"
        if "training_accuracy" in model_metrics
        else "Pass --model-metrics to display evaluation"
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Pediatric Variant Prioritizer Dashboard</title>
  <style>
    :root {{
      --ink: #1f2933;
      --muted: #5d6b7a;
      --line: #d8dee8;
      --surface: #f7f8fb;
      --panel: #ffffff;
      --blue: #2563eb;
      --teal: #0f766e;
      --gold: #b7791f;
      --red: #b42318;
      --green: #287947;
      --purple: #6d5bd0;
      --shadow: 0 12px 24px rgba(31, 41, 51, 0.08);
    }}

    * {{
      box-sizing: border-box;
    }}

    body {{
      margin: 0;
      color: var(--ink);
      background: var(--surface);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.45;
    }}

    header {{
      background: #ffffff;
      border-bottom: 1px solid var(--line);
    }}

    .wrap {{
      width: min(1180px, calc(100vw - 32px));
      margin: 0 auto;
    }}

    .hero {{
      display: grid;
      grid-template-columns: 1.4fr 0.9fr;
      gap: 28px;
      padding: 34px 0 28px;
      align-items: end;
    }}

    h1 {{
      margin: 0 0 10px;
      font-size: 32px;
      line-height: 1.12;
      letter-spacing: 0;
    }}

    .lede {{
      margin: 0;
      color: var(--muted);
      max-width: 760px;
      font-size: 16px;
    }}

    .notice {{
      border-left: 4px solid var(--gold);
      background: #fff8e6;
      padding: 12px 14px;
      font-size: 14px;
      color: #5c4514;
    }}

    main {{
      padding: 24px 0 48px;
    }}

    section {{
      margin-bottom: 26px;
    }}

    h2 {{
      margin: 0 0 12px;
      font-size: 18px;
      letter-spacing: 0;
    }}

    .metrics {{
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 14px;
    }}

    .metric {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
      box-shadow: var(--shadow);
      min-height: 112px;
    }}

    .metric-label {{
      color: var(--muted);
      font-size: 13px;
      margin-bottom: 8px;
    }}

    .metric-value {{
      font-size: 25px;
      font-weight: 750;
      line-height: 1.1;
      overflow-wrap: anywhere;
    }}

    .metric-note {{
      color: var(--muted);
      font-size: 13px;
      margin-top: 7px;
    }}

    .flow {{
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 10px;
      align-items: stretch;
    }}

    .stage {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-top: 4px solid var(--blue);
      border-radius: 8px;
      padding: 13px;
      min-height: 116px;
    }}

    .stage:nth-child(2) {{ border-top-color: var(--teal); }}
    .stage:nth-child(3) {{ border-top-color: var(--purple); }}
    .stage:nth-child(4) {{ border-top-color: var(--gold); }}
    .stage:nth-child(5) {{ border-top-color: var(--green); }}

    .stage-title {{
      font-weight: 750;
      margin-bottom: 5px;
    }}

    .stage-copy {{
      color: var(--muted);
      font-size: 13px;
      margin: 0;
    }}

    .analysis-grid {{
      display: grid;
      grid-template-columns: 0.95fr 1.05fr;
      gap: 18px;
      align-items: start;
    }}

    .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
      padding: 16px;
    }}

    .bars {{
      display: grid;
      gap: 12px;
    }}

    .bar-row {{
      display: grid;
      grid-template-columns: 64px 1fr 54px;
      gap: 10px;
      align-items: center;
      min-height: 30px;
    }}

    .gene {{
      font-weight: 700;
      overflow-wrap: anywhere;
    }}

    .bar-track {{
      height: 18px;
      background: #e9edf4;
      border-radius: 4px;
      overflow: hidden;
      position: relative;
    }}

    .bar {{
      height: 100%;
      background: linear-gradient(90deg, var(--teal), var(--blue));
      min-width: 2px;
    }}

    .bar.negative {{
      background: var(--red);
    }}

    .score {{
      color: var(--muted);
      font-variant-numeric: tabular-nums;
      text-align: right;
    }}

    .detail-title {{
      display: flex;
      justify-content: space-between;
      gap: 10px;
      align-items: center;
      margin-bottom: 12px;
    }}

    .badge {{
      display: inline-flex;
      align-items: center;
      min-height: 24px;
      padding: 3px 8px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 700;
      background: #edf2ff;
      color: #1d4ed8;
    }}

    .badge.pathogenic,
    .badge.likely_pathogenic {{
      background: #fef3f2;
      color: var(--red);
    }}

    .badge.benign {{
      background: #ecfdf3;
      color: var(--green);
    }}

    .badge.uncertain_significance {{
      background: #fff8e6;
      color: #8a5a12;
    }}

    .evidence-list {{
      display: grid;
      gap: 9px;
      margin: 12px 0 0;
      padding: 0;
      list-style: none;
    }}

    .evidence-list li {{
      border-left: 3px solid var(--teal);
      background: #f5fbfa;
      padding: 8px 10px;
      font-size: 14px;
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
      box-shadow: var(--shadow);
    }}

    th,
    td {{
      padding: 10px 12px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      font-size: 14px;
      vertical-align: top;
    }}

    th {{
      color: var(--muted);
      background: #fbfcfe;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}

    tbody tr {{
      cursor: pointer;
    }}

    tbody tr:hover,
    tbody tr.active {{
      background: #eef6ff;
    }}

    .small {{
      color: var(--muted);
      font-size: 13px;
    }}

    @media (max-width: 900px) {{
      .hero,
      .analysis-grid {{
        grid-template-columns: 1fr;
      }}

      .metrics {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }}

      .flow {{
        grid-template-columns: 1fr;
      }}
    }}

    @media (max-width: 640px) {{
      .wrap {{
        width: min(100vw - 20px, 1180px);
      }}

      h1 {{
        font-size: 26px;
      }}

      .metrics {{
        grid-template-columns: 1fr;
      }}

      th,
      td {{
        padding: 9px;
      }}

      .table-wrap {{
        overflow-x: auto;
      }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="wrap hero">
      <div>
        <h1>Pediatric Variant Prioritizer Dashboard</h1>
        <p class="lede">A visual walkthrough of how the example VCF becomes a ranked rare-disease variant review report.</p>
      </div>
      <div class="notice">Educational demo only. Scores explain evidence for review and are not diagnoses.</div>
    </div>
  </header>

  <main class="wrap">
    <section class="metrics" aria-label="Dashboard summary">
      <div class="metric">
        <div class="metric-label">Variants reviewed</div>
        <div class="metric-value">{variant_count}</div>
        <div class="metric-note">Rows from prioritized_variants.csv</div>
      </div>
      <div class="metric">
        <div class="metric-label">Top candidate gene</div>
        <div class="metric-value">{html.escape(top.get("gene", "NA"))}</div>
        <div class="metric-note">{html.escape(top.get("variant_key", ""))}</div>
      </div>
      <div class="metric">
        <div class="metric-label">Highest score</div>
        <div class="metric-value">{html.escape(top.get("score", "0"))}</div>
        <div class="metric-note">Transparent evidence score</div>
      </div>
      <div class="metric">
        <div class="metric-label">Top ML probability</div>
        <div class="metric-value">{html.escape(ml_summary_value)}</div>
        <div class="metric-note">{html.escape(ml_summary_note)}</div>
      </div>
      <div class="metric">
        <div class="metric-label">ML LOO accuracy</div>
        <div class="metric-value">{html.escape(model_metric_value)}</div>
        <div class="metric-note">{html.escape(model_metric_note)}</div>
      </div>
    </section>

    <section>
      <h2>Pipeline View</h2>
      <div class="flow" aria-label="Pipeline stages">
        <div class="stage">
          <div class="stage-title">1. VCF</div>
          <p class="stage-copy">Reads chromosome, position, REF, ALT, gene, consequence, and zygosity.</p>
        </div>
        <div class="stage">
          <div class="stage-title">2. Phenotypes</div>
          <p class="stage-copy">Loads patient HPO terms that describe symptoms in standardized language.</p>
        </div>
        <div class="stage">
          <div class="stage-title">3. Annotation</div>
          <p class="stage-copy">Adds ClinVar-like significance, gnomAD-like frequency, and gene-HPO evidence.</p>
        </div>
        <div class="stage">
          <div class="stage-title">4. Scoring</div>
          <p class="stage-copy">Combines rarity, molecular impact, known significance, phenotype match, and zygosity.</p>
        </div>
        <div class="stage">
          <div class="stage-title">5. Report</div>
          <p class="stage-copy">Writes ranked outputs and can overlay baseline ML probabilities when available.</p>
        </div>
      </div>
    </section>

    <section class="analysis-grid">
      <div class="panel">
        <h2>Score Ranking</h2>
        <div id="bars" class="bars"></div>
        <p class="small">Longer bars indicate higher review priority in this educational scoring baseline.</p>
      </div>
      <div class="panel">
        <div class="detail-title">
          <h2 id="detail-heading">Variant Detail</h2>
          <span id="detail-badge" class="badge">selected</span>
        </div>
        <div id="detail"></div>
      </div>
    </section>

    <section>
      <h2>Ranked Variants</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Rank</th>
              <th>Gene</th>
              <th>Score</th>
              <th>Consequence</th>
              <th>Clinical Significance</th>
              <th>ML Probability</th>
              <th>Matched HPO</th>
            </tr>
          </thead>
          <tbody id="variant-table"></tbody>
        </table>
      </div>
    </section>
  </main>

  <script>
    const variants = {payload};
    const maxScore = {max_score};

    function badgeClass(value) {{
      return String(value || "selected").toLowerCase().replaceAll(" ", "_");
    }}

    function evidenceItems(row) {{
      return String(row.evidence || "")
        .split(" | ")
        .filter(Boolean)
        .map(item => `<li>${{escapeHtml(item)}}</li>`)
        .join("");
    }}

    function escapeHtml(value) {{
      return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    }}

    function renderBars() {{
      const container = document.getElementById("bars");
      container.innerHTML = variants.map(row => {{
        const score = Number(row.score);
        const width = maxScore > 0 ? Math.max(Math.abs(score) / maxScore * 100, 4) : 4;
        const barClass = score < 0 ? "bar negative" : "bar";
        return `
          <div class="bar-row" data-key="${{escapeHtml(row.variant_key)}}">
            <div class="gene">${{escapeHtml(row.gene)}}</div>
            <div class="bar-track"><div class="${{barClass}}" style="width: ${{width}}%"></div></div>
            <div class="score">${{escapeHtml(row.score)}}</div>
          </div>
        `;
      }}).join("");
    }}

    function renderTable(selectedKey) {{
      const body = document.getElementById("variant-table");
      body.innerHTML = variants.map(row => {{
        const active = row.variant_key === selectedKey ? "active" : "";
        return `
          <tr class="${{active}}" data-key="${{escapeHtml(row.variant_key)}}">
            <td>${{escapeHtml(row.rank)}}</td>
            <td><strong>${{escapeHtml(row.gene)}}</strong><div class="small">${{escapeHtml(row.variant_key)}}</div></td>
            <td>${{escapeHtml(row.score)}}</td>
            <td>${{escapeHtml(row.consequence)}}</td>
            <td><span class="badge ${{badgeClass(row.clinical_significance)}}">${{escapeHtml(row.clinical_significance)}}</span></td>
            <td>${{formatProbability(row.ml_probability)}}</td>
            <td>${{escapeHtml(row.matched_hpo_terms || "none")}}</td>
          </tr>
        `;
      }}).join("");

      body.querySelectorAll("tr").forEach(row => {{
        row.addEventListener("click", () => selectVariant(row.dataset.key));
      }});
    }}

    function renderDetail(row) {{
      document.getElementById("detail-heading").textContent = `${{row.gene}} evidence`;
      const badge = document.getElementById("detail-badge");
      badge.className = `badge ${{badgeClass(row.clinical_significance)}}`;
      badge.textContent = row.clinical_significance;

      document.getElementById("detail").innerHTML = `
        <p><strong>Variant:</strong> ${{escapeHtml(row.variant_key)}}</p>
        <p><strong>Condition label:</strong> ${{escapeHtml(row.condition || "not listed")}}</p>
        <p><strong>Allele frequency:</strong> ${{escapeHtml(row.allele_frequency || "missing")}}</p>
        <p><strong>Baseline ML probability:</strong> ${{formatProbability(row.ml_probability)}} ${{formatMlLabel(row.ml_predicted_label)}}</p>
        <p><strong>Zygosity:</strong> ${{escapeHtml(row.zygosity)}} | <strong>Consequence:</strong> ${{escapeHtml(row.consequence)}}</p>
        <p><strong>Matched patient phenotypes:</strong> ${{escapeHtml(row.matched_hpo_terms || "none")}}</p>
        <ul class="evidence-list">${{evidenceItems(row)}}</ul>
      `;
    }}

    function selectVariant(key) {{
      const row = variants.find(item => item.variant_key === key) || variants[0];
      renderDetail(row);
      renderTable(row.variant_key);
    }}

    function formatProbability(value) {{
      if (!value) {{
        return "not run";
      }}
      return Number(value).toFixed(3);
    }}

    function formatMlLabel(value) {{
      if (!value) {{
        return "";
      }}
      return `(predicted label: ${{escapeHtml(value)}})`;
    }}

    renderBars();
    selectVariant(variants[0]?.variant_key);
  </script>
</body>
</html>
"""


if __name__ == "__main__":
    main()

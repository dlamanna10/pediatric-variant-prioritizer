"""Generate a Markdown interpretation report for the public-data run."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a Markdown summary report for the public workflow."
    )
    parser.add_argument(
        "--prioritized",
        default=str(ROOT / "results" / "public_prioritized_variants.csv"),
    )
    parser.add_argument(
        "--predictions",
        default=str(ROOT / "results" / "public_baseline_predictions.csv"),
    )
    parser.add_argument(
        "--importance",
        default=str(ROOT / "results" / "public_baseline_feature_importance.csv"),
    )
    parser.add_argument(
        "--model",
        default=str(ROOT / "results" / "public_baseline_model.json"),
    )
    parser.add_argument(
        "--source",
        default=str(ROOT / "data" / "public" / "SOURCE.md"),
    )
    parser.add_argument(
        "--output",
        default=str(ROOT / "reports" / "public_run_summary.md"),
    )
    args = parser.parse_args()

    prioritized = read_csv(Path(args.prioritized))
    predictions = read_csv(Path(args.predictions))
    importance = read_csv(Path(args.importance))
    model = json.loads(Path(args.model).read_text(encoding="utf-8"))
    source = Path(args.source).read_text(encoding="utf-8")

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        render_report(prioritized, predictions, importance, model, source),
        encoding="utf-8",
    )
    print(f"Wrote {output}")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def render_report(
    prioritized: list[dict[str, str]],
    predictions: list[dict[str, str]],
    importance: list[dict[str, str]],
    model: dict[str, object],
    source: str,
) -> str:
    genes = Counter(row["gene"] for row in prioritized)
    predictions_by_key = {
        row["variant_key"]: row
        for row in predictions
    }
    metrics = model.get("metrics", {})
    if not isinstance(metrics, dict):
        metrics = {}

    lines = [
        "# Public Run Summary",
        "",
        "This report summarizes the public ClinVar/HPO workflow output. It is educational and not clinical decision support.",
        "",
        "## Dataset",
        "",
        f"- Variants analyzed: {len(prioritized)}",
        f"- Genes represented: {', '.join(sorted(genes))}",
        "- Variant source: ClinVar GRCh38 VCF subset",
        "- Phenotype source: HPO genes_to_phenotype subset",
        "- Patient profile: synthetic HPO terms assembled from public HPO annotations",
        "",
        "## Top Ranked Variants",
        "",
        "| Rank | Gene | Variant | Score | ClinVar label | HPO matches | ML probability |",
        "| --- | --- | --- | ---: | --- | --- | ---: |",
    ]

    for row in prioritized[:5]:
        prediction = predictions_by_key.get(row["variant_key"], {})
        probability = prediction.get("predicted_probability", "")
        lines.append(
            "| {rank} | {gene} | `{variant}` | {score} | {label} | {hpo} | {probability} |".format(
                rank=row["rank"],
                gene=escape_table_cell(row["gene"]),
                variant=escape_table_cell(row["variant_key"]),
                score=row["score"],
                label=escape_table_cell(row["clinical_significance"]),
                hpo=escape_table_cell(row["matched_hpo_terms"] or "none"),
                probability=probability or "not run",
            )
        )

    top = prioritized[0]
    top_prediction = predictions_by_key.get(top["variant_key"], {})
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"The top-ranked variant is `{top['variant_key']}` in **{top['gene']}** with an evidence score of **{top['score']}**.",
            f"It ranks highly because: {top['evidence']}.",
            f"The baseline ML probability for this variant is **{top_prediction.get('predicted_probability', 'not run')}**.",
            "",
            "The evidence score and ML probability answer related but different questions. The evidence score is transparent and rule-based. The ML probability is learned from the exported feature table and ClinVar-derived labels.",
            "",
            "## Baseline ML Metrics",
            "",
            f"- Accuracy: {format_metric(metrics.get('accuracy'))}",
            f"- Precision: {format_metric(metrics.get('precision'))}",
            f"- Recall: {format_metric(metrics.get('recall'))}",
            f"- F1: {format_metric(metrics.get('f1'))}",
            f"- AUROC: {format_metric(metrics.get('auroc'))}",
            f"- Leave-one-out accuracy: {format_metric(model.get('leave_one_out_accuracy'))}",
            "",
            "These metrics are from a small public-derived subset and should be treated as workflow checks, not generalizable clinical performance.",
            "",
            "## Top Feature Importance",
            "",
            "| Feature | Coefficient | Direction |",
            "| --- | ---: | --- |",
        ]
    )

    for row in importance[:6]:
        lines.append(
            f"| `{row['feature']}` | {float(row['coefficient']):.3f} | {row['direction']} |"
        )

    lines.extend(
        [
            "",
            "## Limitations",
            "",
            "- The patient HPO profile is synthetic.",
            "- The public dataset is intentionally small.",
            "- Population frequencies are limited to ClinVar embedded public AF fields unless an override file is supplied.",
            "- The model is dependency-free and useful for demonstrating workflow shape, not clinical deployment.",
            "- A production workflow would need validated annotation tools, versioned references, broader evaluation, and clinical review.",
            "",
            "## Source Notes",
            "",
            source.strip(),
            "",
        ]
    )
    return "\n".join(lines)


def format_metric(value: object) -> str:
    if value is None:
        return "not available"
    return f"{float(value):.3f}"


def escape_table_cell(value: str) -> str:
    return value.replace("|", "\\|")


if __name__ == "__main__":
    main()

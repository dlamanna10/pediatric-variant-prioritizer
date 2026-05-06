"""Report writers for prioritized variants."""

from __future__ import annotations

import csv
from pathlib import Path

from .models import AnnotatedVariant


def write_csv_report(variants: list[AnnotatedVariant], output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "rank",
                "score",
                "variant_key",
                "gene",
                "consequence",
                "zygosity",
                "allele_frequency",
                "clinical_significance",
                "condition",
                "matched_hpo_terms",
                "evidence",
            ],
        )
        writer.writeheader()
        for rank, annotated in enumerate(variants, start=1):
            writer.writerow(
                {
                    "rank": rank,
                    "score": f"{annotated.score:.1f}",
                    "variant_key": annotated.variant.key,
                    "gene": annotated.variant.gene,
                    "consequence": annotated.variant.consequence,
                    "zygosity": annotated.variant.zygosity,
                    "allele_frequency": _format_frequency(
                        annotated.gnomad.allele_frequency
                    ),
                    "clinical_significance": annotated.clinvar.significance,
                    "condition": annotated.clinvar.condition,
                    "matched_hpo_terms": "|".join(sorted(annotated.matched_hpo_terms)),
                    "evidence": " | ".join(annotated.evidence),
                }
            )


def _format_frequency(allele_frequency: float | None) -> str:
    if allele_frequency is None:
        return ""
    return f"{allele_frequency:g}"

"""Feature-table export for downstream machine learning experiments."""

from __future__ import annotations

import csv
from pathlib import Path

from .models import AnnotatedVariant
from .scoring import CLINVAR_WEIGHTS, CONSEQUENCE_WEIGHTS, calculate_rarity_score


FEATURE_COLUMNS = [
    "variant_key",
    "gene",
    "consequence",
    "zygosity",
    "allele_frequency",
    "allele_frequency_missing",
    "rarity_score",
    "consequence_score",
    "clinvar_score",
    "is_pathogenic_or_likely_pathogenic",
    "is_benign_or_likely_benign",
    "is_uncertain_significance",
    "phenotype_match_count",
    "phenotype_match_score",
    "is_homozygous",
    "total_evidence_score",
]


def write_feature_table(
    variants: list[AnnotatedVariant],
    output_path: str | Path,
) -> None:
    """Write one ML-ready feature row per annotated and scored variant."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FEATURE_COLUMNS)
        writer.writeheader()
        for variant in variants:
            writer.writerow(variant_to_features(variant))


def variant_to_features(annotated: AnnotatedVariant) -> dict[str, str | int | float]:
    """Convert an annotated variant into numeric/categorical feature columns."""

    clinvar_key = _normalized_clinvar_key(annotated.clinvar.significance)
    allele_frequency = annotated.gnomad.allele_frequency
    phenotype_match_count = len(annotated.matched_hpo_terms)

    return {
        "variant_key": annotated.variant.key,
        "gene": annotated.variant.gene,
        "consequence": annotated.variant.consequence,
        "zygosity": annotated.variant.zygosity,
        "allele_frequency": "" if allele_frequency is None else allele_frequency,
        "allele_frequency_missing": int(allele_frequency is None),
        "rarity_score": calculate_rarity_score(allele_frequency),
        "consequence_score": CONSEQUENCE_WEIGHTS.get(
            annotated.variant.consequence,
            0,
        ),
        "clinvar_score": CLINVAR_WEIGHTS.get(clinvar_key, 0),
        "is_pathogenic_or_likely_pathogenic": int(
            clinvar_key in {"pathogenic", "likely_pathogenic"}
        ),
        "is_benign_or_likely_benign": int(
            clinvar_key in {"benign", "likely_benign"}
        ),
        "is_uncertain_significance": int(clinvar_key == "uncertain_significance"),
        "phenotype_match_count": phenotype_match_count,
        "phenotype_match_score": min(phenotype_match_count * 8, 24),
        "is_homozygous": int(annotated.variant.zygosity == "hom"),
        "total_evidence_score": annotated.score,
    }


def _normalized_clinvar_key(significance: str) -> str:
    return significance.lower().replace(" ", "_")


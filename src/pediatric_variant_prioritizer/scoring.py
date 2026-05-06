"""Transparent evidence-based scoring for variant prioritization."""

from __future__ import annotations

from dataclasses import replace

from .models import AnnotatedVariant


CONSEQUENCE_WEIGHTS = {
    "stop_gained": 20,
    "frameshift_variant": 18,
    "splice_acceptor_variant": 16,
    "splice_donor_variant": 16,
    "missense_variant": 10,
    "synonymous_variant": 0,
}

CLINVAR_WEIGHTS = {
    "pathogenic": 35,
    "likely_pathogenic": 25,
    "uncertain_significance": 8,
    "conflicting_interpretations": 4,
    "likely_benign": -15,
    "benign": -25,
}


def rank_variants(variants: list[AnnotatedVariant]) -> list[AnnotatedVariant]:
    scored = [score_variant(variant) for variant in variants]
    return sorted(
        scored,
        key=lambda item: (item.score, len(item.matched_hpo_terms)),
        reverse=True,
    )


def score_variant(annotated: AnnotatedVariant) -> AnnotatedVariant:
    evidence: list[str] = []
    score = 0.0

    rarity_score = calculate_rarity_score(annotated.gnomad.allele_frequency)
    score += rarity_score
    evidence.append(_rarity_evidence(annotated.gnomad.allele_frequency, rarity_score))

    consequence_score = CONSEQUENCE_WEIGHTS.get(annotated.variant.consequence, 0)
    score += consequence_score
    if consequence_score:
        evidence.append(
            f"{annotated.variant.consequence} consequence adds {consequence_score:g}"
        )

    clinvar_key = annotated.clinvar.significance.lower().replace(" ", "_")
    clinvar_score = CLINVAR_WEIGHTS.get(clinvar_key, 0)
    score += clinvar_score
    if annotated.clinvar.significance != "not_reported":
        evidence.append(
            f"ClinVar-like significance {annotated.clinvar.significance} adds {clinvar_score:g}"
        )

    phenotype_score = min(len(annotated.matched_hpo_terms) * 8, 24)
    score += phenotype_score
    if phenotype_score:
        evidence.append(
            f"{len(annotated.matched_hpo_terms)} phenotype match(es) add {phenotype_score:g}"
        )

    if annotated.variant.zygosity == "hom":
        score += 5
        evidence.append("homozygous observation adds 5")

    return replace(annotated, score=score, evidence=tuple(evidence))


def calculate_rarity_score(allele_frequency: float | None) -> float:
    if allele_frequency is None:
        return 5
    if allele_frequency <= 0.0001:
        return 35
    if allele_frequency <= 0.001:
        return 28
    if allele_frequency <= 0.01:
        return 15
    if allele_frequency <= 0.05:
        return 2
    return -20


def _rarity_evidence(allele_frequency: float | None, score: float) -> str:
    if allele_frequency is None:
        return "missing population frequency adds 5"
    return f"gnomAD-like AF {allele_frequency:g} adds {score:g}"

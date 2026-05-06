"""Reference-table loading and variant annotation."""

from __future__ import annotations

import csv
from pathlib import Path

from .models import (
    AnnotatedVariant,
    ClinVarAnnotation,
    GenePhenotypeAnnotation,
    GnomadAnnotation,
    Variant,
)


class ReferenceData:
    def __init__(
        self,
        clinvar: dict[str, ClinVarAnnotation],
        gnomad: dict[str, GnomadAnnotation],
        gene_phenotypes: dict[str, GenePhenotypeAnnotation],
    ) -> None:
        self.clinvar = clinvar
        self.gnomad = gnomad
        self.gene_phenotypes = gene_phenotypes


def read_patient_hpo(path: str | Path) -> frozenset[str]:
    terms: set[str] = set()
    with Path(path).open(encoding="utf-8") as handle:
        for line in handle:
            term = line.strip()
            if term and not term.startswith("#"):
                terms.add(term)
    return frozenset(terms)


def load_reference_data(reference_dir: str | Path) -> ReferenceData:
    reference_path = Path(reference_dir)
    return ReferenceData(
        clinvar=_load_clinvar(reference_path / "clinvar_mini.csv"),
        gnomad=_load_gnomad(reference_path / "gnomad_mini.csv"),
        gene_phenotypes=_load_gene_phenotypes(reference_path / "gene_phenotype_mini.csv"),
    )


def annotate_variants(
    variants: list[Variant],
    references: ReferenceData,
    patient_hpo_terms: frozenset[str],
) -> list[AnnotatedVariant]:
    annotated: list[AnnotatedVariant] = []
    for variant in variants:
        gene_phenotype = references.gene_phenotypes.get(
            variant.gene,
            GenePhenotypeAnnotation(),
        )
        matched_hpo_terms = patient_hpo_terms.intersection(gene_phenotype.hpo_terms)
        annotated.append(
            AnnotatedVariant(
                variant=variant,
                clinvar=references.clinvar.get(variant.key, ClinVarAnnotation()),
                gnomad=references.gnomad.get(variant.key, GnomadAnnotation()),
                gene_phenotype=gene_phenotype,
                matched_hpo_terms=frozenset(matched_hpo_terms),
            )
        )
    return annotated


def _load_clinvar(path: Path) -> dict[str, ClinVarAnnotation]:
    rows: dict[str, ClinVarAnnotation] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            rows[row["variant_key"]] = ClinVarAnnotation(
                significance=row["clinical_significance"],
                condition=row["condition"],
            )
    return rows


def _load_gnomad(path: Path) -> dict[str, GnomadAnnotation]:
    rows: dict[str, GnomadAnnotation] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            raw_frequency = row["allele_frequency"]
            rows[row["variant_key"]] = GnomadAnnotation(
                allele_frequency=float(raw_frequency) if raw_frequency else None,
            )
    return rows


def _load_gene_phenotypes(path: Path) -> dict[str, GenePhenotypeAnnotation]:
    grouped: dict[str, dict[str, set[str] | list[str]]] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            gene = row["gene"]
            grouped.setdefault(gene, {"hpo_terms": set(), "phenotypes": []})
            grouped[gene]["hpo_terms"].add(row["hpo_id"])  # type: ignore[union-attr]
            grouped[gene]["phenotypes"].append(row["phenotype"])  # type: ignore[union-attr]

    return {
        gene: GenePhenotypeAnnotation(
            hpo_terms=frozenset(values["hpo_terms"]),
            phenotypes=tuple(values["phenotypes"]),
        )
        for gene, values in grouped.items()
    }

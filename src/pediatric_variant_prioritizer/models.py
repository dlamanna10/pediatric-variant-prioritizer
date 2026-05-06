"""Shared data models for variant prioritization."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Variant:
    chrom: str
    pos: int
    ref: str
    alt: str
    gene: str
    consequence: str
    zygosity: str

    @property
    def key(self) -> str:
        return f"{self.chrom}-{self.pos}-{self.ref}-{self.alt}"


@dataclass(frozen=True)
class ClinVarAnnotation:
    significance: str = "not_reported"
    condition: str = ""


@dataclass(frozen=True)
class GnomadAnnotation:
    allele_frequency: float | None = None


@dataclass(frozen=True)
class GenePhenotypeAnnotation:
    hpo_terms: frozenset[str] = field(default_factory=frozenset)
    phenotypes: tuple[str, ...] = ()


@dataclass(frozen=True)
class AnnotatedVariant:
    variant: Variant
    clinvar: ClinVarAnnotation
    gnomad: GnomadAnnotation
    gene_phenotype: GenePhenotypeAnnotation
    matched_hpo_terms: frozenset[str]
    score: float = 0.0
    evidence: tuple[str, ...] = ()

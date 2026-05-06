"""Build a small reproducible public-data subset from ClinVar and HPO.

The generated files are intentionally tiny so the project remains easy to run,
but the source records come from public ClinVar and HPO downloads.
"""

from __future__ import annotations

import csv
import gzip
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "data" / "public"
REFERENCE_DIR = OUTPUT_DIR / "reference"

CLINVAR_VCF_URL = "https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh38/clinvar.vcf.gz"
HPO_GENE_PHENOTYPE_URL = "http://purl.obolibrary.org/obo/hp/hpoa/genes_to_phenotype.txt"

TARGET_GENES = ["SCN1A", "CFTR", "FBN1", "TSC2"]
VARIANTS_PER_GENE = 2
CANDIDATE_POOL_PER_GENE = 80
PHENOTYPES_PER_GENE = 6
PHENOTYPE_POOL_PER_GENE = 100
PATIENT_PROFILE_GENES = ["SCN1A", "TSC2"]
CONSEQUENCE_PRIORITY = [
    "stop_gained",
    "frameshift_variant",
    "splice_acceptor_variant",
    "splice_donor_variant",
    "missense_variant",
    "synonymous_variant",
]
PHENOTYPE_KEYWORDS = [
    "seizure",
    "epilep",
    "development",
    "speech",
    "cognitive",
    "intellectual",
    "fibroma",
    "kidney",
    "hydrocephalus",
]


@dataclass(frozen=True)
class PublicVariant:
    chrom: str
    pos: int
    ref: str
    alt: str
    gene: str
    consequence: str
    clinical_significance: str
    condition: str

    @property
    def key(self) -> str:
        return f"{self.chrom}-{self.pos}-{self.ref}-{self.alt}"


@dataclass(frozen=True)
class GenePhenotype:
    gene: str
    hpo_id: str
    phenotype: str


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)

    variants = collect_clinvar_variants()
    phenotypes = collect_hpo_phenotypes()
    patient_terms = choose_patient_terms(phenotypes)

    write_vcf(variants, OUTPUT_DIR / "clinvar_variants.vcf")
    write_patient_hpo(patient_terms, OUTPUT_DIR / "patient_hpo.txt")
    write_clinvar_reference(variants, REFERENCE_DIR / "clinvar_mini.csv")
    write_gnomad_reference(REFERENCE_DIR / "gnomad_mini.csv")
    write_gene_phenotype_reference(
        phenotypes,
        REFERENCE_DIR / "gene_phenotype_mini.csv",
    )
    write_source_notes(variants, phenotypes, patient_terms, OUTPUT_DIR / "SOURCE.md")

    print(f"Wrote {len(variants)} ClinVar variants to {OUTPUT_DIR}")
    print(f"Wrote {len(phenotypes)} HPO gene-phenotype rows to {REFERENCE_DIR}")
    print(f"Wrote {len(patient_terms)} synthetic patient HPO terms from public HPO")


def collect_clinvar_variants() -> list[PublicVariant]:
    candidates: dict[str, list[PublicVariant]] = defaultdict(list)
    target_genes = set(TARGET_GENES)

    with urlopen(CLINVAR_VCF_URL, timeout=120) as response:
        with gzip.GzipFile(fileobj=response) as gzip_file:
            for raw_line in gzip_file:
                line = raw_line.decode("utf-8")
                if line.startswith("#"):
                    continue

                columns = line.rstrip("\n").split("\t")
                if len(columns) < 8:
                    continue

                chrom, pos, _identifier, ref, alt, _qual, _filter, info = columns[:8]
                if "," in alt or alt.startswith("<"):
                    continue

                parsed_info = parse_info(info)
                gene = parse_gene(parsed_info.get("GENEINFO", ""))
                if gene not in target_genes:
                    continue
                if len(candidates[gene]) >= CANDIDATE_POOL_PER_GENE:
                    continue

                clinical_significance = normalize_clinvar_significance(
                    parsed_info.get("CLNSIG", "")
                )
                if clinical_significance == "not_reported":
                    continue

                candidates[gene].append(
                    PublicVariant(
                        chrom=chrom,
                        pos=int(pos),
                        ref=ref,
                        alt=alt,
                        gene=gene,
                        consequence=parse_consequence(parsed_info.get("MC", "")),
                        clinical_significance=clinical_significance,
                        condition=clean_condition(parsed_info.get("CLNDN", "")),
                    )
                )

                if all(
                    len(candidates[gene]) >= CANDIDATE_POOL_PER_GENE
                    for gene in target_genes
                ):
                    return select_best_variants(candidates)

    return select_best_variants(candidates)


def collect_hpo_phenotypes() -> list[GenePhenotype]:
    grouped: dict[str, list[GenePhenotype]] = defaultdict(list)
    seen: set[tuple[str, str]] = set()
    target_genes = set(TARGET_GENES)

    with urlopen(HPO_GENE_PHENOTYPE_URL, timeout=60) as response:
        for raw_line in response:
            line = raw_line.decode("utf-8").rstrip("\n")
            if not line or line.startswith("#") or line.startswith("ncbi_gene_id"):
                continue

            columns = line.split("\t")
            if len(columns) < 4:
                continue

            gene = columns[1]
            if gene not in target_genes:
                continue
            if len(grouped[gene]) >= PHENOTYPE_POOL_PER_GENE:
                continue
            dedupe_key = (gene, columns[2])
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)

            grouped[gene].append(
                GenePhenotype(
                    gene=gene,
                    hpo_id=columns[2],
                    phenotype=columns[3],
                )
            )

    return [
        phenotype
        for gene in TARGET_GENES
        for phenotype in select_best_phenotypes(grouped.get(gene, []))
    ]


def choose_patient_terms(phenotypes: list[GenePhenotype]) -> list[str]:
    terms: list[str] = []
    for gene in PATIENT_PROFILE_GENES:
        gene_terms = 0
        gene_phenotypes = [
            phenotype
            for phenotype in phenotypes
            if phenotype.gene == gene
        ]
        for phenotype in select_best_phenotypes(gene_phenotypes):
            if phenotype.gene == gene and phenotype.hpo_id not in terms:
                terms.append(phenotype.hpo_id)
                gene_terms += 1
            if gene_terms >= 2:
                break
            if len(terms) >= 4:
                return terms
    return terms


def parse_info(info: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for item in info.split(";"):
        if not item:
            continue
        if "=" in item:
            key, value = item.split("=", 1)
            fields[key] = unquote(value)
        else:
            fields[item] = "true"
    return fields


def parse_gene(geneinfo: str) -> str:
    if not geneinfo:
        return ""
    first_gene = geneinfo.split("|", 1)[0]
    return first_gene.split(":", 1)[0]


def parse_consequence(molecular_consequence: str) -> str:
    consequences = {
        item.split("|", 1)[1]
        for item in molecular_consequence.split(",")
        if "|" in item
    }
    for consequence in CONSEQUENCE_PRIORITY:
        if consequence in consequences:
            return consequence
    return sorted(consequences)[0] if consequences else "unknown"


def normalize_clinvar_significance(raw_significance: str) -> str:
    normalized = raw_significance.lower().replace(" ", "_")
    first_value = normalized.split("|", 1)[0].split(",", 1)[0]
    if "pathogenic" in first_value and "likely" not in first_value:
        return "pathogenic"
    if "likely_pathogenic" in first_value:
        return "likely_pathogenic"
    if "uncertain_significance" in first_value:
        return "uncertain_significance"
    if "likely_benign" in first_value:
        return "likely_benign"
    if "benign" in first_value:
        return "benign"
    if "conflicting" in first_value:
        return "conflicting_interpretations"
    return "not_reported"


def clean_condition(condition: str) -> str:
    if not condition:
        return ""
    return condition.split("|", 1)[0].replace("_", " ")


def flatten_by_target_gene(
    selected: dict[str, list[PublicVariant]],
) -> list[PublicVariant]:
    return [
        variant
        for gene in TARGET_GENES
        for variant in selected.get(gene, [])
    ]


def select_best_variants(
    candidates: dict[str, list[PublicVariant]],
) -> list[PublicVariant]:
    selected: dict[str, list[PublicVariant]] = {}
    for gene in TARGET_GENES:
        selected[gene] = sorted(
            candidates.get(gene, []),
            key=variant_selection_score,
            reverse=True,
        )[:VARIANTS_PER_GENE]
    return flatten_by_target_gene(selected)


def variant_selection_score(variant: PublicVariant) -> int:
    consequence_scores = {
        "stop_gained": 90,
        "frameshift_variant": 85,
        "splice_acceptor_variant": 80,
        "splice_donor_variant": 80,
        "missense_variant": 60,
        "synonymous_variant": 20,
    }
    significance_scores = {
        "pathogenic": 60,
        "likely_pathogenic": 50,
        "uncertain_significance": 20,
        "conflicting_interpretations": 15,
        "likely_benign": 5,
        "benign": 0,
    }
    condition_score = 0 if variant.condition in {"", "not provided"} else 5
    return (
        consequence_scores.get(variant.consequence, 0)
        + significance_scores.get(variant.clinical_significance, 0)
        + condition_score
    )


def select_best_phenotypes(phenotypes: list[GenePhenotype]) -> list[GenePhenotype]:
    return sorted(
        phenotypes,
        key=phenotype_selection_score,
        reverse=True,
    )[:PHENOTYPES_PER_GENE]


def phenotype_selection_score(phenotype: GenePhenotype) -> int:
    name = phenotype.phenotype.lower()
    return sum(
        1
        for keyword in PHENOTYPE_KEYWORDS
        if keyword in name
    )


def write_vcf(variants: list[PublicVariant], path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write("##fileformat=VCFv4.2\n")
        handle.write("##source=ClinVar_GRCh38_public_subset\n")
        handle.write("#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n")
        for variant in variants:
            info = (
                f"GENE={variant.gene};"
                f"CONSEQUENCE={variant.consequence};"
                "ZYGOSITY=het"
            )
            handle.write(
                f"{variant.chrom}\t{variant.pos}\t.\t{variant.ref}\t{variant.alt}"
                f"\t.\tPASS\t{info}\n"
            )


def write_patient_hpo(terms: list[str], path: Path) -> None:
    path.write_text("\n".join(terms) + "\n", encoding="utf-8")


def write_clinvar_reference(variants: list[PublicVariant], path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["variant_key", "clinical_significance", "condition"],
        )
        writer.writeheader()
        for variant in variants:
            writer.writerow(
                {
                    "variant_key": variant.key,
                    "clinical_significance": variant.clinical_significance,
                    "condition": variant.condition,
                }
            )


def write_gnomad_reference(path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["variant_key", "allele_frequency"])
        writer.writeheader()


def write_gene_phenotype_reference(
    phenotypes: list[GenePhenotype],
    path: Path,
) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["gene", "hpo_id", "phenotype"],
        )
        writer.writeheader()
        for phenotype in phenotypes:
            writer.writerow(
                {
                    "gene": phenotype.gene,
                    "hpo_id": phenotype.hpo_id,
                    "phenotype": phenotype.phenotype,
                }
            )


def write_source_notes(
    variants: list[PublicVariant],
    phenotypes: list[GenePhenotype],
    patient_terms: list[str],
    path: Path,
) -> None:
    path.write_text(
        "\n".join(
            [
                "# Public Data Subset",
                "",
                "This directory contains a small reproducible subset built from public",
                "ClinVar and HPO downloads. It is for educational demonstration only.",
                "",
                "## Sources",
                "",
                f"- ClinVar GRCh38 VCF: {CLINVAR_VCF_URL}",
                f"- HPO genes_to_phenotype: {HPO_GENE_PHENOTYPE_URL}",
                "",
                "## Included Genes",
                "",
                ", ".join(TARGET_GENES),
                "",
                "## Generated Files",
                "",
                "- clinvar_variants.vcf: public ClinVar variants transformed into the",
                "  project demo VCF shape",
                "- patient_hpo.txt: synthetic patient profile using HPO terms from the",
                "  public HPO gene-phenotype annotations",
                "- reference/clinvar_mini.csv: ClinVar clinical significance and",
                "  condition fields for the selected variants",
                "- reference/gene_phenotype_mini.csv: HPO gene-phenotype rows for the",
                "  selected genes",
                "- reference/gnomad_mini.csv: header-only placeholder because this",
                "  public subset does not download gnomAD frequencies",
                "",
                f"Selected variants: {len(variants)}",
                f"Selected gene-phenotype rows: {len(phenotypes)}",
                f"Synthetic patient HPO terms: {', '.join(patient_terms)}",
                "",
            ]
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

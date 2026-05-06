"""Command-line interface for variant prioritization."""

from __future__ import annotations

import argparse
from pathlib import Path

from .annotation import annotate_variants, load_reference_data, read_patient_hpo
from .report import write_csv_report
from .scoring import rank_variants
from .vcf import read_vcf


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prioritize candidate rare-disease variants from VCF and HPO terms."
    )
    parser.add_argument("--vcf", required=True, help="Input VCF path")
    parser.add_argument("--hpo", required=True, help="Patient HPO term file")
    parser.add_argument(
        "--reference-dir",
        required=True,
        help="Directory containing miniature reference CSV files",
    )
    parser.add_argument("--output", required=True, help="Output CSV report path")
    return parser


def run(vcf: str, hpo: str, reference_dir: str, output: str) -> list[str]:
    variants = read_vcf(vcf)
    patient_hpo_terms = read_patient_hpo(hpo)
    references = load_reference_data(reference_dir)
    annotated = annotate_variants(variants, references, patient_hpo_terms)
    ranked = rank_variants(annotated)
    write_csv_report(ranked, output)
    return [variant.variant.key for variant in ranked]


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    ranked_keys = run(args.vcf, args.hpo, args.reference_dir, args.output)
    print(f"Wrote {len(ranked_keys)} prioritized variants to {Path(args.output)}")


if __name__ == "__main__":
    main()

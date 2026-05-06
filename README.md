# Pediatric Variant Prioritizer

A rare-disease genomics project for prioritizing candidate variants from a
patient VCF and phenotype terms.

This repository is designed as a portfolio project for clinical genomics,
bioinformatics, and ML-adjacent roles. The first milestone is a transparent
rules-based ranking pipeline. The next milestone is to train a supervised
ranking model using the same feature table produced by the pipeline.

## Problem

Clinical sequencing often returns many variants for one patient. The practical
question is: which variants deserve review first?

This project combines:

- VCF parsing
- variant annotation
- allele-frequency filtering
- ClinVar-style clinical significance
- HPO phenotype matching
- evidence-based prioritization
- report generation for review

## Quick Start

If you are new to genomics, start with:

- `docs/beginner_guide.md`

Run the example prioritization workflow:

```bash
PYTHONPATH=src python3 -m pediatric_variant_prioritizer.cli \
  --vcf data/example/patient.vcf \
  --hpo data/example/patient_hpo.txt \
  --reference-dir data/reference \
  --output results/prioritized_variants.csv
```

Run tests:

```bash
PYTHONPATH=src python3 -m unittest
```

Build the visual dashboard from the generated CSV:

```bash
python3 scripts/build_dashboard.py
```

Then open `dashboard/index.html` in a browser.

## Current Pipeline

1. Parse a small VCF file with gene, consequence, and zygosity fields.
2. Join reference annotations from miniature ClinVar, gnomAD, and HPO-style
   tables.
3. Create interpretable features for each variant.
4. Rank variants by rarity, predicted molecular impact, known clinical
   significance, and phenotype-gene overlap.
5. Write a clinician-readable CSV report with evidence fields.

## ML Roadmap

The scoring system is intentionally modular. A supervised model can replace or
augment `score_variant` once training labels are available.

Good next steps:

- Build a labeled training set from ClinVar pathogenic and benign variants.
- Generate feature rows for each variant: consequence weight, allele frequency,
  phenotype match count, ClinVar label, and gene-disease evidence.
- Train a baseline logistic regression or gradient boosting model.
- Compare model ranking against the transparent rules baseline.
- Add SHAP or permutation importance for model explanations.

## Project Shape

```text
src/pediatric_variant_prioritizer/
  annotation.py   Load reference tables and annotate variants
  cli.py          Command-line interface
  models.py       Shared dataclasses
  report.py       CSV report writer
  scoring.py      Transparent evidence-based ranking
  vcf.py          Minimal VCF parser

data/example/     Tiny synthetic patient data
data/reference/   Tiny reference annotation tables
tests/            Unit tests
```

## Notes

The example data is synthetic and intentionally small. It is suitable for
testing the pipeline shape, not for clinical use.

# Pediatric Variant Prioritizer

[![Tests](https://github.com/dlamanna10/pediatric-variant-prioritizer/actions/workflows/tests.yml/badge.svg)](https://github.com/dlamanna10/pediatric-variant-prioritizer/actions/workflows/tests.yml)

An educational clinical-genomics pipeline that prioritizes rare-disease candidate
variants from a patient VCF, phenotype terms, and lightweight annotation tables.

![Dashboard preview](docs/assets/dashboard.png)

## Why This Matters

Clinical sequencing can return many genetic variants for one patient. Most are
benign or unrelated to the patient's symptoms. This project demonstrates how a
bioinformatics workflow can combine variant-level evidence, population
frequency, clinical significance, and phenotype matching to rank variants for
review.

The current version uses transparent evidence scoring rather than a trained ML
model. That makes the reasoning inspectable and creates a clean baseline for a
future supervised variant-ranking model.

## What It Does

- Parses a small VCF file containing candidate variants.
- Loads patient phenotype terms encoded as HPO IDs.
- Joins ClinVar-style, gnomAD-style, and gene-phenotype reference annotations.
- Scores variants using rarity, predicted molecular consequence, clinical
  significance, HPO overlap, and zygosity.
- Generates a ranked CSV report with plain-language evidence.
- Builds a self-contained HTML dashboard for visual review.
- Includes a reproducible public-data subset built from ClinVar and HPO.

## Dashboard

The dashboard in `dashboard/index.html` shows:

- summary metrics for the ranked variant set
- the pipeline flow from VCF to report
- score bars by candidate gene
- a clickable ranked variant table
- evidence details for each selected variant

Build or rebuild it after generating `results/prioritized_variants.csv`:

```bash
python3 scripts/build_dashboard.py \
  --input results/prioritized_variants.csv \
  --output dashboard/index.html \
  --predictions results/baseline_predictions.csv \
  --model-metrics results/baseline_model.json
```

Then open `dashboard/index.html` in a browser.

## Public ClinVar/HPO Data Workflow

The repository includes a small real public-data subset under `data/public/`.
It is generated from:

- ClinVar GRCh38 VCF
- HPO `genes_to_phenotype.txt`

Rebuild the public subset:

```bash
python3 scripts/build_public_clinvar_dataset.py
```

Run the pipeline on the public subset:

```bash
PYTHONPATH=src python3 -m pediatric_variant_prioritizer.cli \
  --vcf data/public/clinvar_variants.vcf \
  --hpo data/public/patient_hpo.txt \
  --reference-dir data/public/reference \
  --output results/public_prioritized_variants.csv \
  --features-output results/public_variant_features.csv
```

Build a public-data dashboard:

```bash
python3 scripts/build_dashboard.py \
  --input results/public_prioritized_variants.csv \
  --output dashboard/public.html
```

The public subset uses real ClinVar variants and real HPO gene-phenotype
annotations. The patient HPO profile is still synthetic and is assembled from
public HPO terms for demonstration.

## Baseline ML Model

After exporting `results/variant_features.csv`, train the small dependency-free
baseline model:

```bash
PYTHONPATH=src python3 -m pediatric_variant_prioritizer.ml_baseline \
  --features results/variant_features.csv \
  --labels data/example/variant_labels.csv \
  --model-output results/baseline_model.json \
  --predictions-output results/baseline_predictions.csv
```

The labels in `data/example/variant_labels.csv` are synthetic and exist only to
demonstrate the machine-learning workflow. They should not be interpreted as
clinical truth.

Baseline ML outputs:

- `results/baseline_predictions.csv`: per-variant predicted probabilities
- `results/baseline_model.json`: model coefficients and evaluation metrics
- `dashboard/index.html`: visual overlay of baseline ML probabilities and
  leave-one-out accuracy

Current demo metrics:

- training accuracy: `1.000`
- leave-one-out accuracy: `0.750`

These metrics are only a smoke test of the workflow because the label set is
tiny and synthetic.

## Quick Start

Run the example prioritization workflow:

```bash
PYTHONPATH=src python3 -m pediatric_variant_prioritizer.cli \
  --vcf data/example/patient.vcf \
  --hpo data/example/patient_hpo.txt \
  --reference-dir data/reference \
  --output results/prioritized_variants.csv \
  --features-output results/variant_features.csv
```

Run tests:

```bash
PYTHONPATH=src python3 -m unittest
```

If you are new to genomics, start with:

- `docs/beginner_guide.md`

## Example Output

The synthetic demo ranks `TSC2` first because it combines several high-priority
signals:

- very rare gnomAD-style allele frequency
- high-impact `stop_gained` consequence
- `likely_pathogenic` clinical significance
- two HPO phenotype matches
- homozygous zygosity in the simplified example data

The generated report is written to:

```text
results/prioritized_variants.csv
```

Generated result files are intentionally ignored by git so the workflow can be
rerun without committing local outputs.

## ML-Ready Feature Table

The optional `--features-output` argument writes one feature row per ranked
variant. This table is designed as the next step toward supervised modeling.

Example columns include:

- `allele_frequency`
- `rarity_score`
- `consequence_score`
- `clinvar_score`
- `phenotype_match_count`
- `phenotype_match_score`
- `is_homozygous`
- `total_evidence_score`

The current table does not claim clinical labels. It prepares structured inputs
that a future model can learn from once a labeled training set is added.

## Technical Highlights

- Python package layout under `src/`
- standard-library VCF parsing for the demo format
- dataclass-based domain models
- CSV annotation joins
- ML-ready feature table export
- dependency-free logistic baseline model
- transparent evidence-based scoring
- reproducible CLI workflow
- self-contained HTML/CSS/JavaScript dashboard
- unit tests with `unittest`

## Project Structure

```text
src/pediatric_variant_prioritizer/
  annotation.py   Load reference tables and annotate variants
  cli.py          Command-line interface
  features.py     ML-ready feature table export
  ml_baseline.py  Dependency-free baseline ML model
  models.py       Shared dataclasses
  report.py       CSV report writer
  scoring.py      Transparent evidence-based ranking
  vcf.py          Minimal VCF parser

data/example/     Synthetic patient VCF and HPO terms
data/public/      Small public ClinVar/HPO-derived subset
data/reference/   Miniature ClinVar/gnomAD/HPO-style annotation tables
dashboard/        Self-contained visual dashboard
docs/             Beginner guide and README assets
scripts/          Dashboard generator
tests/            Unit tests
```

## Roadmap

- Add real gnomAD allele-frequency annotation to the public workflow.
- Expand the baseline model beyond the tiny synthetic label set.
- Add support for VEP or SnpEff annotated VCFs.
- Add richer model evaluation reports and feature-importance summaries.
- Add public-derived labels or a larger benchmark dataset for model training.

## Disclaimer

This project is for education and portfolio demonstration only. It is not a
medical device, not validated clinical decision support, and not suitable for
diagnosis or patient care.

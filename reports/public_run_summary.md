# Public Run Summary

This report summarizes the public ClinVar/HPO workflow output. It is educational and not clinical decision support.

## Dataset

- Variants analyzed: 12
- Genes represented: CFTR, FBN1, SCN1A, TSC2
- Variant source: ClinVar GRCh38 VCF subset
- Phenotype source: HPO genes_to_phenotype subset
- Patient profile: synthetic HPO terms assembled from public HPO annotations

## Top Ranked Variants

| Rank | Gene | Variant | Score | ClinVar label | HPO matches | ML probability |
| --- | --- | --- | ---: | --- | --- | ---: |
| 1 | SCN1A | `2-165991366-G-GTAAT` | 74.0 | pathogenic | HP:0007270\|HP:0025190 | 0.991288 |
| 2 | SCN1A | `2-165991479-CT-C` | 74.0 | pathogenic | HP:0007270\|HP:0025190 | 0.991288 |
| 3 | TSC2 | `16-2048626-CA-C` | 74.0 | pathogenic | HP:0002465\|HP:0003774 | 0.991288 |
| 4 | TSC2 | `16-2048629-C-CA` | 74.0 | pathogenic | HP:0002465\|HP:0003774 | 0.991288 |
| 5 | CFTR | `7-117480081-GCGCCCGAGAGACCATGCAGAGGT-G` | 58.0 | pathogenic | none | 0.993315 |

## Interpretation

The top-ranked variant is `2-165991366-G-GTAAT` in **SCN1A** with an evidence score of **74.0**.
It ranks highly because: missing population frequency adds 5 | frameshift_variant consequence adds 18 | ClinVar-like significance pathogenic adds 35 | 2 phenotype match(es) add 16.
The baseline ML probability for this variant is **0.991288**.

The evidence score and ML probability answer related but different questions. The evidence score is transparent and rule-based. The ML probability is learned from the exported feature table and ClinVar-derived labels.

## Baseline ML Metrics

- Accuracy: 1.000
- Precision: 1.000
- Recall: 1.000
- F1: 1.000
- AUROC: 1.000
- Leave-one-out accuracy: 1.000

These metrics are from a small public-derived subset and should be treated as workflow checks, not generalizable clinical performance.

## Top Feature Importance

| Feature | Coefficient | Direction |
| --- | ---: | --- |
| `is_pathogenic_or_likely_pathogenic` | 1.088 | positive |
| `is_benign_or_likely_benign` | -1.088 | negative |
| `clinvar_score` | 1.088 | positive |
| `consequence_score` | 0.870 | positive |
| `rarity_score` | -0.466 | negative |
| `phenotype_match_count` | -0.067 | negative |

## Limitations

- The patient HPO profile is synthetic.
- The public dataset is intentionally small.
- Population frequencies are limited to ClinVar embedded public AF fields unless an override file is supplied.
- The model is dependency-free and useful for demonstrating workflow shape, not clinical deployment.
- A production workflow would need validated annotation tools, versioned references, broader evaluation, and clinical review.

## Source Notes

# Public Data Subset

This directory contains a small reproducible subset built from public
ClinVar and HPO downloads. It is for educational demonstration only.

## Sources

- ClinVar GRCh38 VCF: https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh38/clinvar.vcf.gz
- HPO genes_to_phenotype: http://purl.obolibrary.org/obo/hp/hpoa/genes_to_phenotype.txt

## Included Genes

SCN1A, CFTR, FBN1, TSC2

## Generated Files

- clinvar_variants.vcf: public ClinVar variants transformed into the
  project demo VCF shape
- patient_hpo.txt: synthetic patient profile using HPO terms from the
  public HPO gene-phenotype annotations
- reference/clinvar_mini.csv: ClinVar clinical significance and
  condition fields for the selected variants
- reference/gene_phenotype_mini.csv: HPO gene-phenotype rows for the
  selected genes
- reference/gnomad_mini.csv: population allele frequencies from
  ClinVar's embedded AF_EXAC, AF_TGP, or AF_ESP fields when present
- variant_labels.csv: public ClinVar-derived labels for the
  baseline ML workflow

Selected variants: 12
Selected gene-phenotype rows: 24
Synthetic patient HPO terms: HP:0025190, HP:0007270, HP:0002465, HP:0003774

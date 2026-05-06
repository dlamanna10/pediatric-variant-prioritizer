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

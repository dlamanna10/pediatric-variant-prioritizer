---
output:
  html_document: default
  pdf_document: default
---
# Pediatric Variant Prioritizer: Beginner Guide

Generated for this project on May 5, 2026.

Important note: this project is educational. It is not a medical device, not
clinical decision support for real patients, and not a substitute for a clinical
geneticist, genetic counselor, or certified diagnostic laboratory.

## 1. What This Project Is Trying To Do

Imagine a child has symptoms that suggest a possible rare genetic disease. A
sequencing test may find thousands of genetic variants. Most variants are
harmless. A small number may be relevant to the child's symptoms.

This project answers a practical review question:

Which variants should a scientist or clinician look at first?

The project takes:

- a VCF file, which lists genetic variants
- HPO terms, which describe the patient's symptoms in standardized language
- small reference tables that mimic ClinVar, gnomAD, and gene-phenotype data

It produces:

- a ranked CSV report of candidate variants
- evidence explaining why each variant ranked where it did

The first version uses transparent rules instead of a trained ML model. That is
intentional. In clinical genomics, a simple understandable baseline is valuable
before adding machine learning.

## 2. The Big Picture Workflow

The pipeline has five stages.

1. Read the patient VCF.
2. Read the patient's HPO phenotype terms.
3. Annotate each variant with reference information.
4. Score each variant using interpretable evidence.
5. Write a ranked report.

In code, the flow is:

data/example/patient.vcf
  -> vcf.py
  -> annotation.py
  -> scoring.py
  -> report.py
  -> results/prioritized_variants.csv

## 3. Core Medical And Genomics Vocabulary

DNA: The molecule that stores genetic information.

Chromosome: A long package of DNA. Humans usually have 23 pairs of chromosomes.

Gene: A region of DNA that provides instructions for making a functional
product, often a protein.

Variant: A difference in DNA sequence compared with a reference genome.
MedlinePlus Genetics describes a gene variant as a permanent change in the DNA
sequence that makes up a gene. The older word "mutation" is still used, but
"variant" is often preferred because not every change causes disease.

Reference genome: A standard DNA sequence used as a coordinate system. A VCF
entry says where a variant occurs relative to this reference.

Nucleotide: One DNA letter: A, C, G, or T.

REF and ALT: In a VCF, REF is the reference allele and ALT is the alternate
allele observed in the sample.

Allele: A version of a DNA sequence at a position.

Genotype: The alleles a person has at a position.

Heterozygous, shown as het: The person has one reference copy and one alternate
copy at that position.

Homozygous, shown as hom: The person has two copies of the alternate allele at
that position in this simplified project.

Phenotype: An observable trait, sign, or symptom. Examples include seizure,
developmental delay, short stature, or abnormal heart structure.

HPO: Human Phenotype Ontology. HPO gives standardized identifiers for phenotype
terms. For example, HP:0001250 means seizure. This lets different databases and
tools talk about symptoms consistently.

Rare disease: A disease that affects a small number of people. Many rare
diseases are genetic, but not all genetic disease is rare and not all rare
disease is genetic.

## 4. Variant Consequence Terms

A variant consequence describes the predicted effect of a DNA change on a gene
or protein. Real projects often use tools such as Ensembl VEP or SnpEff to
predict these consequences.

missense_variant: A DNA substitution changes one amino acid in the protein. This
may matter or may be harmless.

synonymous_variant: A DNA change does not change the amino acid sequence of the
protein. These are often lower priority, though not always irrelevant.

frameshift_variant: An insertion or deletion changes the reading frame of the
protein. This can strongly disrupt the protein.

stop_gained: A variant creates an early stop signal. This can shorten the
protein and is often treated as high impact.

splice_acceptor_variant and splice_donor_variant: Variants near exon-intron
boundaries that may disrupt RNA splicing.

## 5. ClinVar-Style Significance Terms

ClinVar is an NCBI public archive that aggregates reports about human variants
and their relationships to health.

This project uses simplified ClinVar-like labels:

pathogenic: Evidence supports that the variant can cause disease.

likely_pathogenic: Evidence strongly suggests disease relevance, but may not be
as conclusive as pathogenic.

uncertain_significance: Often called VUS, or variant of uncertain significance.
There is not enough evidence to call it disease-causing or benign.

likely_benign: Evidence suggests the variant is probably not disease-causing.

benign: Evidence supports that the variant is not disease-causing.

Important interpretation rule: a VUS should not be treated as a diagnosis. In
real clinical genetics, VUS interpretation is cautious and usually requires more
evidence.

## 6. gnomAD And Allele Frequency

gnomAD is a large public resource of human genetic variation. It helps answer:

How common is this variant in broader populations?

Allele frequency is the fraction of observed alleles that carry the variant.

Examples:

- 0.12 means 12 percent. That is common.
- 0.01 means 1 percent.
- 0.0001 means 0.01 percent. That is rare.

Why rarity matters: many severe rare-disease-causing variants are uncommon in
general population datasets. If a variant is very common, it is less likely to
cause a severe rare pediatric disease by itself.

Important caveat: rarity alone does not prove pathogenicity. A rare variant can
still be harmless.

## 7. HPO Phenotype Matching

The patient example has this file:

data/example/patient_hpo.txt

It contains:

HP:0001250
HP:0001263
HP:0001629

In the miniature reference table, these correspond to phenotype concepts such
as seizure, global developmental delay, and ventricular septal defect.

The pipeline checks whether the gene connected to a variant has known phenotype
terms that overlap the patient's HPO terms.

Example:

- Patient has HP:0001250 and HP:0001263.
- TSC2 in the reference table is associated with those HPO terms.
- The TSC2 variant gets phenotype-match evidence.

## 8. Understanding The Input VCF

The example VCF is:

data/example/patient.vcf

VCF means Variant Call Format. A VCF is a common text format for genetic
variants. The important columns in this project are:

CHROM: Chromosome where the variant occurs.

POS: Position on that chromosome.

ID: Known variant identifier, if available. The example uses "." for missing.

REF: Reference allele.

ALT: Alternate allele found in the sample.

QUAL: Variant quality score. The example uses "." because this synthetic data
does not model sequencing quality.

FILTER: Whether the variant passed upstream filters.

INFO: Extra annotations. In this project, INFO includes GENE, CONSEQUENCE, and
ZYGOSITY.

Example row:

16  2097090  .  C  A  .  PASS  GENE=TSC2;CONSEQUENCE=stop_gained;ZYGOSITY=hom

Plain-English reading:

On chromosome 16 at position 2,097,090, the reference allele is C and the
alternate allele is A. This synthetic example says the variant is in TSC2,
causes a stop_gained consequence, and is homozygous.

## 9. Understanding The Reference Tables

data/reference/clinvar_mini.csv

This maps variant keys to simplified clinical significance and condition names.
Real work would use ClinVar downloads or annotation tools.

data/reference/gnomad_mini.csv

This maps variant keys to population allele frequencies. Real work would use
gnomAD annotations from a tool such as VEP, Hail, or bcftools plugins.

data/reference/gene_phenotype_mini.csv

This maps genes to HPO terms. Real work would use HPO annotation files,
OMIM/Orphanet/DECIPHER-derived resources, or tools such as Exomiser.

Variant key format:

chrom-pos-ref-alt

Example:

16-2097090-C-A

That key means chromosome 16, position 2,097,090, reference C, alternate A.

## 10. How The Scoring Works

The current score is a transparent heuristic. It is not trained machine
learning yet.

Each variant receives points for evidence:

Rarity:

- very rare variants get more points
- common variants lose points

Consequence:

- stop_gained and frameshift_variant get high impact points
- missense_variant gets moderate points
- synonymous_variant gets no impact points in this simple version

ClinVar-like significance:

- pathogenic and likely_pathogenic add points
- VUS adds fewer points
- benign and likely_benign subtract points

Phenotype match:

- each overlap between patient HPO terms and gene-associated HPO terms adds
  points, up to a cap

Zygosity:

- homozygous adds a small bonus in this simplified example

The key idea: the score is not magic. It is a structured summary of evidence.

## 11. Reading prioritized_variants.csv

The generated report is:

results/prioritized_variants.csv

Columns:

rank: The final order after scoring. Rank 1 is highest priority.

score: Total evidence score.

variant_key: Compact variant identifier using chrom-pos-ref-alt.

gene: Gene associated with the variant.

consequence: Predicted effect on the gene or protein.

zygosity: Whether the variant is heterozygous or homozygous in this simplified
example.

allele_frequency: Population frequency from the miniature gnomAD-like table.

clinical_significance: ClinVar-like label.

condition: Condition name associated with the variant in the miniature
ClinVar-like table.

matched_hpo_terms: Patient phenotype terms that overlap the gene's known
phenotype terms.

evidence: Plain-language reasons for the score.

## 12. Reading variant_features.csv

The optional ML-ready feature table is:

results/variant_features.csv

This file has one row per variant, but it is shaped for modeling instead of
human review.

Important columns:

allele_frequency: Population frequency as a numeric feature.

allele_frequency_missing: 1 if the frequency is missing, otherwise 0.

rarity_score: Numeric summary of how rare the variant is.

consequence_score: Numeric summary of predicted molecular impact.

clinvar_score: Numeric summary of the ClinVar-like significance label.

phenotype_match_count: Number of patient HPO terms that match the gene's known
phenotype terms.

phenotype_match_score: Numeric score derived from phenotype matches.

is_homozygous: 1 if the simplified zygosity field is homozygous, otherwise 0.

total_evidence_score: The final transparent score used for the current ranking.

This table is not a trained model. It is the structured input that a future
model could learn from once labels are available.

## 13. Why TSC2 Ranked First In The Example

The TSC2 row ranks first because it combines several strong signals:

- allele frequency is 0.00001, which is very rare
- consequence is stop_gained, a high-impact consequence
- clinical significance is likely_pathogenic
- the gene has two phenotype matches with the patient HPO terms
- zygosity is homozygous

That does not mean this synthetic example is a real diagnosis. It means the row
is a good candidate for review according to the evidence rules.

## 14. Where Machine Learning Fits

Right now, the project uses hand-written scoring rules. Machine learning can be
added once there is a labeled training dataset.

A future ML version could:

1. Convert each variant into a feature row.
2. Use labels such as pathogenic, benign, or candidate-positive.
3. Train a model such as logistic regression, random forest, or gradient
   boosting.
4. Compare the model against the transparent rules baseline.
5. Explain the model using feature importance or SHAP values.

Possible features:

- allele frequency
- consequence weight
- number of phenotype matches
- ClinVar significance
- zygosity
- gene-disease evidence strength
- inheritance-model compatibility

Good project story for interviews:

I first built a transparent clinical-genomics baseline. Then I used the same
feature table to train and evaluate an ML ranker, while keeping explanations
available for review.

## 15. What Would Make This More Real

The current project is a miniature educational version. Real clinical genomics
pipelines need much more.

Next upgrades:

- accept VCF annotations from Ensembl VEP or SnpEff
- add inheritance model logic using parents or family trios
- add gene-disease validity resources
- use full ClinVar and gnomAD data
- support copy number variants and structural variants
- add quality-control filters
- add a Streamlit dashboard
- train an ML model on a labeled dataset
- add citations and audit trails for every evidence item

## 16. Common Pitfalls

High score does not equal diagnosis.

Rare does not automatically mean harmful.

Common does not automatically mean harmless in every context, but common
variants are usually deprioritized for severe rare pediatric disease.

VUS means uncertain. It should not be overinterpreted.

Phenotype matching depends on how accurately symptoms are encoded.

Reference databases change over time. A real system needs version tracking.

Population frequency must be interpreted carefully because datasets may not
represent every ancestry equally.

## 17. Project File Map

README.md: Project overview and quick-start commands.

src/pediatric_variant_prioritizer/vcf.py: Reads the VCF.

src/pediatric_variant_prioritizer/annotation.py: Loads reference tables and
adds annotations to variants.

src/pediatric_variant_prioritizer/scoring.py: Assigns evidence-based scores.

src/pediatric_variant_prioritizer/features.py: Writes ML-ready feature rows.

src/pediatric_variant_prioritizer/report.py: Writes the output CSV.

src/pediatric_variant_prioritizer/cli.py: Command-line entry point.

data/example/patient.vcf: Synthetic patient variant file.

data/example/patient_hpo.txt: Synthetic patient phenotype terms.

data/reference/*.csv: Tiny reference tables for the first demo.

tests/test_pipeline.py: Tests that the pipeline runs and ranks expected
variants.

results/prioritized_variants.csv: Generated ranked report.

results/variant_features.csv: Generated ML-ready feature table.

## 18. Source References

ClinVar, NCBI:
https://www.ncbi.nlm.nih.gov/clinvar/

ClinVar clinical significance documentation:
https://www.ncbi.nlm.nih.gov/clinvar/docs/clinsig/

MedlinePlus Genetics, gene variants:
https://medlineplus.gov/genetics/understanding/mutationsanddisorders/genemutation/

MedlinePlus Genetics, inheritance patterns:
https://medlineplus.gov/genetics/understanding/inheritance/inheritancepatterns/

MedlinePlus Genetics, variant types:
https://medlineplus.gov/genetics/understanding/mutationsanddisorders/possiblemutations/

Ensembl Variant Effect Predictor:
https://www.ensembl.org/info/docs/tools/vep/index.html

gnomAD browser:
https://gnomad.broadinstitute.org/

Human Phenotype Ontology:
https://obophenotype.github.io/human-phenotype-ontology/

VCF specification repository:
https://github.com/samtools/hts-specs

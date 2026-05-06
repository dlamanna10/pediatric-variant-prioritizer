from pathlib import Path
import csv
import tempfile
import unittest

from pediatric_variant_prioritizer.cli import run
from pediatric_variant_prioritizer.ml_baseline import run as train_baseline
from pediatric_variant_prioritizer.scoring import rank_variants
from pediatric_variant_prioritizer.annotation import (
    annotate_variants,
    load_reference_data,
    read_patient_hpo,
)
from pediatric_variant_prioritizer.vcf import read_vcf


ROOT = Path(__file__).resolve().parents[1]


class PipelineTest(unittest.TestCase):
    def test_pipeline_ranks_pathogenic_phenotype_matched_variant_first(self) -> None:
        variants = read_vcf(ROOT / "data/example/patient.vcf")
        references = load_reference_data(ROOT / "data/reference")
        patient_hpo = read_patient_hpo(ROOT / "data/example/patient_hpo.txt")

        annotated = annotate_variants(variants, references, patient_hpo)
        ranked = rank_variants(annotated)

        self.assertEqual(ranked[0].variant.gene, "TSC2")
        self.assertGreater(ranked[0].score, ranked[-1].score)
        self.assertEqual(ranked[-1].variant.gene, "CFTR")

    def test_cli_writes_prioritized_csv(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "prioritized.csv"
            ranked_keys = run(
                str(ROOT / "data/example/patient.vcf"),
                str(ROOT / "data/example/patient_hpo.txt"),
                str(ROOT / "data/reference"),
                str(output),
            )

            self.assertTrue(output.exists())
            self.assertEqual(len(ranked_keys), 4)

            with output.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))

            self.assertEqual(rows[0]["gene"], "TSC2")
            self.assertEqual(rows[0]["rank"], "1")

    def test_cli_can_write_ml_ready_feature_table(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "prioritized.csv"
            features_output = Path(temp_dir) / "variant_features.csv"

            run(
                str(ROOT / "data/example/patient.vcf"),
                str(ROOT / "data/example/patient_hpo.txt"),
                str(ROOT / "data/reference"),
                str(output),
                str(features_output),
            )

            self.assertTrue(features_output.exists())

            with features_output.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))

            self.assertEqual(len(rows), 4)
            self.assertEqual(rows[0]["gene"], "TSC2")
            self.assertEqual(rows[0]["phenotype_match_count"], "2")
            self.assertEqual(rows[0]["is_homozygous"], "1")
            self.assertEqual(rows[-1]["gene"], "CFTR")
            self.assertEqual(rows[-1]["is_benign_or_likely_benign"], "1")

    def test_baseline_model_trains_from_feature_table_and_labels(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "prioritized.csv"
            features_output = Path(temp_dir) / "variant_features.csv"
            model_output = Path(temp_dir) / "baseline_model.json"
            predictions_output = Path(temp_dir) / "baseline_predictions.csv"

            run(
                str(ROOT / "data/example/patient.vcf"),
                str(ROOT / "data/example/patient_hpo.txt"),
                str(ROOT / "data/reference"),
                str(output),
                str(features_output),
            )
            result = train_baseline(
                str(features_output),
                str(ROOT / "data/example/variant_labels.csv"),
                str(model_output),
                str(predictions_output),
            )

            self.assertTrue(model_output.exists())
            self.assertTrue(predictions_output.exists())
            self.assertEqual(len(result.predictions), 4)
            self.assertGreaterEqual(result.training_accuracy, 0.75)

            probabilities = {
                row["variant_key"]: row["predicted_probability"]
                for row in result.predictions
            }
            self.assertGreater(
                probabilities["16-2097090-C-A"],
                probabilities["7-117559593-C-T"],
            )

    def test_public_clinvar_hpo_subset_runs_through_pipeline(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "public_prioritized.csv"
            features_output = Path(temp_dir) / "public_features.csv"

            ranked_keys = run(
                str(ROOT / "data/public/clinvar_variants.vcf"),
                str(ROOT / "data/public/patient_hpo.txt"),
                str(ROOT / "data/public/reference"),
                str(output),
                str(features_output),
            )

            self.assertEqual(len(ranked_keys), 8)

            with output.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))

            self.assertEqual(rows[0]["gene"], "TSC2")
            self.assertEqual(rows[0]["clinical_significance"], "pathogenic")
            self.assertIn("HP:0002465", rows[0]["matched_hpo_terms"])

            with features_output.open(encoding="utf-8", newline="") as handle:
                feature_rows = list(csv.DictReader(handle))

            self.assertEqual(feature_rows[0]["allele_frequency_missing"], "1")


if __name__ == "__main__":
    unittest.main()

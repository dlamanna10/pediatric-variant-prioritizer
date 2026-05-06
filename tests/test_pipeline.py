from pathlib import Path
import csv
import tempfile
import unittest

from pediatric_variant_prioritizer.cli import run
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


if __name__ == "__main__":
    unittest.main()

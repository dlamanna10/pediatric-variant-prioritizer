"""Run the public ClinVar/HPO workflow end to end."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the public workflow end to end.")
    parser.add_argument(
        "--refresh-public-data",
        action="store_true",
        help="Download and rebuild the public ClinVar/HPO subset before running.",
    )
    parser.add_argument(
        "--frequency-overrides",
        help="Optional gnomAD-style CSV with variant_key and allele_frequency columns.",
    )
    args = parser.parse_args()

    env = os.environ.copy()
    env["PYTHONPATH"] = "src"

    if args.refresh_public_data:
        command = [sys.executable, "scripts/build_public_clinvar_dataset.py"]
        if args.frequency_overrides:
            command.extend(["--frequency-overrides", args.frequency_overrides])
        run(command, env)

    run(
        [
            sys.executable,
            "-m",
            "pediatric_variant_prioritizer.cli",
            "--vcf",
            "data/public/clinvar_variants.vcf",
            "--hpo",
            "data/public/patient_hpo.txt",
            "--reference-dir",
            "data/public/reference",
            "--output",
            "results/public_prioritized_variants.csv",
            "--features-output",
            "results/public_variant_features.csv",
        ],
        env,
    )
    run(
        [
            sys.executable,
            "-m",
            "pediatric_variant_prioritizer.ml_baseline",
            "--features",
            "results/public_variant_features.csv",
            "--labels",
            "data/public/variant_labels.csv",
            "--model-output",
            "results/public_baseline_model.json",
            "--predictions-output",
            "results/public_baseline_predictions.csv",
            "--importance-output",
            "results/public_baseline_feature_importance.csv",
        ],
        env,
    )
    run(
        [
            sys.executable,
            "scripts/build_dashboard.py",
            "--input",
            "results/public_prioritized_variants.csv",
            "--output",
            "dashboard/public.html",
            "--predictions",
            "results/public_baseline_predictions.csv",
            "--model-metrics",
            "results/public_baseline_model.json",
        ],
        env,
    )
    run([sys.executable, "scripts/build_public_run_report.py"], env)


def run(command: list[str], env: dict[str, str]) -> None:
    print("$ " + " ".join(command))
    subprocess.run(command, cwd=ROOT, env=env, check=True)


if __name__ == "__main__":
    main()

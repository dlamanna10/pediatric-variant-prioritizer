"""Small dependency-free baseline model for ML workflow demonstration."""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path


DEFAULT_FEATURES = [
    "rarity_score",
    "consequence_score",
    "clinvar_score",
    "phenotype_match_count",
    "phenotype_match_score",
    "is_homozygous",
    "is_pathogenic_or_likely_pathogenic",
    "is_benign_or_likely_benign",
    "is_uncertain_significance",
]


@dataclass(frozen=True)
class LogisticModel:
    feature_names: list[str]
    means: list[float]
    scales: list[float]
    coefficients: list[float]
    intercept: float


@dataclass(frozen=True)
class TrainingResult:
    model: LogisticModel
    training_accuracy: float
    leave_one_out_accuracy: float
    metrics: dict[str, float | int]
    predictions: list[dict[str, str | float | int]]
    feature_importance: list[dict[str, str | float]]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Train a tiny logistic baseline from exported variant features."
    )
    parser.add_argument("--features", required=True, help="ML-ready feature CSV")
    parser.add_argument("--labels", required=True, help="Variant labels CSV")
    parser.add_argument("--model-output", required=True, help="Output model JSON path")
    parser.add_argument(
        "--predictions-output",
        required=True,
        help="Output prediction CSV path",
    )
    parser.add_argument(
        "--importance-output",
        help="Optional output feature-importance CSV path",
    )
    return parser


def run(
    features: str,
    labels: str,
    model_output: str,
    predictions_output: str,
    importance_output: str | None = None,
) -> TrainingResult:
    feature_rows = _read_csv(Path(features))
    label_rows = _read_csv(Path(labels))
    variant_keys, matrix, targets = _build_training_matrix(feature_rows, label_rows)

    model = train_logistic_regression(matrix, targets, DEFAULT_FEATURES)
    probabilities = [predict_probability(model, row) for row in matrix]
    predictions = _prediction_rows(variant_keys, targets, probabilities)
    metrics = calculate_classification_metrics(targets, probabilities)
    training_accuracy = float(metrics["accuracy"])
    leave_one_out_accuracy = _leave_one_out_accuracy(matrix, targets)
    feature_importance = calculate_feature_importance(model)

    result = TrainingResult(
        model=model,
        training_accuracy=training_accuracy,
        leave_one_out_accuracy=leave_one_out_accuracy,
        metrics=metrics,
        predictions=predictions,
        feature_importance=feature_importance,
    )
    _write_model_json(result, Path(model_output))
    _write_predictions(predictions, Path(predictions_output))
    if importance_output:
        _write_feature_importance(feature_importance, Path(importance_output))
    return result


def train_logistic_regression(
    matrix: list[list[float]],
    targets: list[int],
    feature_names: list[str],
    learning_rate: float = 0.2,
    iterations: int = 4000,
    l2_penalty: float = 0.01,
) -> LogisticModel:
    means, scales = _fit_standardizer(matrix)
    standardized = [_standardize(row, means, scales) for row in matrix]
    coefficients = [0.0 for _ in feature_names]
    intercept = 0.0
    sample_count = len(targets)

    for _ in range(iterations):
        gradients = [0.0 for _ in coefficients]
        intercept_gradient = 0.0
        for row, target in zip(standardized, targets):
            probability = _sigmoid(intercept + _dot(coefficients, row))
            error = probability - target
            intercept_gradient += error
            for index, value in enumerate(row):
                gradients[index] += error * value

        intercept -= learning_rate * intercept_gradient / sample_count
        for index in range(len(coefficients)):
            gradient = gradients[index] / sample_count + l2_penalty * coefficients[index]
            coefficients[index] -= learning_rate * gradient

    return LogisticModel(
        feature_names=feature_names,
        means=means,
        scales=scales,
        coefficients=coefficients,
        intercept=intercept,
    )


def predict_probability(model: LogisticModel, row: list[float]) -> float:
    standardized = _standardize(row, model.means, model.scales)
    return _sigmoid(model.intercept + _dot(model.coefficients, standardized))


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    result = run(
        args.features,
        args.labels,
        args.model_output,
        args.predictions_output,
        args.importance_output,
    )
    print(f"Training accuracy: {result.training_accuracy:.3f}")
    print(f"Leave-one-out accuracy: {result.leave_one_out_accuracy:.3f}")
    print(f"Precision: {result.metrics['precision']:.3f}")
    print(f"Recall: {result.metrics['recall']:.3f}")
    print(f"F1: {result.metrics['f1']:.3f}")
    print(f"AUROC: {result.metrics['auroc']:.3f}")
    print(f"Wrote model to {Path(args.model_output)}")
    print(f"Wrote predictions to {Path(args.predictions_output)}")
    if args.importance_output:
        print(f"Wrote feature importance to {Path(args.importance_output)}")


def calculate_feature_importance(
    model: LogisticModel,
) -> list[dict[str, str | float]]:
    rows: list[dict[str, str | float]] = []
    for feature_name, coefficient in zip(model.feature_names, model.coefficients):
        rows.append(
            {
                "feature": feature_name,
                "coefficient": coefficient,
                "absolute_coefficient": abs(coefficient),
                "direction": "positive" if coefficient >= 0 else "negative",
            }
        )
    return sorted(
        rows,
        key=lambda row: float(row["absolute_coefficient"]),
        reverse=True,
    )


def calculate_classification_metrics(
    targets: list[int],
    probabilities: list[float],
) -> dict[str, float | int]:
    true_positive = true_negative = false_positive = false_negative = 0
    for target, probability in zip(targets, probabilities):
        predicted = int(probability >= 0.5)
        if target == 1 and predicted == 1:
            true_positive += 1
        elif target == 0 and predicted == 0:
            true_negative += 1
        elif target == 0 and predicted == 1:
            false_positive += 1
        elif target == 1 and predicted == 0:
            false_negative += 1

    total = len(targets)
    accuracy = (true_positive + true_negative) / total if total else 0.0
    precision_denominator = true_positive + false_positive
    recall_denominator = true_positive + false_negative
    precision = (
        true_positive / precision_denominator
        if precision_denominator
        else 0.0
    )
    recall = (
        true_positive / recall_denominator
        if recall_denominator
        else 0.0
    )
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )
    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "auroc": calculate_auroc(targets, probabilities),
        "true_positive": true_positive,
        "true_negative": true_negative,
        "false_positive": false_positive,
        "false_negative": false_negative,
    }


def calculate_auroc(targets: list[int], probabilities: list[float]) -> float:
    positive_scores = [
        probability
        for target, probability in zip(targets, probabilities)
        if target == 1
    ]
    negative_scores = [
        probability
        for target, probability in zip(targets, probabilities)
        if target == 0
    ]
    if not positive_scores or not negative_scores:
        return 0.0

    wins = 0.0
    comparisons = 0
    for positive_score in positive_scores:
        for negative_score in negative_scores:
            comparisons += 1
            if positive_score > negative_score:
                wins += 1
            elif positive_score == negative_score:
                wins += 0.5
    return wins / comparisons


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _build_training_matrix(
    feature_rows: list[dict[str, str]],
    label_rows: list[dict[str, str]],
) -> tuple[list[str], list[list[float]], list[int]]:
    labels_by_key = {
        row["variant_key"]: int(row["candidate_label"])
        for row in label_rows
    }
    variant_keys: list[str] = []
    matrix: list[list[float]] = []
    targets: list[int] = []

    for row in feature_rows:
        variant_key = row["variant_key"]
        if variant_key not in labels_by_key:
            continue
        variant_keys.append(variant_key)
        matrix.append([_to_float(row[name]) for name in DEFAULT_FEATURES])
        targets.append(labels_by_key[variant_key])

    if len(set(targets)) < 2:
        raise ValueError("Training labels must include at least one positive and negative")
    if not matrix:
        raise ValueError("No feature rows matched labels")
    return variant_keys, matrix, targets


def _prediction_rows(
    variant_keys: list[str],
    targets: list[int],
    probabilities: list[float],
) -> list[dict[str, str | float | int]]:
    rows: list[dict[str, str | float | int]] = []
    for variant_key, target, probability in zip(variant_keys, targets, probabilities):
        rows.append(
            {
                "variant_key": variant_key,
                "candidate_label": target,
                "predicted_probability": round(probability, 6),
                "predicted_label": int(probability >= 0.5),
            }
        )
    return rows


def _leave_one_out_accuracy(matrix: list[list[float]], targets: list[int]) -> float:
    probabilities: list[float] = []
    held_out_targets: list[int] = []
    for index in range(len(targets)):
        train_matrix = matrix[:index] + matrix[index + 1 :]
        train_targets = targets[:index] + targets[index + 1 :]
        if len(set(train_targets)) < 2:
            continue
        model = train_logistic_regression(train_matrix, train_targets, DEFAULT_FEATURES)
        probabilities.append(predict_probability(model, matrix[index]))
        held_out_targets.append(targets[index])
    if not held_out_targets:
        return 0.0
    return _accuracy(held_out_targets, probabilities)


def _accuracy(targets: list[int], probabilities: list[float]) -> float:
    correct = 0
    for target, probability in zip(targets, probabilities):
        predicted = int(probability >= 0.5)
        correct += int(predicted == target)
    return correct / len(targets)


def _write_model_json(result: TrainingResult, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "model_type": "standardized_logistic_regression",
        "feature_names": result.model.feature_names,
        "means": result.model.means,
        "scales": result.model.scales,
        "coefficients": result.model.coefficients,
        "intercept": result.model.intercept,
        "training_accuracy": result.training_accuracy,
        "leave_one_out_accuracy": result.leave_one_out_accuracy,
        "metrics": result.metrics,
        "feature_importance": result.feature_importance,
        "label_note": "Synthetic labels for workflow demonstration only",
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_predictions(
    rows: list[dict[str, str | float | int]],
    path: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "variant_key",
        "candidate_label",
        "predicted_probability",
        "predicted_label",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_feature_importance(
    rows: list[dict[str, str | float]],
    path: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "feature",
        "coefficient",
        "absolute_coefficient",
        "direction",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _fit_standardizer(matrix: list[list[float]]) -> tuple[list[float], list[float]]:
    columns = list(zip(*matrix))
    means = [sum(column) / len(column) for column in columns]
    scales: list[float] = []
    for mean, column in zip(means, columns):
        variance = sum((value - mean) ** 2 for value in column) / len(column)
        scale = math.sqrt(variance)
        scales.append(scale if scale > 0 else 1.0)
    return means, scales


def _standardize(row: list[float], means: list[float], scales: list[float]) -> list[float]:
    return [
        (value - mean) / scale
        for value, mean, scale in zip(row, means, scales)
    ]


def _dot(left: list[float], right: list[float]) -> float:
    return sum(left_value * right_value for left_value, right_value in zip(left, right))


def _sigmoid(value: float) -> float:
    if value >= 0:
        return 1 / (1 + math.exp(-value))
    exp_value = math.exp(value)
    return exp_value / (1 + exp_value)


def _to_float(value: str) -> float:
    if value == "":
        return 0.0
    return float(value)


if __name__ == "__main__":
    main()

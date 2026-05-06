"""Minimal VCF parsing for the portfolio pipeline.

The parser expects INFO fields for GENE, CONSEQUENCE, and ZYGOSITY. Real
production workflows would usually consume VEP, SnpEff, or bcftools output.
"""

from __future__ import annotations

from pathlib import Path

from .models import Variant


def parse_info(info: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for item in info.split(";"):
        if not item:
            continue
        if "=" in item:
            key, value = item.split("=", 1)
            fields[key] = value
        else:
            fields[item] = "true"
    return fields


def read_vcf(path: str | Path) -> list[Variant]:
    variants: list[Variant] = []
    with Path(path).open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            chrom, pos, _variant_id, ref, alt, *_rest = line.split("\t")
            info = _rest[2] if len(_rest) >= 3 else ""
            parsed_info = parse_info(info)
            variants.append(
                Variant(
                    chrom=chrom,
                    pos=int(pos),
                    ref=ref,
                    alt=alt,
                    gene=parsed_info.get("GENE", "UNKNOWN"),
                    consequence=parsed_info.get("CONSEQUENCE", "unknown"),
                    zygosity=parsed_info.get("ZYGOSITY", "unknown"),
                )
            )
    return variants

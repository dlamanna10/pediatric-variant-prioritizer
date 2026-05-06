"""Minimal VCF parsing for the portfolio pipeline.

The parser accepts the simple project INFO fields GENE, CONSEQUENCE, and
ZYGOSITY. It also has lightweight fallback support for common VEP CSQ and SnpEff
ANN annotations, which makes the pipeline easier to connect to real annotation
tools without adding dependencies.
"""

from __future__ import annotations

from pathlib import Path

from .models import Variant


CONSEQUENCE_PRIORITY = [
    "stop_gained",
    "frameshift_variant",
    "splice_acceptor_variant",
    "splice_donor_variant",
    "missense_variant",
    "synonymous_variant",
]


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


def parse_gene_and_consequence(parsed_info: dict[str, str], alt: str) -> tuple[str, str]:
    gene = parsed_info.get("GENE", "")
    consequence = parsed_info.get("CONSEQUENCE", "")
    if gene and consequence:
        return gene, consequence

    if parsed_info.get("ANN"):
        ann_gene, ann_consequence = parse_ann(parsed_info["ANN"], alt)
        gene = gene or ann_gene
        consequence = consequence or ann_consequence

    if parsed_info.get("CSQ"):
        csq_gene, csq_consequence = parse_csq(parsed_info["CSQ"], alt)
        gene = gene or csq_gene
        consequence = consequence or csq_consequence

    return gene or "UNKNOWN", consequence or "unknown"


def parse_ann(annotation: str, alt: str) -> tuple[str, str]:
    for record in annotation.split(","):
        fields = record.split("|")
        if len(fields) < 4:
            continue
        if fields[0] != alt:
            continue
        return fields[3] or "UNKNOWN", choose_consequence(fields[1])
    return "", ""


def parse_csq(annotation: str, alt: str) -> tuple[str, str]:
    for record in annotation.split(","):
        fields = record.split("|")
        if len(fields) < 4:
            continue
        if fields[0] != alt:
            continue
        return fields[3] or "UNKNOWN", choose_consequence(fields[1])
    return "", ""


def choose_consequence(raw_consequence: str) -> str:
    consequences = raw_consequence.replace("&", "|").split("|")
    for consequence in CONSEQUENCE_PRIORITY:
        if consequence in consequences:
            return consequence
    return consequences[0] if consequences and consequences[0] else "unknown"


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
            gene, consequence = parse_gene_and_consequence(parsed_info, alt)
            variants.append(
                Variant(
                    chrom=chrom,
                    pos=int(pos),
                    ref=ref,
                    alt=alt,
                    gene=gene,
                    consequence=consequence,
                    zygosity=parsed_info.get("ZYGOSITY", "unknown"),
                )
            )
    return variants

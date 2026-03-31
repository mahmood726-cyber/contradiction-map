# -*- coding: utf-8 -*-
"""ContradictionMap — detect contradictory conclusions across Cochrane meta-analyses.

Pipeline:
  Phase 1: Build study-MA membership matrix from Pairwise70 .rda files
  Phase 2: Find MA pairs from DIFFERENT reviews sharing >=2 studies
  Phase 3: Classify contradictions (direct / significance / magnitude)
  Phase 4: Compute corpus statistics and export results

Usage:
  python detect_contradictions.py                   # full 501 reviews
  python detect_contradictions.py --max-reviews 100 # dev mode
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from itertools import combinations
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

# Import MetaAudit's loader and recompute engine
sys.path.insert(0, "C:/MetaAudit")
from metaaudit.loader import (  # noqa: E402
    DataType,
    load_all_reviews,
    load_rda_file,
    split_by_analysis,
)
from metaaudit.recompute import recompute_ma  # noqa: E402

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PAIRWISE70_DIR = Path(r"C:\Users\user\OneDrive - NHS\Documents\Pairwise70\data")
OUTPUT_DIR = Path(r"C:\Models\ContradictionMap")
DATA_DIR = OUTPUT_DIR / "data"
RESULTS_DIR = OUTPUT_DIR / "results"
AUDIT_RESULTS_PATH = Path(r"C:\MetaAudit\results\audit_results.json")

SEED = 42
np.random.seed(SEED)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def normalize_study_name(name: str) -> str:
    """Normalize study names for cross-review matching.

    Strips whitespace, lowercases, collapses multiple spaces.
    """
    s = str(name).strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def extract_review_id(filename: str) -> str:
    """Extract the CDXXXXXX review ID from a filename like CD000028_pub4_data."""
    m = re.match(r"(CD\d+)", filename)
    return m.group(1) if m else filename


@dataclass
class MAResult:
    """Recomputed statistics for one meta-analysis."""
    ma_id: str               # e.g. CD000028__A1
    review_id: str            # e.g. CD000028
    review_file_stem: str     # e.g. CD000028_pub4_data
    analysis_number: int
    k: int
    estimate: float
    p_value: float
    significant: bool
    ci_lower: float
    ci_upper: float
    I2: float
    tau2: float
    data_type: str            # binary / continuous / giv
    measure: str              # logOR / MD / GIV
    studies: set              # normalized study names
    outcome: Optional[str] = None
    comparison: Optional[str] = None


# ---------------------------------------------------------------------------
# Phase 1: Build study-MA membership + recompute pooled effects
# ---------------------------------------------------------------------------
def phase1_build_membership(max_reviews: int | None = None,
                            ) -> tuple[dict[str, set[str]], dict[str, MAResult]]:
    """Load all reviews, recompute pooled effects, and build study membership.

    Returns:
        study_to_mas: dict mapping normalized study name -> set of ma_ids
        ma_results: dict mapping ma_id -> MAResult
    """
    print(f"[Phase 1] Loading reviews from {PAIRWISE70_DIR}")
    t0 = time.time()

    reviews = load_all_reviews(str(PAIRWISE70_DIR), max_reviews=max_reviews)
    print(f"  Loaded {len(reviews)} reviews in {time.time() - t0:.1f}s")

    study_to_mas: dict[str, set[str]] = defaultdict(set)
    ma_results: dict[str, MAResult] = {}

    n_recomputed = 0
    n_skipped = 0

    for review in reviews:
        review_id = extract_review_id(review.review_id)
        file_stem = review.review_id

        for ag in review.analyses:
            ma_id = f"{review_id}__A{ag.analysis_number}"

            # Extract normalized study names for this analysis
            studies_raw = ag.df["Study"].dropna().unique() if "Study" in ag.df.columns else []
            studies_norm = {normalize_study_name(s) for s in studies_raw}

            # Register in membership
            for study in studies_norm:
                study_to_mas[study].add(ma_id)

            # Recompute pooled effect
            try:
                recomp = recompute_ma(ag.df, ag.data_type)
            except Exception as e:
                n_skipped += 1
                continue

            if recomp.k < 2 or not math.isfinite(recomp.estimate):
                n_skipped += 1
                continue

            ma_results[ma_id] = MAResult(
                ma_id=ma_id,
                review_id=review_id,
                review_file_stem=file_stem,
                analysis_number=ag.analysis_number,
                k=recomp.k,
                estimate=recomp.estimate,
                p_value=recomp.p_value,
                significant=recomp.significant,
                ci_lower=recomp.ci_lower,
                ci_upper=recomp.ci_upper,
                I2=recomp.I2,
                tau2=recomp.tau2,
                data_type=recomp.data_type.value,
                measure=recomp.measure,
                studies=studies_norm,
                outcome=ag.outcome,
                comparison=ag.comparison,
            )
            n_recomputed += 1

    print(f"  Recomputed {n_recomputed} MAs, skipped {n_skipped} (k<2 or NaN)")
    print(f"  Unique studies in membership: {len(study_to_mas)}")

    return dict(study_to_mas), ma_results


# ---------------------------------------------------------------------------
# Phase 2: Find overlapping MA pairs from different reviews
# ---------------------------------------------------------------------------
@dataclass
class OverlapPair:
    """A pair of MAs from different reviews sharing studies."""
    ma_id_1: str
    ma_id_2: str
    review_id_1: str
    review_id_2: str
    shared_studies: set
    n_shared: int
    n_ma1: int
    n_ma2: int
    jaccard: float


def phase2_find_overlapping_pairs(
    study_to_mas: dict[str, set[str]],
    ma_results: dict[str, MAResult],
    min_shared: int = 2,
) -> list[OverlapPair]:
    """Find all MA pairs from different reviews sharing >= min_shared studies."""
    print(f"\n[Phase 2] Finding overlapping MA pairs (min_shared={min_shared})")
    t0 = time.time()

    # Build pairwise overlap counts using inverted index
    pair_studies: dict[tuple[str, str], set[str]] = defaultdict(set)

    for study, mas in study_to_mas.items():
        # Only consider MAs we successfully recomputed
        valid_mas = [m for m in mas if m in ma_results]
        if len(valid_mas) < 2:
            continue
        for i, ma1 in enumerate(sorted(valid_mas)):
            for ma2 in sorted(valid_mas)[i + 1:]:
                # Only pairs from DIFFERENT reviews
                r1 = ma_results[ma1].review_id
                r2 = ma_results[ma2].review_id
                if r1 == r2:
                    continue
                key = (ma1, ma2) if ma1 < ma2 else (ma2, ma1)
                pair_studies[key].add(study)

    # Filter to pairs with >= min_shared
    pairs = []
    for (ma1, ma2), shared in pair_studies.items():
        if len(shared) < min_shared:
            continue
        r1 = ma_results[ma1]
        r2 = ma_results[ma2]
        n1 = len(r1.studies)
        n2 = len(r2.studies)
        union_size = n1 + n2 - len(shared)
        jaccard = len(shared) / union_size if union_size > 0 else 0.0

        pairs.append(OverlapPair(
            ma_id_1=ma1,
            ma_id_2=ma2,
            review_id_1=r1.review_id,
            review_id_2=r2.review_id,
            shared_studies=shared,
            n_shared=len(shared),
            n_ma1=n1,
            n_ma2=n2,
            jaccard=jaccard,
        ))

    pairs.sort(key=lambda p: (-p.n_shared, -p.jaccard))
    print(f"  Found {len(pairs)} MA pairs with >= {min_shared} shared studies in {time.time() - t0:.1f}s")

    return pairs


# ---------------------------------------------------------------------------
# Phase 3: Classify contradictions
# ---------------------------------------------------------------------------
CONTRADICTION_TYPES = {
    "direct": "Both significant, opposite directions",
    "significance": "One significant (p<0.05), one not",
    "magnitude": "Both significant same direction, effect sizes differ >2x",
    "none": "No contradiction detected",
}


@dataclass
class Contradiction:
    """A detected contradiction between two MAs."""
    ma_id_1: str
    ma_id_2: str
    review_id_1: str
    review_id_2: str
    contradiction_type: str
    effect_1: float
    effect_2: float
    p_1: float
    p_2: float
    sig_1: bool
    sig_2: bool
    n_shared: int
    jaccard: float
    outcome_1: Optional[str] = None
    outcome_2: Optional[str] = None
    comparison_1: Optional[str] = None
    comparison_2: Optional[str] = None
    measure_1: str = ""
    measure_2: str = ""


def _effect_direction(estimate: float) -> int:
    """Return +1 if favors experimental, -1 if favors control, 0 if null."""
    if estimate > 0:
        return 1
    elif estimate < 0:
        return -1
    return 0


def classify_contradiction(
    r1: MAResult,
    r2: MAResult,
    overlap: OverlapPair,
) -> Contradiction:
    """Classify the type of contradiction between two MAs.

    For binary outcomes (logOR), positive = favors experimental (higher odds).
    For continuous (MD), positive = experimental has higher mean.
    Direction interpretation depends on outcome, but opposite signs = opposite conclusions.
    """
    dir1 = _effect_direction(r1.estimate)
    dir2 = _effect_direction(r2.estimate)

    if r1.significant and r2.significant and dir1 != 0 and dir2 != 0 and dir1 != dir2:
        ctype = "direct"
    elif r1.significant != r2.significant:
        ctype = "significance"
    elif (r1.significant and r2.significant and dir1 == dir2 and dir1 != 0):
        # Both significant, same direction: check magnitude
        abs1 = abs(r1.estimate)
        abs2 = abs(r2.estimate)
        ratio = max(abs1, abs2) / max(min(abs1, abs2), 1e-10)
        if ratio > 2.0:
            ctype = "magnitude"
        else:
            ctype = "none"
    else:
        ctype = "none"

    return Contradiction(
        ma_id_1=r1.ma_id,
        ma_id_2=r2.ma_id,
        review_id_1=r1.review_id,
        review_id_2=r2.review_id,
        contradiction_type=ctype,
        effect_1=r1.estimate,
        effect_2=r2.estimate,
        p_1=r1.p_value,
        p_2=r2.p_value,
        sig_1=r1.significant,
        sig_2=r2.significant,
        n_shared=overlap.n_shared,
        jaccard=overlap.jaccard,
        outcome_1=r1.outcome,
        outcome_2=r2.outcome,
        comparison_1=r1.comparison,
        comparison_2=r2.comparison,
        measure_1=r1.measure,
        measure_2=r2.measure,
    )


def phase3_classify(
    pairs: list[OverlapPair],
    ma_results: dict[str, MAResult],
) -> list[Contradiction]:
    """Classify all overlapping pairs for contradictions."""
    print(f"\n[Phase 3] Classifying contradictions for {len(pairs)} pairs")
    t0 = time.time()

    contradictions = []
    for pair in pairs:
        r1 = ma_results.get(pair.ma_id_1)
        r2 = ma_results.get(pair.ma_id_2)
        if r1 is None or r2 is None:
            continue
        c = classify_contradiction(r1, r2, pair)
        contradictions.append(c)

    n_by_type = defaultdict(int)
    for c in contradictions:
        n_by_type[c.contradiction_type] += 1

    print(f"  Classification complete in {time.time() - t0:.1f}s")
    for ctype in ["direct", "significance", "magnitude", "none"]:
        print(f"    {ctype}: {n_by_type.get(ctype, 0)}")

    return contradictions


# ---------------------------------------------------------------------------
# Phase 4: Compute corpus statistics + export
# ---------------------------------------------------------------------------
def phase4_export(
    study_to_mas: dict[str, set[str]],
    ma_results: dict[str, MAResult],
    pairs: list[OverlapPair],
    contradictions: list[Contradiction],
) -> dict:
    """Export all results and compute summary statistics."""
    print(f"\n[Phase 4] Exporting results")
    t0 = time.time()

    # Ensure output directories exist
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Study membership (study -> list of MAs)
    membership_export = {
        study: sorted(mas)
        for study, mas in sorted(study_to_mas.items())
        if len(mas) >= 2  # Only multi-MA studies are interesting
    }
    membership_path = DATA_DIR / "study_membership.json"
    with open(membership_path, "w", encoding="utf-8") as f:
        json.dump(membership_export, f, indent=2, ensure_ascii=False)
    print(f"  Wrote {len(membership_export)} multi-MA studies to {membership_path}")

    # 2. Overlapping pairs CSV
    pairs_rows = []
    for p in pairs:
        pairs_rows.append({
            "ma_id_1": p.ma_id_1,
            "ma_id_2": p.ma_id_2,
            "review_id_1": p.review_id_1,
            "review_id_2": p.review_id_2,
            "n_shared": p.n_shared,
            "n_ma1": p.n_ma1,
            "n_ma2": p.n_ma2,
            "jaccard": round(p.jaccard, 4),
            "shared_studies": "; ".join(sorted(p.shared_studies)),
        })
    pairs_df = pd.DataFrame(pairs_rows)
    pairs_path = DATA_DIR / "overlapping_pairs.csv"
    pairs_df.to_csv(pairs_path, index=False, encoding="utf-8")
    print(f"  Wrote {len(pairs_df)} overlapping pairs to {pairs_path}")

    # 3. Contradictions CSV
    contra_rows = []
    for c in contradictions:
        contra_rows.append({
            "ma_id_1": c.ma_id_1,
            "ma_id_2": c.ma_id_2,
            "review_id_1": c.review_id_1,
            "review_id_2": c.review_id_2,
            "contradiction_type": c.contradiction_type,
            "effect_1": round(c.effect_1, 6),
            "effect_2": round(c.effect_2, 6),
            "p_1": round(c.p_1, 6),
            "p_2": round(c.p_2, 6),
            "sig_1": c.sig_1,
            "sig_2": c.sig_2,
            "n_shared": c.n_shared,
            "jaccard": round(c.jaccard, 4),
            "outcome_1": c.outcome_1 or "",
            "outcome_2": c.outcome_2 or "",
            "comparison_1": c.comparison_1 or "",
            "comparison_2": c.comparison_2 or "",
            "measure_1": c.measure_1,
            "measure_2": c.measure_2,
        })
    contra_df = pd.DataFrame(contra_rows)
    contra_path = RESULTS_DIR / "contradictions.csv"
    contra_df.to_csv(contra_path, index=False, encoding="utf-8")
    print(f"  Wrote {len(contra_df)} contradiction records to {contra_path}")

    # 4. Summary statistics
    n_actual = len([c for c in contradictions if c.contradiction_type != "none"])
    n_direct = len([c for c in contradictions if c.contradiction_type == "direct"])
    n_sig = len([c for c in contradictions if c.contradiction_type == "significance"])
    n_mag = len([c for c in contradictions if c.contradiction_type == "magnitude"])
    n_none = len([c for c in contradictions if c.contradiction_type == "none"])

    # Which reviews are most contradicted
    review_contra_count: dict[str, int] = defaultdict(int)
    for c in contradictions:
        if c.contradiction_type != "none":
            review_contra_count[c.review_id_1] += 1
            review_contra_count[c.review_id_2] += 1
    top_reviews = sorted(review_contra_count.items(), key=lambda x: -x[1])[:10]

    # Load audit results for quality flag correlation
    quality_correlation = _compute_quality_correlation(contradictions, ma_results)

    summary = {
        "total_mas_recomputed": len(ma_results),
        "total_unique_studies": len(study_to_mas),
        "multi_ma_studies": len(membership_export),
        "total_overlapping_pairs": len(pairs),
        "contradictions": {
            "total": n_actual,
            "direct": n_direct,
            "significance": n_sig,
            "magnitude": n_mag,
            "no_contradiction": n_none,
            "pct_of_pairs_with_any": round(100 * n_actual / len(pairs), 1) if pairs else 0,
        },
        "top_contradicted_reviews": [
            {"review_id": r, "n_contradictions": n} for r, n in top_reviews
        ],
        "quality_correlation": quality_correlation,
        "parameters": {
            "min_shared_studies": 2,
            "significance_threshold": 0.05,
            "magnitude_ratio_threshold": 2.0,
            "seed": SEED,
        },
    }

    summary_path = RESULTS_DIR / "summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"  Wrote summary to {summary_path}")

    elapsed = time.time() - t0
    print(f"  Export complete in {elapsed:.1f}s")

    return summary


def _compute_quality_correlation(
    contradictions: list[Contradiction],
    ma_results: dict[str, MAResult],
) -> dict:
    """Check if contradicted MAs have worse MetaAudit quality flags.

    Returns summary statistics comparing audit severity counts for
    contradicted vs non-contradicted MAs.
    """
    try:
        with open(AUDIT_RESULTS_PATH, "r", encoding="utf-8") as f:
            audit_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"available": False, "reason": "audit_results.json not found or invalid"}

    # Map review_file_stem__AN to audit key format
    # audit keys: CD000028_pub4_data__A1
    # our ma_ids: CD000028__A1
    # We need to map our IDs to audit keys
    contradicted_ma_ids = set()
    for c in contradictions:
        if c.contradiction_type != "none":
            contradicted_ma_ids.add(c.ma_id_1)
            contradicted_ma_ids.add(c.ma_id_2)

    # Build mapping from review_id + analysis_number to audit key
    ma_to_audit_key: dict[str, str] = {}
    for audit_key in audit_data:
        # Extract review_id and analysis number from audit key
        # Format: CD000028_pub4_data__A1
        m = re.match(r"(CD\d+).*__A(\d+)$", audit_key)
        if m:
            our_id = f"{m.group(1)}__A{m.group(2)}"
            ma_to_audit_key[our_id] = audit_key

    def count_severity(ma_id: str) -> dict[str, int]:
        """Count severity levels for an MA's audit detectors."""
        audit_key = ma_to_audit_key.get(ma_id)
        if audit_key is None or audit_key not in audit_data:
            return {}
        detectors = audit_data[audit_key]
        counts: dict[str, int] = defaultdict(int)
        for det in detectors:
            sev = det.get("severity", "UNKNOWN")
            counts[sev] += 1
        return dict(counts)

    # Aggregate for contradicted vs non-contradicted
    contra_severities: dict[str, list[int]] = defaultdict(list)
    noncontra_severities: dict[str, list[int]] = defaultdict(list)

    for ma_id in ma_results:
        counts = count_severity(ma_id)
        if not counts:
            continue
        target = contra_severities if ma_id in contradicted_ma_ids else noncontra_severities
        for sev in ["CRITICAL", "FAIL", "WARN", "PASS"]:
            target[sev].append(counts.get(sev, 0))

    result = {"available": True}
    for sev in ["CRITICAL", "FAIL", "WARN"]:
        c_vals = contra_severities.get(sev, [])
        nc_vals = noncontra_severities.get(sev, [])
        result[f"contradicted_mean_{sev}"] = round(np.mean(c_vals), 3) if c_vals else None
        result[f"noncontradicted_mean_{sev}"] = round(np.mean(nc_vals), 3) if nc_vals else None
        result[f"n_contradicted"] = len(contra_severities.get("PASS", []))
        result[f"n_noncontradicted"] = len(noncontra_severities.get("PASS", []))

    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="ContradictionMap pipeline")
    parser.add_argument("--max-reviews", type=int, default=None,
                        help="Limit to first N reviews (for development)")
    parser.add_argument("--min-shared", type=int, default=2,
                        help="Minimum shared studies for overlap (default: 2)")
    args = parser.parse_args()

    print("=" * 70)
    print("  ContradictionMap: Detecting Contradictory Cochrane Meta-Analyses")
    print("=" * 70)
    if args.max_reviews:
        print(f"  [DEV MODE] Limited to first {args.max_reviews} reviews")
    print()

    # Phase 1
    study_to_mas, ma_results = phase1_build_membership(
        max_reviews=args.max_reviews,
    )

    # Phase 2
    pairs = phase2_find_overlapping_pairs(
        study_to_mas, ma_results, min_shared=args.min_shared,
    )

    if not pairs:
        print("\n  No overlapping pairs found. Exiting.")
        # Still export empty results
        phase4_export(study_to_mas, ma_results, pairs, [])
        return

    # Phase 3
    contradictions = phase3_classify(pairs, ma_results)

    # Phase 4
    summary = phase4_export(study_to_mas, ma_results, pairs, contradictions)

    # Final report
    print("\n" + "=" * 70)
    print("  RESULTS SUMMARY")
    print("=" * 70)
    print(f"  Total MAs recomputed:        {summary['total_mas_recomputed']}")
    print(f"  Unique studies:              {summary['total_unique_studies']}")
    print(f"  Overlapping MA pairs:        {summary['total_overlapping_pairs']}")
    print(f"  Contradictions detected:     {summary['contradictions']['total']}")
    print(f"    - Direct (opposite sig):   {summary['contradictions']['direct']}")
    print(f"    - Significance mismatch:   {summary['contradictions']['significance']}")
    print(f"    - Magnitude (>2x diff):    {summary['contradictions']['magnitude']}")
    pct = summary['contradictions']['pct_of_pairs_with_any']
    print(f"    - % of pairs contradicted: {pct}%")
    if summary["top_contradicted_reviews"]:
        print(f"\n  Most contradicted reviews:")
        for entry in summary["top_contradicted_reviews"][:5]:
            print(f"    {entry['review_id']}: {entry['n_contradictions']} contradictions")
    print("=" * 70)


if __name__ == "__main__":
    main()

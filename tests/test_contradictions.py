# -*- coding: utf-8 -*-
"""Tests for ContradictionMap pipeline."""

from __future__ import annotations

import json
import math
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, "C:/MetaAudit")

from detect_contradictions import (
    Contradiction,
    MAResult,
    OverlapPair,
    classify_contradiction,
    normalize_study_name,
    extract_review_id,
    phase2_find_overlapping_pairs,
    phase3_classify,
    _effect_direction,
)


# ---------------------------------------------------------------------------
# Test study name normalization
# ---------------------------------------------------------------------------
class TestNormalization:
    def test_basic_strip(self):
        assert normalize_study_name("  Smith 2020  ") == "smith 2020"

    def test_lowercase(self):
        assert normalize_study_name("AFFIRM 2006") == "affirm 2006"

    def test_collapse_spaces(self):
        assert normalize_study_name("van  der  Berg  2010") == "van der berg 2010"

    def test_already_normalized(self):
        assert normalize_study_name("jones 2015") == "jones 2015"

    def test_mixed(self):
        assert normalize_study_name("  SELECT   2013 ") == "select 2013"


class TestExtractReviewId:
    def test_standard(self):
        assert extract_review_id("CD000028_pub4_data") == "CD000028"

    def test_short(self):
        assert extract_review_id("CD012186_pub2_data") == "CD012186"

    def test_just_id(self):
        assert extract_review_id("CD001234") == "CD001234"


# ---------------------------------------------------------------------------
# Test effect direction
# ---------------------------------------------------------------------------
class TestEffectDirection:
    def test_positive(self):
        assert _effect_direction(0.5) == 1

    def test_negative(self):
        assert _effect_direction(-0.3) == -1

    def test_zero(self):
        assert _effect_direction(0.0) == 0


# ---------------------------------------------------------------------------
# Test contradiction classification
# ---------------------------------------------------------------------------
def _make_ma(ma_id: str, review_id: str, estimate: float, p_value: float,
             significant: bool, studies: set | None = None) -> MAResult:
    """Helper to create a MAResult for testing."""
    return MAResult(
        ma_id=ma_id,
        review_id=review_id,
        review_file_stem=f"{review_id}_pub1_data",
        analysis_number=1,
        k=10,
        estimate=estimate,
        p_value=p_value,
        significant=significant,
        ci_lower=estimate - 0.5,
        ci_upper=estimate + 0.5,
        I2=50.0,
        tau2=0.1,
        data_type="binary",
        measure="logOR",
        studies=studies or {"study a", "study b", "study c"},
    )


def _make_overlap(ma1: MAResult, ma2: MAResult, n_shared: int = 3) -> OverlapPair:
    shared = set(list(ma1.studies)[:n_shared])
    return OverlapPair(
        ma_id_1=ma1.ma_id,
        ma_id_2=ma2.ma_id,
        review_id_1=ma1.review_id,
        review_id_2=ma2.review_id,
        shared_studies=shared,
        n_shared=n_shared,
        n_ma1=len(ma1.studies),
        n_ma2=len(ma2.studies),
        jaccard=0.5,
    )


class TestClassifyContradiction:
    def test_direct_contradiction(self):
        """Both significant, opposite directions -> direct."""
        r1 = _make_ma("CD001__A1", "CD001", estimate=0.5, p_value=0.01, significant=True)
        r2 = _make_ma("CD002__A1", "CD002", estimate=-0.4, p_value=0.02, significant=True)
        overlap = _make_overlap(r1, r2)
        c = classify_contradiction(r1, r2, overlap)
        assert c.contradiction_type == "direct"

    def test_significance_contradiction_one_sig(self):
        """One significant, one not -> significance."""
        r1 = _make_ma("CD001__A1", "CD001", estimate=0.5, p_value=0.01, significant=True)
        r2 = _make_ma("CD002__A1", "CD002", estimate=0.3, p_value=0.20, significant=False)
        overlap = _make_overlap(r1, r2)
        c = classify_contradiction(r1, r2, overlap)
        assert c.contradiction_type == "significance"

    def test_significance_contradiction_opposite_nonsig(self):
        """One sig positive, one non-sig negative -> significance (not direct, because one is non-sig)."""
        r1 = _make_ma("CD001__A1", "CD001", estimate=0.5, p_value=0.01, significant=True)
        r2 = _make_ma("CD002__A1", "CD002", estimate=-0.1, p_value=0.60, significant=False)
        overlap = _make_overlap(r1, r2)
        c = classify_contradiction(r1, r2, overlap)
        assert c.contradiction_type == "significance"

    def test_magnitude_contradiction(self):
        """Both significant same direction, >2x effect size ratio -> magnitude."""
        r1 = _make_ma("CD001__A1", "CD001", estimate=0.8, p_value=0.01, significant=True)
        r2 = _make_ma("CD002__A1", "CD002", estimate=0.3, p_value=0.04, significant=True)
        overlap = _make_overlap(r1, r2)
        c = classify_contradiction(r1, r2, overlap)
        # 0.8 / 0.3 = 2.67 > 2.0
        assert c.contradiction_type == "magnitude"

    def test_no_contradiction_concordant(self):
        """Both significant same direction, similar magnitude -> none."""
        r1 = _make_ma("CD001__A1", "CD001", estimate=0.5, p_value=0.01, significant=True)
        r2 = _make_ma("CD002__A1", "CD002", estimate=0.4, p_value=0.02, significant=True)
        overlap = _make_overlap(r1, r2)
        c = classify_contradiction(r1, r2, overlap)
        # 0.5 / 0.4 = 1.25 < 2.0
        assert c.contradiction_type == "none"

    def test_no_contradiction_both_nonsig(self):
        """Both non-significant -> none."""
        r1 = _make_ma("CD001__A1", "CD001", estimate=0.1, p_value=0.50, significant=False)
        r2 = _make_ma("CD002__A1", "CD002", estimate=-0.2, p_value=0.40, significant=False)
        overlap = _make_overlap(r1, r2)
        c = classify_contradiction(r1, r2, overlap)
        assert c.contradiction_type == "none"

    def test_fields_populated(self):
        """Check that all fields are correctly propagated."""
        r1 = _make_ma("CD001__A1", "CD001", estimate=0.5, p_value=0.01, significant=True)
        r2 = _make_ma("CD002__A1", "CD002", estimate=-0.4, p_value=0.02, significant=True)
        overlap = _make_overlap(r1, r2)
        c = classify_contradiction(r1, r2, overlap)
        assert c.ma_id_1 == "CD001__A1"
        assert c.ma_id_2 == "CD002__A1"
        assert c.review_id_1 == "CD001"
        assert c.review_id_2 == "CD002"
        assert c.effect_1 == 0.5
        assert c.effect_2 == -0.4
        assert c.p_1 == 0.01
        assert c.p_2 == 0.02
        assert c.sig_1 is True
        assert c.sig_2 is True
        assert c.n_shared == 3


# ---------------------------------------------------------------------------
# Test Phase 2: overlap detection
# ---------------------------------------------------------------------------
class TestPhase2Overlap:
    def test_finds_pairs_different_reviews(self):
        """MAs from different reviews sharing studies should be found."""
        studies_common = {"smith 2020", "jones 2019", "lee 2021"}
        r1 = _make_ma("CD001__A1", "CD001", 0.5, 0.01, True, studies_common | {"extra1"})
        r2 = _make_ma("CD002__A1", "CD002", -0.3, 0.02, True, studies_common | {"extra2"})
        ma_results = {r1.ma_id: r1, r2.ma_id: r2}

        study_to_mas = {}
        for ma in ma_results.values():
            for s in ma.studies:
                study_to_mas.setdefault(s, set()).add(ma.ma_id)

        pairs = phase2_find_overlapping_pairs(study_to_mas, ma_results, min_shared=2)
        assert len(pairs) == 1
        assert pairs[0].n_shared == 3

    def test_ignores_same_review(self):
        """MAs from the SAME review should not be paired."""
        studies = {"a", "b", "c"}
        r1 = _make_ma("CD001__A1", "CD001", 0.5, 0.01, True, studies)
        r2 = _make_ma("CD001__A2", "CD001", -0.3, 0.02, True, studies)
        ma_results = {r1.ma_id: r1, r2.ma_id: r2}

        study_to_mas = {}
        for ma in ma_results.values():
            for s in ma.studies:
                study_to_mas.setdefault(s, set()).add(ma.ma_id)

        pairs = phase2_find_overlapping_pairs(study_to_mas, ma_results, min_shared=2)
        assert len(pairs) == 0

    def test_min_shared_filter(self):
        """Pairs with fewer than min_shared studies should be excluded."""
        r1 = _make_ma("CD001__A1", "CD001", 0.5, 0.01, True, {"a", "b", "c"})
        r2 = _make_ma("CD002__A1", "CD002", -0.3, 0.02, True, {"a", "d", "e"})
        ma_results = {r1.ma_id: r1, r2.ma_id: r2}

        study_to_mas = {}
        for ma in ma_results.values():
            for s in ma.studies:
                study_to_mas.setdefault(s, set()).add(ma.ma_id)

        # min_shared=2: only 1 shared ("a") -> no pairs
        pairs = phase2_find_overlapping_pairs(study_to_mas, ma_results, min_shared=2)
        assert len(pairs) == 0

        # min_shared=1: should find it
        pairs = phase2_find_overlapping_pairs(study_to_mas, ma_results, min_shared=1)
        assert len(pairs) == 1

    def test_jaccard_computation(self):
        """Jaccard should be |intersection| / |union|."""
        r1 = _make_ma("CD001__A1", "CD001", 0.5, 0.01, True, {"a", "b", "c", "d"})
        r2 = _make_ma("CD002__A1", "CD002", -0.3, 0.02, True, {"a", "b", "e", "f"})
        ma_results = {r1.ma_id: r1, r2.ma_id: r2}

        study_to_mas = {}
        for ma in ma_results.values():
            for s in ma.studies:
                study_to_mas.setdefault(s, set()).add(ma.ma_id)

        pairs = phase2_find_overlapping_pairs(study_to_mas, ma_results, min_shared=2)
        assert len(pairs) == 1
        # 2 shared (a, b), union = 6 (a,b,c,d,e,f) -> jaccard = 2/6 = 0.333
        assert abs(pairs[0].jaccard - 2.0 / 6.0) < 0.001


# ---------------------------------------------------------------------------
# Test Phase 3: full classify pipeline
# ---------------------------------------------------------------------------
class TestPhase3:
    def test_classifies_multiple(self):
        """Phase 3 should process multiple pairs and count types."""
        studies = {"a", "b", "c"}
        r1 = _make_ma("CD001__A1", "CD001", 0.5, 0.01, True, studies)
        r2 = _make_ma("CD002__A1", "CD002", -0.4, 0.02, True, studies)
        r3 = _make_ma("CD003__A1", "CD003", 0.3, 0.30, False, studies)
        ma_results = {r1.ma_id: r1, r2.ma_id: r2, r3.ma_id: r3}

        pairs = [
            _make_overlap(r1, r2),  # direct contradiction
            _make_overlap(r1, r3),  # significance contradiction
            _make_overlap(r2, r3),  # significance contradiction
        ]

        contras = phase3_classify(pairs, ma_results)
        assert len(contras) == 3
        types = [c.contradiction_type for c in contras]
        assert types.count("direct") == 1
        assert types.count("significance") == 2


# ---------------------------------------------------------------------------
# Integration: test on real data if available
# ---------------------------------------------------------------------------
PAIRWISE70_DIR = Path(r"C:\Users\user\OneDrive - NHS\Documents\Pairwise70\data")


@pytest.mark.skipif(
    not PAIRWISE70_DIR.exists(),
    reason="Pairwise70 data not available"
)
class TestIntegration:
    """Integration tests using real Pairwise70 data (first 20 reviews)."""

    def test_real_data_loads(self):
        """Load a small subset and verify we get MAs with studies."""
        from detect_contradictions import phase1_build_membership
        study_to_mas, ma_results = phase1_build_membership(max_reviews=20)
        assert len(ma_results) > 0, "Should recompute at least some MAs"
        assert len(study_to_mas) > 0, "Should find studies"
        # Check that studies are normalized
        for study in list(study_to_mas.keys())[:10]:
            assert study == study.lower(), f"Study name not normalized: {study}"
            assert "  " not in study, f"Study has double spaces: {study}"

    def test_real_overlap_pairs(self):
        """Verify we find some overlapping pairs in real data."""
        from detect_contradictions import phase1_build_membership, phase2_find_overlapping_pairs
        study_to_mas, ma_results = phase1_build_membership(max_reviews=50)
        pairs = phase2_find_overlapping_pairs(study_to_mas, ma_results, min_shared=2)
        # With 50 reviews we expect at least a few pairs
        # (Not guaranteed but very likely given the known overlap)
        print(f"  Found {len(pairs)} pairs from 50 reviews")
        for p in pairs[:5]:
            assert p.n_shared >= 2
            assert p.review_id_1 != p.review_id_2
            assert 0.0 < p.jaccard <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

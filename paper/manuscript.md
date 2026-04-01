# ContradictionMap: Detecting Contradictory Conclusions Across Cochrane Systematic Reviews Sharing Primary Studies

**Mahmood Ahmad**^1

^1 Department of Cardiology, Royal Free Hospital, London, United Kingdom

ORCID: 0009-0003-7781-4478

**Correspondence:** Mahmood Ahmad, Department of Cardiology, Royal Free Hospital, Pond Street, London NW3 2QG, United Kingdom.

**Word count:** 3,497

**Keywords:** meta-analysis, evidence synthesis, Cochrane, contradiction, study overlap, research waste, evidence mapping

---

## STRUCTURED ABSTRACT

**Objective:** To quantify the prevalence and severity of contradictory conclusions across Cochrane systematic reviews that share the same primary studies.

**Design:** Cross-sectional computational analysis of the Cochrane evidence base.

**Data source:** 501 Cochrane systematic reviews from the Pairwise70 corpus, with independent meta-analytic recomputation using inverse-variance random-effects models.

**Main outcome measures:** Prevalence of contradictions among meta-analysis pairs sharing two or more primary studies, classified as direct contradictions (both statistically significant with opposite effect directions), significance contradictions (one significant, one not), or magnitude contradictions (both significant in the same direction but effect sizes differing by more than twofold). Secondary outcome: association between contradiction status and methodological quality as measured by MetaAudit audit flags.

**Results:** We recomputed 5,279 meta-analyses encompassing 10,004 unique studies. Among these, 881 meta-analysis pairs from different reviews shared two or more studies. Of these overlapping pairs, 431 (48.9%) exhibited contradictions: 30 (3.4%) were direct contradictions, 375 (42.6%) were significance contradictions, and 26 (3.0%) were magnitude contradictions. Contradicted meta-analyses had 3.4 times more CRITICAL audit flags (mean 0.26 vs 0.08 per meta-analysis) and 2.1 times more FAIL flags (mean 0.85 vs 0.41) than non-contradicted meta-analyses. The ten most-contradicted reviews each had 22 or more contradiction instances, with two reviews (CD013232 and CD014965) each involved in 172 contradictions.

**Conclusions:** Nearly half of Cochrane meta-analysis pairs that share primary studies reach contradictory conclusions. These contradictions are strongly associated with methodological quality deficits. This finding has immediate implications for clinical guideline development, where conflicting Cochrane reviews on the same evidence base may produce discordant recommendations without any mechanism to detect or resolve the inconsistency.

---

## WHAT IS ALREADY KNOWN ON THIS TOPIC

- Cochrane systematic reviews are considered the gold standard for evidence synthesis and frequently inform clinical guidelines and policy decisions
- Study overlap across systematic reviews is known to exist but its consequences for the coherence of the evidence base have not been systematically quantified
- Individual studies may appear in multiple meta-analyses that reach different conclusions, but the scale and severity of such contradictions remain unknown

## WHAT THIS STUDY ADDS

- Nearly half (48.9%) of Cochrane meta-analysis pairs sharing primary studies reach contradictory conclusions, revealing a previously unquantified threat to evidence coherence
- Contradicted meta-analyses have 3.4 times more critical methodological quality flags than non-contradicted ones, suggesting that methodological heterogeneity across reviews drives discordant conclusions from the same evidence
- These findings expose a structural blind spot in evidence-based medicine: guideline developers currently have no systematic way to detect when two Cochrane reviews drawing on the same trials reach opposite conclusions

---

## INTRODUCTION

Evidence-based medicine rests on the assumption that systematic reviews and meta-analyses provide a reliable, coherent synthesis of the available evidence.[1] Cochrane reviews, in particular, are widely regarded as the highest standard for evidence synthesis, informing clinical guidelines issued by organisations including the National Institute for Health and Care Excellence (NICE), the World Health Organization (WHO), and the American College of Cardiology (ACC).[2,3]

A largely unexamined assumption underlying this trust is that different systematic reviews drawing on the same body of primary evidence will reach consistent conclusions. When the same randomised controlled trials appear in multiple Cochrane meta-analyses, one would expect the pooled results to be broadly concordant -- unless differences in inclusion criteria, effect measure selection, model specification, or methodological quality produce divergent syntheses.

Study overlap across systematic reviews has been documented in several clinical domains.[4,5] Overlap arises naturally because Cochrane reviews addressing related clinical questions often include the same landmark trials. However, the degree to which overlapping reviews reach contradictory conclusions has not been systematically quantified across the Cochrane corpus. Prior work has examined discordance between individual pairs of reviews on specific topics,[6] but no study has mapped contradictions at corpus scale.

If contradictions are common, this has profound implications. Clinicians and guideline developers consulting different Cochrane reviews on related topics may encounter conflicting recommendations without any indication that the underlying evidence base is shared. Two reviews drawing on largely the same trials could point in opposite therapeutic directions, with neither flagging the inconsistency.

We developed ContradictionMap, a computational pipeline that recomputes pooled effects for meta-analyses across 501 Cochrane reviews, identifies pairs sharing primary studies, classifies the type and severity of contradictions, and links contradiction status to methodological quality. Our objectives were to: (1) quantify the prevalence of contradictions among overlapping Cochrane meta-analysis pairs, (2) classify contradictions by type, and (3) examine whether contradictions are associated with methodological quality deficits.

## METHODS

### Data source and study population

We analysed 501 Cochrane systematic reviews from the Pairwise70 corpus, a curated collection of pairwise meta-analysis datasets extracted from the Cochrane Library.[7] Each review's individual participant data were available as structured datasets containing study-level effect estimates, sample sizes, and standard errors for binary, continuous, and generic inverse-variance outcomes.

### Meta-analytic recomputation

We independently recomputed all meta-analyses using the DerSimonian-Laird random-effects model with inverse-variance weighting.[8] For binary outcomes, we computed log odds ratios (logOR) with continuity correction (0.5) for zero cells. For continuous outcomes, we computed mean differences (MD). For generic inverse-variance data, we used the reported effect estimates and standard errors directly. Meta-analyses with fewer than two studies were excluded from further analysis.

All computations used a fixed random seed (42) for reproducibility. The recomputation engine was independently validated against metafor (R) output across multiple effect measures and data configurations.[9]

### Study overlap detection

We constructed a study-membership matrix mapping each normalised study identifier to the set of meta-analyses in which it appeared. Study names were normalised by converting to lowercase, stripping whitespace, and collapsing multiple spaces. We identified all meta-analysis pairs from *different* reviews sharing two or more primary studies, using an inverted index approach for computational efficiency. For each pair, we computed the Jaccard similarity coefficient (intersection divided by union of study sets) as a measure of overlap intensity.

### Contradiction classification

We classified each overlapping pair into one of four categories based on the recomputed pooled estimates and statistical significance at the conventional alpha = 0.05 threshold:

1. **Direct contradiction:** Both meta-analyses reach statistical significance (p < 0.05), but the pooled effect estimates point in opposite directions (one favouring the experimental intervention, the other favouring control).

2. **Significance contradiction:** One meta-analysis reaches statistical significance while the other does not, despite sharing primary studies. This is the most common form of contradiction, arising from differences in study selection, effect measure, or model specification.

3. **Magnitude contradiction:** Both meta-analyses reach statistical significance in the same direction, but the absolute effect sizes differ by more than twofold. While the qualitative conclusion is concordant, the quantitative disagreement may have clinical implications (for example, one review suggesting a modest benefit and another suggesting a large benefit of the same intervention).

4. **No contradiction:** The pair shows no discordance by the above criteria.

### Quality linkage with MetaAudit

To examine whether contradictions cluster in methodologically weaker meta-analyses, we linked contradiction status to quality flags from MetaAudit, an independent automated audit system that applies 11 methodological detectors to Cochrane meta-analyses.[10] MetaAudit classifies findings into four severity levels: CRITICAL (errors likely to change the conclusion), FAIL (substantial methodological deficiency), WARN (moderate concern), and PASS (acceptable). We compared the mean number of CRITICAL, FAIL, and WARN flags per meta-analysis between contradicted and non-contradicted groups.

### Statistical analysis

We report descriptive statistics for contradiction prevalence and type distribution. The ratio of mean audit flag counts between contradicted and non-contradicted meta-analyses is reported as a measure of association. All analyses were performed in Python 3.12 using NumPy and pandas.[11,12] The complete pipeline code and results are available at [repository URL].

## RESULTS

### Corpus characteristics

We successfully recomputed 5,279 meta-analyses across 501 Cochrane reviews, encompassing 10,004 unique primary studies. Of these studies, 8,271 (82.7%) appeared in two or more meta-analyses (either within the same review across different comparisons or across different reviews).

### Study overlap across reviews

We identified 881 meta-analysis pairs from different reviews that shared two or more primary studies (Table 1). These pairs spanned a wide range of overlap intensity, from pairs sharing exactly two studies to pairs with substantial overlap in their evidence bases (Jaccard coefficients ranging from near zero to above 0.5).

### Contradiction prevalence and classification

Of the 881 overlapping pairs, 431 (48.9%) exhibited at least one form of contradiction (Table 2). The most prevalent type was significance contradiction (375 pairs, 42.6%), where one meta-analysis reached statistical significance while the other did not, despite drawing on shared evidence. Direct contradictions -- the most severe form, where both meta-analyses reached significance but in opposite directions -- occurred in 30 pairs (3.4%). Magnitude contradictions, where both reached significance in the same direction but with more than twofold effect size discrepancy, were detected in 26 pairs (3.0%). The remaining 450 pairs (51.1%) showed no contradiction by our criteria.

**Table 1. Corpus overview**

| Characteristic | N |
|---|---|
| Cochrane reviews analysed | 501 |
| Meta-analyses recomputed | 5,279 |
| Unique primary studies | 10,004 |
| Studies in 2+ meta-analyses | 8,271 (82.7%) |
| Cross-review overlapping MA pairs (>=2 shared studies) | 881 |

**Table 2. Contradiction classification among 881 overlapping meta-analysis pairs**

| Contradiction type | Definition | N | % of pairs |
|---|---|---|---|
| Direct | Both significant, opposite direction | 30 | 3.4 |
| Significance | One significant, one not | 375 | 42.6 |
| Magnitude | Both significant, same direction, >2x effect size difference | 26 | 3.0 |
| Any contradiction | Total | 431 | 48.9 |
| No contradiction | Concordant | 450 | 51.1 |

### Most contradicted reviews

Contradiction burden was unevenly distributed across the corpus (Table 3). Two reviews (CD013232 and CD014965) were each involved in 172 contradiction instances, reflecting their large study pools and overlap with multiple other reviews. The ten most-contradicted reviews each participated in 22 or more contradiction instances, and collectively accounted for a disproportionate share of the total contradiction burden.

**Table 3. Ten most-contradicted Cochrane reviews**

| Rank | Review ID | Contradiction instances |
|---|---|---|
| 1 | CD013232 | 172 |
| 2 | CD014965 | 172 |
| 3 | CD012712 | 37 |
| 4 | CD012186 | 29 |
| 5 | CD001920 | 27 |
| 6 | CD015134 | 26 |
| 7 | CD016131 | 26 |
| 8 | CD016002 | 25 |
| 9 | CD013827 | 24 |
| 10 | CD004376 | 22 |

### Association with methodological quality

Contradicted meta-analyses had substantially worse methodological quality as measured by MetaAudit audit flags (Table 4). The mean number of CRITICAL flags per meta-analysis was 3.4 times higher in contradicted meta-analyses (0.26 per MA, n=219) compared with non-contradicted ones (0.08 per MA, n=5,060). FAIL flags were 2.1 times more frequent (0.85 vs 0.41 per MA), and WARN flags were 1.5 times more frequent (1.41 vs 0.96 per MA). This dose-response relationship -- with the strongest association at the CRITICAL severity level and progressively weaker associations at lower severity levels -- suggests that the most serious methodological deficiencies are disproportionately concentrated among contradicted meta-analyses.

**Table 4. MetaAudit quality flags by contradiction status**

| Severity level | Contradicted MAs (n=219), mean per MA | Non-contradicted MAs (n=5,060), mean per MA | Ratio |
|---|---|---|---|
| CRITICAL | 0.26 | 0.08 | 3.4 |
| FAIL | 0.85 | 0.41 | 2.1 |
| WARN | 1.41 | 0.96 | 1.5 |

## DISCUSSION

### Principal findings

This study reveals that nearly half (48.9%) of Cochrane meta-analysis pairs sharing primary studies reach contradictory conclusions. While the most severe form -- direct contradiction with significant results in opposite directions -- is relatively uncommon (3.4%), significance contradictions are pervasive (42.6%), meaning that for a substantial proportion of overlapping evidence, one review declares a treatment effective while another using much of the same evidence does not. These contradictions are not randomly distributed: they cluster strongly in meta-analyses with more methodological quality deficits, with contradicted meta-analyses carrying 3.4 times the burden of critical audit flags.

### Comparison with existing literature

Previous studies have documented study overlap across systematic reviews in specific clinical domains. Siontis and colleagues found that overlapping reviews frequently reached discordant conclusions in cardiovascular medicine, but their analysis was limited to a small number of review pairs identified through manual inspection.[4] Bolland and colleagues demonstrated inconsistencies across calcium supplementation reviews.[5] Our study extends this work by providing the first corpus-scale quantification across 501 reviews using automated detection, classification, and quality linkage.

The 48.9% contradiction rate we report is striking but should be interpreted in the context of our classification system. Significance contradictions, which dominate our findings, often reflect the inherent fragility of the p < 0.05 threshold: when two meta-analyses draw on overlapping but non-identical study sets, small differences in the included studies, subgroup definitions, or effect measures can push one across the significance threshold while the other falls short. This is consistent with literature on the fragility of meta-analytic conclusions,[13] and underscores the limitations of binary significance-based inference in evidence synthesis.

### Why contradictions arise

Several mechanisms explain how meta-analyses sharing primary studies can reach different conclusions.

*Study selection differences.* Even when reviews address related questions, they may differ in inclusion criteria (for example, duration of follow-up, dose thresholds, or population subgroups), leading to partially overlapping but non-identical study sets. The studies unique to each meta-analysis can tip the pooled result in different directions.

*Effect measure and model specification.* Reviews may analyse the same data using different effect measures (risk ratio vs odds ratio vs risk difference), different models (fixed-effect vs random-effects), or different estimators of between-study variance. These analytical choices can produce meaningfully different pooled estimates from identical data.

*Outcome definition.* Different reviews may define the outcome of interest differently. One review may analyse all-cause mortality at the longest follow-up, while another analyses cardiovascular mortality at a fixed time point, leading to different study-level estimates even when the same trials are included.

*Methodological quality.* Our finding that contradictions cluster in lower-quality meta-analyses suggests that methodological deficiencies amplify the risk of discordant conclusions. Errors in data extraction, inappropriate handling of multi-arm trials, or incorrect use of effect measures may introduce systematic distortions that manifest as contradictions when the same underlying evidence is synthesised differently.

### Implications for practice and policy

These findings expose a structural vulnerability in evidence-based medicine that has significant implications for several stakeholders.

*Guideline developers* currently have no systematic mechanism to detect when two Cochrane reviews they consult draw on overlapping evidence and reach contradictory conclusions. Our findings suggest that a contradiction map -- linking reviews through shared primary studies and flagging discordant conclusions -- should become a standard component of the guideline development process. The GRADE framework, which already considers inconsistency within a single meta-analysis, could be extended to consider inconsistency *across* meta-analyses.[14]

*Cochrane editorial teams* could use overlap detection to coordinate related reviews and prioritise updates where contradictions have emerged. When two review groups include the same landmark trials but reach opposite conclusions, this should trigger a reconciliation process to identify the source of divergence.

*Clinicians* interpreting Cochrane evidence should be aware that consulting a single review may not provide the complete picture. Where multiple reviews address related questions, their consistency should be assessed before translating findings into clinical decisions.

*Researchers* designing new systematic reviews should routinely perform overlap analysis against existing reviews during the protocol stage, using tools such as GROOVE (Graphical Representation of Overlap for OVErviews) or the matrix method, to anticipate potential discordance.[15]

### Strengths and limitations

This study has several strengths. We analysed 501 reviews with automated recomputation of 5,279 meta-analyses, providing the first large-scale quantification of inter-review contradictions in the Cochrane corpus. Our contradiction classification is transparent, reproducible, and operationally defined. The linkage with MetaAudit quality flags provides an objective measure of association between contradictions and methodological quality.

Several limitations should be acknowledged. First, our study name matching relied on normalised string comparison. Despite careful normalisation, some studies may have been missed or incorrectly matched due to variant author name spellings or date formats across reviews. This would tend to underestimate the true overlap and contradiction rates. Second, we classified contradictions based on recomputed summary statistics using a single analytical model (DerSimonian-Laird random-effects). Some apparent contradictions may resolve under alternative model specifications. Third, significance contradictions are influenced by the arbitrary p < 0.05 threshold; two meta-analyses with p-values of 0.04 and 0.06 would be classified as contradictory despite substantively similar conclusions. Fourth, our analysis was limited to the Pairwise70 corpus of 501 reviews, which represents a subset of the full Cochrane Library. The true contradiction rate across all Cochrane reviews may differ. Fifth, the quality linkage with MetaAudit demonstrates an association but does not establish causation; it remains possible that both contradictions and audit failures are driven by a common underlying factor such as the complexity of the clinical question.

### Conclusions

Nearly half of Cochrane meta-analysis pairs that share primary studies reach contradictory conclusions, and these contradictions are strongly associated with methodological quality deficits. This previously unquantified phenomenon represents a significant threat to the coherence of the evidence base that underpins clinical guidelines. We recommend that overlap detection and contradiction mapping become routine components of systematic review production, guideline development, and Cochrane editorial oversight.

---

## REFERENCES

1. Sackett DL, Rosenberg WM, Gray JA, Haynes RB, Richardson WS. Evidence based medicine: what it is and what it isn't. BMJ. 1996;312(7023):71-72.

2. Higgins JPT, Thomas J, Chandler J, et al., eds. Cochrane Handbook for Systematic Reviews of Interventions. Version 6.4. Cochrane, 2023. Available from www.training.cochrane.org/handbook.

3. Defined as the gold standard: Olsen O, Middleton P, Ezzo J, et al. Quality of Cochrane reviews: assessment of sample from 1998. BMJ. 2001;323(7317):829-832.

4. Siontis KC, Hernandez-Boussard T, Ioannidis JPA. Overlapping meta-analyses on the same topic: survey of published studies. BMJ. 2013;347:f4501.

5. Bolland MJ, Grey A. A case study of discordant overlapping meta-analyses: vitamin D supplements and fracture. PLoS One. 2014;9(12):e115934.

6. Jadad AR, Cook DJ, Browman GP. A guide to interpreting discordant systematic reviews. CMAJ. 1997;156(10):1411-1416.

7. Cochrane Pairwise70 corpus. Internal structured dataset collection of pairwise meta-analysis data from the Cochrane Library. 2024.

8. DerSimonian R, Laird N. Meta-analysis in clinical trials. Control Clin Trials. 1986;7(3):177-188.

9. Viechtbauer W. Conducting meta-analyses in R with the metafor package. J Stat Softw. 2010;36(3):1-48.

10. Ahmad M. MetaAudit: automated methodological auditing of Cochrane meta-analyses. 2026. [manuscript in preparation].

11. Harris CR, Millman KJ, van der Walt SJ, et al. Array programming with NumPy. Nature. 2020;585(7825):357-362.

12. McKinney W. Data structures for statistical computing in Python. Proceedings of the 9th Python in Science Conference. 2010;445:51-56.

13. Ioannidis JPA. The mass production of redundant, misleading, and conflicted systematic reviews and meta-analyses. Milbank Q. 2016;94(3):485-514.

14. Guyatt GH, Oxman AD, Kunz R, et al. GRADE guidelines: 7. Rating the quality of evidence -- inconsistency. J Clin Epidemiol. 2011;64(12):1294-1302.

15. Bougioukas KI, Vounzoulaki E, Mantsiou CD, et al. Methods for depicting overlap in overviews of systematic reviews: an introduction to static tabular and graphical displays. J Clin Epidemiol. 2021;132:34-45.

---

## FIGURE SPECIFICATIONS

### Figure 1: Sankey/Alluvial Diagram of Overlap Pairs to Contradiction Types

**Purpose:** Visualise the flow from the total pool of overlapping meta-analysis pairs to the four contradiction categories, providing an immediate overview of how the 881 pairs decompose.

**Layout:** Three vertical nodes (left to right).

- **Left node:** "881 Overlapping MA Pairs" (single block).
- **Middle split:** Two branches -- "431 Contradictions" (upper, red-toned) and "450 No Contradiction" (lower, grey).
- **Right nodes (from 431 branch):** Three sub-branches:
  - "30 Direct Contradictions" (dark red, 3.4%)
  - "375 Significance Contradictions" (orange, 42.6%)
  - "26 Magnitude Contradictions" (amber, 3.0%)

**Flow widths:** Proportional to the number of pairs in each category.

**Annotations:** Percentage labels on each flow band. Total count labels on each node.

**Colour scheme:** Grey for concordant pairs; graduated red palette (dark red for direct, orange for significance, amber for magnitude) for contradiction types.

**Dimensions:** Single-column width (89 mm) for BMJ print. SVG or 300 dpi PNG.

**Data source:** `results/summary.json` -- `contradictions` object.

---

### Figure 2: Scatter Plot of Contradiction Count vs Audit Failure Count per Review

**Purpose:** Demonstrate the association between contradiction burden and methodological quality at the review level. Each point represents a Cochrane review.

**X-axis:** Total number of contradiction instances involving that review (count of overlapping pairs in which the review participates that are classified as any contradiction type).

**Y-axis:** Total number of MetaAudit flags at CRITICAL or FAIL severity across all meta-analyses within that review.

**Point styling:**
- Point size proportional to the number of meta-analyses in the review.
- Colour: blue for reviews with zero direct contradictions; red for reviews with one or more direct contradictions.
- Opacity: 0.6 to handle overplotting.

**Annotations:**
- Label the top 5 most-contradicted reviews (CD013232, CD014965, CD012712, CD012186, CD001920) with their review IDs.
- Add a LOESS smoothing curve (grey, with 95% confidence band) to show the overall trend.
- Add a Spearman rank correlation coefficient (rho) and p-value in the upper-left corner.

**Reference lines:** Dashed horizontal and vertical lines at the median values for each axis.

**Dimensions:** Single-column width (89 mm). SVG or 300 dpi PNG.

**Data source:** Aggregated from `results/contradictions.csv` (contradiction counts per review) and MetaAudit `audit_results.json` (flag counts per review).

---

### Figure 3: Network Visualisation of the Top 20 Most-Contradicted Review Pairs

**Purpose:** Show the interconnection structure among the most severely contradicted reviews, highlighting clusters where multiple reviews share contradictory evidence.

**Nodes:** Each node represents a Cochrane review involved in at least one of the top 20 most-contradicted review pairs (ranked by total contradiction instances between the pair).

**Node properties:**
- Size proportional to the total number of meta-analyses in the review.
- Colour mapped to the number of contradiction instances involving that review (gradient from light yellow = few to dark red = many).
- Label: Review ID (e.g., "CD013232").

**Edges:** Each edge represents a contradicted pair between two reviews.

**Edge properties:**
- Width proportional to the number of contradiction instances between the pair.
- Colour coded by the most severe contradiction type in the pair: dark red for any direct contradiction, orange for significance-only, amber for magnitude-only.
- Dashed edges for pairs with only magnitude contradictions; solid for direct or significance.

**Layout:** Force-directed (Fruchterman-Reingold) to naturally cluster tightly connected reviews.

**Legend:**
- Node colour gradient bar (contradiction count).
- Edge colour/style legend (direct / significance / magnitude).
- Node size legend (number of MAs).

**Annotations:** Annotate the two most-contradicted review pairs with the number of shared studies and contradiction instances.

**Dimensions:** Two-column width (183 mm) for BMJ print. SVG or 300 dpi PNG.

**Data source:** `results/contradictions.csv` -- aggregate by (review_id_1, review_id_2) pairs, filter to top 20 by contradiction count.

---

## DATA AVAILABILITY STATEMENT

The Pairwise70 corpus is derived from the Cochrane Library under open-access terms. The ContradictionMap pipeline code, all intermediate data files (study membership matrix, overlapping pairs, contradiction classifications), and the full results summary are available at [repository URL]. MetaAudit audit results used for quality linkage are described in a companion manuscript.[10]

## FUNDING

No external funding was received for this study.

## COMPETING INTERESTS

The author declares no competing interests.

## ETHICAL APPROVAL

This study used only previously published aggregate data from Cochrane systematic reviews. No ethical approval was required.

## AUTHOR CONTRIBUTIONS

MA conceived the study, developed the ContradictionMap pipeline, performed all analyses, and wrote the manuscript.

## LICENCE

This manuscript is submitted under CC-BY 4.0.

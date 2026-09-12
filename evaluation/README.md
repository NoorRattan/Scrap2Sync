# Evaluation evidence

The initial benchmark contains 72 fictional cases authored by OpenAI GPT-6 / Codex at 2026-09-05T13:55:15Z, before formatter implementation or output inspection. Each case records its provenance. All names, projects, tickets, diagnostics and links are fictional; links use the reserved example.invalid domain. No workplace notes or private specification examples are included.

**RISK-005:** the benchmark author and implementation team share model context. This is a disclosed model-authored portfolio benchmark, with no independence or human-authorship claim. A later sealed external evaluation can supplement this evidence.

The frozen source is `dataset/benchmark.jsonl`; `benchmark.sha256` records its SHA-256. The UTF-8 file uses LF line endings and one canonical JSON object per line. The creation helper reproduces those exact bytes and refuses to replace a different existing freeze. Do not regenerate a different dataset after observing results. Corrections require a new version and hash, with previous comparisons invalidated.

`rubric.json` declares criteria, denominators and fixed gates before execution. `rubric.sha256` records its hash. The benchmark contains 69 valid requests and three empty-invalid requests. Each required coverage slice has at least three cases. Nine cases exercise exactly 10,000 normalized Unicode code points, including three indivisible URLs and three quoted diagnostics. These explicitly exercise the owner-approved 10,000-code-point per-item correction while retaining the 20,000 total draft ceiling.

Invalid-input cases must receive a validation error before either formatter runs; they remain visible in reports and are excluded from successful-response denominators. A source fact with an empty `allowedSections` array is an explicit absence assertion: negated-blocker-only notes should leave the draft sections empty, without inventing a work item. Ambiguous cases remain subject to factuality and preservation checks but are excluded from unambiguous placement F1. Full conventions appear in the rubric.

Provider failure tags describe deterministic integration scenarios. Stub execution tests adapter behavior and fallback transitions; it cannot establish live model quality or usefulness. Credentialed provider measurements remain unrun unless separately authorized. Semantic scores require named reviewer provenance and case-level evidence; string matching alone is not semantic review.

To verify the freeze from the repository root, run `python evaluation/freeze_benchmark.py`. The helper validates the canonical case fields, unique IDs, exact supporting spans, protected strings, input bounds, minimum case count and coverage counts before comparing the bytes and hash. It never imports formatter code. Keep authored cases and their rubric separate from implementation-discovered regression fixtures.

## Executing and reviewing results

Use the API project's Python environment from the repository root:

```text
python evaluation/evaluate.py
python -m unittest discover -s evaluation -p test_evaluate.py -v
```

The adapter explicitly disables the external provider. Valid cases run through the complete local generation service and a common-validator recheck. Invalid cases use actual in-process API requests. Each result records its case ID, response, source fragments, checks and immutable backend source fingerprint. Service-call timings are diagnostic only; they do not measure client-visible painting or establish a product latency claim.

`reports/case-results.jsonl` contains traceable automated evidence. `reports/semantic-review-packet.jsonl` contains full source and anonymized output. The companion `semantic-review-compact.jsonl` abbreviates only long fields, labels every omission, and includes full-value lengths/hashes. Refer to the full packet when reviewing omitted text. The packet removes engine-identifying notices for single-output factuality review; without a live primary result there is no pairwise usefulness comparison.

Complete a copy of `semantic-review-template.json` after actually reading the source, output and rubric. Record reviewer identity, timestamp, rationale, semantic counts, placements, warnings and editing effort for each reviewed case. Automated span matches never fill semantic scores. Review records are tied to the exact packet hash, so changed output requires a new review. A secondary reviewer can score at least 20 overlapping cases; shared model context remains disclosed and does not establish independence.

To regenerate the report from stored execution evidence and completed review files:

```text
python evaluation/evaluate.py --reuse-results --review evaluation/reports/primary-review.json --review evaluation/reports/secondary-review.json --require-semantic-pass
```

The first review file supplies primary scores; later files provide agreement evidence. Disagreements remain visible and require documented adjudication. The runner refuses altered frozen inputs or stale review hashes. Every re-execution archives the prior run, including its failures, under `reports/runs/`. A default zero exit status means automated checks passed; final factuality acceptance additionally requires completed semantic review and `--require-semantic-pass`. Live provider metrics remain explicitly unrun, and absent browser latency or provider integration reports are never labelled passed.

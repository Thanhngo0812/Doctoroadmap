"""Ticket 18b/c falsifiability checks: mutate in memory, never edit product files.

Only synthetic unit tests are run. Exit 1 if any removed rule goes undetected.
"""
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

DOMAIN = "doc2roadmap.domain.secondary_features"
STAGE = "doc2roadmap.application.use_cases.build_secondary_ml_edges"
MODEL = "doc2roadmap.infrastructure.secondary_model"
TEST_DOMAIN = "tests/unit/domain/test_secondary_features.py"
TEST_STAGE = "tests/unit/application/test_build_secondary_ml_edges.py"
TEST_MODEL = "tests/unit/infrastructure/test_secondary_model.py"
MUTATIONS = [
    ("word_boundary", DOMAIN, 'r"(?<!\\w)"', 'r""', TEST_DOMAIN + "::test_word_boundaries_and_y_syllable_normalization"),
    ("syllable_y", DOMAIN, '"_".join(_mention_normalize(part) for part in word.split())',
     '_mention_normalize(word.replace(" ", "_"))', TEST_DOMAIN + "::test_word_boundaries_and_y_syllable_normalization"),
    ("candidate_contract", DOMAIN, 'target.get("teaching_status") not in NOT_TARGET', 'True',
     TEST_DOMAIN + "::test_features_order_structure_contract_and_missing_cells"),
    ("taught_main", STAGE, ' or not main.payload.get("main_complete")', '',
     TEST_STAGE + "::test_plan_zero_cost_no_scoring_and_refuses_incomplete_main"),
    ("cache", STAGE, 'if cached is not None:', 'if False:',
     TEST_STAGE + "::test_execute_creates_only_hard_contract_edges_preserves_cost_and_reuses_cache"),
    ("k_zero", STAGE, 'if selected is None or threshold is None or selected[0] < threshold:',
     'if selected is None or (threshold is not None and selected[0] < threshold):', TEST_STAGE + "::test_k_zero_and_no_candidates_never_create_edges"),
    ("threshold", STAGE, 'selected[0] < threshold', 'False',
     TEST_STAGE + "::test_actual_below_threshold_pair_and_main_pruning_do_not_raise_threshold"),
    ("main_pruning", STAGE, 'ledger, main_edges, route=route)', 'ledger, [], route=route)',
     TEST_STAGE + "::test_new_edge_prunes_later_pair_and_main_pruning_excludes_threshold_population"),
    ("dynamic_pruning", STAGE, 'ledger, current, route=route)', 'ledger, main_edges, route=route)',
     TEST_STAGE + "::test_new_hard_path_prunes_later_pair_and_model_provenance_changes_cache"),
    ("best_direction", STAGE, 'selected = max(options)', 'selected = min(options)',
     TEST_STAGE + "::test_higher_direction_and_threshold_are_selected_from_calibrated_candidate_scores"),
    ("hard_only", STAGE, '"prerequisite_kind": "can_de_hieu"', '"prerequisite_kind": "cong_cu"',
     TEST_STAGE + "::test_execute_creates_only_hard_contract_edges_preserves_cost_and_reuses_cache"),
    ("evidence_kind", STAGE, '"evidence_kind": "trong_dinh_nghia"', '"evidence_kind": "noi_ro"',
     TEST_STAGE + "::test_execute_creates_only_hard_contract_edges_preserves_cost_and_reuses_cache"),
    ("contract_validator", STAGE, 'require_kind=True', 'require_kind=False',
     TEST_STAGE + "::test_actual_main_contract_rejects_quote_not_in_original_evidence_chunk"),
    ("closest_quote", STAGE, 'abs(i - (anchor_index or 0))', '-abs(i - (anchor_index or 0))',
     TEST_STAGE + "::test_quote_nearest_anchor_that_passes_contract_is_used"),
    ("retry_quotes", STAGE, 'executor_log.extend(operations)', 'executor_log.extend(operations); break',
     TEST_STAGE + "::test_rejected_nearest_quote_falls_back_to_first_valid_quote"),
    ("determinism", STAGE, 'result = {**payload,', 'result = {**payload, "nonce": __import__("time").time_ns(),',
     TEST_STAGE + "::test_execute_creates_only_hard_contract_edges_preserves_cost_and_reuses_cache"),
    ("model_hash", MODEL, 'if model_hash != manifest.get("sha256_model"):', 'if False:',
     TEST_MODEL + "::test_broken_model_files_stop_with_clear_error[hash]"),
    ("feature_order", MODEL, 'if manifest.get("dac_trung") != list(FEATURE_NAMES):', 'if False:',
     TEST_MODEL + "::test_broken_model_files_stop_with_clear_error[features]"),
    ("missing_value", MODEL, 'self.missing if row[name] in ("", None)', '0.0 if row[name] in ("", None)',
     TEST_MODEL + "::test_scores_blank_as_minus_one_and_interpolates_clipping_both_ends"),
    ("calibration", MODEL, 'return np.interp(scores, self.points, self.probabilities).tolist()', 'return list(scores)',
     TEST_MODEL + "::test_scores_blank_as_minus_one_and_interpolates_clipping_both_ends"),
    ("fixed_population", STAGE, 'judged = {r["pair_id"] for r in log if not r["status"].startswith("pruned_")}',
     'judged = {p["pair_id"] for p in eligible}',
     TEST_STAGE + "::test_fixed_point_changes_initial_threshold_and_discards_trial_edges_and_logs"),
    ("cycle_larger", STAGE, 'max(history[history.index(next_threshold):])', 'min(history[history.index(next_threshold):])',
     TEST_STAGE + "::test_two_threshold_cycle_selects_larger_threshold_not_last_computed"),
    ("cycle_only", STAGE, 'max(history[history.index(next_threshold):])', 'max(history)',
     TEST_STAGE + "::test_cycle_maximum_excludes_transient_threshold_before_cycle"),
    ("zero_after_pruning", STAGE, 'if not next_k:', 'if next_threshold == threshold and not next_k:',
     TEST_STAGE + "::test_zero_k_after_dynamic_pruning_removes_trial_edges_and_stops"),
    ("iteration_limit", STAGE, 'for _ in range(10):', 'for _ in range(11):',
     TEST_STAGE + "::test_threshold_iteration_limit_is_ten_not_early_convergence_or_unbounded"),
    ("limit_maximum", STAGE, 'threshold, stop_reason = max(history), "iteration_limit"',
     'threshold, stop_reason = min(history), "iteration_limit"',
     TEST_STAGE + "::test_threshold_iteration_limit_is_ten_not_early_convergence_or_unbounded"),
    ("final_assembly", STAGE, 'if reassembled:', 'if False:',
     TEST_STAGE + "::test_cycle_reassembles_chosen_threshold_instead_of_saving_last_trial"),
    ("threshold_cache", STAGE, 'round-sum-isotonic-on-judged-directions-fixed-point-10-v1',
     'round-sum-isotonic-on-main-unpruned-directions-v1',
     TEST_STAGE + "::test_fixed_point_rule_does_not_reuse_old_one_shot_cache"),
]


def run(case):
    name, module, old, new, test = case
    code = ("import importlib,sys; from pathlib import Path; "
            f"m=importlib.import_module({module!r}); s=Path(m.__file__).read_text(encoding='utf-8'); "
            f"assert {old!r} in s; exec(compile(s.replace({old!r},{new!r},1),m.__file__,'exec'),m.__dict__); "
            "import pytest; sys.exit(pytest.main(" + repr([test, "-q", "-o", "addopts=", "-p", "no:cacheprovider",
                                                             "--basetemp", f"tmp/pytest-18bc-mutant-{name}"]) + "))")
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                            encoding="utf-8", errors="replace", env={**os.environ, "PYTHONPATH": "src"})
    detected = result.returncode == 1 and "FAILED " in result.stdout
    print(json.dumps({"mutation": name, "detected": detected, "exit": result.returncode}), flush=True)
    if not detected:
        print(result.stdout[-2200:], result.stderr[-500:], flush=True)
    return detected


if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(run, MUTATIONS))
    print(json.dumps({"detected": sum(results), "total": len(results)}))
    sys.exit(0 if all(results) else 1)

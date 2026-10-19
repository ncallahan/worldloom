from __future__ import annotations

import subprocess
import sys
from collections import Counter

from experiments.anchored_succession.contradiction_reporter import report_contradictions
from experiments.anchored_succession.fixtures import generated_parity_instance
from experiments.anchored_succession.measure_construction import succession_chain_problem
from experiments.anchored_succession.model import Anchor, Person, Problem, Rules
from experiments.anchored_succession.oracle import oracle_result
from experiments.anchored_succession.scenarios import stage3_scenarios
from experiments.anchored_succession.stage5_instances import generate_stage5_larger_instance


def test_planted_250_year_chain_has_no_reported_contradictions():
    problem, planted, lower_bound = succession_chain_problem(
        6, horizon_years=250, include_soft_anchors=True
    )
    assert lower_bound == 6
    assert len(planted.titular) == 6
    assert report_contradictions(problem) == ()


def test_known_pin_overlap_and_hand_calculated_eligibility_are_reported():
    overlap = report_contradictions(
        stage3_scenarios()["scenario_2_conflicting_hard_anchors"]
    )
    overlap_findings = [item for item in overlap if item.code == "ANCHOR_OVERLAP"]
    assert len(overlap_findings) == 1
    assert overlap_findings[0].anchor_ids == ("pin-A", "pin-B")
    assert "16–19" in overlap_findings[0].explanation
    assert "pin-A" in overlap_findings[0].explanation
    assert "pin-B" in overlap_findings[0].explanation

    eligibility_problem = Problem(
        people=(Person("A", birth=10, death=20),),
        anchors=(Anchor("hand-ineligible", "hard", "A", start=30, end=33),),
        rules=Rules(
            min_accession_age=16,
            min_reign=3,
            max_reign=8,
            horizon_start=0,
            horizon_end=40,
        ),
    )
    eligibility = report_contradictions(eligibility_problem)
    assert len(eligibility) == 1
    assert eligibility[0].code == "ELIGIBILITY"
    assert eligibility[0].anchor_ids == ("hand-ineligible",)
    assert "30–33" in eligibility[0].explanation
    assert "earliest age-eligible year 26" in eligibility[0].explanation
    assert "death year 20" in eligibility[0].explanation


def test_seeded_small_instances_have_no_false_positive_flags_against_oracle(capsys):
    counts = Counter()
    oracle_infeasible_not_flagged = 0
    total_flagged = 0
    for index in range(20):
        problem = generated_parity_instance(index, seed=20261015)
        oracle = oracle_result(problem, node_cap=100_000)
        findings = report_contradictions(problem)
        counts["oracle_" + oracle.status] += 1
        if findings:
            total_flagged += 1
            assert oracle.status == "infeasible", (
                f"false-positive contradiction on seeded instance {index}: "
                f"oracle={oracle.status}, findings={findings}"
            )
            counts.update(item.code for item in findings)
        elif oracle.status == "infeasible":
            oracle_infeasible_not_flagged += 1
    assert total_flagged > 0, "non-vacuity guard: at least one seeded case must be flagged"
    assert counts["oracle_solved"] > 0
    assert counts["oracle_infeasible"] > 0
    with capsys.disabled():
        print(
            "Solver-free reporter seeded-small results: "
            f"instances=20, oracle-feasible={counts['oracle_solved']}, "
            f"oracle-infeasible={counts['oracle_infeasible']}, flagged-infeasible={total_flagged}, "
            f"oracle-infeasible-not-flagged={oracle_infeasible_not_flagged}, "
            f"flags-by-code={{ELIGIBILITY:{counts['ELIGIBILITY']}, "
            f"ANCHOR_OVERLAP:{counts['ANCHOR_OVERLAP']}, "
            f"NO_KIN_PATH:{counts['NO_KIN_PATH']}}}"
        )


def test_stage5_larger_instances_report_actual_flags_without_solver(capsys):
    counts = Counter()
    not_flagged = []
    for index in range(20):
        generated = generate_stage5_larger_instance(index)
        findings = report_contradictions(generated.problem)
        if not findings:
            not_flagged.append(index)
        counts.update(item.code for item in findings)
    assert len(not_flagged) <= 20
    assert sum(counts.values()) > 0, "non-vacuity guard: Stage 5 sample must exercise a check"
    with capsys.disabled():
        print(
            "Solver-free reporter Stage 5 results: instances=20, "
            f"flag-counts={{ELIGIBILITY:{counts['ELIGIBILITY']}, "
            f"ANCHOR_OVERLAP:{counts['ANCHOR_OVERLAP']}, "
            f"NO_KIN_PATH:{counts['NO_KIN_PATH']}, GAP_COVERAGE:{counts['GAP_COVERAGE']}}}, "
            f"not-flagged-count={len(not_flagged)}, not-flagged-indices={not_flagged}"
        )


def test_reporter_and_stage5_generator_import_without_solver_packages():
    script = (
        "import sys; "
        "import experiments.anchored_succession.contradiction_reporter; "
        "import experiments.anchored_succession.stage5_instances; "
        "assert not any(name == 'ortools' or name.startswith('ortools.') for name in sys.modules); "
        "assert not any(name == 'clingo' or name.startswith('clingo.') for name in sys.modules)"
    )
    completed = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr

from __future__ import annotations

from doc2roadmap.application.phase_b.quiz import QuizUseCase
from doc2roadmap.domain import phase_b_pricing
from doc2roadmap.domain.phase_b_limits import BSettings
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore

from sa68_support import make_book


def test_dry_run_quiz_cost_uses_shared_price_table_and_separate_model_ids(monkeypatch):
    class Model:
        def __init__(self, model_id):
            self.model_id = model_id

    monkeypatch.setitem(phase_b_pricing.PRICES_USD_PER_MILLION,
                        "generator-test", {"input": 2.0, "output": 4.0})
    monkeypatch.setitem(phase_b_pricing.PRICES_USD_PER_MILLION,
                        "verifier-test", {"input": 3.0, "output": 5.0})
    usecase = QuizUseCase(make_book(plain=1, formula=False), InMemoryPhaseBStore(), Model("generator-test"),
                          verifier_model=Model("verifier-test"),
                          settings=BSettings(quiz_generation_max_output_tokens=50, quiz_verifier_max_output_tokens=20))

    result = usecase.make_quiz("d", "m", "alice", dry_run=True)
    gen_input, gen_output, verify_input, verify_output = usecase._bank_estimate_token_breakdown(
        usecase._material(usecase._concepts("m", ["n1"])[0]))
    expected = (phase_b_pricing.estimate_cost("generator-test", gen_input, gen_output)
                + phase_b_pricing.estimate_cost("verifier-test", verify_input, verify_output))

    assert (gen_output, verify_output) == (2 * 50, 2 * 20)
    assert result["estimated_usd"] == round(expected, 6)
    assert result["estimated_calls"] == 4

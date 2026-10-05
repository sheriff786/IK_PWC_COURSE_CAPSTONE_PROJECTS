"""Closed-loop recovery: each failure class must get a DIFFERENT strategy,
not the same call repeated. These run with no network access."""

from contractiq.resilience import (
    AUTH,
    QUOTA,
    RATE_LIMIT,
    SCHEMA,
    TRANSIENT,
    SchemaFailure,
    call_with_recovery,
    diagnose,
)


class _RateLimitError(Exception):
    pass


def test_failures_are_classified_not_treated_uniformly():
    assert diagnose(Exception("You have no credits remaining")) == QUOTA
    assert diagnose(Exception("insufficient_quota")) == QUOTA
    assert diagnose(Exception("Invalid API key provided")) == AUTH
    assert diagnose(_RateLimitError("429 Too Many Requests")) == RATE_LIMIT
    assert diagnose(TimeoutError("request timed out")) == TRANSIENT
    assert diagnose(SchemaFailure("unparseable")) == SCHEMA


def test_quota_failure_is_not_retried():
    """A retry cannot refill an empty balance — burning attempts on it just
    hides the real problem, so the loop must fail fast."""
    attempts = []

    def operation(model):
        attempts.append(model)
        raise Exception("You have no credits remaining")

    result = call_with_recovery(operation, stage="test", model="cheap",
                                 max_attempts=3, on_give_up=lambda s, e: "degraded")
    assert result == "degraded"
    assert len(attempts) == 1, "quota failure must not be retried"


def test_schema_failure_escalates_to_a_stronger_model():
    """Repeating the same model after a parse failure is the one strategy
    already known not to work — the loop must change models instead."""
    attempts = []

    def operation(model):
        attempts.append(model)
        if model == "cheap":
            raise SchemaFailure("bad output")
        return "parsed-by-stronger-model"

    result = call_with_recovery(operation, stage="test", model="cheap",
                                 escalation_model="strong", max_attempts=3)
    assert result == "parsed-by-stronger-model"
    assert attempts == ["cheap", "strong"]


def test_transient_failure_retries_same_model_then_succeeds():
    attempts = []

    def operation(model):
        attempts.append(model)
        if len(attempts) == 1:
            raise TimeoutError("timed out")
        return "ok"

    result = call_with_recovery(operation, stage="test", model="cheap", max_attempts=3)
    assert result == "ok"
    assert attempts == ["cheap", "cheap"], "transient errors back off, they don't escalate"


def test_exhausted_attempts_degrade_gracefully_instead_of_crashing():
    def operation(model):
        raise TimeoutError("always down")

    result = call_with_recovery(operation, stage="test", model="cheap", max_attempts=2,
                                 on_give_up=lambda s, e: None)
    assert result is None, "caller stays alive with a degraded result"

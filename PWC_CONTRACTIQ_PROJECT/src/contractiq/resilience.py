"""
ContractIQ — closed-loop failure recovery.

Used by every LLM call path (agents.py, retrieval.py). The loop is
explicitly: DETECT a failure -> DIAGNOSE what kind it is -> SELECT a
strategy that differs from the one that just failed -> LOG the outcome.

This is deliberately NOT "retry the same call N times": repeating an
identical request is the one strategy already known not to work for the
failure that just happened. Each failure class gets a different response:

  transient (timeout, 5xx, connection)  -> exponential backoff, same model
  rate_limit                            -> longer backoff, same model
  schema / refusal                      -> escalate to the stronger model
  quota / auth                          -> do NOT retry; fail fast and
                                           degrade gracefully (a retry
                                           cannot fix an empty balance)
"""

from __future__ import annotations

import json
import random
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional, TypeVar

from .config import (
    ESCALATION_AGENT_MODEL,
    REPORTS_ROOT,
    RETRY_BASE_DELAY_SECONDS,
    RETRY_MAX_ATTEMPTS,
    RETRY_MAX_DELAY_SECONDS,
)

T = TypeVar("T")

_RECOVERY_LOG = REPORTS_ROOT / "phase7_recovery_events.jsonl"

TRANSIENT = "transient"
RATE_LIMIT = "rate_limit"
SCHEMA = "schema"
QUOTA = "quota"
AUTH = "auth"
UNKNOWN = "unknown"

# Failure classes that no amount of retrying can fix — retrying them just
# burns wall-clock time and hides the real problem from the operator.
_NON_RETRYABLE = {QUOTA, AUTH}


class SchemaFailure(Exception):
    """Call succeeded at the transport level but the model returned output
    that could not be parsed into the required structure (or refused)."""


def diagnose(exc: BaseException) -> str:
    """Classifies a failure so a DIFFERENT strategy can be chosen per class.
    Matches on type name + message text rather than importing every SDK's
    exception hierarchy, so this keeps working if a provider is swapped."""
    if isinstance(exc, SchemaFailure):
        return SCHEMA

    name = type(exc).__name__.lower()
    message = str(exc).lower()

    if "insufficient_quota" in message or "credit balance" in message or "no credits" in message:
        return QUOTA
    if "authenticationerror" in name or "invalid api key" in message or "unauthorized" in message:
        return AUTH
    if "ratelimit" in name or "rate limit" in message or "429" in message:
        return RATE_LIMIT
    if any(k in name for k in ("timeout", "connection", "apierror", "internalserver")):
        return TRANSIENT
    if any(k in message for k in ("timeout", "temporarily unavailable", "503", "502", "500")):
        return TRANSIENT
    return UNKNOWN


def _backoff_seconds(attempt: int, failure_class: str) -> float:
    """Exponential backoff with jitter. Rate limits get a longer floor —
    retrying a 429 as fast as a timeout just re-triggers the 429."""
    multiplier = 3.0 if failure_class == RATE_LIMIT else 1.0
    delay = min(RETRY_BASE_DELAY_SECONDS * (2 ** attempt) * multiplier, RETRY_MAX_DELAY_SECONDS)
    return delay + random.uniform(0, 0.3 * delay)  # jitter avoids thundering herd


def log_recovery_event(stage: str, attempt: int, failure_class: str,
                        strategy: str, outcome: str, detail: str = "") -> None:
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "stage": stage,
        "attempt": attempt,
        "failure_class": failure_class,
        "strategy": strategy,
        "outcome": outcome,
        "detail": detail[:400],
    }
    with open(_RECOVERY_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def read_recovery_events() -> list[Dict[str, Any]]:
    if not _RECOVERY_LOG.exists():
        return []
    return [json.loads(line) for line in _RECOVERY_LOG.read_text(encoding="utf-8").splitlines()
            if line.strip()]


def call_with_recovery(
    operation: Callable[[str], T],
    *,
    stage: str,
    model: str,
    escalation_model: str = ESCALATION_AGENT_MODEL,
    max_attempts: int = RETRY_MAX_ATTEMPTS,
    on_give_up: Optional[Callable[[str, BaseException], T]] = None,
) -> T:
    """Runs `operation(model)` under the closed recovery loop above.

    `operation` takes the model name so the loop can hand it a DIFFERENT
    model when escalation is the chosen strategy. If every attempt fails,
    `on_give_up` produces a degraded-but-valid result (graceful degradation)
    instead of raising — callers above this layer stay alive and the partial
    outcome is still recorded honestly.
    """
    current_model = model
    last_exc: Optional[BaseException] = None

    for attempt in range(max_attempts):
        try:
            result = operation(current_model)
            if attempt > 0:
                log_recovery_event(stage, attempt, diagnose(last_exc) if last_exc else UNKNOWN,
                                    f"recovered_on_model={current_model}", "success")
            return result
        except BaseException as exc:  # noqa: BLE001 - classified below, never swallowed silently
            last_exc = exc
            failure_class = diagnose(exc)

            if failure_class in _NON_RETRYABLE:
                log_recovery_event(stage, attempt, failure_class, "fail_fast", "gave_up", str(exc))
                break

            if attempt == max_attempts - 1:
                log_recovery_event(stage, attempt, failure_class, "none_left", "gave_up", str(exc))
                break

            # Select a strategy that DIFFERS from the one that just failed.
            if failure_class == SCHEMA:
                strategy = f"escalate_model:{current_model}->{escalation_model}"
                current_model = escalation_model
            else:
                delay = _backoff_seconds(attempt, failure_class)
                strategy = f"backoff:{delay:.1f}s"
                time.sleep(delay)

            log_recovery_event(stage, attempt, failure_class, strategy, "retrying", str(exc))

    if on_give_up is not None and last_exc is not None:
        return on_give_up(stage, last_exc)
    assert last_exc is not None
    raise last_exc

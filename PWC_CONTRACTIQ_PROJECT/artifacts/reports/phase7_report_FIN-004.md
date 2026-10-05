# ContractIQ Risk Report — FIN-004

**Overall risk:** MEDIUM  
**Assessment ID:** assessment-FIN-004-468e2923  
**Run ID:** 70ad431a9a5f  
**Document version:** 1  
**Model version:** gpt-4o-mini  
**Prompt version:** phase5-specialist-prompts-v1  
**Policy version:** risk-policy-v1  
**Created at:** 2026-09-26T13:09:52.866704  
**Report generated:** 2026-10-05T20:14:09.217366+00:00

## Specialist statuses
- **legal**: OK, 0 finding(s), retry_count=0
- **financial**: OK, 3 finding(s), retry_count=0
- **operational**: OK, 4 finding(s), retry_count=0

## Findings (by severity)
- **[MEDIUM] Payment Terms and Schedule** (confidence=0.9)
  - rationale: The contract specifies the payment terms clearly, including the due date and conditions for late payment.
  - evidence: `['FIN-004-c0']` — "Payment due within 15 calendar days of invoice date. Late payment subject to 1.5% monthly interest."
- **[MEDIUM] Late Payment Penalty Details** (confidence=0.9)
  - rationale: The evidence specifies the penalties for late payments, including the interest rate applicable.
  - evidence: `['FIN-004-c0']` — "Late payment subject to 1.5% monthly interest."
- **[MEDIUM] Pricing Structure and Fee Schedule** (confidence=0.3)  ⚠ uncertainty: failed_verification
  - rationale: The evidence provides a detailed breakdown of the pricing structure, including subtotal, GST, and total invoice amount, as well as payment terms and conditions.
  - evidence: `['FIN-004-c0']` — "Subtotal: INR 3,300,000
GST @18%: INR 594,000
Total Invoice Amount: INR 3,894,000
Payment due within 15 calendar days of invoice date.
Late payment subject to 1.5% monthly interest."
- **[MEDIUM] Scope of Work and Deliverables** (confidence=0.9)
  - rationale: The evidence provides details about the products and services delivered under the contract, including hardware delivery, acceptance testing, and warranty support.
  - evidence: `['FIN-004-c0']` — "1. Description of Products / Services"
- **[MEDIUM] Acceptance Criteria for Deliverables** (confidence=0.9)
  - rationale: The evidence specifies the acceptance testing criteria for the deliverables, which include functional tests, performance benchmarks, and network integration tests, along with the requirement to report discrepancies within a specified timeframe.
  - evidence: `['FIN-004-c0']` — "Acceptance testing included: functional tests, performance benchmarks, and network integration tests."
- **[MEDIUM] Service Level and Performance Commitments** (confidence=0.9)
  - rationale: The vendor commits to providing 24x7 remote and onsite support for troubleshooting and preventive maintenance, which is a key service level commitment.
  - evidence: `['FIN-004-c0']` — "Primevolta provides 24x7 remote and onsite support for troubleshooting and preventive maintenance."
- **[MEDIUM] Service Performance Measurement and Reporting** (confidence=0.9)
  - rationale: The evidence specifies that acceptance testing included functional tests, performance benchmarks, and network integration tests, which are key indicators of service performance measurement.
  - evidence: `['FIN-004-c0']` — "Acceptance testing included: functional tests, performance benchmarks, and network integration tests."

## Uncertainty / unresolved issues
_None reported._

## Recommendations (consensus actions)
_None — no HIGH/CRITICAL findings to flag._
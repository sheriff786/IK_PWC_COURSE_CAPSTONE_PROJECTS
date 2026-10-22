# ContractIQ Risk Report — GOV-004

**Overall risk:** MEDIUM  
**Assessment ID:** assessment-GOV-004-6c71cbf8  
**Run ID:** b7b805378ac9  
**Document version:** 1  
**Model version:** gpt-4o-mini  
**Prompt version:** phase5-specialist-prompts-v1  
**Policy version:** risk-policy-v1  
**Created at:** 2026-10-22T23:59:56.587640  
**Report generated:** 2026-10-22T18:32:54.277440+00:00

## Specialist statuses
- **financial**: OK, 4 finding(s), retry_count=0
- **legal**: OK, 1 finding(s), retry_count=0
- **operational**: OK, 6 finding(s), retry_count=0

## Findings (by severity)
- **[HIGH] Service Level Commitments** (confidence=0.95)
  - rationale: The vendor commits to specific service levels as outlined in the Key Performance Indicators (KPIs).
  - evidence: `['GOV-004-c1', 'GOV-004-c0']` — "Delivery SLA compliance ≥ 98%
Preventive maintenance completion ≥ 95%
Invoice error rate ≤ 0.5%
Dispute resolution average ≤ 10 business days"
- **[MEDIUM] Pricing Adjustment Proposal** (confidence=0.9)
  - rationale: The evidence specifies a proposed pricing adjustment reflecting inflation and service enhancements.
  - evidence: `['GOV-004-c0']` — "Pricing adjustment: 5–7% increase reflecting inflation, supply chain escalation, and service enhancement investments."
- **[MEDIUM] Price Adjustment Clause Identified** (confidence=0.9)
  - rationale: The evidence indicates a proposed pricing adjustment reflecting inflation and supply chain escalation, which constitutes a price escalation clause.
  - evidence: `['GOV-004-c0']` — "Pricing adjustment: 5–7% increase reflecting inflation, supply chain escalation, and service enhancement investments."
- **[MEDIUM] Renewal Pricing Adjustment** (confidence=0.9)
  - rationale: The renewal pricing reflects an increase due to various factors, indicating a structured approach to renewal terms.
  - evidence: `['GOV-004-c0']` — "Pricing adjustment: 5–7% increase reflecting inflation, supply chain escalation, and service enhancement investments."
- **[MEDIUM] Financial Exposure Cap and Penalties** (confidence=0.85)
  - rationale: The evidence discusses the introduction of penalties for SLA breaches, which implies a cap on financial exposure related to service level agreements.
  - evidence: `['GOV-004-c0']` — "Include penalties for repeated SLA breaches beyond three instances per contract year."
- **[MEDIUM] Notice Period for Termination** (confidence=0.9)
  - rationale: The evidence specifies the notice period required for early termination of the contract.
  - evidence: `['GOV-004-c0']` — "Early termination: 90-day notice with full reconciliation of outstanding invoices and obligations."
- **[MEDIUM] Scope of Work and Deliverables** (confidence=0.9)
  - rationale: The evidence outlines the obligations and performance metrics related to hardware supply, maintenance, and support services, which define the scope of work under the agreement.
  - evidence: `['GOV-004-c0']` — "This document serves as a detailed reference for negotiating the renewal of the Master Service Agreement (MSA) between PrimeVolta Hardware Solutions (Vendor) and FinSecure Services (Client)."
- **[MEDIUM] Acceptance Criteria for Deliverables** (confidence=0.9)
  - rationale: The acceptance criteria for deliverables under this agreement are defined by the Key Performance Indicators (KPIs) outlined in the contract, which specify the minimum performance levels required for compliance.
  - evidence: `['GOV-004-c1', 'GOV-004-c0']` — "Delivery SLA compliance ≥ 98%
Preventive maintenance completion ≥ 95%
Invoice error rate ≤ 0.5%
Dispute resolution average ≤ 10 business days"
- **[MEDIUM] SLA Breach Penalties** (confidence=0.9)
  - rationale: The evidence discusses proposed SLA revisions and penalties for repeated SLA breaches, indicating that remedies are in place for missed service level targets.
  - evidence: `['GOV-004-c0']` — "Include penalties for repeated SLA breaches beyond three instances per contract year."
  - recommendation: Consider finalizing the proposed SLA revisions and penalties to ensure accountability.
- **[MEDIUM] Client-Side Obligations for Vendor Performance** (confidence=0.9)
  - rationale: The evidence outlines specific client action items that the vendor relies on for performance, indicating dependencies on the client's obligations.
  - evidence: `['GOV-004-c1', 'GOV-004-c0']` — "Client Action Items
Review historical dispute data and provide feedback on pain points.
Assess acceptance of revised KPIs and SLA penalties.
Confirm governance and reporting requirements for dashboard..."
  - recommendation: Ensure timely feedback and assessment of revised KPIs and SLA penalties to support vendor performance.
- **[MEDIUM] Performance Reporting Mechanisms** (confidence=0.9)
  - rationale: The contract outlines specific Key Performance Indicators (KPIs) and governance requirements for performance reporting, including monthly operational dashboards and quarterly executive reviews.
  - evidence: `['GOV-004-c0']` — "Monthly operational dashboards detailing delivery status, SLA compliance, invoice alignment, and dispute trends."
  - recommendation: Ensure adherence to the outlined KPIs and governance structures for effective performance monitoring.

## Uncertainty / unresolved issues
_None reported._

## Recommendations (consensus actions)
- Review: [operational] Service Level Commitments
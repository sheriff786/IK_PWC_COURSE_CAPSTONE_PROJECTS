# ContractIQ Risk Report — GOV-004

**Overall risk:** MEDIUM  
**Assessment ID:** assessment-GOV-004-ccf0633b  
**Run ID:** 5f8d35c6feb4  
**Document version:** 1  
**Model version:** gpt-4o-mini  
**Prompt version:** phase5-specialist-prompts-v1  
**Policy version:** risk-policy-v1  
**Created at:** 2026-09-26T13:10:36.429772  
**Report generated:** 2026-10-05T20:14:09.217735+00:00

## Specialist statuses
- **financial**: OK, 4 finding(s), retry_count=0
- **operational**: OK, 6 finding(s), retry_count=0
- **legal**: OK, 2 finding(s), retry_count=0

## Findings (by severity)
- **[HIGH] Service Level Commitments** (confidence=0.95)
  - rationale: The vendor commits to specific service levels as outlined in the Key Performance Indicators (KPIs) section of the contract.
  - evidence: `['GOV-004-c1', 'GOV-004-c0']` — "Delivery SLA compliance ≥ 98%
Preventive maintenance completion ≥ 95%
Invoice error rate ≤ 0.5%
Dispute resolution average ≤ 10 business days"
- **[MEDIUM] Proposed Pricing Adjustment** (confidence=0.9)
  - rationale: The contract outlines a proposed pricing adjustment reflecting inflation and service enhancements, indicating a structured pricing approach.
  - evidence: `['GOV-004-c0']` — "Pricing adjustment: 5–7% increase reflecting inflation, supply chain escalation, and service enhancement investments."
- **[MEDIUM] Price Adjustment Clause Identified** (confidence=0.9)
  - rationale: The contract includes a pricing adjustment clause that reflects inflation and supply chain escalation.
  - evidence: `['GOV-004-c0']` — "Pricing adjustment: 5–7% increase reflecting inflation, supply chain escalation, and service enhancement investments."
- **[MEDIUM] Renewal Pricing Adjustment** (confidence=0.9)
  - rationale: The proposed renewal terms include a pricing adjustment that reflects various factors such as inflation and service enhancements.
  - evidence: `['GOV-004-c0']` — "Pricing adjustment: 5–7% increase reflecting inflation, supply chain escalation, and service enhancement investments."
- **[MEDIUM] Penalties for SLA Breaches** (confidence=0.85)
  - rationale: The contract includes provisions for penalties related to SLA breaches, which indicates a cap on financial exposure in terms of penalties.
  - evidence: `['GOV-004-c0']` — "Include penalties for repeated SLA breaches beyond three instances per contract year."
- **[MEDIUM] Scope of Work and Deliverables** (confidence=0.9)
  - rationale: The evidence outlines the obligations and performance metrics related to the hardware supply, maintenance, and support services provided by PrimeVolta Hardware Solutions to FinSecure Services, which defines the scope of work under the agreement.
  - evidence: `['GOV-004-c0']` — "This document serves as a detailed reference for negotiating the renewal of the Master Service Agreement (MSA) between PrimeVolta Hardware Solutions (Vendor) and FinSecure Services (Client)."
- **[MEDIUM] Acceptance Criteria for Deliverables** (confidence=0.9)
  - rationale: The acceptance criteria for deliverables are defined by the Key Performance Indicators (KPIs) outlined in the contract, which specify the minimum performance levels required for compliance.
  - evidence: `['GOV-004-c1', 'GOV-004-c0']` — "Delivery SLA compliance ≥ 98%
Preventive maintenance completion ≥ 95%
Invoice error rate ≤ 0.5%
Dispute resolution average ≤ 10 business days"
- **[MEDIUM] SLA Breach Penalties** (confidence=0.9)
  - rationale: The contract includes provisions for penalties related to SLA breaches, specifically mentioning that penalties will be included for repeated SLA breaches beyond three instances per contract year.
  - evidence: `['GOV-004-c0']` — "Include penalties for repeated SLA breaches beyond three instances per contract year."
  - recommendation: Ensure that the SLA penalties are clearly defined and communicated to all stakeholders.
- **[MEDIUM] Client-Side Obligations for Vendor Performance** (confidence=0.9)
  - rationale: The evidence outlines specific client action items that the vendor relies on for performance, indicating dependencies on the client's obligations.
  - evidence: `['GOV-004-c1', 'GOV-004-c0']` — "Client Action Items
Review historical dispute data and provide feedback on pain points.
Assess acceptance of revised KPIs and SLA penalties.
Confirm governance and reporting requirements for dashboard..."
  - recommendation: Ensure timely feedback and assessment of revised KPIs and SLA penalties to support vendor performance.
- **[MEDIUM] Performance Reporting Mechanisms** (confidence=0.9)
  - rationale: The contract specifies various Key Performance Indicators (KPIs) that measure service performance, including delivery SLA compliance, preventive maintenance completion, invoice error rate, and dispute resolution timelines. Additionally, it outlines governance and reporting requirements such as monthly operational dashboards and quarterly executive reviews to discuss performance metrics.
  - evidence: `['GOV-004-c0']` — "Monthly operational dashboards detailing delivery status, SLA compliance, invoice alignment, and dispute trends."
  - recommendation: Ensure that the reporting mechanisms are implemented effectively to track and improve performance against the KPIs.
- **[MEDIUM] Conditions for Termination for Cause** (confidence=0.9)
  - rationale: The contract specifies conditions under which it can be terminated, including the requirement for a 90-day notice and full reconciliation of outstanding invoices and obligations.
  - evidence: `['GOV-004-c0']` — "Early termination: 90-day notice with full reconciliation of outstanding invoices and obligations."
- **[MEDIUM] Notice Period for Termination** (confidence=0.9)
  - rationale: The evidence specifies the notice period required for early termination of the contract.
  - evidence: `['GOV-004-c0']` — "Early termination: 90-day notice with full reconciliation of outstanding invoices and obligations."

## Uncertainty / unresolved issues
_None reported._

## Recommendations (consensus actions)
- Review: [operational] Service Level Commitments
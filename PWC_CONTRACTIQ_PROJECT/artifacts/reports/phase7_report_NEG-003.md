# ContractIQ Risk Report — NEG-003

**Overall risk:** MEDIUM  
**Assessment ID:** assessment-NEG-003-6868216e  
**Run ID:** 2751da02eb2e  
**Document version:** 1  
**Model version:** gpt-4o-mini  
**Prompt version:** phase5-specialist-prompts-v1  
**Policy version:** risk-policy-v1  
**Created at:** 2026-10-22T23:59:36.425211  
**Report generated:** 2026-10-22T18:32:54.287441+00:00

## Specialist statuses
- **financial**: OK, 3 finding(s), retry_count=0
- **operational**: OK, 3 finding(s), retry_count=0
- **legal**: OK, 6 finding(s), retry_count=0

## Findings (by severity)
- **[HIGH] Scope of Work Defined** (confidence=0.3)  ⚠ uncertainty: failed_verification
  - rationale: The evidence clearly outlines the scope of work and deliverables under the agreement, specifying the responsibilities of the Vendor.
  - evidence: `['NEG-003-c0']` — "Vendor shall supply the Hardware as per specifications in Annexure A. Vendor shall provide installation, configuration, and integration services. Vendor shall provide training to Client staff for a pe..."
- **[HIGH] Service Level Commitments** (confidence=0.9)
  - rationale: The vendor commits to a service uptime SLA of 99.9%, which was a request from the client, indicating a performance commitment under the agreement.
  - evidence: `['NEG-003-c0']` — "Client requested inclusion of service uptime SLA of 99.9% (Vendor initially proposed 98%)."
- **[MEDIUM] Pricing Structure and Payment Terms** (confidence=0.9)
  - rationale: The evidence provides a detailed breakdown of the pricing structure and payment terms for the contract, including total contract value and payment milestones.
  - evidence: `['NEG-003-c0']` — "4.1 Total Contract Value: $2,500,000 USD.
4.2 Payment Schedule:
30% advance on signing the agreement
50% upon delivery and acceptance of Hardware
20% upon completion of installation and integration"
- **[MEDIUM] Cap on Financial Exposure** (confidence=0.9)
  - rationale: The contract specifies that the Vendor's liability shall not exceed the total contract value, which indicates a cap on financial exposure.
  - evidence: `['NEG-003-c0']` — "Vendor’s liability shall not exceed total contract value."
- **[MEDIUM] Acceptance Criteria for Deliverables** (confidence=0.9)
  - rationale: The evidence discusses the payment schedule tied to acceptance testing, indicating that acceptance criteria are part of the agreement.
  - evidence: `['NEG-003-c0']` — "Client requested milestone-based payments tied to acceptance testing rather than delivery date."
- **[MEDIUM] Limitation of Liability Specified** (confidence=0.9)
  - rationale: The evidence specifies that the Vendor's liability is limited to the total contract value, addressing the topic of liability cap.
  - evidence: `['NEG-003-c0']` — "Vendor’s liability shall not exceed total contract value."
- **[MEDIUM] Indemnification Obligations** (confidence=0.9)
  - rationale: The evidence specifies the indemnification obligations of the Vendor towards the Client.
  - evidence: `['NEG-003-c0']` — "7.1 Vendor shall indemnify Client for damages arising from Vendor’s gross negligence."
- **[MEDIUM] Termination for Cause Conditions** (confidence=0.9)
  - rationale: The contract specifies that either party may terminate the agreement on material breach with 60 days’ notice.
  - evidence: `['NEG-003-c0']` — "Either party may terminate on material breach with 60 days’ notice."
- **[MEDIUM] Termination for Convenience Notice Period** (confidence=0.9)
  - rationale: The evidence specifies the notice period required for termination for convenience.
  - evidence: `['NEG-003-c0']` — "Termination for convenience requires 90 days’ notice with proportional payments for delivered goods."
- **[MEDIUM] Confidentiality Obligations Survival Duration** (confidence=0.9)
  - rationale: The evidence specifies the duration for which confidentiality obligations survive after the agreement ends.
  - evidence: `['NEG-003-c0']` — "Confidentiality obligations shall survive termination of this agreement for 3 years."
- **[MEDIUM] Governing Law and Dispute Resolution** (confidence=0.9)
  - rationale: The evidence specifies the governing law and the method for resolving disputes, indicating that arbitration will be used if amicable resolution fails.
  - evidence: `['NEG-003-c0']` — "Failing that, disputes shall be referred to arbitration under [Country] Arbitration Act."
- **[LOW] Payment Terms and Schedule** (confidence=0.9)
  - rationale: The payment terms and schedule are clearly outlined in the contract, specifying the percentages due at various stages of the agreement.
  - evidence: `['NEG-003-c0']` — "4.2 Payment Schedule:
30% advance on signing the agreement
50% upon delivery and acceptance of Hardware
20% upon completion of installation and integration"

## Uncertainty / unresolved issues
- HITL [operational] 'Scope of Work Defined': quoted evidence could not be verified against source text — needs human confirmation before use.

## Recommendations (consensus actions)
- Review: [operational] Scope of Work Defined
- Review: [operational] Service Level Commitments
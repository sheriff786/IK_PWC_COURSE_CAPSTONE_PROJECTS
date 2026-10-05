# ContractIQ Risk Report — NEG-003

**Overall risk:** MEDIUM  
**Assessment ID:** assessment-NEG-003-19bc435e  
**Run ID:** 9fab9bac90c2  
**Document version:** 1  
**Model version:** gpt-4o-mini  
**Prompt version:** phase5-specialist-prompts-v1  
**Policy version:** risk-policy-v1  
**Created at:** 2026-09-26T13:10:25.185893  
**Report generated:** 2026-10-05T20:14:09.221992+00:00

## Specialist statuses
- **operational**: OK, 4 finding(s), retry_count=0
- **financial**: OK, 3 finding(s), retry_count=0
- **legal**: OK, 6 finding(s), retry_count=0

## Findings (by severity)
- **[HIGH] Service Level Commitments** (confidence=0.3)  ⚠ uncertainty: failed_verification
  - rationale: The vendor commits to a service uptime SLA of 99.9%, which was a request from the client, and also provides technical support 24x7.
  - evidence: `['NEG-003-c0']` — "Client requested inclusion of service uptime SLA of 99.9% (Vendor initially proposed 98%). Vendor shall provide technical support 24x7."
- **[MEDIUM] Scope of Work Defined** (confidence=0.9)
  - rationale: The evidence clearly outlines the scope of work and deliverables under the agreement, specifying the responsibilities of the Vendor.
  - evidence: `['NEG-003-c0']` — "3. Scope of Supply
3.1 Vendor shall supply the Hardware as per specifications in Annexure A.
3.2 Vendor shall provide installation, configuration, and integration services.
3.3 Vendor shall provide tr..."
- **[MEDIUM] Acceptance Criteria for Deliverables** (confidence=0.85)
  - rationale: The evidence specifies that the Client requested milestone-based payments tied to acceptance testing, indicating that acceptance criteria are part of the agreement.
  - evidence: `['NEG-003-c0']` — "Client requested milestone-based payments tied to acceptance testing rather than delivery date."
- **[MEDIUM] Client-Side Obligations for Vendor Performance** (confidence=0.85)
  - rationale: The vendor relies on the client to fulfill certain obligations that are critical for the vendor's performance, such as timely acceptance of hardware and adherence to payment schedules tied to acceptance testing.
  - evidence: `['NEG-003-c0']` — "Client requested milestone-based payments tied to acceptance testing rather than delivery date."
- **[MEDIUM] Pricing Structure and Payment Terms** (confidence=0.9)
  - rationale: The contract specifies a clear pricing structure and payment terms, detailing the total contract value and the payment schedule based on milestones.
  - evidence: `['NEG-003-c0']` — "4.1 Total Contract Value: $2,500,000 USD.
4.2 Payment Schedule:
30% advance on signing the agreement
50% upon delivery and acceptance of Hardware
20% upon completion of installation and integration"
- **[MEDIUM] Cap on Financial Exposure** (confidence=0.9)
  - rationale: The contract specifies that the Vendor's liability shall not exceed the total contract value, which effectively caps the financial exposure.
  - evidence: `['NEG-003-c0']` — "Vendor’s liability shall not exceed total contract value."
- **[MEDIUM] Limitation of Liability** (confidence=0.9)
  - rationale: The evidence explicitly states that the Vendor's liability is limited to the total contract value, which addresses the topic of liability cap.
  - evidence: `['NEG-003-c0']` — "Vendor’s liability shall not exceed total contract value."
- **[MEDIUM] Indemnification Obligations of Vendor** (confidence=0.9)
  - rationale: The evidence specifies the indemnification obligations of the Vendor towards the Client.
  - evidence: `['NEG-003-c0']` — "7.1 Vendor shall indemnify Client for damages arising from Vendor’s gross negligence."
- **[MEDIUM] Termination for Cause Conditions** (confidence=0.9)
  - rationale: The contract specifies that either party may terminate the agreement on material breach with 60 days’ notice, indicating the conditions under which termination for cause can occur.
  - evidence: `['NEG-003-c0']` — "Either party may terminate on material breach with 60 days’ notice."
- **[MEDIUM] Termination for Convenience Notice Period** (confidence=0.9)
  - rationale: The evidence specifies the notice period required for termination for convenience.
  - evidence: `['NEG-003-c0']` — "Termination for convenience requires 90 days’ notice with proportional payments for delivered goods."
- **[MEDIUM] Governing Law and Dispute Resolution** (confidence=0.9)
  - rationale: The evidence specifies the governing law and the method for resolving disputes between the parties.
  - evidence: `['NEG-003-c0']` — "9.2 Failing that, disputes shall be referred to arbitration under [Country] Arbitration Act."
- **[LOW] Payment Terms and Schedule** (confidence=0.9)
  - rationale: The payment terms and schedule are clearly outlined in the contract, specifying the percentages due at various stages of the agreement.
  - evidence: `['NEG-003-c0']` — "4.2 Payment Schedule:
30% advance on signing the agreement
50% upon delivery and acceptance of Hardware
20% upon completion of installation and integration"
- **[LOW] Confidentiality Obligations Survival Duration** (confidence=0.9)
  - rationale: The evidence explicitly states the duration for which confidentiality obligations survive after the agreement ends.
  - evidence: `['NEG-003-c0']` — "Confidentiality obligations shall survive termination of this agreement for 3 years."

## Uncertainty / unresolved issues
_None reported._

## Recommendations (consensus actions)
- Review: [operational] Service Level Commitments
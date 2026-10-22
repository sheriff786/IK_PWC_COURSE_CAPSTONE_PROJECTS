# ContractIQ Risk Report — COM-001

**Overall risk:** MEDIUM  
**Assessment ID:** assessment-COM-001-afa835b6  
**Run ID:** f8ac4b480c0b  
**Document version:** 1  
**Model version:** gpt-4o-mini  
**Prompt version:** phase5-specialist-prompts-v1  
**Policy version:** risk-policy-v1  
**Created at:** 2026-10-22T23:58:55.595561  
**Report generated:** 2026-10-22T18:32:54.269445+00:00

## Specialist statuses
- **operational**: OK, 1 finding(s), retry_count=0
- **financial**: OK, 4 finding(s), retry_count=0
- **legal**: OK, 2 finding(s), retry_count=0

## Findings (by severity)
- **[HIGH] Governing Law and Dispute Resolution** (confidence=0.95)
  - rationale: The evidence explicitly outlines the process for dispute resolution and mentions arbitration as the method to resolve disputes, along with the governing law reference.
  - evidence: `['COM-001-c0']` — "Any dispute arising from this Agreement shall first be addressed through amicable discussions between the parties. If unresolved, the matter shall be referred to arbitration under the Indian Arbitrati..."
- **[MEDIUM] Scope of Work Defined** (confidence=0.3)  ⚠ uncertainty: failed_verification
  - rationale: The evidence clearly outlines the scope of products covered under the agreement, detailing the categories of products that the Vendor will supply to the Client.
  - evidence: `['COM-001-c0']` — "This Agreement covers the following categories of products supplied by Vendor to Client: Servers (Rack-mounted, Blade, and Tower), Networking Equipment (Switches, Routers, Firewalls), Storage Solution..."
- **[MEDIUM] Payment Terms and Schedule** (confidence=0.9)
  - rationale: The evidence clearly outlines the payment terms, including the due dates and conditions for payment under the agreement.
  - evidence: `['COM-001-c0']` — "Payment shall be made by Client within thirty (30) days from the date of invoice."
- **[MEDIUM] Late Payment Penalties** (confidence=0.9)
  - rationale: The contract specifies the penalties for late payments, including interest rates and conditions for suspension of deliveries.
  - evidence: `['COM-001-c0']` — "Late payments shall attract interest at 1.5% per month, calculated from the due date until the date of actual payment."
- **[MEDIUM] Pricing Structure Defined** (confidence=0.9)
  - rationale: The agreement explicitly outlines the pricing structure for products and services provided by the Vendor to the Client, including details on base pricing and conditions for price revisions.
  - evidence: `['COM-001-c0']` — "The pricing of each product is established in Table 1: Base Pricing, which shall be effective for the duration of this Agreement, unless modified through mutual written consent."
- **[MEDIUM] Price Revision Clause Present** (confidence=0.9)
  - rationale: The contract includes a clause that allows for price revisions based on inflation and changes in raw material costs, indicating a form of price escalation mechanism.
  - evidence: `['COM-001-c0']` — "Vendor may revise the prices annually, subject to inflation, changes in raw material costs, or new technology adoption."
- **[MEDIUM] Termination for Convenience Notice Period** (confidence=0.9)
  - rationale: The evidence specifies the notice period required for termination of the agreement without cause.
  - evidence: `['COM-001-c0']` — "Either party may terminate the Agreement by providing 60 days written notice to the other party."

## Uncertainty / unresolved issues
- HITL [operational] 'Scope of Work Defined': quoted evidence could not be verified against source text — needs human confirmation before use.

## Recommendations (consensus actions)
- Review: [legal] Governing Law and Dispute Resolution
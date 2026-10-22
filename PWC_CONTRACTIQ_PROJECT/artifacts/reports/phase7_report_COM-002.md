# ContractIQ Risk Report — COM-002

**Overall risk:** MEDIUM  
**Assessment ID:** assessment-COM-002-82c209c2  
**Run ID:** e66c81b9605b  
**Document version:** 1  
**Model version:** gpt-4o-mini  
**Prompt version:** phase5-specialist-prompts-v1  
**Policy version:** risk-policy-v1  
**Created at:** 2026-10-22T23:59:14.076320  
**Report generated:** 2026-10-22T18:32:54.270442+00:00

## Specialist statuses
- **operational**: OK, 1 finding(s), retry_count=0
- **financial**: OK, 4 finding(s), retry_count=0
- **legal**: OK, 3 finding(s), retry_count=0

## Findings (by severity)
- **[HIGH] Intellectual Property Ownership** (confidence=0.9)
  - rationale: The Vendor retains all intellectual property rights over hardware design, firmware, and proprietary software, indicating ownership of the intellectual property created under this agreement.
  - evidence: `['COM-002-c0']` — "Vendor retains all intellectual property rights over hardware design, firmware, and proprietary software."
- **[HIGH] Governing Law and Dispute Resolution** (confidence=0.95)
  - rationale: The evidence explicitly states the governing law and the method for resolving disputes.
  - evidence: `['COM-002-c0']` — "Unresolved disputes will be referred to arbitration under the Indian Arbitration and Conciliation Act, 1996. Arbitration proceedings will take place in [City, State], India, in English."
- **[MEDIUM] Scope of Work and Deliverables Defined** (confidence=0.3)  ⚠ uncertainty: failed_verification
  - rationale: The evidence clearly outlines the products and services that fall under the agreement, which constitutes the scope of work.
  - evidence: `['COM-002-c0']` — "The following products and services fall under this Agreement: Enterprise Servers (Rack-mounted, Blade, Tower), Networking Equipment (Switches, Firewalls, Routers), Data Storage Solutions (NAS, SAN, C..."
- **[MEDIUM] Payment Terms Overview** (confidence=0.9)
  - rationale: The evidence clearly outlines the payment terms under the agreement, specifying the advance payment and the timeline for the remaining payment.
  - evidence: `['COM-002-c0']` — "Client shall pay 50% advance upon purchase order confirmation and the remaining 50% within 30 days after delivery and acceptance."
- **[MEDIUM] Late Payment Penalties** (confidence=0.9)
  - rationale: The contract specifies that late payments will incur interest charges, which directly addresses the topic of late payment penalties.
  - evidence: `['COM-002-c0']` — "Late payments shall accrue interest at 1.25% per month."
- **[MEDIUM] Pricing Structure Defined** (confidence=0.9)
  - rationale: The agreement clearly outlines the pricing structure, including base prices, tiered volume discounts, and payment terms.
  - evidence: `['COM-002-c0']` — "The Vendor shall provide products at the following base prices, subject to tiered volume and contract duration discounts:"
- **[MEDIUM] Price Revision Clause Present** (confidence=0.9)
  - rationale: The agreement includes a clause that allows for price revisions based on changes in raw material costs, inflation, or regulatory requirements, indicating a form of price escalation mechanism.
  - evidence: `['COM-002-c0']` — "Prices may be reviewed semi-annually to reflect changes in raw material costs, inflation, or regulatory requirements."
- **[MEDIUM] Termination for Convenience Notice Period** (confidence=0.9)
  - rationale: The evidence specifies the notice period required for termination without cause.
  - evidence: `['COM-002-c0']` — "Either party may terminate by providing 60 days’ prior written notice."

## Uncertainty / unresolved issues
- HITL [operational] 'Scope of Work and Deliverables Defined': quoted evidence could not be verified against source text — needs human confirmation before use.

## Recommendations (consensus actions)
- Review: [legal] Intellectual Property Ownership
- Review: [legal] Governing Law and Dispute Resolution
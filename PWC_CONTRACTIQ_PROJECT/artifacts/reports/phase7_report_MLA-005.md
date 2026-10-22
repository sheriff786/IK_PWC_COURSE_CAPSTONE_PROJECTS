# ContractIQ Risk Report — MLA-005

**Overall risk:** HIGH  
**Assessment ID:** assessment-MLA-005-85273e72  
**Run ID:** 4e7a14c44359  
**Document version:** 1  
**Model version:** gpt-4o-mini  
**Prompt version:** phase5-specialist-prompts-v1  
**Policy version:** risk-policy-v1  
**Created at:** 2026-10-22T23:57:29.596211  
**Report generated:** 2026-10-22T18:32:54.283441+00:00

## Specialist statuses
- **legal**: OK, 1 finding(s), retry_count=0
- **financial**: OK, 5 finding(s), retry_count=0
- **operational**: OK, 4 finding(s), retry_count=0

## Findings (by severity)
- **[HIGH] Pricing Structure Overview** (confidence=0.95)
  - rationale: The evidence provides a comprehensive overview of the pricing structure, including device pricing frameworks, service rates, and cost transparency.
  - evidence: `['MLA-005-c0']` — "The Vendor shall provide the Client with a meticulously detailed device pricing framework that lists the per-unit cost of every hardware category supplied under this collaboration."
- **[HIGH] Scope of Work and Deliverables Defined** (confidence=0.95)
  - rationale: The evidence clearly outlines the scope of work and deliverables under the agreement, detailing various products, services, and components involved in the BFSI deployments.
  - evidence: `['MLA-005-c0']` — "The scope of this Agreement is intentionally broad, covering every category of hardware, firmware, software-adjacent service, engineering activity, logistical operation, and maintenance initiative lik..."
- **[MEDIUM] Confidentiality Obligations Survival** (confidence=0.9)
  - rationale: The evidence explicitly states the duration for which confidentiality obligations survive after the agreement ends.
  - evidence: `['MLA-005-c3']` — "This confidentiality obligation shall survive termination of this Agreement for a minimum of five years."
- **[MEDIUM] Payment Terms and Invoice Requirements** (confidence=0.9)
  - rationale: The evidence outlines the requirements for invoicing and pricing structures, ensuring that all invoices correspond to the agreed pricing categories and values, which directly relates to payment terms.
  - evidence: `['MLA-005-c2']` — "All invoices raised by the Vendor shall strictly correspond to the pricing categories and values stated in this Agreement."
- **[MEDIUM] Price Escalation Clauses Present** (confidence=0.9)
  - rationale: The contract includes specific clauses regarding price protection and escalation constraints, detailing how prices can be reviewed and adjusted based on objective cost evidence.
  - evidence: `['MLA-005-c2']` — "Accordingly, all hardware prices, deployment prices, and service prices defined within this Agreement shall remain protected for a minimum of twelve months from the date of execution."
- **[MEDIUM] Renewal Pricing and Terms** (confidence=0.85)
  - rationale: The contract specifies that any pricing amendments must be documented through a written addendum and that the Vendor will continue to honor all accepted purchase orders based on the current rate card until a new version is formally transitioned. This indicates that renewal pricing is tied to the existing rate card unless formally amended.
  - evidence: `['MLA-005-c3']` — "The Vendor shall continue to honour all accepted purchase orders based on the current rate card until the Parties formally transition to a new version."
- **[MEDIUM] Cap on Financial Exposure** (confidence=0.9)
  - rationale: The contract explicitly states that the Vendor shall not introduce any new financial charge outside this Agreement without explicit written approval, which protects the Client from unexpected financial exposure and ensures absolute commercial predictability throughout the contract term.
  - evidence: `['MLA-005-c2', 'MLA-005-c3']` — "This protects the Client from unexpected financial exposure and ensures absolute commercial predictability throughout the contract term."
- **[MEDIUM] Vendor's Service Level Commitments** (confidence=0.9)
  - rationale: The Vendor commits to maintaining predictable pricing and service delivery without introducing unexpected charges, ensuring commercial predictability and protecting the Client from financial exposure.
  - evidence: `['MLA-005-c3', 'MLA-005-c2']` — "The Client shall not be obligated to pay for resource wait times, idle engineer hours, or vendor-driven deployment delays. This protects the Client from unexpected financial exposure and ensures absol..."
- **[MEDIUM] Client-Side Obligations for Vendor Performance** (confidence=0.9)
  - rationale: The Vendor's performance is contingent upon the Client's provision of manpower for complex operations, as specified in the pricing model for on-site support and managed services.
  - evidence: `['MLA-005-c2']` — "If the Client requires manpower for complex operations such as security sandbox testing, PSU audit compliance support, mass firmware rollout campaigns, or large-scale device refresh cycles, such activ..."
- **[MEDIUM] Performance Reporting in AMC** (confidence=0.9)
  - rationale: The evidence specifies that the Vendor agrees to provide performance analytics reporting as part of the Annual Maintenance Contracts (AMC), which directly relates to how service performance is measured or reported under this agreement.
  - evidence: `['MLA-005-c1']` — "Annual Maintenance Contracts (AMC) shall also be priced under this Agreement, ensuring that AMC charges reflect industry-aligned maintenance obligations such as scheduled preventive visits, firmware p..."

## Uncertainty / unresolved issues
_None reported._

## Recommendations (consensus actions)
- Review: [financial] Pricing Structure Overview
- Review: [operational] Scope of Work and Deliverables Defined
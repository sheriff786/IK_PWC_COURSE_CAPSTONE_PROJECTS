# ContractIQ Risk Report — MLA-005

**Overall risk:** HIGH  
**Assessment ID:** assessment-MLA-005-6e98505e  
**Run ID:** 184773c1572c  
**Document version:** 1  
**Model version:** gpt-4o-mini  
**Prompt version:** phase5-specialist-prompts-v1  
**Policy version:** risk-policy-v1  
**Created at:** 2026-10-06T01:57:41.956491  
**Report generated:** 2026-10-05T20:32:44.995364+00:00

## Specialist statuses
- **legal**: OK, 1 finding(s), retry_count=0
- **financial**: OK, 5 finding(s), retry_count=0
- **operational**: OK, 4 finding(s), retry_count=0

## Findings (by severity)
- **[HIGH] Pricing Structure Overview** (confidence=0.95)
  - rationale: The evidence provides a comprehensive overview of the pricing structure, including device pricing frameworks, service rates, and cost components, ensuring clarity and predictability for the Client.
  - evidence: `['MLA-005-c0']` — "The Vendor shall provide the Client with a meticulously detailed device pricing framework that lists the per-unit cost of every hardware category supplied under this collaboration."
- **[HIGH] Cap on Financial Exposure and Charges** (confidence=0.9)
  - rationale: The contract explicitly prohibits the Vendor from introducing any new financial charges outside the Agreement, ensuring that the Client is protected from unexpected financial exposure and maintains commercial predictability throughout the contract term.
  - evidence: `['MLA-005-c2', 'MLA-005-c3']` — "The Client shall not be obligated to pay for resource wait times, idle engineer hours, or vendor-driven deployment delays. This protects the Client from unexpected financial exposure and ensures absol..."
- **[HIGH] Scope of Work and Deliverables Defined** (confidence=0.95)
  - rationale: The evidence clearly outlines the scope of work and deliverables under the agreement, detailing various products, services, and components involved in the BFSI deployments.
  - evidence: `['MLA-005-c0']` — "The scope of this Agreement is intentionally broad, covering every category of hardware, firmware, software-adjacent service, engineering activity, logistical operation, and maintenance initiative lik..."
- **[MEDIUM] Confidentiality Obligations Survival** (confidence=0.9)
  - rationale: The evidence explicitly states the duration for which confidentiality obligations survive after the agreement ends.
  - evidence: `['MLA-005-c3']` — "This confidentiality obligation shall survive termination of this Agreement for a minimum of five years."
- **[MEDIUM] Payment Terms and Conditions** (confidence=0.85)
  - rationale: The evidence outlines the pricing structure and conditions under which payments are to be made, including invoice requirements and price protection mechanisms.
  - evidence: `['MLA-005-c2']` — "All invoices raised by the Vendor shall strictly correspond to the pricing categories and values stated in this Agreement. No invoice may include line items that deviate from or exceed the approved ra..."
- **[MEDIUM] Price Escalation Clauses Present** (confidence=0.9)
  - rationale: The contract includes specific clauses regarding price protection and escalation constraints, detailing how and when price adjustments can occur, as well as the conditions under which they are permissible.
  - evidence: `['MLA-005-c2']` — "Accordingly, all hardware prices, deployment prices, and service prices defined within this Agreement shall remain protected for a minimum of twelve months from the date of execution."
- **[MEDIUM] Renewal Pricing and Terms** (confidence=0.85)
  - rationale: The contract specifies that any pricing amendments must be documented through a written addendum, and the Vendor will continue to honor all accepted purchase orders based on the current rate card until a new version is formally transitioned. This indicates that renewal pricing is tied to the existing rate card unless formally amended.
  - evidence: `['MLA-005-c3']` — "The Vendor shall continue to honour all accepted purchase orders based on the current rate card until the Parties formally transition to a new version."
- **[MEDIUM] Service Level and Performance Commitments** (confidence=0.9)
  - rationale: The evidence outlines the Vendor's commitments regarding pricing stability, service delivery, and the prohibition of unexpected charges, which are critical components of service level agreements.
  - evidence: `['MLA-005-c3', 'MLA-005-c2']` — "The Client shall not be obligated to pay for resource wait times, idle engineer hours, or vendor-driven deployment delays. This protects the Client from unexpected financial exposure and ensures absol..."
- **[MEDIUM] Client-Side Obligations for Vendor Performance** (confidence=0.85)
  - rationale: The evidence specifies that the Vendor's performance is contingent upon the Client's requirements for manpower and operational dependencies, particularly for complex operations and installation services.
  - evidence: `['MLA-005-c2']` — "If the Client requires manpower for complex operations such as security sandbox testing, PSU audit compliance support, mass firmware rollout campaigns, or large-scale device refresh cycles, such activ..."
- **[MEDIUM] Performance Reporting in AMC** (confidence=0.9)
  - rationale: The evidence specifies that the Vendor agrees to provide performance analytics reporting as part of the Annual Maintenance Contracts (AMC), which is a key aspect of service performance measurement and reporting.
  - evidence: `['MLA-005-c1']` — "Annual Maintenance Contracts (AMC) shall also be priced under this Agreement, ensuring that AMC charges reflect industry-aligned maintenance obligations such as scheduled preventive visits, firmware p..."

## Uncertainty / unresolved issues
_None reported._

## Recommendations (consensus actions)
- Review: [financial] Pricing Structure Overview
- Review: [financial] Cap on Financial Exposure and Charges
- Review: [operational] Scope of Work and Deliverables Defined
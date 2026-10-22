# ContractIQ Risk Report — FIN-001

**Overall risk:** HIGH  
**Assessment ID:** assessment-FIN-001-82028c93  
**Run ID:** 12ec1bcb384e  
**Document version:** 1  
**Model version:** gpt-4o-mini  
**Prompt version:** phase5-specialist-prompts-v1  
**Policy version:** risk-policy-v1  
**Created at:** 2026-10-22T23:58:05.673622  
**Report generated:** 2026-10-22T18:32:54.273439+00:00

## Specialist statuses
- **financial**: OK, 3 finding(s), retry_count=0
- **operational**: OK, 3 finding(s), retry_count=0
- **legal**: OK, 2 finding(s), retry_count=0

## Findings (by severity)
- **[HIGH] Acceptance Criteria for Deliverables** (confidence=0.9)
  - rationale: The acceptance criteria for deliverables are specified in the milestone billing section, which outlines the payment structure based on the successful installation and acceptance testing of hardware.
  - evidence: `['FIN-001-c0']` — "30% advance upon PO acceptance
40% upon delivery of hardware to site
30% upon successful installation and acceptance testing"
- **[HIGH] Governing Law and Dispute Resolution** (confidence=0.95)
  - rationale: The evidence explicitly states the governing law and outlines the process for resolving disputes.
  - evidence: `['FIN-001-c0']` — "This Agreement shall be governed by the laws of India."
- **[MEDIUM] Payment Terms and Schedule** (confidence=0.9)
  - rationale: The evidence clearly outlines the payment terms and schedule under the agreement, specifying due dates and conditions for payments.
  - evidence: `['FIN-001-c0']` — "Payment is due within 30 calendar days from the date of invoice receipt."
- **[MEDIUM] Late Payment Penalties** (confidence=0.9)
  - rationale: The contract specifies the penalties for late payments, including the interest rate applicable to outstanding amounts.
  - evidence: `['FIN-001-c0']` — "Late payments will attract an interest of 1.5% per month on the outstanding amount."
- **[MEDIUM] Pricing Structure and Payment Terms** (confidence=0.3)  ⚠ uncertainty: failed_verification
  - rationale: The evidence outlines the pricing structure, including billing frequency, payment terms, and milestone billing for large orders, which directly addresses the topic of pricing structure.
  - evidence: `['FIN-001-c0']` — "Invoices will be issued monthly for recurring supply contracts. For one-time orders exceeding INR 5,00,000, invoices will be issued upon delivery. Payment is due within 30 calendar days from the date ..."
- **[MEDIUM] Scope of Work Defined** (confidence=0.9)
  - rationale: The evidence clearly outlines the scope of work under the agreement, specifying the hardware products to be supplied by the Vendor to the Client.
  - evidence: `['FIN-001-c0']` — "This Agreement covers all hardware products supplied by the Vendor to the Client, including but not limited to networking devices, servers, storage systems, and electronic peripherals."
- **[MEDIUM] Client Obligations for Vendor Performance** (confidence=0.9)
  - rationale: The evidence outlines specific obligations of the Client that the Vendor relies on for performance, particularly regarding timely processing of invoices and approval of payments.
  - evidence: `['FIN-001-c0']` — "5. Obligations of the Client
Process invoices promptly to avoid delay in payments.
Notify the Vendor of any discrepancies within 7 days of receiving an invoice.
Ensure authorized personnel approve mil..."
- **[MEDIUM] Termination for Convenience Notice Period** (confidence=0.9)
  - rationale: The evidence specifies the notice period required for termination without cause.
  - evidence: `['FIN-001-c0']` — "Either party may terminate this Agreement with 30 days’ written notice."

## Uncertainty / unresolved issues
- HITL [financial] 'Pricing Structure and Payment Terms': quoted evidence could not be verified against source text — needs human confirmation before use.

## Recommendations (consensus actions)
- Review: [operational] Acceptance Criteria for Deliverables
- Review: [legal] Governing Law and Dispute Resolution
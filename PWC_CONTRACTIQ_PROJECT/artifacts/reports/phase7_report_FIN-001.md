# ContractIQ Risk Report — FIN-001

**Overall risk:** MEDIUM  
**Assessment ID:** assessment-FIN-001-de01d392  
**Run ID:** 4ab5437ecba9  
**Document version:** 1  
**Model version:** gpt-4o-mini  
**Prompt version:** phase5-specialist-prompts-v1  
**Policy version:** risk-policy-v1  
**Created at:** 2026-09-26T13:09:32.373271  
**Report generated:** 2026-10-05T20:14:09.215827+00:00

## Specialist statuses
- **financial**: OK, 3 finding(s), retry_count=0
- **operational**: OK, 3 finding(s), retry_count=0
- **legal**: OK, 2 finding(s), retry_count=0

## Findings (by severity)
- **[MEDIUM] Payment Terms and Schedule** (confidence=0.9)
  - rationale: The evidence provides specific details about the payment terms and schedule under the agreement, including due dates and conditions for late payments.
  - evidence: `['FIN-001-c0']` — "Payment is due within 30 calendar days from the date of invoice receipt. Late payments will attract an interest of 1.5% per month on the outstanding amount."
- **[MEDIUM] Late Payment Penalty Details** (confidence=0.9)
  - rationale: The evidence specifies the penalties for late payments, including the interest rate applicable to outstanding amounts.
  - evidence: `['FIN-001-c0']` — "Late payments will attract an interest of 1.5% per month on the outstanding amount."
- **[MEDIUM] Pricing Structure and Payment Terms** (confidence=0.3)  ⚠ uncertainty: failed_verification
  - rationale: The evidence provides a detailed description of the pricing structure, including billing frequency, payment terms, and milestone billing for large orders.
  - evidence: `['FIN-001-c0']` — "Invoices will be issued monthly for recurring supply contracts. For one-time orders exceeding INR 5,00,000, invoices will be issued upon delivery. Payment is due within 30 calendar days from the date ..."
- **[MEDIUM] Scope of Work Defined** (confidence=0.9)
  - rationale: The evidence clearly outlines the scope of work under the agreement, specifying the types of hardware products to be supplied by the Vendor to the Client.
  - evidence: `['FIN-001-c0']` — "This Agreement covers all hardware products supplied by the Vendor to the Client, including but not limited to networking devices, servers, storage systems, and electronic peripherals."
- **[MEDIUM] Acceptance Criteria for Deliverables** (confidence=0.9)
  - rationale: The acceptance criteria for deliverables are specified in the milestone billing section, which outlines the payment structure based on the successful installation and acceptance testing of hardware.
  - evidence: `['FIN-001-c0']` — "30% advance upon PO acceptance
40% upon delivery of hardware to site
30% upon successful installation and acceptance testing"
- **[MEDIUM] Client Obligations for Vendor Performance** (confidence=0.9)
  - rationale: The evidence outlines specific obligations of the Client that are essential for the Vendor's performance, particularly in relation to invoicing and payment processes.
  - evidence: `['FIN-001-c0']` — "5. Obligations of the Client
Process invoices promptly to avoid delay in payments.
Notify the Vendor of any discrepancies within 7 days of receiving an invoice.
Ensure authorized personnel approve mil..."
- **[MEDIUM] Termination for Convenience Notice Period** (confidence=0.9)
  - rationale: The evidence specifies the notice period required for termination without cause.
  - evidence: `['FIN-001-c0']` — "Either party may terminate this Agreement with 30 days’ written notice."
- **[MEDIUM] Governing Law and Dispute Resolution** (confidence=0.9)
  - rationale: The evidence explicitly states the governing law and outlines the process for resolving disputes.
  - evidence: `['FIN-001-c0']` — "This Agreement shall be governed by the laws of India."

## Uncertainty / unresolved issues
_None reported._

## Recommendations (consensus actions)
_None — no HIGH/CRITICAL findings to flag._
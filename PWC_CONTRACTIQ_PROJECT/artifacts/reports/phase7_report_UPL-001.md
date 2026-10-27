# ContractIQ Risk Report — UPL-001

**Overall risk:** MEDIUM  
**Assessment ID:** assessment-UPL-001-16c15751  
**Run ID:** 14070006eaec  
**Document version:** 1  
**Model version:** gpt-4o-mini  
**Prompt version:** phase5-specialist-prompts-v1  
**Policy version:** risk-policy-v1  
**Created at:** 2026-10-24T11:13:11.241848  
**Report generated:** 2026-10-24T05:53:15.637462+00:00

## Specialist statuses
- **financial**: OK, 3 finding(s), retry_count=0
- **operational**: OK, 5 finding(s), retry_count=0
- **legal**: OK, 4 finding(s), retry_count=0

## Findings (by severity)
- **[MEDIUM] Payment Terms and Schedule** (confidence=0.9)
  - rationale: The payment terms specify that the standard payment term is 45 calendar days from the Client’s receipt of a valid invoice and required supporting documents, with late payment interest applicable on overdue amounts.
  - evidence: `['UPL-001-c0']` — "Standard payment term: 45 calendar days from the Client’s receipt of a valid invoice and required supporting documents."
- **[MEDIUM] Late Payment Interest Rate** (confidence=0.9)
  - rationale: The contract specifies the interest rate applicable to late payments, indicating the penalties for overdue amounts.
  - evidence: `['UPL-001-c0']` — "Late payment interest, where legally permitted and applicable, will be 1.25% per month on undisputed overdue amounts."
- **[MEDIUM] Pricing Structure and Billing Terms** (confidence=0.9)
  - rationale: The agreement outlines the pricing structure, including standard billing, milestone billing, and payment terms, which are essential components of the pricing structure.
  - evidence: `['UPL-001-c0']` — "Recurring supply or support arrangements will be invoiced monthly, on the final business day of the billing month."
- **[MEDIUM] Scope of Work Defined** (confidence=0.9)
  - rationale: The scope of work under this agreement includes specific hardware and related services as outlined in the contract.
  - evidence: `['UPL-001-c0']` — "This Agreement applies to hardware and related services supplied under purchase orders accepted by both parties, including: Servers, network switches, routers, storage systems, security appliances, an..."
- **[MEDIUM] Acceptance Criteria for Deliverables** (confidence=0.9)
  - rationale: The evidence specifies that the Client must review milestone evidence and provide acceptance or written reasons for rejection within a reasonable period, indicating the acceptance criteria for deliverables.
  - evidence: `['UPL-001-c0', 'UPL-001-c1']` — "Review milestone evidence and provide acceptance or written reasons for rejection within a reasonable period."
- **[MEDIUM] Vendor Performance Commitments** (confidence=0.9)
  - rationale: The vendor commits to supply goods and perform services in accordance with the accepted purchase order and agreed delivery schedule, and to notify the client of expected material delivery delays.
  - evidence: `['UPL-001-c0']` — "Supply goods and perform services in accordance with the accepted PO and agreed delivery schedule."
- **[MEDIUM] Client Obligations for Vendor Performance** (confidence=0.9)
  - rationale: The evidence outlines specific obligations of the Client that the Vendor relies on for performance, including providing valid purchase orders, arranging access for delivery and installation, and reviewing invoices.
  - evidence: `['UPL-001-c0', 'UPL-001-c1']` — "6. Obligations of the Client
Provide valid purchase orders and identify authorized contacts for delivery, invoice, and payment queries.
Review invoices and notify the Vendor of a discrepancy within 5 ..."
- **[MEDIUM] Service Performance Reporting Mechanism** (confidence=0.9)
  - rationale: The agreement outlines a structured approach to performance reporting through invoicing and reconciliation processes, ensuring transparency and accountability in service delivery.
  - evidence: `['UPL-001-c1']` — "The Vendor will provide a monthly statement showing invoices issued, amounts received, open balances, credit notes, and overdue undisputed amounts."
  - recommendation: Ensure regular reviews of performance reports to align service delivery with expectations.
- **[MEDIUM] Termination for Cause or Material Breach** (confidence=0.8)
  - rationale: The contract allows for termination by either party with a written notice, which can be interpreted as a condition for termination for cause or material breach.
  - evidence: `['UPL-001-c1']` — "Either party may terminate this Agreement by giving 45 calendar days’ written notice, unless a relevant PO states otherwise."
- **[MEDIUM] Termination for Convenience Notice Period** (confidence=0.9)
  - rationale: The contract specifies the notice period required for termination without cause.
  - evidence: `['UPL-001-c1']` — "Either party may terminate this Agreement by giving 45 calendar days’ written notice, unless a relevant PO states otherwise."
- **[MEDIUM] Confidentiality Obligations Survival** (confidence=0.9)
  - rationale: The confidentiality obligations survive termination as they relate to the protection of non-public information received during the agreement.
  - evidence: `['UPL-001-c1']` — "Each party will protect non-public billing, commercial, operational, and financial information received from the other party and will use it only for purposes connected with this Agreement."
- **[MEDIUM] Governing Law and Dispute Resolution** (confidence=0.9)
  - rationale: The evidence specifies the governing law and outlines the dispute resolution process.
  - evidence: `['UPL-001-c1']` — "This sample Agreement is intended to be governed by the laws of India. The parties should insert the agreed city and state for jurisdiction and obtain appropriate legal review before execution."

## Uncertainty / unresolved issues
_None reported._

## Recommendations (consensus actions)
_None — no HIGH/CRITICAL findings to flag._
# ContractIQ Risk Report — FIN-002

**Overall risk:** MEDIUM  
**Assessment ID:** assessment-FIN-002-21416512  
**Run ID:** 450b2abe514c  
**Document version:** 1  
**Model version:** gpt-4o-mini  
**Prompt version:** phase5-specialist-prompts-v1  
**Policy version:** risk-policy-v1  
**Created at:** 2026-10-22T23:58:23.392200  
**Report generated:** 2026-10-22T18:32:54.274442+00:00

## Specialist statuses
- **financial**: OK, 3 finding(s), retry_count=0
- **operational**: OK, 4 finding(s), retry_count=0
- **legal**: OK, 2 finding(s), retry_count=0

## Findings (by severity)
- **[HIGH] Governing Law and Dispute Resolution** (confidence=0.95)
  - rationale: The evidence explicitly states the governing law and the method for resolving disputes.
  - evidence: `['FIN-002-c0']` — "This Agreement shall be governed by the laws of India. Disputes will be under the jurisdiction of courts located in [City, State]."
- **[MEDIUM] Payment Terms and Schedule** (confidence=0.9)
  - rationale: The evidence provides specific details regarding the payment terms and schedule under the agreement, including invoicing frequency and payment deadlines.
  - evidence: `['FIN-002-c0']` — "3.3 Payment Terms:
Standard credit period: 30 calendar days from invoice date.
Late payment penalty: 1.5% per month on overdue amounts.
Advance payments will not exceed 20% of total PO unless mutually..."
- **[MEDIUM] Late Payment Penalty** (confidence=0.9)
  - rationale: The contract specifies a penalty for late payments, which directly addresses the topic of late payment penalties.
  - evidence: `['FIN-002-c0']` — "Late payment penalty: 1.5% per month on overdue amounts."
- **[MEDIUM] Pricing Structure and Billing Schedule** (confidence=0.9)
  - rationale: The evidence provides a detailed description of the pricing structure and billing schedule for the agreement between Primevolta Hardware Solutions and FinSecure Services.
  - evidence: `['FIN-002-c0']` — "3. Billing Schedule & Frequency
3.1 Standard Billing:
Monthly Invoicing: For ongoing supply contracts, invoices will be raised on the last business day of each month.
Delivery-Based Billing: For one-t..."
- **[MEDIUM] Scope of Work Defined** (confidence=0.9)
  - rationale: The evidence clearly outlines the scope of work under the agreement, detailing the hardware components and associated services to be provided.
  - evidence: `['FIN-002-c0']` — "This Agreement covers the supply of: Hardware components including servers, storage arrays, networking devices, and electronic peripherals. Multi-site deliveries for BFSI branch rollouts. Associated s..."
- **[MEDIUM] Vendor Performance Commitments** (confidence=0.3)  ⚠ uncertainty: failed_verification
  - rationale: The vendor commits to deliver goods as per the specifications and timelines mentioned in the purchase order (PO) and to notify the client of any deviations in the delivery schedule at least 7 business days in advance.
  - evidence: `['FIN-002-c0']` — "Deliver goods as per the specifications and timelines mentioned in the PO. Notify the Client of any deviations in delivery schedule at least 7 business days in advance."
- **[MEDIUM] Client Obligations for Vendor Performance** (confidence=0.9)
  - rationale: The evidence outlines specific obligations of the Client that the Vendor relies on for performance, including timely processing of invoices and providing access to sites for installation and testing activities.
  - evidence: `['FIN-002-c0']` — "6. Obligations of Client
Process invoices within the agreed payment timeline.
Notify the Vendor of any discrepancies in invoices or deliveries within 7 business days.
Approve milestone payments and si..."
- **[MEDIUM] Service Performance Measurement and Reporting** (confidence=0.9)
  - rationale: The agreement specifies that the Vendor shall provide monthly revenue tracking reports and that the Client may request quarterly reconciliation reports to ensure alignment between delivered hardware, invoices, and payments.
  - evidence: `['FIN-002-c0']` — "Vendor shall provide monthly revenue tracking reports detailing billed, unbilled, and pending payments."
- **[MEDIUM] Termination for Convenience Notice Period** (confidence=0.9)
  - rationale: The contract specifies the notice period required for termination without cause.
  - evidence: `['FIN-002-c0']` — "Either party may terminate the agreement with 30 days’ notice, without affecting outstanding invoices or milestones."

## Uncertainty / unresolved issues
- HITL [operational] 'Vendor Performance Commitments': quoted evidence could not be verified against source text — needs human confirmation before use.

## Recommendations (consensus actions)
- Review: [legal] Governing Law and Dispute Resolution
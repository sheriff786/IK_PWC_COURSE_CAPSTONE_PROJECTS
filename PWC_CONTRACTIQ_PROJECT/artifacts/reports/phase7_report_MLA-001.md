# ContractIQ Risk Report — MLA-001

**Overall risk:** HIGH  
**Assessment ID:** assessment-MLA-001-af9d04b9  
**Run ID:** 3d137d6c4acb  
**Document version:** 1  
**Model version:** gpt-4o-mini  
**Prompt version:** phase5-specialist-prompts-v1  
**Policy version:** risk-policy-v1  
**Created at:** 2026-09-26T13:08:20.693724  
**Report generated:** 2026-10-05T20:14:09.217735+00:00

## Specialist statuses
- **financial**: OK, 4 finding(s), retry_count=0
- **operational**: OK, 5 finding(s), retry_count=0
- **legal**: OK, 7 finding(s), retry_count=0

## Findings (by severity)
- **[HIGH] Scope of Work Defined** (confidence=0.95)
  - rationale: The evidence clearly outlines the scope of services provided under the agreement, detailing the responsibilities and deliverables of the Vendor.
  - evidence: `['MLA-001-c0']` — "The scope of services covered under this Agreement encompasses the comprehensive supply, delivery, installation, commissioning, maintenance, and long-term operational support of the Vendor’s hardware ..."
- **[HIGH] Service Level Commitments by Vendor** (confidence=0.95)
  - rationale: The evidence explicitly outlines the service level commitments made by the Vendor, including incident acknowledgment and resolution timelines based on severity levels.
  - evidence: `['MLA-001-c1']` — "The Vendor commits to resolving Critical incidents within four hours, High severity incidents within eight hours, Medium severity incidents within one business day, and Low severity incidents within s..."
- **[HIGH] Service Performance Measurement and Reporting** (confidence=0.9)
  - rationale: The contract specifies that the Vendor shall furnish weekly and monthly performance reports summarizing incidents, resolutions, SLA compliance, bottlenecks, and recommendations for improvement.
  - evidence: `['MLA-001-c1']` — "The Vendor shall furnish weekly and monthly performance reports summarizing incidents, resolutions, SLA compliance, bottlenecks, and recommendations for improvement."
- **[HIGH] Limitation of Liability Found** (confidence=0.9)
  - rationale: The contract explicitly states a cap on total liability, limiting it to the total amount paid by the Client to the Vendor in the preceding twelve months, except for certain breaches.
  - evidence: `['MLA-001-c2']` — "Except for breaches involving confidentiality, intellectual property misuse, or acts of gross negligence or willful misconduct, each Party’s total cumulative liability under this Agreement shall not e..."
- **[HIGH] Intellectual Property Ownership** (confidence=0.95)
  - rationale: The evidence clearly states that all intellectual property rights associated with the Vendor’s products remain the exclusive property of the Vendor, and the Client is granted a limited license to use the firmware and software.
  - evidence: `['MLA-001-c2']` — "All intellectual property rights, including copyrights, patents, trademarks, trade secrets, firmware binaries, source code, configuration files, PCB layouts, circuit diagrams, and proprietary design e..."
- **[HIGH] Governing Law and Dispute Resolution** (confidence=0.95)
  - rationale: The evidence clearly outlines the governing law and the method for resolving disputes, specifying arbitration as the resolution method and mentioning the applicable jurisdiction.
  - evidence: `['MLA-001-c3', 'MLA-001-c2']` — "This Agreement shall be governed by and interpreted in accordance with the laws of the jurisdiction specified in the SOW. Any dispute, controversy, or claim arising out of or relating to this Agreemen..."
- **[MEDIUM] Payment Terms and Schedule** (confidence=0.9)
  - rationale: The payment terms specify that the Client shall make payments within forty-five (45) days from the date of receipt of the completed invoice, and any disputed component of an invoice must be notified within seven (7) days.
  - evidence: `['MLA-001-c1']` — "The Client shall make payments within forty-five (45) days from the date of receipt of the completed invoice, subject to validation and reconciliation."
- **[MEDIUM] Late Payment Penalty Details** (confidence=0.9)
  - rationale: The contract specifies the penalties for late payments, including interest charges.
  - evidence: `['MLA-001-c1']` — "Delay in invoice settlement beyond the stipulated period shall attract an interest charge of one percent (1%) per month until full payment is made."
- **[MEDIUM] Pricing Structure Defined** (confidence=0.9)
  - rationale: The evidence clearly outlines the pricing structure and billing terms applicable to the agreement, including references to a Rate Card and specific payment terms.
  - evidence: `['MLA-001-c1']` — "All pricing applicable to this Agreement shall be governed by the Rate Card or the individual SOWs executed between the Parties."
- **[MEDIUM] Cap on Financial Exposure** (confidence=0.9)
  - rationale: The contract specifies a limitation on liability, capping the total cumulative liability of each party under the agreement.
  - evidence: `['MLA-001-c2']` — "each Party’s total cumulative liability under this Agreement shall not exceed the total amount paid by the Client to the Vendor in the preceding twelve (12) months."
- **[MEDIUM] Service Level Agreement Remedies** (confidence=0.9)
  - rationale: The contract specifies that continued failure to meet SLA commitments may result in service credits or financial penalties as detailed in the Rate Card or annexures.
  - evidence: `['MLA-001-c1']` — "Continued failure to meet SLA commitments may result in service credits or financial penalties as detailed in the Rate Card or annexures."
- **[MEDIUM] Client Payment Obligations** (confidence=0.9)
  - rationale: The evidence outlines the obligations of the Client regarding payment terms, which are critical for the Vendor's performance.
  - evidence: `['MLA-001-c1']` — "The Client shall make payments within forty-five (45) days from the date of receipt of the completed invoice, subject to validation and reconciliation."
- **[MEDIUM] Indemnification Obligations** (confidence=0.9)
  - rationale: The evidence clearly outlines the indemnification obligations of both parties under the agreement, specifying the conditions under which each party agrees to indemnify the other.
  - evidence: `['MLA-001-c2']` — "The Vendor agrees to indemnify and defend the Client against any third-party claims, damages, losses, liabilities, or expenses arising from product defects, workmanship deficiencies, or bodily injury ..."
- **[MEDIUM] Termination for Cause Conditions** (confidence=0.9)
  - rationale: The contract specifies conditions under which it can be terminated for cause, including material breaches that are not cured within a specified time frame.
  - evidence: `['MLA-001-c0']` — "This Agreement may also be terminated for cause if either Party materially breaches its obligations and fails to cure such breach within a period of thirty (30) days from the receipt of a written noti..."
- **[MEDIUM] Termination for Convenience Notice Period** (confidence=0.9)
  - rationale: The contract specifies the notice period required for termination without cause.
  - evidence: `['MLA-001-c0']` — "Either Party may terminate this Agreement for convenience by providing the other Party with not less than ninety (90) days’ prior written notice without the need to furnish any justification for such ..."
- **[MEDIUM] Confidentiality Obligations Survival** (confidence=0.9)
  - rationale: The evidence explicitly states the duration for which confidentiality obligations survive after the agreement ends.
  - evidence: `['MLA-001-c2']` — "The confidentiality obligations shall survive for five (5) years following the termination of this Agreement."

## Uncertainty / unresolved issues
_None reported._

## Recommendations (consensus actions)
- Review: [operational] Scope of Work Defined
- Review: [operational] Service Level Commitments by Vendor
- Review: [operational] Service Performance Measurement and Reporting
- Review: [legal] Limitation of Liability Found
- Review: [legal] Intellectual Property Ownership
- Review: [legal] Governing Law and Dispute Resolution
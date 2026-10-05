# ContractIQ Risk Report — MLA-004

**Overall risk:** HIGH  
**Assessment ID:** assessment-MLA-004-2e71c6b2  
**Run ID:** a1700c698b0f  
**Document version:** 1  
**Model version:** gpt-4o-mini  
**Prompt version:** phase5-specialist-prompts-v1  
**Policy version:** risk-policy-v1  
**Created at:** 2026-10-06T01:57:27.899796  
**Report generated:** 2026-10-05T20:32:44.995364+00:00

## Specialist statuses
- **operational**: OK, 1 finding(s), retry_count=0
- **financial**: OK, 0 finding(s), retry_count=0
- **legal**: OK, 5 finding(s), retry_count=0

## Findings (by severity)
- **[HIGH] Conditions for Termination for Cause** (confidence=0.9)
  - rationale: The evidence outlines the consequences of breach, including the right to terminate existing contracts and seek injunctive relief, which indicates conditions under which the agreement can be terminated for cause.
  - evidence: `['MLA-004-c2']` — "the Disclosing Party may suspend ongoing work, restrict access, terminate existing contracts, and demand immediate return of all Confidential Information."
- **[HIGH] Intellectual Property Ownership** (confidence=0.9)
  - rationale: The evidence explicitly states that all intellectual property rights connected to the Confidential Information remain solely with the Disclosing Party, indicating ownership of any work product created under this agreement.
  - evidence: `['MLA-004-c1']` — "All intellectual property rights connected to the Confidential Information remain solely with the Disclosing Party."
- **[HIGH] Governing Law and Dispute Resolution** (confidence=0.95)
  - rationale: The evidence explicitly outlines the governing law and dispute resolution process, including arbitration.
  - evidence: `['MLA-004-c2']` — "This Agreement shall be governed by and interpreted in accordance with the laws of the jurisdiction mutually agreed between the Parties. In case a dispute arises regarding interpretation, execution, b..."
- **[MEDIUM] Client-Side Obligations for Performance** (confidence=0.85)
  - rationale: The vendor relies on the client to provide various forms of Confidential Information necessary for the collaboration, including operational models, project plans, and compliance interpretations, which are essential for the vendor's performance.
  - evidence: `['MLA-004-c0']` — "Such information includes, but is not limited to, engineering documentation such as block diagrams, circuit layouts, PCB manufacturing files, embedded code, source binaries, firmware logic, secure boo..."
- **[MEDIUM] Confidentiality Obligations Survival Period** (confidence=0.9)
  - rationale: The confidentiality obligations contained herein shall survive termination and shall continue to bind both Parties for a period of five (5) years from the date of termination or final disclosure, whichever is later.
  - evidence: `['MLA-004-c2']` — "The confidentiality obligations contained herein shall survive termination and shall continue to bind both Parties for a period of five (5) years from the date of termination or final disclosure, whic..."
- **[MEDIUM] Assignment and Change of Control Restrictions** (confidence=0.9)
  - rationale: The contract explicitly states that neither Party may assign, transfer, or delegate its rights or obligations without written approval from the other Party.
  - evidence: `['MLA-004-c2']` — "Neither Party may assign, transfer, or delegate its rights or obligations without written approval from the other Party."

## Uncertainty / unresolved issues
_None reported._

## Recommendations (consensus actions)
- Review: [legal] Conditions for Termination for Cause
- Review: [legal] Intellectual Property Ownership
- Review: [legal] Governing Law and Dispute Resolution
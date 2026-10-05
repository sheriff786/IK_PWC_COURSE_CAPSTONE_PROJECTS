# ContractIQ Risk Report — MLA-003

**Overall risk:** HIGH  
**Assessment ID:** assessment-MLA-003-bafd0d2c  
**Run ID:** f0320f00f433  
**Document version:** 1  
**Model version:** gpt-4o-mini  
**Prompt version:** phase5-specialist-prompts-v1  
**Policy version:** risk-policy-v1  
**Created at:** 2026-09-26T13:08:47.758843  
**Report generated:** 2026-10-05T20:14:09.219986+00:00

## Specialist statuses
- **operational**: OK, 1 finding(s), retry_count=0
- **financial**: OK, 1 finding(s), retry_count=0
- **legal**: OK, 5 finding(s), retry_count=0

## Findings (by severity)
- **[HIGH] Client-Side Obligations for Confidential Information** (confidence=0.9)
  - rationale: The vendor relies on the client to maintain strict confidentiality and protect sensitive information, which is crucial for the performance of their obligations under the contract.
  - evidence: `['MLA-003-c0']` — "The Receiving Party shall maintain the strictest levels of confidentiality in handling, accessing, storing, processing, transferring, and destroying Confidential Information received from the Disclosi..."
- **[HIGH] Conditions for Termination for Cause** (confidence=0.9)
  - rationale: The evidence specifies that the Disclosing Party has the right to terminate ongoing engagements in the event of unauthorized use or disclosure of Confidential Information, which constitutes a material breach.
  - evidence: `['MLA-003-c2']` — "The Disclosing Party shall also have the right to terminate ongoing engagements, withdraw access privileges, demand immediate return of all Confidential Information, and pursue appropriate legal actio..."
- **[HIGH] Intellectual Property Ownership** (confidence=0.9)
  - rationale: The contract explicitly states that the Receiving Party shall not claim any intellectual property rights from the Confidential Information or any work product arising from it.
  - evidence: `['MLA-003-c2']` — "The Receiving Party shall not claim, register, patent, or derive any intellectual property rights from the Confidential Information or any work product arising from it."
- **[MEDIUM] Pricing Structure Mentioned** (confidence=0.3)  ⚠ uncertainty: failed_verification
  - rationale: The contract explicitly mentions 'pricing models' and 'rate cards' as part of the Confidential Information, indicating that there is a pricing structure included in the agreement.
  - evidence: `['MLA-003-c0']` — "Confidential Information includes... pricing models, rate cards, proposals, contract drafts, financial analyses, internal controls, business forecasts, deployment plans, and security arrangements."
- **[MEDIUM] Confidentiality Obligations Survival Period** (confidence=0.9)
  - rationale: The confidentiality obligations set forth herein shall survive for a period of five (5) years from the date of termination or from the last disclosure of Confidential Information, whichever occurs later.
  - evidence: `['MLA-003-c1']` — "Notwithstanding termination, the confidentiality obligations set forth herein shall survive for a period of five (5) years from the date of termination or from the last disclosure of Confidential Info..."
- **[MEDIUM] Governing Law and Dispute Resolution** (confidence=0.9)
  - rationale: The evidence explicitly outlines the governing law and dispute resolution process for the contract.
  - evidence: `['MLA-003-c2']` — "This Agreement shall be governed by and construed in accordance with the laws of the jurisdiction mutually agreed by the Parties. Any disputes arising from or relating to this Agreement shall first be..."
- **[MEDIUM] Assignment and Change of Control Restrictions** (confidence=0.9)
  - rationale: The contract explicitly states that neither party may assign or transfer its rights or obligations under this Agreement without prior written consent from the other party.
  - evidence: `['MLA-003-c2']` — "Neither Party may assign or transfer its rights or obligations under this Agreement without the prior written consent of the other Party."

## Uncertainty / unresolved issues
_None reported._

## Recommendations (consensus actions)
- Review: [operational] Client-Side Obligations for Confidential Information
- Review: [legal] Conditions for Termination for Cause
- Review: [legal] Intellectual Property Ownership
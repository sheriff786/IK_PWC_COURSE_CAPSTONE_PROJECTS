# ContractIQ Risk Report — MLA-003

**Overall risk:** HIGH  
**Assessment ID:** assessment-MLA-003-ed04ebbd  
**Run ID:** 89a8a8f38e86  
**Document version:** 1  
**Model version:** gpt-4o-mini  
**Prompt version:** phase5-specialist-prompts-v1  
**Policy version:** risk-policy-v1  
**Created at:** 2026-10-06T01:57:13.959007  
**Report generated:** 2026-10-05T20:32:44.995364+00:00

## Specialist statuses
- **financial**: OK, 0 finding(s), retry_count=0
- **operational**: OK, 2 finding(s), retry_count=0
- **legal**: OK, 5 finding(s), retry_count=0

## Findings (by severity)
- **[HIGH] Client-Side Obligations for Confidential Information** (confidence=0.9)
  - rationale: The vendor relies on the client to maintain strict confidentiality and protect sensitive information, which is crucial for the performance of their obligations under the contract.
  - evidence: `['MLA-003-c0']` — "The Receiving Party shall maintain the strictest levels of confidentiality in handling, accessing, storing, processing, transferring, and destroying Confidential Information received from the Disclosi..."
- **[HIGH] Conditions for Termination for Cause** (confidence=0.9)
  - rationale: The evidence specifies that the Disclosing Party has the right to terminate ongoing engagements in the event of unauthorized use or disclosure of Confidential Information, which constitutes a material breach.
  - evidence: `['MLA-003-c2']` — "The Disclosing Party shall also have the right to terminate ongoing engagements, withdraw access privileges, demand immediate return of all Confidential Information, and pursue appropriate legal actio..."
- **[HIGH] Intellectual Property Ownership** (confidence=0.9)
  - rationale: The contract explicitly states that the Receiving Party shall not claim, register, patent, or derive any intellectual property rights from the Confidential Information or any work product arising from it.
  - evidence: `['MLA-003-c2']` — "The Receiving Party shall not claim, register, patent, or derive any intellectual property rights from the Confidential Information or any work product arising from it."
- **[MEDIUM] Scope of Work Defined** (confidence=0.9)
  - rationale: The contract outlines the purpose of the agreement, which includes facilitating a secure, controlled, and confidential exchange of information required to evaluate, plan, carry out, deploy, or support various hardware, technology, manufacturing, integration, compliance, and operational activities relating to the BFSI sector.
  - evidence: `['MLA-003-c0']` — "for the purpose of facilitating a secure, controlled, and confidential exchange of information required to evaluate, plan, carry out, deploy, or support various hardware, technology, manufacturing, in..."
- **[MEDIUM] Confidentiality Obligations Survival Period** (confidence=0.9)
  - rationale: The contract specifies the duration for which confidentiality obligations survive after termination.
  - evidence: `['MLA-003-c1']` — "Notwithstanding termination, the confidentiality obligations set forth herein shall survive for a period of five (5) years from the date of termination or from the last disclosure of Confidential Info..."
- **[MEDIUM] Governing Law and Dispute Resolution** (confidence=0.9)
  - rationale: The evidence clearly outlines the governing law and dispute resolution process for the contract.
  - evidence: `['MLA-003-c2']` — "This Agreement shall be governed by and construed in accordance with the laws of the jurisdiction mutually agreed by the Parties. Any disputes arising from or relating to this Agreement shall first be..."
- **[MEDIUM] Assignment and Change of Control Restrictions** (confidence=0.9)
  - rationale: The contract explicitly states that neither party may assign or transfer its rights or obligations under this Agreement without the prior written consent of the other Party.
  - evidence: `['MLA-003-c2']` — "Neither Party may assign or transfer its rights or obligations under this Agreement without the prior written consent of the other Party."

## Uncertainty / unresolved issues
_None reported._

## Recommendations (consensus actions)
- Review: [operational] Client-Side Obligations for Confidential Information
- Review: [legal] Conditions for Termination for Cause
- Review: [legal] Intellectual Property Ownership
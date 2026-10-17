# Risk assessment (lightweight FMEA)

**System:** DrugLabel QA v1.0. **Status:** approved 2026-10-17.

Scales 1 (low) to 5 (high). **S** = severity of the harm if the failure reaches a user; **L** = likelihood
before the mitigation, based on what development and evaluation showed; **D** = detectability (1 = almost
always caught, 5 = rarely caught) with the mitigation in place. **RPN** = S × L × D, computed with the
mitigation's detectability. Evidence refers to the test cases in [`test_protocol.md`](test_protocol.md).

| ID | Failure mode | Effect | S | L | D | RPN | Mitigation | Requirements | Tests |
|---|---|---|---|---|---|---|---|---|---|
| R-01 | Hallucination: a statement not supported by the labels | Wrong information acted on | 5 | 3 | 2 | 30 | Answer only from passages (prompt); per-sentence grounding check; judge faithfulness in evaluation; low grounding held for review | REQ-01, REQ-07, REQ-08 | TC-01, TC-03, TC-04 |
| R-02 | Wrong drug or wrong product (e.g. dipyridamole tablets vs injection) | Information about another drug applied to the asked one | 5 | 3 | 2 | 30 | Representative label per drug and route; route shown with each passage; wrong-drug check holds single-drug answers citing another drug; entity normalization | REQ-07, REQ-09 | TC-04, TC-08 |
| R-03 | Outdated label | Superseded information given | 4 | 2 | 3 | 24 | Most recent label preferred within a drug and route; label date shown with each passage; openFDA snapshot date recorded at ingest; versioned data layers | REQ-11, REQ-15 | TC-09, TC-14 |
| R-04 | Prompt injection in source text | Model follows instructions planted in a passage | 4 | 1 | 2 | 8 | Prompt treats passages as data; injection test with a poisoned passage; citation and grounding checks | REQ-10 | TC-06 |
| R-05 | Missed interaction or incomplete list in a multi-label answer | User believes no other drug is concerned | 5 | 4 | 2 | 40 | Hybrid retrieval (graph + text); every answer drawing on several labels held for human review | REQ-07, REQ-09 | TC-01, TC-04 |
| R-06 | Incorrect or corrupted citation | Claim cannot be verified, or points to the wrong passage | 4 | 3 | 1 | 12 | Numbered passages in prompt v2, mapped to IDs in code; every citation checked against retrieved passages; invalid citations held | REQ-02, REQ-03, REQ-07 | TC-01, TC-02, TC-04 |
| R-07 | Patient-specific advice given | Individual treatment decision without a clinician | 5 | 2 | 2 | 20 | PATIENT_SPECIFIC refusal in the prompt; patient-wording check holds any answered question that reads like a single patient | REQ-05, REQ-07 | TC-01, TC-05 |
| R-08 | Out-of-scope drug answered from model memory | Unverified information outside the dataset | 4 | 2 | 1 | 8 | NOT_IN_LABELS refusal; answers without valid citations are held | REQ-04, REQ-06, REQ-07 | TC-01, TC-04 |
| R-09 | Model provider unavailable or model changed | Service interruption, or results not reproducible | 3 | 3 | 1 | 9 | Paid API with dated model snapshot; model that answered recorded per run; retries with backoff; cached evaluation; no silent fallback model | REQ-11 | TC-10 |
| R-10 | Evaluation judge wrong | Quality over- or under-estimated | 3 | 3 | 2 | 18 | Judge from another vendor; validated against blind human grades with a criterion fixed in advance; computed metrics where possible | REQ-14 | TC-12 |
| R-11 | Golden set error | Evaluation measures against a wrong answer | 3 | 3 | 2 | 18 | Human review of every item against source passages with a written procedure; deviations corrected and versioned (golden set 1.1) | REQ-08, REQ-14 | TC-01, TC-12 |
| R-12 | Result not reproducible | An answer cannot be explained in an audit | 3 | 2 | 1 | 6 | Commit, dirty flag, prompt hash, data versions, snapshot hash, model logged in MLflow for every run; Langfuse trace per answer | REQ-11, REQ-12 | TC-10, TC-11 |

**Residual risk.** The highest remaining risks are R-05 and R-01: a multi-label answer can omit a drug, and
grounding is a lexical proxy. Both are mitigated by routing to human review rather than by the model
alone: in the evaluation of the release configuration, every answer the judge rated incorrect was held.
The system is decision support for trained staff, not a replacement for consulting the label.

## Approval

| Role | Name | Date | Decision |
|---|---|---|---|
| Risk owner | Ivan Namor | 2026-10-17 | Approved |

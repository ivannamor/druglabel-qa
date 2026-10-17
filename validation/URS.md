# User Requirements Specification (URS)

**System:** DrugLabel QA, a question-answering assistant over FDA drug labels for medical information
and pharmacovigilance staff. **Version:** 1.0 (release candidate `v1.0.0`). **Status:** approved 2026-10-17.

Intended use: answer factual questions about the content of the official labels in the dataset
(anticoagulants, antiplatelets and the drugs that interact with them), with a citation to the label
passage for every statement. Not intended for clinical decisions about individual patients.

Each requirement is verified by the tests in [`test_protocol.md`](test_protocol.md); the links are in
[`traceability_matrix.csv`](traceability_matrix.csv). Risks addressed are in
[`risk_assessment.md`](risk_assessment.md).

| ID | Requirement | Priority |
|---|---|---|
| REQ-01 | Answers state only information contained in the label passages provided to the model, not general knowledge. | Must |
| REQ-02 | Every factual statement in an answer cites the label passage it comes from, by chunk ID. | Must |
| REQ-03 | Every citation is verifiable: it refers to a passage that was retrieved for the question and that traces back to its label ID, set ID, label version and effective date. | Must |
| REQ-04 | When the labels do not contain the answer, the system says so instead of answering. | Must |
| REQ-05 | The system declines questions asking for a treatment or dose decision for an individual patient. | Must |
| REQ-06 | Questions about drugs outside the dataset, or on topics labels do not cover, are refused. | Must |
| REQ-07 | Answers that fail automated checks (missing or invalid citation, weak grounding, wrong drug, answers drawing on several drug labels) are not released; they are recorded in a human review queue with the reasons. | Must |
| REQ-08 | On a reviewed golden set, answers meet predefined accuracy criteria, and no released answer is incorrect beyond a predefined tolerance. | Must |
| REQ-09 | Questions whose answer spans several labels (e.g. "which anticoagulants interact with X?") are supported, through the knowledge graph combined with text retrieval. | Should |
| REQ-10 | Instructions contained in source text are treated as data and not followed (prompt injection). | Must |
| REQ-11 | Every answer and every evaluation run is reproducible from recorded information: git commit, prompt name and hash, data versions, model and parameters. | Must |
| REQ-12 | Every model call is traced with latency, tokens and cost. | Should |
| REQ-13 | A configuration is released only after a validation run meets the predefined acceptance criteria; the approval records who approved and when. | Must |
| REQ-14 | The automated judge used for evaluation is validated against human grading before its scores are relied on. | Must |
| REQ-15 | Source data is kept as received (raw layer) and every derived dataset is versioned and linked to the version it was built from. | Must |

## Approval

| Role | Name | Date | Decision |
|---|---|---|---|
| Requirements owner | Ivan Namor | 2026-10-17 | Approved |

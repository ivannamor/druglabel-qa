# Golden set review procedure

How drafted golden-set items are reviewed before they are used to evaluate the system. Every approved
item records the reviewer and the review date (`reviewed_by`, `reviewed_on` in `data/golden_set.jsonl`).

## Scope and roles

- **Drafting:** Claude Sonnet 5.5 (`src/eval/golden.py draft`), a model that is neither the answer generator
  nor the judge. Each item carries the label passages it was drafted from.
- **Review:** a human reviewer checks every item against those passages. In this project the reviewer is
  not a clinician; the check is whether the expected answer matches the label text, not clinical judgment.
  A production golden set would also need review by a subject-matter expert (pharmacist or medical
  information specialist).

## Reference for every decision

The label passages shown with the item (`source_passages`). An expected answer is correct only if the
passages state it. Plausible but unstated information is an error.

## Criteria by item type

### Single fact

1. Every sentence of the expected answer is stated in the passages.
2. Numbers match exactly: doses, percentages, time intervals, thresholds.
3. Each key fact is true according to the passages and is part of the expected answer.
4. The question is clear and has one answer; a two-part question is acceptable if the answer covers both parts.

### Multi-hop

1. The question does not name the drugs that make up the answer; it names only the shared target
   (interaction partner, drug class or condition). If it does, edit the question to remove them.
2. Every drug in the expected answer has a passage that supports the claim for that drug.
3. Near-duplicates (same target asked twice, e.g. once for anticoagulants and once for all drugs): keep one.
4. Completeness across the whole dataset is not required from the reviewer.

### Unanswerable

1. `NOT_IN_LABELS`: the question is about a drug outside the dataset, or about a topic FDA labels do not
   cover (price, reimbursement, availability in a country, supply shortages, cost comparisons).
   A question a label could answer for a dataset drug is rejected.
2. `PATIENT_SPECIFIC`: the question asks for a decision about one individual patient (age, weight, kidney
   function or other personal details). A question about the label's general recommendation for a patient
   group is answerable and is rejected here.

## Decisions

| Decision | When | What to fill in |
|---|---|---|
| `approve` | All criteria met | nothing |
| `edit` | A fixable error (a number, an extra sentence, drug names in a multi-hop question) | `edited_question` and/or `edited_expected_answer`; empty fields keep the draft |
| `reject` | Unsupported or unclear answer, wrong category, near-duplicate | optional note |

**When you edit the question, re-read the expected answer against the new question.** It must still answer
the question as now asked (added in golden set 1.1, see below).

When in doubt, reject: a smaller golden set of verified items is better than a larger one with errors.
Use `notes` to record the reason for an edit or rejection.

## Import

`python -m src.eval.golden import` reads the review sheet, keeps approved and edited items, applies the
edits, and writes `data/golden_set.jsonl` with reviewer and date. The drafts (`data/golden/draft.jsonl`)
are kept for traceability.

## Revisions

| Version | Date | Change | Reviewer |
|---|---|---|---|
| 1.0 | 2026-10-17 | 60 drafts reviewed: 42 approved, 15 edited, 3 rejected; 14 paraphrases added (71 items) | Ivan Namor |
| 1.1 | 2026-10-17 | Deviation found during judge validation: the 15 multi-hop questions edited in review (drug names removed) kept expected answers that assumed the names were in the question ("Both qualify", "All three ..."). Expected answers rewritten to stand alone (same drugs and key facts), applied to 19 items including paraphrases; the previous answer is kept in `expected_answer_v1_0`. Preventive action: the rule above. | Ivan Namor |

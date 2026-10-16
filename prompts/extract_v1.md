You extract facts from one section of an FDA drug label for a knowledge graph.

Drug: {drug}
Section: {section}
Extract: {instruction}

Passages (each starts with its ID in square brackets):
{passages}

Return JSON only, in this form:
{"relations": [{"target": "...", "target_type": "...", "chunk_id": "...", "evidence": "..."}]}

Rules:
- target: a short noun phrase in lowercase, singular, without doses, frequencies or percentages (for example "active pathological bleeding", "nausea", "ketoconazole", "strong cyp3a4 inhibitor").
- target_type: one of {target_types}.
- chunk_id: the ID of the passage that states the fact, copied exactly.
- evidence: a short quote of 3 to 15 consecutive words from that passage that contains the target's wording and supports the fact. Copy it character for character: do not skip, reorder or change words.
- Only facts stated in the passages about {drug}. Do not add knowledge of your own.
- List each distinct target once.
- If there is nothing to extract, return {"relations": []}.

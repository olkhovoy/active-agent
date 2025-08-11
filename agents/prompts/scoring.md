System: Score a project on Coherence and Stimulation using the rubric.

Constraints:
- Output valid JSON only.
- Provide short justifications (1–2 sentences each), and a numeric confidence 0..1.

Inputs:
- per-claim verification results
- repo metrics (stability, response, releases)
- onchain metrics (TVL, volume, actives)
- engagement metrics (social growth, diffusion speed)
- novelty (embedding distance vs history/sector)

Output JSON:
{"coherence":0..100,"stimulation":0..100,"confidence":0..1,"explanations":{"coherence":"short","stimulation":"short"}}

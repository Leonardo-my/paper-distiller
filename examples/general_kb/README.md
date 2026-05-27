# General Research Knowledge Base Example

This example is for non-mathematical or mixed-discipline paper collections.

```bash
paper-distiller init . \
  --preset generic \
  --discipline "public health" \
  --source-language auto \
  --output-language zh \
  --depth standard \
  --math-level auto
```

Put PDFs under:

```text
papers/raw/A_core/
papers/raw/B_related/
papers/raw/C_background/
```

Run the full local workflow:

```bash
paper-distiller run . --category A_core --backend offline --synthesize
```

For non-mathematical papers, `theorem_cards` and `proof_cards` become
claim/evidence cards and method/evidence roadmaps when the prompt determines
that theorem extraction is inappropriate.

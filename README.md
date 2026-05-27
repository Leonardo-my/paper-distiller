# Paper Distiller

Paper Distiller is a Python CLI framework for turning research papers into a
structured Markdown knowledge base.

It is designed for workflows where an LLM drafts notes, theorem cards, proof
roadmaps, writing-pattern cards, and audit reports, while the software enforces
folder layout, metadata updates, repeatable prompts, and reliability checks.

The first bundled preset, `stat-transfer`, is built for statistical transfer
learning literature reviews. You can add your own presets for other fields.

## What It Does

- Initializes a reproducible paper knowledge-base layout.
- Extracts PDF text into `papers/text/...`.
- Treats `paper.pdf` and `paper_Supplement.pdf` as one paper.
- Generates one-paper distillation outputs from prompt templates.
- Supports `A_core`, `B_related`, and `C_background` paper tiers.
- Updates `metadata/reading_status.csv` without marking human verification
  automatically.
- Runs structural checks for missing outputs, missing audit files, and missing
  reliability labels.
- Supports pluggable LLM backends:
  - `offline`: writes scaffold files for manual or later LLM completion.
  - `command`: pipes prompts to any command you provide.
  - `openai`: optional OpenAI Responses API backend.

## Quick Start

```bash
python -m pip install -e ".[dev,openai]"
paper-distiller init ./my-kb --preset stat-transfer
```

Put PDFs here:

```text
my-kb/papers/raw/A_core/
my-kb/papers/raw/B_related/
my-kb/papers/raw/C_background/
```

Extract text:

```bash
paper-distiller extract ./my-kb
```

Generate scaffold Markdown without an API call:

```bash
paper-distiller distill ./my-kb A_core my-paper --backend offline
```

Batch-generate all extracted `A_core` papers:

```bash
paper-distiller distill-batch ./my-kb --category A_core --backend offline
```

Generate with OpenAI:

```bash
set OPENAI_API_KEY=...
paper-distiller distill ./my-kb A_core my-paper --backend openai --model gpt-5.5
```

Or use any local command that reads a prompt from stdin and prints Markdown:

```bash
paper-distiller distill ./my-kb A_core my-paper --backend command --llm-command "my-llm-cli --markdown"
```

Check the knowledge base:

```bash
paper-distiller check ./my-kb
paper-distiller status ./my-kb
```

## Output Layout

```text
papers/raw/{A_core,B_related,C_background}/
papers/text/{A_core,B_related,C_background}/

notes/
  literature/{A_core,B_related,C_background}/
  theorem_cards/{A_core,B_related,C_background}/
  proof_cards/{A_core,B_related,C_background}/
  writing_patterns/{A_core,B_related,C_background}/
  verification/{A_core,B_related,C_background}/
  concept_cards/
  topic_maps/batches/
  research_gaps/

metadata/
  bibliography.csv
  reading_status.csv

prompts/
```

For each `A_core` paper, the default preset generates:

- literature note
- theorem card
- proof card
- writing-pattern card
- audit report

For `B_related`, it generates:

- literature note
- theorem card
- audit report

For `C_background`, it generates:

- short literature note
- audit report

## Reliability Model

Paper Distiller does not pretend OCR and LLM output are final truth. Its default
rules are conservative:

- Do not invent venues, citation counts, submission targets, or author intent.
- Mark uncertain formulas as `needs PDF check`.
- Preserve theorem, lemma, assumption, algorithm, and equation numbers.
- Distinguish exact formulas, upper bounds, lower bounds, asymptotic limits,
  consistency, optimality, and oracle optimality.
- Never set `human_verified = true` automatically.
- Treat audit reports as skeptical checks, not summaries.

## Development

```bash
python -m pip install -e ".[dev]"
pytest
ruff check .
```

## Publishing To GitHub

If you have GitHub CLI installed and authenticated:

```bash
gh repo create paper-distiller --public --source . --remote origin --push
```

Without GitHub CLI, create an empty public repository named `paper-distiller` on
GitHub, then run:

```bash
git remote add origin https://github.com/<your-user>/paper-distiller.git
git branch -M main
git push -u origin main
```

## License

MIT.

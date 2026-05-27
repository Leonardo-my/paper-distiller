# Paper Distiller

Paper Distiller is a Python CLI framework for turning research papers into a
structured Markdown knowledge base.

It is designed for workflows where an LLM drafts notes, theorem cards, proof
roadmaps, writing-pattern cards, and audit reports, while the software enforces
folder layout, metadata updates, repeatable prompts, and reliability checks.

The bundled `generic` preset is field-agnostic and works across disciplines.
The `stat-transfer` preset is a specialized statistical transfer learning
workflow. You can add your own presets for other fields.

## What It Does

- Initializes a reproducible paper knowledge-base layout.
- Extracts PDF text into `papers/text/...`.
- Treats `paper.pdf` and `paper_Supplement.pdf` as one paper.
- Generates one-paper distillation outputs from prompt templates.
- Generates cross-paper batch synthesis files from completed single-paper notes.
- Supports `A_core`, `B_related`, and `C_background` paper tiers.
- Supports discipline, language, depth, audience, and math-level profiles.
- Updates `metadata/reading_status.csv` without marking human verification
  automatically.
- Runs structural checks for missing outputs, missing audit files, and missing
  reliability labels.
- Supports pluggable LLM backends:
  - `offline`: writes scaffold files for manual or later LLM completion.
  - `command`: pipes prompts to any command you provide.
  - `openai`: optional OpenAI Responses API backend.

## Quick Start

Install from GitHub:

```bash
python -m pip install "paper-distiller[openai] @ git+https://github.com/Leonardo-my/paper-distiller.git"
```

Or install from a local clone for development:

```bash
python -m pip install -e ".[dev,openai]"
```

Create a knowledge base:

```bash
paper-distiller init ./my-kb --preset generic --discipline biology --output-language en
```

See available presets:

```bash
paper-distiller presets
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

## One-Command Workflow

After initialization, users can place PDFs under `papers/raw/...` and run:

```bash
paper-distiller run ./my-kb --category A_core --backend openai --model gpt-5.5
```

For a batch that should also produce cross-paper synthesis:

```bash
paper-distiller run ./my-kb --category A_core --backend openai --model gpt-5.5 --synthesize --batch-id batch_01
```

The CLI is not a background folder watcher. Users explicitly run the command
after adding PDFs, which keeps API usage and generated files predictable.

## Discipline And Language Profiles

Paper Distiller is not limited to mathematical papers. Use the `generic` preset
for broad disciplinary coverage:

```bash
paper-distiller init ./my-kb \
  --preset generic \
  --discipline "public health" \
  --source-language auto \
  --output-language zh \
  --depth deep \
  --math-level light
```

Supported profile options:

```text
--preset            generic | stat-transfer | custom preset directory name
--discipline        free text, e.g. biology, economics, history, medicine
--source-language   auto | en | zh
--output-language   en | zh | bilingual | same-as-source
--depth             short | standard | deep
--audience          free text, e.g. researcher, clinician, graduate student
--math-level        auto | none | light | heavy
```

The profile is stored in:

```text
paper_distiller.toml
```

All generation commands read this file. You can override the profile for a
single run:

```bash
paper-distiller distill ./my-kb A_core example-paper \
  --backend openai \
  --model gpt-5.5 \
  --discipline economics \
  --output-language bilingual \
  --math-level auto
```

View or update a project profile without editing TOML:

```bash
paper-distiller profile ./my-kb

paper-distiller profile ./my-kb \
  --discipline "environmental epidemiology" \
  --output-language bilingual \
  --depth deep \
  --install-templates
```

For non-mathematical papers, the generic preset adapts theorem/proof cards into
claim/evidence and method/evidence roadmaps instead of forcing formulas.

For statistical transfer learning or other theorem-heavy fields, use:

```bash
paper-distiller init ./transfer-kb \
  --preset stat-transfer \
  --discipline "statistical transfer learning" \
  --output-language bilingual \
  --math-level heavy
```

## Workflow Coverage

Single `A_core` paper:

```bash
paper-distiller distill ./my-kb A_core my-paper --backend openai --model gpt-5.5
```

Generates exactly these five files:

```text
notes/literature/A_core/my-paper.md
notes/theorem_cards/A_core/my-paper-theorems.md
notes/proof_cards/A_core/my-paper-proof-techniques.md
notes/writing_patterns/A_core/my-paper-writing-patterns.md
notes/verification/A_core/my-paper-audit.md
```

Multiple `A_core` papers with synthesis:

```bash
paper-distiller distill-batch ./my-kb --category A_core --backend openai --model gpt-5.5 --synthesize --batch-id batch_01
```

Generates the five single-paper files for each paper, plus:

```text
notes/topic_maps/batches/batch_01_overview.md
notes/topic_maps/batches/batch_01_theorem_comparison.md
notes/topic_maps/batches/batch_01_assumption_map.md
notes/topic_maps/batches/batch_01_proof_technique_map.md
notes/research_gaps/batch_01_gap_list.md
notes/verification/batch_01_synthesis_audit.md
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

For an `A_core` batch synthesis, the default preset generates:

- `notes/topic_maps/batches/{batch_id}_overview.md`
- `notes/topic_maps/batches/{batch_id}_theorem_comparison.md`
- `notes/topic_maps/batches/{batch_id}_assumption_map.md`
- `notes/topic_maps/batches/{batch_id}_proof_technique_map.md`
- `notes/research_gaps/{batch_id}_gap_list.md`
- `notes/verification/{batch_id}_synthesis_audit.md`

You can also run synthesis separately after single-paper files exist:

```bash
paper-distiller synthesize ./my-kb batch_01 --category A_core --backend openai --model gpt-5.5
```

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

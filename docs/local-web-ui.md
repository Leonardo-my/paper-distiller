# Local Web UI Walkthrough

This is the easiest route for non-developers. The app runs locally in a browser
and writes Markdown files to a normal folder on the user's computer.

## Install From GitHub

```bash
python -m pip install "paper-distiller[openai,ui] @ git+https://github.com/Leonardo-my/paper-distiller.git"
paper-distiller-ui
```

The UI opens in the default browser. If it does not open automatically, use the
URL printed in the terminal, usually:

```text
http://localhost:8501
```

## Install From A Downloaded ZIP

1. Install Python 3.10 or newer.
2. Download the GitHub repository ZIP and unzip it.
3. Open PowerShell or a terminal in the unzipped folder.
4. Run:

```bash
python -m pip install -e ".[openai,ui]"
paper-distiller-ui
```

For a launch that does not open a browser automatically:

```bash
paper-distiller-ui --headless
```

## Basic User Flow

1. In the sidebar, choose a knowledge-base folder. If the folder does not exist,
   Paper Distiller creates the required layout automatically when the user saves
   the profile, uploads PDFs, or starts a run.
2. Select a preset:
   - `generic` for broad literature review workflows.
   - `stat-transfer` for statistical transfer learning papers.
3. Choose output language, depth, audience, and math level.
4. Upload PDFs into `A_core`, `B_related`, or `C_background`.
5. Choose a backend:
   - `offline` creates scaffold Markdown without API calls.
   - `openai` uses the OpenAI backend and requires an API key plus a model name.
   - `command` pipes prompts to any command that reads from stdin and prints Markdown.
6. Press `Run`.
7. Open `Results` to preview Markdown, inspect structural checks, or download a
   ZIP containing generated Markdown outputs.

## Model Backends

OpenAI:

```powershell
$env:OPENAI_API_KEY="..."
paper-distiller run ./my-kb --category A_core --backend openai --model YOUR_MODEL_NAME
```

Command backend for other providers or local tools:

```bash
paper-distiller run ./my-kb --category A_core --backend command --llm-command "your-llm-command"
```

The command must read the prompt from stdin and write Markdown to stdout. This
keeps the framework independent from any single model vendor.

## Expected Outputs

For one `A_core` paper, the app creates:

```text
notes/literature/A_core/{paper-stem}.md
notes/theorem_cards/A_core/{paper-stem}-theorems.md
notes/proof_cards/A_core/{paper-stem}-proof-techniques.md
notes/writing_patterns/A_core/{paper-stem}-writing-patterns.md
notes/verification/A_core/{paper-stem}-audit.md
```

For an `A_core` batch with synthesis enabled, the app also creates:

```text
notes/topic_maps/batches/{batch_id}_overview.md
notes/topic_maps/batches/{batch_id}_theorem_comparison.md
notes/topic_maps/batches/{batch_id}_assumption_map.md
notes/topic_maps/batches/{batch_id}_proof_technique_map.md
notes/research_gaps/{batch_id}_gap_list.md
notes/verification/{batch_id}_synthesis_audit.md
```

## Notes

- Scanned image PDFs need OCR before extraction.
- `paper.pdf` and `paper_Supplement.pdf` are treated as one paper.
- API keys entered in the UI are only set for the current local process.
- The UI binds to `localhost` by default, so it is intended for local use on the
  user's own computer.

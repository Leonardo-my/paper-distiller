# Statistical Transfer Learning Example

This example shows the expected project shape. It intentionally contains no
PDFs or generated notes.

```bash
paper-distiller init . --preset stat-transfer
paper-distiller extract .
paper-distiller distill . A_core example-paper --backend offline
paper-distiller check .
```

End-to-end after placing PDFs:

```bash
paper-distiller run . --category A_core --backend offline
```

Batch synthesis after several `A_core` papers have been distilled:

```bash
paper-distiller synthesize . batch_01 --category A_core --backend offline
```

Use these PDF names for a paper with supplementary material:

```text
papers/raw/A_core/example-paper.pdf
papers/raw/A_core/example-paper_Supplement.pdf
```

They are processed as one paper and produce one set of Markdown outputs.

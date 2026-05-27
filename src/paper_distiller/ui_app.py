"""Streamlit app for Paper Distiller."""

from __future__ import annotations

import os
from pathlib import Path

from .config import DistillationConfig, load_config, save_config
from .constants import CATEGORIES
from .llm import OPENAI_MODEL_ENV, build_backend
from .metadata import ensure_metadata_files, read_status, upsert_status
from .paths import KnowledgeBasePaths, PaperId
from .pdf import extract_group_text, scan_pdf_groups
from .pipeline import distill_paper
from .synthesis import generate_synthesis
from .templates import PRESET_DESCRIPTIONS, copy_preset_templates, list_package_presets
from .ui_core import collect_markdown_files, save_uploaded_pdfs, zip_markdown_files
from .validators import check_kb


def run_app() -> None:
    import streamlit as st

    st.set_page_config(page_title="Paper Distiller", page_icon="PD", layout="wide")
    st.title("Paper Distiller")
    st.caption("Local research-paper distillation into structured Markdown knowledge bases.")

    paths = _sidebar_project(st)
    config = _sidebar_profile(st, paths)
    backend_settings = _sidebar_backend(st)

    tab_upload, tab_run, tab_results = st.tabs(["Upload", "Run", "Results"])
    with tab_upload:
        _upload_tab(st, paths)
    with tab_run:
        _run_tab(st, paths, config, backend_settings)
    with tab_results:
        _results_tab(st, paths)


def _sidebar_project(st: object) -> KnowledgeBasePaths:
    st.sidebar.header("Project")
    default_root = str(Path.cwd() / "paper-distiller-kb")
    root_text = st.sidebar.text_input("Knowledge base folder", value=default_root)
    paths = KnowledgeBasePaths(Path(root_text).expanduser().resolve())
    st.sidebar.code(str(paths.root), language=None)
    return paths


def _sidebar_profile(st: object, paths: KnowledgeBasePaths) -> DistillationConfig:
    st.sidebar.header("Profile")
    presets = list_package_presets()
    current = load_config(paths.config_file)
    preset_index = presets.index(current.preset) if current.preset in presets else 0

    preset = st.sidebar.selectbox(
        "Preset",
        presets,
        index=preset_index,
        help="\n".join(f"{key}: {value}" for key, value in PRESET_DESCRIPTIONS.items()),
    )
    discipline = st.sidebar.text_input("Discipline", value=current.discipline)
    source_language = st.sidebar.selectbox(
        "Source language",
        ["auto", "en", "zh"],
        index=_safe_index(["auto", "en", "zh"], current.source_language),
    )
    output_language = st.sidebar.selectbox(
        "Output language",
        ["en", "zh", "bilingual", "same-as-source"],
        index=_safe_index(["en", "zh", "bilingual", "same-as-source"], current.output_language),
    )
    depth = st.sidebar.selectbox(
        "Depth",
        ["short", "standard", "deep"],
        index=_safe_index(["short", "standard", "deep"], current.depth),
    )
    audience = st.sidebar.text_input("Audience", value=current.audience)
    math_level = st.sidebar.selectbox(
        "Math level",
        ["auto", "none", "light", "heavy"],
        index=_safe_index(["auto", "none", "light", "heavy"], current.math_level),
    )

    config = DistillationConfig(
        preset=preset,
        discipline=discipline,
        source_language=source_language,
        output_language=output_language,
        depth=depth,
        audience=audience,
        math_level=math_level,
    ).normalized()

    if st.sidebar.button("Initialize / Save Profile", type="primary"):
        paths.ensure_layout()
        ensure_metadata_files(paths.metadata_dir)
        save_config(paths.config_file, config)
        copy_preset_templates(config.preset, paths.prompts_dir)
        st.sidebar.success("Project initialized and profile saved.")

    return config


def _sidebar_backend(st: object) -> dict[str, str | None]:
    st.sidebar.header("Model")
    backend = st.sidebar.selectbox("Backend", ["offline", "openai", "command"])
    model = None
    api_key = None
    command = None
    if backend == "openai":
        model = st.sidebar.text_input(
            "Model",
            value=os.environ.get(OPENAI_MODEL_ENV, ""),
            placeholder="Required unless PAPER_DISTILLER_OPENAI_MODEL is set",
        )
        api_key = st.sidebar.text_input("OPENAI_API_KEY", type="password")
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
    elif backend == "command":
        command = st.sidebar.text_input(
            "LLM command",
            placeholder="my-llm-cli --markdown",
        )
    else:
        st.sidebar.info("Offline mode writes scaffold Markdown without calling a model.")

    return {
        "backend": backend,
        "model": model or None,
        "llm_command": command,
    }


def _upload_tab(st: object, paths: KnowledgeBasePaths) -> None:
    st.subheader("Upload PDFs")
    st.write(
        "Upload files into `papers/raw/{category}`. Supplement files should end "
        "with `_Supplement.pdf`."
    )
    category = st.selectbox("Upload category", list(CATEGORIES), key="upload-category")
    uploads = st.file_uploader("PDF files", type=["pdf"], accept_multiple_files=True)
    if st.button("Save uploaded PDFs"):
        paths.ensure_layout()
        saved = save_uploaded_pdfs(uploads or [], paths, category)
        if saved:
            st.success(f"Saved {len(saved)} PDF file(s).")
            for path in saved:
                st.code(str(path), language=None)
        else:
            st.warning("No PDF files were saved.")

    st.divider()
    st.subheader("Current raw PDFs")
    raw_files = sorted(paths.raw_dir.rglob("*.pdf")) if paths.raw_dir.exists() else []
    if raw_files:
        for path in raw_files:
            st.write(path.relative_to(paths.root).as_posix())
    else:
        st.caption("No PDFs found yet.")


def _run_tab(
    st: object,
    paths: KnowledgeBasePaths,
    config: DistillationConfig,
    backend_settings: dict[str, str | None],
) -> None:
    st.subheader("Run Workflow")
    category = st.selectbox("Process category", list(CATEGORIES), key="run-category")
    synthesize = st.checkbox("Generate batch synthesis", value=False)
    batch_id = st.text_input("Batch id", value="batch_01")
    force = st.checkbox("Overwrite existing extracted/generated files", value=False)
    limit = st.number_input("Limit papers (0 = no limit)", min_value=0, value=0, step=1)

    if st.button("Run", type="primary"):
        try:
            _run_workflow(
                st,
                paths=paths,
                config=config,
                category=category,
                backend=backend_settings["backend"] or "offline",
                model=backend_settings["model"],
                llm_command=backend_settings["llm_command"],
                synthesize=synthesize,
                batch_id=batch_id,
                force=force,
                limit=int(limit) or None,
            )
        except Exception as exc:  # noqa: BLE001 - user-facing UI error boundary
            st.error(str(exc))


def _run_workflow(
    st: object,
    *,
    paths: KnowledgeBasePaths,
    config: DistillationConfig,
    category: str,
    backend: str,
    model: str | None,
    llm_command: str | None,
    synthesize: bool,
    batch_id: str,
    force: bool,
    limit: int | None,
) -> None:
    paths.ensure_layout()
    ensure_metadata_files(paths.metadata_dir)
    save_config(paths.config_file, config)
    copy_preset_templates(config.preset, paths.prompts_dir, force=force)

    with st.spinner("Extracting PDF text..."):
        extracted, skipped = _extract_all(paths, category=category, force=force)
    st.info(f"Extracted {extracted} paper(s); skipped {skipped}.")

    papers = _find_extracted_papers(paths, category=category, limit=limit)
    if not papers:
        st.warning("No extracted text files found for this category.")
        return

    progress = st.progress(0)
    status = st.empty()
    written_count = 0
    for index, paper in enumerate(papers, start=1):
        status.write(f"Distilling {paper.category}/{paper.stem} ({index}/{len(papers)})")
        llm = build_backend(
            backend,
            target_name=f"{paper.category}/{paper.stem}",
            model=model,
            llm_command=llm_command,
        )
        written_count += len(distill_paper(paths, paper, llm, config=config, force=force))
        progress.progress(index / len(papers))
    st.success(f"Distillation complete. Wrote {written_count} file(s).")

    if synthesize:
        with st.spinner("Generating synthesis files..."):
            llm = build_backend(
                backend,
                target_name=f"synthesis/{batch_id}",
                model=model,
                llm_command=llm_command,
            )
            synthesis_files = generate_synthesis(
                paths,
                batch_id=batch_id,
                category=category,
                backend=llm,
                config=config,
                force=force,
            )
        st.success(f"Wrote {len(synthesis_files)} synthesis file(s).")

    issues = check_kb(paths)
    if issues:
        st.warning(f"Structural check found {len(issues)} issue(s). Open Results for details.")
    else:
        st.success("Structural check passed.")


def _results_tab(st: object, paths: KnowledgeBasePaths) -> None:
    st.subheader("Metadata")
    rows = read_status(paths.reading_status_csv)
    if rows:
        st.dataframe(rows, use_container_width=True)
    else:
        st.caption("No reading status rows yet.")

    st.subheader("Structural Check")
    issues = check_kb(paths)
    if issues:
        st.dataframe(
            [
                {
                    "severity": issue.severity,
                    "path": str(issue.path or ""),
                    "message": issue.message,
                }
                for issue in issues
            ],
            use_container_width=True,
        )
    else:
        st.success("No structural issues found.")

    st.subheader("Markdown Outputs")
    markdown_files = collect_markdown_files(paths)
    if not markdown_files:
        st.caption("No Markdown outputs yet.")
        return

    selected = st.selectbox("Preview file", [file.relative_path for file in markdown_files])
    selected_file = next(file for file in markdown_files if file.relative_path == selected)
    st.markdown(selected_file.path.read_text(encoding="utf-8", errors="replace"))

    zip_bytes = zip_markdown_files(markdown_files)
    st.download_button(
        "Download Markdown ZIP",
        data=zip_bytes,
        file_name="paper-distiller-notes.zip",
        mime="application/zip",
    )


def _extract_all(
    paths: KnowledgeBasePaths,
    category: str,
    force: bool = False,
) -> tuple[int, int]:
    groups = [group for group in scan_pdf_groups(paths.raw_dir) if group.paper.category == category]
    done = 0
    skipped = 0
    for group in groups:
        text_path = paths.text_file(group.paper)
        if text_path.exists() and not force:
            skipped += 1
            continue
        text_path.parent.mkdir(parents=True, exist_ok=True)
        text_path.write_text(extract_group_text(group), encoding="utf-8")
        upsert_status(
            paths.reading_status_csv,
            group.paper.raw_file_name,
            {"extracted": True, "human_verified": False},
        )
        done += 1
    return done, skipped


def _find_extracted_papers(
    paths: KnowledgeBasePaths,
    category: str,
    limit: int | None,
) -> list[PaperId]:
    text_dir = paths.text_dir / category
    if not text_dir.exists():
        return []
    papers = [PaperId(category=category, stem=path.stem) for path in sorted(text_dir.glob("*.txt"))]
    if limit is not None:
        return papers[:limit]
    return papers


def _safe_index(values: list[str], value: str) -> int:
    try:
        return values.index(value)
    except ValueError:
        return 0


if __name__ == "__main__":
    run_app()

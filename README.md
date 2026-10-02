# Tour de gross: BB surgery circuit and simulation design bundle

This bundle provides a theory report, implementation/test design and small independently executable reference checks for reproducing Appendix A.7 / Figure 15 of arXiv:2506.03094v1. It covers gross in-module XX and Y measurement, Bell-connected inter-module XX measurement and physical shift automorphisms, with two-gross support planned throughout.

Read the self-contained `report/report.tex` first; rebuild the PDF locally if needed. The report follows four main sections: Introduction; general framework; BB in-/inter-module examples; implementation details. `report/references.bib` is an editable bibliography export; the self-contained TeX uses a built-in bibliography so it compiles without BibTeX.

Then read `docs/IMPLEMENTATION_PLAN.md`, `docs/ARCHITECTURE.md`, `docs/REPRODUCTION_SPEC.md` and `docs/VALIDATION_PLAN.md`. Start Codex with `AGENTS.md`, `STATUS.md` and `prompts/00_source_audit.md`; give subsequent prompts one at a time.

## Development setup

Use the Anaconda environment `tour_de_gross`; see [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md). The installable scaffold is `src/gross_design_bandle/` (distribution `gross-design-bandle`). External source checkouts live in `external_libs/`; fork them before modifications. Generated results and local checkouts are ignored by Git.

```bash
conda env create -f environment.yml
conda activate tour_de_gross
python -m pip install --no-build-isolation -e .
```

## Automated development prompts

The tmux controller and JSON phase gates are documented in [prompts/scripts/README.md](prompts/scripts/README.md). Use `prompts/scripts/run_codex_pipeline.sh --preflight` to check the local CLI/environment and `--dry-run --through 11` to inspect the plan. Implementation starts only when you explicitly launch the runner. Each phase uses a feature branch/worktree; after acceptance, the controller commits, merges into `main`, and pushes both refs to `origin`.

## What is already executable

```bash
python -m pip install -r requirements-audit.txt
python -m pytest -q tests/test_reference.py
python tools/audit_reference.py --output evidence/algebra_audit.json
python tools/reconstruct_fits.py --output evidence/reference_fits.csv
```

The reference audit validates the transcribed code/logical/graph data for gross and two-gross and checks omitted-cycle membership in the combined binary stabilizer span, rank and commutation of X, XX, Y and an algebraic inter-XX reconstruction. Nine utility tests pass. It does not simulate physical noise or certify a circuit distance. The fit script evaluates published rounded fit parameters; its output is not sampled data.

## What remains to build

The physical Stim circuit generator, full signed instrument tests, schedule/flow compiler, primitive-fault model, Relay adapter and Monte Carlo package are designed but not implemented. `configs/strict_inter_template.json` is deliberately an unresolved design template, not a runnable simulation configuration. Exact-reproduction blockers are documented rather than silently filled in.

Figure 15 contains two-gross idle and shift data only. Two-gross measurement simulations are an extension. Also, the printed inter-module K=23 needs a source-defined observable set; a full two-block centralizer has K=47. Current Relay parameters must be mapped semantically to Table 7. Both points are handled explicitly in the design.

## Contents

`report/` contains the journal-style report and editable sources. `reference/` contains source provenance, code/LPU JSON and Tables 6--7 data. `tools/`, `tests/` and `evidence/` contain the limited executed reference checks. `docs/` holds the engineering and scientific contracts; `prompts/` contains fourteen bounded implementation phases. `STATUS.md` distinguishes completed reference work from future simulation work.

To rebuild the report: `cd report && pdflatex -interaction=nonstopmode -halt-on-error report.tex` twice. No external figures or fonts are required.

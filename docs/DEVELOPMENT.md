# Development setup

Use the Anaconda environment named `tour_de_gross` (underscores; no spaces). The main distribution is `gross-design-bandle`, imported as `gross_design_bandle`, at `src/gross_design_bandle/`. This spelling follows the requested package path. Only an installable scaffold exists; no simulator or CLI is implemented.

```bash
conda env create -f environment.yml
conda activate tour_de_gross
python -m pip install --no-build-isolation -e .
python -m pytest -q tests/test_reference.py
```

If the environment already exists, activate it and install `requirements-audit-lock.txt` with `python -m pip install -r requirements-audit-lock.txt`. For noninteractive commands use `conda run --no-capture-output -n tour_de_gross ...`. Always keep installs and tests in this environment.

`environment.yml` plus `requirements-audit-lock.txt` defines the audit setup. `locks/conda-linux-64.explicit.txt` records the actual Conda artifacts for this machine; recreate the Conda layer with `conda create -n tour_de_gross --file locks/conda-linux-64.explicit.txt` and then install the pip lock and editable package. This is an audit-only lock. Stim, qLDPC and Relay require compatibility/license/source audits in prompt 00 before installation.

External source checkouts belong in `external_libs/` (on this machine `/home/quantum_teresheys/workspace/tour_de_gross_design_bundle/external_libs`). Install dependencies into Conda. Fork external libraries before modifying them; see `external_libs/README.md`. Pin source commits and record blob hashes and license attribution. Keep adapters in the main package when source changes are unnecessary.

Git tracks source, scientific fixtures, docs, locks and four small curated delivery evidence files. Generated circuits, sampling outputs, caches, logs, external checkouts and report build products remain local. New evidence belongs under ignored `evidence/setup/` or phase-specific directories; summarize actual results and paths in STATUS. Never ignore `reference/` or regenerate its fixtures from the implementation under test.

The original delivered checksum index is preserved as `SHA256SUMS.delivery.txt`; it includes a report PDF absent from the supplied workspace. `SHA256SUMS.txt` indexes current nonignored source files except checksum indexes themselves. Setup does not advance implementation phases: prompt 00 is still next and O1--O5 remain unresolved.

The Codex/tmux development controller, phase JSON gates and CLI availability checks are documented in `prompts/scripts/README.md`. It does not start automatically.

Each feature is implemented and validated in a separate worktree on `feature/<phase-stem>`, based on clean synchronized `main`. The controller commits successful work, merges it to main and atomically pushes both refs to origin. Work from the canonical main checkout when launching the pipeline; see the runner guide for failed-feature and publication recovery.

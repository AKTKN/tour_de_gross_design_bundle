# External library workspace

Keep external source checkouts in this directory. Checkouts and build products are ignored by Git; this policy file is tracked. Python packages are installed into the `tour_de_gross` Conda environment, not with `pip --target external_libs`.

Before editing an external library, first create a GitHub fork under the user's account, clone that fork here and preserve the original repository as the upstream remote. Never push changes to upstream. For read-only inspection, a pinned upstream checkout is sufficient. Forking is authorized when needed for the requested phase; it does not authorize unrelated upstream changes.

Read licenses before copying or adapting code. Record upstream/fork URLs, exact commits, inspected blob hashes, license paths and local modifications in the phase source lock. Use editable installs from a fork for modified libraries. Do not vendor whole external repositories into this package or track nested repository contents. No external libraries have been fetched during setup; compatibility and source verification belong to prompt 00.

# Sources and provenance

Canonical scientific source: Theodore J. Yoder et al., *Tour de gross: A modular quantum computer based on bivariate bicycle codes*, arXiv:2506.03094v1 (2025). https://arxiv.org/abs/2506.03094v1 . The 68-page PDF, not the differently numbered experimental HTML rendering, defines equation references in this bundle.

The source-to-artifact map is: A.1 / Eqs. (27)--(38) -> BB polynomials, logical bases and shifts; A.3 / Eqs. (39)--(64) and Fig. 5 -> LPU fixtures and selected cycles; A.4 / Figs. 13(b) and 14 -> protocol and adapter semantics (factory adapter is outside the requested implementation scope); A.5 / Eqs. (65)--(72) -> scheduling constraints and reference coloring; A.7 / Fig. 15 / Tables 6--7 -> noise, observables, decoder parameters and fits; A.8 / Tables 4 and 8 -> distance-test design.

Foundational references are Dominic J. Williamson and Theodore J. Yoder, *Low-overhead fault-tolerant quantum computation by gauging logical operators*, arXiv:2410.02213 (2024; later revision inspected); Andrew W. Cross, Zhiyang He, Patrick Rall and Theodore J. Yoder, *Improved QLDPC Surgery: Logical Measurements and Bridging Codes*, arXiv:2407.18393 (2024); and Esha Swaroop, Tomas Jochym-O'Connor and Theodore J. Yoder, *Universal adapters between quantum LDPC codes*, arXiv:2410.03628 (2024). These establish general constructions; their generic graphs are not substituted for the TdG finite-size fixtures.

The later failure-spectrum companion is Michael E. Beverland, Malcolm Carroll, Andrew W. Cross and Theodore J. Yoder, *Fail fast: techniques to probe rare events in quantum error correction*, arXiv:2511.15177 (2025). It is useful background, not permission to silently change the older Figure-15 estimator.

Software source inspection used live GitHub file reads. Observed commit and blob IDs are recorded in `reference/sources.json`. In particular:

- qLDPC's `src/qldpc/experimental/surgery/__init__.py` names the single/joint PPM public APIs. Its `circuit.py` implements a CSS-based circuit layer and describes its observable convention. Its README warns that surgery is experimental and lacks independent expert review.
- SlidingWindowDecoder's `src/build_circuit.py::build_circuit` provides the concrete seven CNOT layers with staggered eight-step memory cycles, basis-dependent initial/final measurements and conventional depolarization.
- Relay's README and pyproject show the current Rust-backed Python interface and optional Stim integration. The historical Table-7 recurrence mapping was not executed or validated here.
- The bicycle architecture compiler README describes logical PBC/ISA compilation and resource estimation. It is not evidence that all physical Stim circuits underlying Figure 15 are provided there.

The delivered reference JSON is an original transcription of mathematical data. Upstream source files and the user Library PDF are not redistributed. The standalone audit code is newly written for this design, not copied from those repositories. Read and retain upstream licenses before copying code during implementation.

# Pre-publication clean-up checklist

While the project is being built, internal details are committed on purpose so that the people and
agents working on it share one context (see CLAUDE.md → *Git and GitHub*). Work through this list
**before the repo or report is announced publicly**. Add an item whenever you commit something
that should not ship.

## Content to remove or anonymise
- [ ] `docs/initial/`: internal blueprint and agent brief (product plans, internal chat context). Move them out of the repo and leave a short note.
- [ ] The internal product codename ("Project Sunset") in CLAUDE.md, ADR 0003, the evaluation protocol, the MCE card and the notes of test prompt `cs-001`.
- [ ] Real YouTube channel names, per-channel hours and corpus paths in `data/sources/hk-youtube-conversational.md` and `data/mixes/tts-lang-phase1-v0.yaml`. Replace them with aliases (`ch01`…).
- [ ] The same in `data/sources/README.md` (YouTube channel table with URLs), `data/pipelines/youtube-ingest.md` (channel status) and the prompts / channel lists inside `data/pipelines/scripts/`.
- [ ] The call-in live-stream source: its callers are members of the public. Remove its name, and never publish its audio, transcripts or cloned voices.
- [ ] `data/schemas/README.md` example row: it quotes a real creator's transcript and names a speaker. Replace it with a made-up row.
- [ ] Unverified claims about named third-party models (e.g. `jmtl` in the base-model card and the CV `yue` card). Measure them or label them as unverified.
- [ ] Test prompts `col-005` and `cs-004` paraphrase a creator's lines. Consider rewording them in a new test-set version.
- [ ] Any host names, home paths or user names in `experiments/*/env/` (`scripts/capture-env.sh` masks them, but check runs captured another way).

## Git history
- [ ] All of the above also lives in history. Before going public, either rewrite history (e.g. `git filter-repo`) and force-push after telling every collaborator, or publish from a fresh repo that holds only the cleaned tree.
- [ ] Commit author e-mails show in history. Check that every contributor is happy for theirs to be public.

## Final checks
- [ ] Grep the tree for names, paths, codenames and e-mails from the lists above.
- [ ] Each data card's licence section allows whatever the report publishes (samples, statistics, manifests).

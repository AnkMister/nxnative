# Integration records

Branch logs are archived here. Source paths are repository-relative. External
acceptance evidence is retained by the task owner and is not part of the source
checkout. Historical commands use named placeholders instead of machine paths.

`OOT_EVIDENCE_ROOT` selects external integration evidence; `OOT_SHARED_CONTEXT`
selects the shared task workspace; `OOT_READONLY_GAME_ROOT` and
`OOT_PROTECTED_BASELINE` identify protected read-only inputs. `OOT_PYTHON` and
`OOT_PYTHON_BIN` select the existing uv environment. Resolve these explicitly
before using a historical command. These names are documentation placeholders,
not new game feature flags. Never point writable outputs at protected inputs.

Current delivery: [flags](FLAGS.md), [play build](PLAY-BUILD.md),
[verification](VERIFICATION.md), [next merges](NEXT-MERGES.md) and
[storage](STORAGE.md). All requested finished branches and reviewed replacements
are integrated; no finished branch remains pending.

# APM Codex Sound Pack Design

## Goal

Make the GUPPI CESP/OpenPeon sound pack installable with Microsoft APM and play
GUPPI sounds for OpenAI Codex lifecycle events on macOS, without requiring a
separate PeonPing installation.

## Constraints

- Preserve `openpeon.json`, `sounds/`, and `icons/` as the canonical CESP pack.
- Target macOS playback only for the first release, using the built-in `afplay`.
- Do not add network activity, notifications, or external runtime dependencies.
- Keep hook work asynchronous so Codex is not delayed by audio playback.
- Use the APM `codex` target; `~/.agents/` alone is insufficient because it
  deploys skills, not lifecycle hooks.

## Architecture

The repository becomes an APM package through `apm.yml` and an `.apm/hooks/`
hook descriptor. APM merges the descriptor into Codex's hook configuration and
copies the hook runtime into its managed hook directory. The CESP assets remain
in APM's managed package store (`apm_modules/` for project scope and
`~/.apm/apm_modules/` for global scope); the runtime locates that store before
selecting a sound. It reads Codex hook JSON on stdin, maps the event to a CESP
category, and launches `afplay` in the background.

The initial event mapping is:

| Codex event | CESP category |
| --- | --- |
| `SessionStart` | `session.start` |
| `UserPromptSubmit` | `task.acknowledge` |
| `PermissionRequest` | `input.required` |
| `PreCompact` | `resource.limit` |
| `Stop` | `task.complete` |

Unknown, malformed, and intentionally noisy events are silent. A process-wide
environment flag can disable acknowledgement sounds by default, avoiding an
audio cue for every prompt unless the user explicitly enables it.

## Distribution

Consumers install the package with:

```bash
apm install lirantal/agent-plugin-guppi-sound-pack --target codex --global
```

For reproducibility, documentation recommends a semver tag once released. APM
owns deployed files; users must not hand-edit generated Codex hook files.

## Verification

Tests cover the event mapping, CESP manifest loading, event-specific sound
selection, disabled acknowledgement behavior, malformed input, and absent
playback support. An integration test invokes APM against a scratch project and
checks that the generated Codex hook configuration and copied asset bundle are
usable.

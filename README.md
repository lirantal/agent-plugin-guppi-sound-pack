# GUPPI Sound Pack for Codex

GUPPI is a CESP/OpenPeon sound pack inspired by the AI from the Bobiverse
novels. Install it with [Microsoft APM](https://github.com/microsoft/apm) to
hear GUPPI when Codex starts, needs permission, compacts context, or completes
work.

<img align="right" src="./icons/guppi.png" width="128" height="128" alt="GUPPI" />

## Requirements

- macOS
- [APM](https://github.com/microsoft/apm) installed and on your `PATH`
- Codex with local lifecycle hooks enabled

## Install

Run this once from any directory:

```bash
apm install lirantal/agent-plugin-guppi-sound-pack --target codex --global
```

### Trust the hooks (required)

Codex does not run non-managed command hooks until you review and trust them.
Open the Hooks UI in the Codex app, review the installed commands, and choose
**Trust all and continue**. You can do the same from the Codex CLI:

```bash
codex
```

Then run `/hooks`, review the commands, and select **Trust all and continue**.
Codex records trust for the current hook definitions, so review and trust them
again after an update if Codex marks them as changed.

Then fully quit and reopen the Codex/ChatGPT desktop app and start a new task.

## What happens

APM registers a small hook under `~/.codex/` and stores the sound pack under
`~/.apm/apm_modules/`. Use Codex normally; the hook plays a random matching
GUPPI line for these events:

| Codex event | Sound category |
| --- | --- |
| Session start | `session.start` |
| Permission request | `input.required` |
| Context compaction | `resource.limit` |
| Task complete | `task.complete` |

Prompt acknowledgements are silent by default. For Codex CLI, enable them with:

```bash
GUPPI_ACKNOWLEDGE=1 codex
```

## Update

```bash
apm update --global --target codex --yes
```

If you do not hear sounds, reopen Codex and confirm the hook is trusted. Let
APM manage `~/.codex/` and `~/.apm/`; do not move or edit its generated files.

## Notes

- This is a macOS-first APM/Codex hook package, not a Codex marketplace UI
  plugin.
- Install from this Git repository. Current APM archive packing does not retain
  the root CESP audio assets this package needs.
- The original CESP/OpenPeon manifest and sounds remain compatible with tools
  such as [PeonPing](https://github.com/PeonPing/peon-ping).

## License

GUPPI quotes are copyright Dennis E. Taylor and used here under fair use. This
sound pack is licensed [CC-BY-NC-4.0](LICENSE). The GUPPI image is
[CC-BY-SA](https://bobiverse.fandom.com/wiki/GUPPI) by Michael Wheatland.

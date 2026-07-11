# GUPPI Sound Pack

<img align="right" src="./icons/guppi.png" width=128 height=128 style="padding: 6px" /> This is a [peon-ping](https://github.com/PeonPing/peon-ping) sound pack based
on GUPPI, the fictional computer from the [Bobiverse](https://bobiverse.fandom.com/wiki/Bobiverse_Wiki) novels, cloned via the [Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS)
model. The quotes are direct quotes by GUPPI from the book series, but the voices
are all generated with AI.

GUPPI ("General Unit Primary Peripheral Interface") is a piece of software
designed by FAITH's Project HEAVEN to serve as an interface between a replicant
and the machine systems to which they are connected. [1](https://bobiverse.fandom.com/wiki/GUPPI).

Now GUPPI can support you while coding in Claude, Codex and many other tools.

## Install for Codex with APM (macOS)

This repository is an [APM](https://github.com/microsoft/apm) package for Codex.
It installs a lightweight Codex lifecycle hook and uses macOS's built-in
`afplay` command to play GUPPI sounds without delaying the agent.

```bash
apm install lirantal/agent-plugin-guppi-sound-pack --target codex --global
```

APM writes the generated Codex hook configuration under `~/.codex/` and keeps
the pack assets in `~/.apm/apm_modules/`. Do not move or hand-edit either
location; rerun APM to update or repair the installation.

The hook maps these Codex lifecycle events to CESP categories:

| Codex event | GUPPI category |
| --- | --- |
| Session start | `session.start` |
| Permission request | `input.required` |
| Context compaction | `resource.limit` |
| Agent turn complete | `task.complete` |

Task acknowledgements are intentionally silent by default. To enable them for
the Codex CLI, launch it with `GUPPI_ACKNOWLEDGE=1 codex`.

After installation, start a new Codex task and review/trust the new hook if
Codex prompts you. The same `~/.codex` configuration is the integration point
for Codex desktop environments that support local lifecycle hooks.

### Update and remove

Update the global dependency and redeploy its Codex hook with:

```bash
apm update --global --target codex --yes
```

To remove it, use APM's dependency-management commands rather than deleting
generated files manually.

### Scope

The initial APM integration targets macOS only. The CESP/OpenPeon manifest and
sound assets remain usable by other compatible tools, including PeonPing.

Install directly from this Git repository. Current APM archive packing does not
retain the root CESP data assets required by this hook runtime.

## License

GUPPI quotes are copyright Dennis E. Taylor used here under fair use. This sound
pack is licensed [CC-BY-NC-4.0](LICENSE). The GUPPI image is [CC-BY-SA](https://bobiverse.fandom.com/wiki/GUPPI) Michael Wheatland.

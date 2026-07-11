# APM Codex Sound Pack Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish the GUPPI CESP assets as a self-contained APM package that plays macOS sounds for Codex lifecycle events.

**Architecture:** An APM hook descriptor invokes a Python runtime in `.apm/hooks/`. APM deploys the runtime to Codex's hook directory while retaining the CESP assets in its package store; the runtime resolves that store from the workspace or global APM home before asynchronously starting `afplay`.

**Tech Stack:** Microsoft APM CLI, Codex hook JSON, Python 3 standard library, macOS `afplay`, `unittest`.

## Global Constraints

- Preserve `openpeon.json`, `sounds/`, and `icons/` as canonical CESP assets.
- Target `codex` and macOS only; do not add Windows or Linux playback support.
- Do not add network calls or third-party Python dependencies.
- Hooks must return quickly and never block Codex waiting for a sound.
- `task.acknowledge` is opt-in through `GUPPI_ACKNOWLEDGE=1`; all other mapped categories are enabled by default.

---

### Task 1: Define the event-routing contract

**Files:**
- Create: `tests/test_guppi_player.py`
- Create: `.apm/hooks/guppi_player.py`

**Interfaces:**
- Produces `event_category(event_name: str) -> str | None`.
- Produces `select_sound(manifest_path: Path, category: str, acknowledge: bool) -> Path | None`.
- Produces `locate_manifest(payload: Mapping[str, object]) -> Path | None`.

- [ ] **Step 1: Write the failing routing tests**

```python
class EventCategoryTests(unittest.TestCase):
    def test_maps_supported_codex_events(self):
        self.assertEqual(event_category("SessionStart"), "session.start")
        self.assertEqual(event_category("PermissionRequest"), "input.required")
        self.assertEqual(event_category("PreCompact"), "resource.limit")
        self.assertEqual(event_category("Stop"), "task.complete")

    def test_unknown_event_is_silent(self):
        self.assertIsNone(event_category("PostToolUse"))
```

- [ ] **Step 2: Run the routing tests and verify they fail**

Run: `python3 -m unittest tests.test_guppi_player.EventCategoryTests -v`

Expected: FAIL because `guppi_player` does not exist.

- [ ] **Step 3: Implement the minimal event-routing API**

```python
EVENT_CATEGORIES = {
    "SessionStart": "session.start",
    "UserPromptSubmit": "task.acknowledge",
    "PermissionRequest": "input.required",
    "PreCompact": "resource.limit",
    "Stop": "task.complete",
}

def event_category(event_name: str) -> str | None:
    return EVENT_CATEGORIES.get(event_name)
```

- [ ] **Step 4: Run the routing tests and verify they pass**

Run: `python3 -m unittest tests.test_guppi_player.EventCategoryTests -v`

Expected: PASS.

- [ ] **Step 5: Add and verify sound-selection tests**

```python
def test_selects_a_manifest_sound(self):
    sound = select_sound(ROOT / "openpeon.json", "task.complete", acknowledge=False)
    self.assertTrue(sound.is_file())
    self.assertEqual(sound.suffix, ".wav")

def test_acknowledgement_is_disabled_without_opt_in(self):
    self.assertIsNone(select_sound(ROOT / "openpeon.json", "task.acknowledge", acknowledge=False))
```

Run: `python3 -m unittest tests.test_guppi_player.SoundSelectionTests -v`

Expected before implementation: FAIL because `select_sound` is missing.

- [ ] **Step 6: Implement manifest validation and selection**

```python
def select_sound(manifest_path: Path, category: str, acknowledge: bool) -> Path | None:
    if category == "task.acknowledge" and not acknowledge:
        return None
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    sounds = manifest.get("categories", {}).get(category, {}).get("sounds", [])
    existing = [manifest_path.parent / item["file"] for item in sounds if isinstance(item, dict)]
    existing = [path for path in existing if path.is_file()]
    return random.choice(existing) if existing else None
```

- [ ] **Step 7: Run the complete task test file**

Run: `python3 -m unittest tests.test_guppi_player -v`

Expected: PASS.

### Task 2: Add non-blocking macOS playback

**Files:**
- Modify: `.apm/hooks/guppi_player.py`
- Modify: `tests/test_guppi_player.py`

**Interfaces:**
- Produces `play_sound(sound_path: Path, runner: Callable[..., object]) -> None`.
- Produces `main(stdin: TextIO, environ: Mapping[str, str], runner: Callable[..., object]) -> int`.

- [ ] **Step 1: Write failing playback and stdin tests**

```python
def test_main_plays_stop_event_asynchronously(self):
    calls = []
    result = main(io.StringIO('{"hook_event_name":"Stop"}'), {}, lambda *args, **kwargs: calls.append((args, kwargs)))
    self.assertEqual(result, 0)
    self.assertEqual(calls[0][0][0][0], "afplay")
    self.assertTrue(calls[0][1]["start_new_session"])

def test_main_ignores_malformed_input(self):
    self.assertEqual(main(io.StringIO("not json"), {}, subprocess.Popen), 0)
```

- [ ] **Step 2: Run the new tests and verify they fail**

Run: `python3 -m unittest tests.test_guppi_player.PlaybackTests -v`

Expected: FAIL because `main` does not exist.

- [ ] **Step 3: Implement non-blocking playback**

```python
def play_sound(sound_path: Path, runner: Callable[..., object]) -> None:
    runner(["afplay", str(sound_path)], stdin=subprocess.DEVNULL,
           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
           start_new_session=True)
```

`main` must parse stdin JSON, look up `hook_event_name`, evaluate
`GUPPI_ACKNOWLEDGE == "1"`, choose a sound, call `play_sound`, and return `0`
for every invalid or unsupported input case.

- [ ] **Step 4: Run all runtime tests**

Run: `python3 -m unittest tests.test_guppi_player -v`

Expected: PASS.

### Task 3: Package and install through APM

**Files:**
- Create: `apm.yml`
- Create: `.apm/hooks/guppi-hooks.json`
- Create: `tests/test_apm_install.py`
- Modify: `Readme.md`
- Modify: `.gitignore`

**Interfaces:**
- `apm.yml` declares package name `guppi-sound-pack`, version `1.1.0`, `targets: [codex]`, and `includes: auto`.
- `.apm/hooks/guppi-hooks.json` registers the five supported Codex event names and invokes `./guppi_player.py` with Python 3.

- [ ] **Step 1: Write a failing isolated-install test**

```python
def test_apm_deploys_codex_hooks_and_pack_assets(self):
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        (root / ".codex").mkdir()
        result = subprocess.run([
            "apm", "install", str(REPO_ROOT), "--target", "codex", "--root", str(root)
        ], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        hooks = json.loads((root / ".codex/hooks.json").read_text())
        self.assertIn("Stop", hooks["hooks"])
        self.assertTrue(any((root / ".codex/hooks").rglob("openpeon.json")))
```

- [ ] **Step 2: Run the integration test and verify it fails**

Run: `python3 -m unittest tests.test_apm_install -v`

Expected: FAIL because `apm.yml` and the hook descriptor do not exist.

- [ ] **Step 3: Add APM manifest and Codex hook descriptor**

`apm.yml` contains package metadata, the `codex` target, `includes: auto`, and
an explicit empty `dependencies.apm` list. The hook descriptor has one command
hook per supported event and invokes `python3 ./guppi_player.py`.

- [ ] **Step 4: Run the integration test and inspect generated paths**

Run: `python3 -m unittest tests.test_apm_install -v`

Expected: PASS, with `hooks.json` and `guppi_player.py` under the scratch
`.codex/` deployment root, and `openpeon.json` plus WAV assets under its APM
package store.

- [ ] **Step 5: Document installation and lifecycle behavior**

Add README sections for the global install command, Codex hook trust/restart
expectation, update command, acknowledgement opt-in, macOS-only scope, and
the fact that APM owns generated `.codex` files.

- [ ] **Step 6: Add generated APM directories to `.gitignore`**

Ignore `apm_modules/`, `apm.lock.yaml`, `.codex/`, and `.agents/` while keeping
the source `.apm/` directory tracked.

- [ ] **Step 7: Run complete verification**

Run: `python3 -m unittest discover -s tests -v && apm audit`

Expected: all unit/integration tests pass and APM reports no blocking package
validation errors.

- [ ] **Step 8: Commit**

```bash
git add apm.yml .apm tests Readme.md .gitignore docs/superpowers
git commit -m "feat: package GUPPI sounds for APM Codex hooks"
```

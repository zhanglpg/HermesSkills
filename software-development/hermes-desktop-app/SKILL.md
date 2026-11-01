---
name: hermes-desktop-app
description: Use when installing or updating the Hermes desktop app.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos, linux, windows]
metadata:
  hermes:
    tags: [desktop, electron, install, update, verification]
    category: software-development
    related_skills: [inspecting-hermes-desktop-dom, hermes-desktop-plugins]
---

# Hermes Desktop App: install, rebuild, update

Lifecycle for the desktop application on a machine whose agent came from a
source checkout (`~/.hermes/hermes-agent`). It shares config, API keys,
sessions, skills and memory with the CLI — it is never a second install, so
don't set anything up twice.

## When to Use

- Installing or repairing the desktop app on a machine that already runs the CLI.
- After `hermes update` touched the app, or the Dock icon seems to run old code.
- Answering "does Hermes update itself?" / "why did nothing auto-update?".

## Which update owner you have

The **running install** decides, not the data home: a source checkout updates
through `hermes update`, and a desktop built from that checkout hands off to
it. A bundled macOS/Windows package instead updates through its in-app control
via electron-updater. `hermes doctor` reports provenance; the docs page
`getting-started/updating` is authoritative on the full matrix.

## Install / rebuild

```bash
hermes desktop --build-only   # npm install + electron packaging, no launch
hermes desktop --skip-build   # relaunch the built artifact
hermes desktop                # build if needed, then launch
```

- The artifact lands in `apps/desktop/release/<arch>/<Product>.app`. Warm
  builds take a couple of minutes; a cold one downloads Electron and takes
  much longer. Run it in the background with a completion notification — that
  is a long build, not a hung command.
- With no Developer ID in the environment the build ad-hoc signs using a stable
  identity and says so; that identity is what keeps TCC grants alive across
  rebuilds. Use `--setup-tcc-identity` when grants keep resetting.
- A source build self-reports version `0.0.0`. That is a build-stamp artifact,
  not a broken build — `hermes --version` from the CLI is the real version.

## Putting it in /Applications

Symlink the release bundle instead of copying it:
`ln -s <release>/<arch>/<Product>.app /Applications/<Product>.app`. The link
follows every rebuild, so there is one copy of the code and no second bundled
runtime.

Expect `hermes update` to take that path over: it rebuilds the bundle and
copies it over `/Applications/<Product>.app` with `ditto`, signature intact,
so the symlink may become a real copy. That is the updater syncing the Dock and
Spotlight entry — expected, not breakage. It skips the copy while the app is
running and tells the user to quit and rerun. Never `rm -rf` a stale copy to
"clear" it: destructive writes under /Applications trip the command gate, and
the updater already handles replacement.

## Verify a launch without a screenshot

Screen capture is frequently unavailable (no Screen Recording grant), so prove
the boot from the app's own log — `~/.hermes/logs/desktop.log`. These are four
independent landmarks:

```
[backend] using Hermes at <path>            # local runtime resolved
[boot] Hermes gateway is ready              # backend bound
[gateway-route win=main] ... conn=local     # window created and routed
[bot-roster win=main] snapshot active=...   # UI populated
```

`using Hermes at <path>` is what separates a working local backend from the
connect/install screen. Add `pgrep -fl "Contents/MacOS/<Product>"` for the
renderer and GPU children, and `lsappinfo find bundleid=<bundle-id>` for the
Launch Services record. Report that evidence and say the screenshot was
unavailable — never imply the app failed to launch.

## What updates itself, and what does not

- **Core: nothing.** `updates.check` (default `true`) is a passive version and
  banner notice only. `hermes update --check` and `hermes update --plan` are
  the read-only queries; neither installs anything.
- **Plugins:** `plugins.auto_update_check_hours` (default 24) runs a background
  *check* in the gateway and surfaces an Update button. Nothing changes until
  the update is accepted.
- **`hermes update`** is the real thing: quick state snapshot → gateways paused
  and restarted on the new code → PM dependency sync → desktop rebuild and copy
  → config migration. Budget a gateway-offline window.
- **Unattended is supported but must be scheduled:** `hermes update -y` from a
  cronjob. The updater explicitly handles running inside the gateway's own
  process tree (a cron session's ancestor gateway) and asks for a self-restart
  instead of deadlocking, so this is a supported pattern rather than a hack.
  Pick a quiet hour and expect the desktop rebuild to be skipped while the app
  is open.

## Pitfalls

- `hermes update --check` printing `stable vX.Y.Z; this checkout is newer and
  waits for the next release` means "nothing to do", not an error. Do not
  reach for a reinstall.
- Do not put the packaged DMG over a machine that already has a source
  install: it adds a second bundled Python runtime and a second update owner.
  Offer it only when the signed/notarized build is specifically wanted.
- The update channel is stored per install (`update.installs` in
  `config.yaml`). `--channel` is a one-run override, `--set-channel` persists;
  a checkout that never chose a channel only moves forward.

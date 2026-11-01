---
name: macos-hardware-inspection
description: Use when probing a Mac's displays, USB, and audio I/O.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [macos, hardware, display, usb, audio, system-profiler]
    category: apple
    related_skills: [macos-computer-use]
---

# macOS Hardware Inspection

Answer "what display is this / what is plugged into it / why is there no
microphone" from the OS itself. Every probe here is read-only and needs no
installs — never guess a model number from a marketing name when the EDID
and the USB plane will tell you exactly what the machine sees.

## When to Use

- "What monitor is this / what model did I buy?" — identify it from EDID
  rather than from the name macOS puts in Displays.
- "Can I plug X into this monitor?" (mic, headset, hub, dock) — decide it from
  the jack and port spec plus what the monitor's own hub enumerates.
- "Why is there no microphone / no audio input?" — count CoreAudio streams
  before blaming a device.
- Any question whose answer must be what the machine actually has, not what the
  product box claims.

## Procedure

1. **Identify the display.** `system_profiler SPDisplaysDataType -json` carries
   what the EDID does. Fields that matter per display:
   `_name`, `_spdisplays_display-vendor-id`, `_spdisplays_display-product-id`,
   `_spdisplays_display-week/-year`, `_spdisplays_pixels` (panel resolution),
   `spdisplays_resolution` (the HiDPI mode actually driving it), and
   `spdisplays_pixelresolution` (a hint at the panel class, e.g. `5k-uhgplus`).
2. **Decode the vendor id** to the EDID PNP id: three 5-bit letters, MSB first
   (`0x1e6d` → GSM = LG Display). The product id does *not* name the model by
   itself — constrain with panel resolution × inch class (218 PPI at
   5120×2880 is a 27"), the branding string, and the build year, then confirm
   on the vendor's spec page. **The port list on that page is usually the real
   answer** to the question being asked.
3. **Map peripherals to the display.** `ioreg -p IOUSB -w0` prints the IOUSB
   plane as a tree. A monitor's internal hub shows as a `USB2.1 Hub` /
   `USB3.x Hub` node with brand-named children (`<Brand> Monitor Controls`,
   `<Brand> Monitor Headset MIC`). Their presence proves the display's
   upstream USB data path is live — which is what decides whether a peripheral
   plugged into the monitor reaches the Mac.
4. **Enumerate real audio capability.** Run `scripts/audio_io_devices.py`. It
   prints every CoreAudio device with its input/output stream counts. Zero
   devices with `in>0` means this Mac cannot capture audio at all right now,
   regardless of what hardware appears to be attached.

## Pitfalls

- **`ioreg -l | grep IODisplayEDID` is the obvious EDID route and on current
  macOS it commonly returns nothing.** Use the `system_profiler -json` form —
  it still reports vendor id, product id, week/year, and pixel dimensions.
  Don't conclude EDID is unreadable.
- **`system_profiler SPUSBDataType` can print an empty list, valid-looking
  empty JSON included, while USB devices are plainly enumerated.** Cross-check
  with `ioreg -p IOUSB -w0`; devices in the IOUSB plane mean the SPUSB report
  is not evidence of absence.
- **"Process running" is not "window exists".** `pgrep` proves the process;
  app-enumeration APIs can report `windows: []` for every app on the machine.
  Use `lsappinfo find bundleid=<id>` plus the application's own log line for
  window-level proof.
- **Never infer "no microphone" from an output-only listing.** Count input
  streams. A monitor exposing a `… Headset MIC` USB device still produces no
  recording device until something is plugged into its 4-pole jack — the jack
  detection gates the ADC, so the device enumerates with zero input streams.
- **Desktop Macs may have no built-in microphone at all** (Mac mini ships with
  a speaker). Enumerate before asserting the machine can capture audio.
- **Answer a "can I add a mic to this monitor" question from the jack spec,
  not the product name.** `Headphone out: 4-pole (Sound+Mic)` means a
  TRRS/CTIA headset carries mic in on that one connector; a `Mic In` row
  reading `-` means there is no other mic input. Three-pole stereo headphones
  give audio out only.
- **Quote derived facts, not symptoms.** "A 4-pole jack plus a `Headset MIC`
  device on its internal hub" is verifiable; "it says it supports a mic" is
  not.

## Scripts

- `scripts/audio_io_devices.py` — CoreAudio device list with per-device
  input/output stream counts (ctypes, no dependencies, macOS-only).
- `scripts/usb_tree.py` — compact IOUSB plane tree with vendor/product ids and
  product names.

## Reporting

Lead with the answer to the question asked (yes/no, then the mechanism), then
what the OS evidence was. Distinguish what is verifiable now from what needs
the user to plug something in and re-check.

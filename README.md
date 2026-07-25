# Rufus for Linux (Native Port)

A native Linux port of Rufus: same look and feel as the Windows app, built with
Python/CustomTkinter, backed by native Linux tools (`dd`, `mkfs.*`, `lsblk`).

## Features
- **Exact UI Replica**: Looks and feels like Rufus 4.4 on Windows.
- **Native Backend**: Uses `dd` for image writing and `mkfs.vfat` / `mkfs.ntfs` / `mkfs.ext4` for formatting.
- **No Terminal Needed**: Launches via a desktop icon with a graphical (`pkexec`) password prompt.
- **Automated Builds**: GitHub Actions builds a `.deb` on every push and release (see `.github/workflows/build-deb.yml`).

## Installation
1. Download the latest `rufus-linux_4.4-1_amd64.deb` from the repo's **Actions** tab (as a build artifact) or from a **Release**.
2. Install it:
   ```bash
   sudo apt install ./rufus-linux_4.4-1_amd64.deb
   ```
3. Launch **"Rufus 4.4 Linux"** from your application menu, or run `/opt/rufus-linux/rufus_launcher.sh`.

`customtkinter` isn't packaged for apt, so the package's `postinst` script installs it
automatically via `pip3 install --break-system-packages customtkinter` the first time you
install the `.deb`. If that fails (e.g. no network at install time), run it manually:
```bash
pip3 install --break-system-packages customtkinter
```

## Repository layout
```
src/rufus_linux.py                 # the application itself
linux-packaging/rufus_launcher.sh  # pkexec launcher (preserves DISPLAY/XAUTHORITY)
linux-packaging/rufus.desktop      # application menu entry
debian/                            # packaging metadata (control, rules, install, changelog, postinst)
.github/workflows/build-deb.yml    # CI: builds and uploads the .deb
```

## Building from source
```bash
# Run directly (needs root for real disk operations, and customtkinter installed):
pip3 install --break-system-packages customtkinter
sudo python3 src/rufus_linux.py

# Build the .deb yourself:
sudo apt install debhelper devscripts build-essential
dpkg-buildpackage -us -uc -b
# -> ../rufus-linux_4.4-1_amd64.deb
```

## What was fixed in this pass
- `debian/` packaging was incomplete (missing `changelog`, `debhelper-compat`,
  `source/format`) so `dpkg-buildpackage` couldn't run at all — added all of it,
  and verified a clean local build.
- Installed scripts weren't guaranteed to be executable inside the `.deb`; added a
  `dh_fixperms` override in `debian/rules` that explicitly `chmod 0755`s both scripts.
- `customtkinter` isn't an apt package, so a fresh `apt install` would crash on
  first launch with `ModuleNotFoundError`; added a `postinst` step that installs it via pip.
- The launcher used `pkexec <script>` directly, which drops `DISPLAY`/`XAUTHORITY`
  on some systems and leaves the Tk window unable to open as root; it now runs
  `pkexec env DISPLAY=... XAUTHORITY=... python3 <script>` explicitly.
- Error dialogs from `dd`/`mkfs` failures showed only the generic Python exception
  text instead of the actual `stderr` from the failing command; now captured and shown.
- Device refresh could keep a stale/removed device selected after a rescan, and
  didn't handle "no devices found" gracefully; both fixed.
- Added `.github/workflows/build-deb.yml`, which was referenced in this README but
  didn't exist — it now builds on every push/PR, lints with `lintian`, uploads the
  `.deb` as a workflow artifact, and attaches it to GitHub Releases automatically.

## Safety note
This tool runs `dd` and `mkfs` directly against block devices you select — it
**will destroy all data** on the chosen device. The app already asks for
confirmation before doing so; double-check the device path before continuing.

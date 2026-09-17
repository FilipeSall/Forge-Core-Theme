# Forge Core browser icons and launcher watcher

## Context

The Snap Firefox launcher is `firefox_firefox.desktop` and declares an absolute
`Icon=/snap/firefox/current/default256.png`. An icon theme cannot override an
absolute path. GLib/GIO does, however, give the user application directory
precedence over the system application directories when the desktop ID is the
same. Therefore the correct override is a user-local copy with the same basename
and `Icon=firefox`; a different basename would create a duplicate application.

The current session already resolves Firefox through
`~/.local/share/applications/firefox_firefox.desktop`, and GTK resolves the
Forge-Core PNG. The remaining stale App Grid result is GNOME Shell retaining its
in-process app/icon state when the icon-theme setting is written to the value it
already has. A real theme transition (`Yaru -> Forge-Core`) is needed to notify
the shell.

## Design

### Launcher discovery and overrides

`scripts/browser_icons.py` remains the single source of truth for launcher
discovery, patching, state, and restore. It derives the application roots from
`XDG_DATA_HOME` and `XDG_DATA_DIRS`, then adds the standard system/user Flatpak
export roots. It identifies Firefox, Brave, and Safari from the primary
`[Desktop Entry]` group, exact normalized browser tokens, and package metadata;
localized/action groups and unrelated launchers are ignored.

Only entries whose main `Icon=` value is absolute are copied or patched. The
target is always `~/.local/share/applications/<same-basename>.desktop`, so GIO
resolves the override instead of the system launcher. Relative icon names are
left untouched and are covered by Forge-Core manifest aliases.

Before changing an existing user-local launcher, the exact regular file is backed
up in the Forge-Core state directory. Symlink launchers are rejected rather than
followed. Newly created overrides are recorded separately. Restore removes only
files still carrying the Forge-Core marker and matching the managed hash, and
restores backups on uninstall; modified files are preserved with a warning. No
file under `/usr/share` or `/var/lib/snapd` is edited.

Apply and restore take an inter-process lock shared with the watcher. A prepared
state record is atomically written before each launcher mutation, and launcher,
backup, and state writes use temporary files plus `os.replace`/`fsync` where
applicable. This prevents a concurrent watcher or an interruption from losing
the information required to restore the original file.

The manifest keeps the canonical icon names `firefox`, `brave`, and `safari`,
plus known APT/Snap/Flatpak aliases (`firefox_firefox`, `org.mozilla.firefox`,
`org.mozilla.Firefox`, `brave-browser`, `brave_brave`, `com.brave.Browser`,
`com.apple.Safari`, and `safari-browser`). Aliases are theme assets only; they do
not create desktop entries.

### Future-install watcher

The installer copies the watcher and its library into the Forge-Core state
directory, then writes a user service named
`forge-core-browser-icons.service` to `~/.config/systemd/user` and enables it
with `systemctl --user`. The service runs a dependency-free Python watcher.
Every two seconds it snapshots `*.desktop` files in all supported application
roots. A changed snapshot triggers the idempotent browser apply operation, which
means a newly installed APT, Snap, or Flatpak browser is handled without a
manual command.

On every reconciliation, an override created by Forge Core is removed when its
last non-user launcher disappears. A user-modified override is preserved and
reported instead. The installer refuses to overwrite an existing unit with the
same name unless it contains the Forge-Core marker.

The watcher does not create entries for absent browsers. It only writes an
override after finding a real launcher with an absolute icon. If Forge-Core is
the active theme and an override changed, the watcher briefly selects the
fallback theme and selects Forge-Core again. This emits the GNOME setting change
that refreshes the App Grid, dock, and menus. If another icon theme is active,
the watcher does not force Forge-Core on the user. The refresh re-reads the
setting after each transition and stops without a second write if the user
changes the theme or a `gsettings` operation fails.

If `systemctl --user` is unavailable, installation still applies existing
launchers and reports that future-install watching could not be enabled. The
watcher is stopped, disabled, and removed by uninstall. Existing launcher
backups are restored before the state directory is cleaned. The uninstall never
removes a pre-existing unit with the same name if it lacks the Forge-Core marker.

### Cache and validation

Installation regenerates the user icon cache when `gtk-update-icon-cache` is
available, refreshes the user desktop database, and performs a real theme
transition when needed. Validation uses:

- `Gio.DesktopAppInfo` to report the resolved desktop filename and `Icon=`;
- GTK3 and GTK4 `Gtk.IconTheme.has_icon()` plus lookup, file-path, and
  Forge-Core-prefix checks for canonical names and aliases;
- image metadata and visual inspection of the generated 128x128 Firefox PNG;
- watcher behavior with synthetic desktop entries in a temporary application
  root, including add/update/remove, symlink rejection, and adversarial names,
  proving no phantom entries are created;
- build, install, active-theme `gsettings`, uninstall/restore, and `git diff
  --check`.

## Error handling and safety

- All scripts run as the normal user and reject root execution.
- Missing application roots are skipped; missing watcher support is non-fatal for
  the base theme installation.
- Prepared state is written before each launcher mutation; the final managed
  hash is written after the atomic patch. This ordering is intentional so an
  interruption leaves enough information for restore.
- The watcher handles malformed or unreadable desktop files by skipping them.
- Existing unrelated worktree changes, especially wallpaper assets, are not
  touched by build/install/uninstall changes.

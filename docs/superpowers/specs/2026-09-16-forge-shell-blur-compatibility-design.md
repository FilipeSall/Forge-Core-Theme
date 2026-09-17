# Forge Shell blur compatibility

## Problem

On GNOME Shell 46, `forge-core-shell@forgecore.local` fails during `enable()`
because `Shell.BlurEffect` does not expose a `sigma` property. The installed
GNOME Shell GIR exposes `radius` (integer), `brightness` (float), and `mode`.

## Design

Preserve `Shell.BlurMode.BACKGROUND` and brightness `0.72`, and configure the
GNOME 46 blur with radius `22`. Rename the blur constant from `SIGMA` to
`RADIUS` and pass it as the `radius` constructor property. Apply the identical
change to the source tree and installed extension copy so that the running
installation and future installs remain consistent.

## Verification

1. Extract the writable `BlurEffect` properties with `xmllint` from
   `/usr/share/gnome-shell/Shell-14.gir`; the expected names are `brightness`,
   `mode`, and `radius`, with no `sigma`.
2. Before the change, a source check for `sigma:` fails compatibility. After
   the change, both source and installed copies must use `radius:` and contain
   no `sigma:` property.
3. Record a timestamp, disable and enable the extension, then verify that
   `gnome-extensions info forge-core-shell@forgecore.local` reports `ACTIVE`
   and that the journal since that timestamp contains no error attributed to
   `forge-core-shell@forgecore.local`.
4. Open Quick Settings and the date/calendar menu and visually confirm that
   both actors have the Forge background blur. This final visual assertion is
   manual because GNOME Shell does not expose effect instances through the
   extension CLI.

## Scope

No stylesheet, theme token, package, or unrelated extension behavior changes.

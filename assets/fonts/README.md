# Forge Core font assets

Font binaries are intentionally excluded from this repository. `scripts/install-fonts.sh`
downloads IBM Plex Sans from IBM Plex releases and Oxanium from the official Google
Fonts repository. JetBrains Mono is validated from the installed distribution package
or downloaded from JetBrains only when absent.

All three families are under the SIL Open Font License 1.1. See their upstream
repositories for the full license text. Keeping binaries out of the repository makes
the source tree small and ensures installs use the declared official upstreams.

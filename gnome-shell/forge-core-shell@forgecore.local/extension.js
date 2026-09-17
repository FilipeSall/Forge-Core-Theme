import Shell from 'gi://Shell';
import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import GObject from 'gi://GObject';
import St from 'gi://St';
import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import * as QuickSettings from 'resource:///org/gnome/shell/ui/quickSettings.js';

const EFFECT_NAME = 'forge-core-glass';
const INTERFACE_SCHEMA = 'org.gnome.desktop.interface';
const BACKGROUND_SCHEMA = 'org.gnome.desktop.background';
const FORGE_ICON_THEME = 'Forge-Core';
const YARU_ICON_THEME = 'Yaru';
const FORGE_CURSOR_THEME = 'Forge-Core-Cursor';
const YARU_CURSOR_THEME = 'Yaru';
const FORGE_GTK_THEME = 'Yaru-dark';
const FORGE_COLOR_SCHEME = 'prefer-dark';
const THEME_MODE_FILE = GLib.build_filenamev([
    GLib.get_user_data_dir(), 'forge-core', 'icon-theme-mode',
]);
const GTK_CSS_DIR = GLib.build_filenamev([GLib.get_user_config_dir(), 'gtk-3.0']);
const GTK_CSS_FILE = GLib.build_filenamev([GTK_CSS_DIR, 'gtk.css']);
const GTK_OVERLAY_FILE = GLib.build_filenamev([
    GTK_CSS_DIR, 'forge-core-desktop-menu.css',
]);
const GTK_OVERLAY_BEGIN = '/* forge-core:begin */';
const GTK_OVERLAY_END = '/* forge-core:end */';
const WALLPAPER_AUTOSTART_FILE = GLib.build_filenamev([
    GLib.get_user_config_dir(), 'autostart', 'forge-core-wallpaper-rotator.desktop',
]);
const WALLPAPER_STATE_FILE = GLib.build_filenamev([
    GLib.get_user_cache_dir(), 'forge-core-wallpaper', 'theme-state.json',
]);
const WALLPAPER_ROTATION_STATE_FILE = GLib.build_filenamev([
    GLib.get_user_cache_dir(), 'forge-core-wallpaper', 'state.json',
]);
const APPEARANCE_STATE_FILE = GLib.build_filenamev([
    GLib.get_user_data_dir(), 'forge-core', 'appearance-state.json',
]);
const USER_SYSTEMD_DIR = GLib.build_filenamev([
    GLib.get_user_config_dir(), 'systemd', 'user',
]);
const BROWSER_WATCHER_UNIT = 'forge-core-browser-icons.service';
const FOLDER_CHOOSER_TIMER = 'forge-core-folder-chooser-icons.timer';
const FOLDER_CHOOSER_SERVICE = 'forge-core-folder-chooser-icons.service';
const FOLDER_CHOOSER_CLEANUP_SERVICE = 'forge-core-folder-chooser-icons-cleanup.service';
const CURSOR_DEFAULT_FILE = GLib.build_filenamev([
    GLib.get_home_dir(), '.icons', 'default', 'index.theme',
]);
const CURSOR_BACKUP_FILE = GLib.build_filenamev([
    GLib.get_user_data_dir(), 'forge-core', 'backup', 'default-index.theme',
]);
const PREVIOUS_CURSOR_THEME_FILE = GLib.build_filenamev([
    GLib.get_user_data_dir(), 'forge-core', 'previous-cursor-theme',
]);
const RADIUS = 22;
const BRIGHTNESS = 0.72;
const BATTERY_CHARGING_CLASS = 'forge-core-battery-charging';
const BATTERY_PULSE_CLASS = 'forge-core-battery-charge-pulse';
const BATTERY_PULSE_INTERVAL_MS = 900;
const ATTACH_RETRY_INTERVAL_MS = 100;
const ATTACH_RETRY_LIMIT = 50;

const ForgeThemeToggle = GObject.registerClass(
class ForgeThemeToggle extends QuickSettings.QuickToggle {
    _init(onClicked) {
        super._init({
            title: 'Tema',
            subtitle: YARU_ICON_THEME,
            iconName: 'preferences-desktop-theme-symbolic',
            toggleMode: true,
        });

        this._onClicked = onClicked;
        this.connect('clicked', () => this._onClicked(this.checked));
    }
});

function readThemeMode() {
    try {
        if (!GLib.file_test(THEME_MODE_FILE, GLib.FileTest.EXISTS))
            return null;

        const [ok, contents] = GLib.file_get_contents(THEME_MODE_FILE);
        if (!ok)
            return null;

        const mode = new TextDecoder().decode(contents).trim();
        return mode === FORGE_ICON_THEME || mode === YARU_ICON_THEME
            ? mode
            : null;
    } catch (error) {
        logError(error, 'Forge Core: failed to read the theme mode');
        return null;
    }
}

function writeThemeMode(mode) {
    try {
        GLib.mkdir_with_parents(GLib.path_get_dirname(THEME_MODE_FILE), 0o755);
        GLib.file_set_contents(THEME_MODE_FILE, `${mode}\n`);
    } catch (error) {
        logError(error, 'Forge Core: failed to persist the theme mode');
    }
}

function readFile(path) {
    if (!GLib.file_test(path, GLib.FileTest.EXISTS))
        return null;

    const [ok, contents] = GLib.file_get_contents(path);
    return ok ? new TextDecoder().decode(contents) : null;
}

function writeFile(path, contents) {
    GLib.mkdir_with_parents(GLib.path_get_dirname(path), 0o755);
    GLib.file_set_contents(path, contents);
}

function removeFile(path) {
    try {
        if (GLib.file_test(path, GLib.FileTest.EXISTS))
            Gio.File.new_for_path(path).delete(null);
    } catch (error) {
        logError(error, `Forge Core: failed to remove ${path}`);
    }
}

function updateGtkOverlay(enabled) {
    try {
        if (enabled && !GLib.file_test(GTK_OVERLAY_FILE, GLib.FileTest.EXISTS))
            return;

        const current = readFile(GTK_CSS_FILE);
        if (current === null && !enabled)
            return;

        let contents = current ?? '';
        const begin = contents.indexOf(GTK_OVERLAY_BEGIN);
        const endMarker = contents.indexOf(GTK_OVERLAY_END, begin + GTK_OVERLAY_BEGIN.length);

        if (enabled) {
            const overlay = readFile(GTK_OVERLAY_FILE);
            if (overlay === null)
                return;

            const block = `${GTK_OVERLAY_BEGIN}\n${overlay.trimEnd()}\n${GTK_OVERLAY_END}`;
            if (begin >= 0 && endMarker >= 0) {
                const end = endMarker + GTK_OVERLAY_END.length;
                contents = `${contents.slice(0, begin)}${block}${contents.slice(end)}`;
            } else if (begin < 0) {
                contents = `${block}\n\n${contents}`;
            }
        } else if (begin >= 0 && endMarker >= 0) {
            let end = endMarker + GTK_OVERLAY_END.length;
            if (contents[end] === '\n')
                end++;
            contents = `${contents.slice(0, begin)}${contents.slice(end)}`;
        }

        if (contents !== current)
            writeFile(GTK_CSS_FILE, contents);
    } catch (error) {
        logError(error, 'Forge Core: failed to update the GTK overlay');
    }
}

function updateDefaultCursorTheme(theme) {
    try {
        const current = readFile(CURSOR_DEFAULT_FILE);
        if (theme === FORGE_CURSOR_THEME) {
            if (current === null || current.includes('Comment=Forge Core')) {
                writeFile(CURSOR_DEFAULT_FILE,
                    `[Icon Theme]\nName=Default\nComment=Forge Core\nInherits=${theme}\n`);
            }
            return;
        }

        const backup = readFile(CURSOR_BACKUP_FILE);
        if (backup && !backup.includes('Comment=Forge Core') &&
            !backup.includes(`Inherits=${FORGE_CURSOR_THEME}`)) {
            writeFile(CURSOR_DEFAULT_FILE, backup);
            return;
        }

        const previous = readFile(PREVIOUS_CURSOR_THEME_FILE)?.trim();
        if (current?.includes('Comment=Forge Core') ||
            current?.includes(`Inherits=${FORGE_CURSOR_THEME}`)) {
            writeFile(CURSOR_DEFAULT_FILE,
                `[Icon Theme]\nName=Default\nInherits=${previous || theme}\n`);
        }
    } catch (error) {
        logError(error, 'Forge Core: failed to update the default cursor theme');
    }
}

function spawnCommand(argv) {
    try {
        const process = Gio.Subprocess.new(argv,
            Gio.SubprocessFlags.STDOUT_SILENCE | Gio.SubprocessFlags.STDERR_SILENCE);
        process.wait_check_async(null, (source, result) => {
            try {
                source.wait_check_finish(result);
            } catch {
                // Optional Forge helpers may be absent or already stopped.
            }
        });
    } catch (error) {
        logError(error, `Forge Core: failed to run ${argv[0]}`);
    }
}

function unitInstalled(unit) {
    return GLib.file_test(
        GLib.build_filenamev([USER_SYSTEMD_DIR, unit]),
        GLib.FileTest.EXISTS);
}

function setUserUnit(unit, enabled) {
    if (!unitInstalled(unit))
        return;

    spawnCommand([
        '/usr/bin/systemctl', '--user', enabled ? 'enable' : 'disable',
        '--now', unit,
    ]);
}

function startUserUnit(unit) {
    if (!unitInstalled(unit))
        return;

    spawnCommand([
        '/usr/bin/systemctl', '--user', 'start', unit,
    ]);
}

function wallpaperCommand() {
    const desktop = readFile(WALLPAPER_AUTOSTART_FILE);
    if (!desktop)
        return null;

    const match = desktop.match(/^Exec=(\S+)/m);
    const command = match?.[1] ?? null;
    if (!command || !command.startsWith('/'))
        return null;

    return command;
}

function setWallpaperAutostart(enabled) {
    const current = readFile(WALLPAPER_AUTOSTART_FILE);
    if (current === null)
        return;

    const value = enabled ? 'true' : 'false';
    const line = `X-GNOME-Autostart-enabled=${value}`;
    const next = /^X-GNOME-Autostart-enabled=.*$/m.test(current)
        ? current.replace(/^X-GNOME-Autostart-enabled=.*$/m, line)
        : `${current.trimEnd()}\n${line}\n`;

    if (next !== current)
        writeFile(WALLPAPER_AUTOSTART_FILE, next);
}

function setWallpaperProcess(enabled) {
    const command = wallpaperCommand();
    if (!command)
        return;

    if (enabled) {
        // A previous Forge session may have rotated recently, while Yaru has
        // restored the visible background in the meantime. Force one fresh
        // render whenever Forge is explicitly activated.
        removeFile(WALLPAPER_ROTATION_STATE_FILE);
        spawnCommand([command]);
    } else {
        spawnCommand(['/usr/bin/pkill', '-TERM', '-f', command]);
    }
}

function readWallpaperState() {
    try {
        const contents = readFile(WALLPAPER_STATE_FILE);
        return contents ? JSON.parse(contents) : null;
    } catch (error) {
        logError(error, 'Forge Core: failed to read the previous wallpaper state');
        return null;
    }
}

function writeWallpaperState(state) {
    try {
        writeFile(WALLPAPER_STATE_FILE, `${JSON.stringify(state)}\n`);
    } catch (error) {
        logError(error, 'Forge Core: failed to save the previous wallpaper state');
    }
}

function hasChargingIcon(gicon) {
    const names = (typeof gicon?.get_names === 'function'
        ? gicon.get_names()
        : gicon?.names) ?? [];

    return names.some(name => typeof name === 'string' &&
        name.startsWith('battery-level-') && name.endsWith('-charging-symbolic'));
}

function retryAttach(label, attach, onSettled) {
    let attempts = 0;

    return GLib.timeout_add(GLib.PRIORITY_DEFAULT, ATTACH_RETRY_INTERVAL_MS, () => {
        attempts++;

        let attached = false;
        try {
            attached = attach();
        } catch (error) {
            logError(error, `Forge Core: failed to attach the ${label}`);
            attached = true;
        }

        if (!attached && attempts < ATTACH_RETRY_LIMIT)
            return GLib.SOURCE_CONTINUE;

        if (!attached)
            log(`Forge Core: gave up attaching the ${label} after ${attempts} attempts`);

        onSettled();
        return GLib.SOURCE_REMOVE;
    });
}

export default class ForgeCoreShellExtension extends Extension {
    enable() {
        this._blurred = [];
        this._shellTheme = St.ThemeContext.get_for_stage(global.stage).get_theme();
        this._shellStylesheet = Gio.File.new_for_path(
            GLib.build_filenamev([this.path, 'stylesheet.css']));
        this._shellStylesLoaded = true;
        for (const name of ['quickSettings', 'dateMenu']) {
            const box = Main.panel.statusArea[name]?.menu?.box;
            if (!box || box.get_effect(EFFECT_NAME))
                continue;
            box.add_effect_with_name(EFFECT_NAME, new Shell.BlurEffect({
                mode: Shell.BlurMode.BACKGROUND,
                radius: RADIUS,
                brightness: BRIGHTNESS,
            }));
            this._blurred.push(box);
        }

        this._powerSetupId = retryAttach('power indicators',
            () => this._attachPowerIndicators(),
            () => {
                this._powerSetupId = 0;
            });

        if (!this._attachThemeToggle()) {
            this._themeSetupId = retryAttach('theme toggle',
                () => this._attachThemeToggle(),
                () => {
                    this._themeSetupId = 0;
                });
        }
    }

    disable() {
        this._stopThemeTracking();
        this._stopPowerTracking();

        for (const box of this._blurred ?? []) {
            if (box.get_effect(EFFECT_NAME))
                box.remove_effect_by_name(EFFECT_NAME);
        }
        this._blurred = null;
    }

    _attachThemeToggle() {
        if (this._themeToggle)
            return true;

        const quickSettings = Main.panel.statusArea.quickSettings;
        const darkModeToggle = quickSettings?._darkMode?.quickSettingsItems?.[0];
        const firstItem = quickSettings?.menu?.getFirstItem?.();
        const insertionTarget = darkModeToggle ?? firstItem;
        if (!quickSettings || !insertionTarget)
            return false;

        this._themeSettings = new Gio.Settings({schema_id: INTERFACE_SCHEMA});
        this._backgroundSettings = new Gio.Settings({schema_id: BACKGROUND_SCHEMA});
        this._darkModeToggle = darkModeToggle;
        // Yaru must keep the native Dark Style control available. Forge hides it
        // only while its own fixed dark appearance is active.
        this._darkModeInitialVisibility = Boolean(darkModeToggle);
        const persistedTheme = readThemeMode();
        this._selectedTheme = persistedTheme ?? (
            this._themeSettings.get_string('icon-theme') === FORGE_ICON_THEME
                ? FORGE_ICON_THEME
                : YARU_ICON_THEME
        );
        if (!persistedTheme)
            writeThemeMode(this._selectedTheme);

        this._themeToggle = new ForgeThemeToggle(
            checked => this._selectTheme(checked ? FORGE_ICON_THEME : YARU_ICON_THEME));
        quickSettings.menu.insertItemBefore(this._themeToggle, insertionTarget);

        this._themeSignals = [
            this._themeSettings.connect('changed::icon-theme',
                () => this._syncThemeMode()),
            this._themeSettings.connect('changed::gtk-theme',
                () => this._syncThemeMode()),
            this._themeSettings.connect('changed::color-scheme',
                () => this._syncThemeMode()),
        ];

        this._syncThemeMode();
        return true;
    }

    _selectTheme(theme) {
        this._selectedTheme = theme;
        writeThemeMode(theme);

        if (theme === FORGE_ICON_THEME && !this._previousAppearance)
            this._captureAppearance();

        this._setThemeSetting('icon-theme', theme);
        this._syncThemeMode();
    }

    _setThemeSetting(key, value) {
        if (this._themeSettings?.get_string(key) !== value)
            this._themeSettings.set_string(key, value);
    }

    _setForgeStylesheet(enabled) {
        if (!this._shellTheme || !this._shellStylesheet)
            return;

        try {
            if (enabled && !this._shellStylesLoaded) {
                this._shellTheme.load_stylesheet(this._shellStylesheet);
                this._shellStylesLoaded = true;
            } else if (!enabled && this._shellStylesLoaded) {
                this._shellTheme.unload_stylesheet(this._shellStylesheet);
                this._shellStylesLoaded = false;
            }
        } catch (error) {
            logError(error, 'Forge Core: failed to switch the Shell stylesheet');
        }
    }

    _captureWallpaper() {
        writeWallpaperState({
            pictureUri: this._backgroundSettings.get_string('picture-uri'),
            pictureUriDark: this._backgroundSettings.get_string('picture-uri-dark'),
            pictureOptions: this._backgroundSettings.get_string('picture-options'),
        });
    }

    _restoreWallpaper() {
        const previous = readWallpaperState();
        if (!previous) {
            this._backgroundSettings.reset('picture-uri');
            this._backgroundSettings.reset('picture-uri-dark');
            this._backgroundSettings.reset('picture-options');
            return;
        }

        for (const [key, value] of [
            ['picture-uri', previous.pictureUri],
            ['picture-uri-dark', previous.pictureUriDark],
            ['picture-options', previous.pictureOptions],
        ]) {
            if (typeof value === 'string' &&
                this._backgroundSettings.get_string(key) !== value) {
                this._backgroundSettings.set_string(key, value);
            }
        }
    }

    _setForgeAutomation(forgeActive, previousForgeActive) {
        if (forgeActive) {
            // Do not start external wallpaper/systemd helpers while GNOME Shell
            // is booting. They can trigger a GPU redraw during Shell startup;
            // explicit activation through the toggle is sufficient and safer.
            if (previousForgeActive === false) {
                this._captureWallpaper();
                setWallpaperAutostart(true);
                setWallpaperProcess(true);
                setUserUnit(BROWSER_WATCHER_UNIT, true);
                setUserUnit(FOLDER_CHOOSER_TIMER, true);
                startUserUnit(FOLDER_CHOOSER_SERVICE);
            }
            return;
        }

        setWallpaperAutostart(false);
        setWallpaperProcess(false);
        setUserUnit(BROWSER_WATCHER_UNIT, false);
        setUserUnit(FOLDER_CHOOSER_TIMER, false);
        startUserUnit(FOLDER_CHOOSER_CLEANUP_SERVICE);

        const currentWallpaper = this._backgroundSettings?.get_string('picture-uri') ?? '';
        if (previousForgeActive === true || currentWallpaper.includes('forge-core-wallpaper'))
            this._restoreWallpaper();
    }

    _syncDesktopTheme(forgeActive, previousForgeActive) {
        updateGtkOverlay(forgeActive);
        updateDefaultCursorTheme(forgeActive ? FORGE_CURSOR_THEME : YARU_CURSOR_THEME);

        const cursorTheme = forgeActive ? FORGE_CURSOR_THEME : YARU_CURSOR_THEME;
        if (forgeActive && !GLib.file_test(
            GLib.build_filenamev([GLib.get_user_data_dir(), 'icons', cursorTheme]),
            GLib.FileTest.IS_DIR)) {
            return;
        }

        this._setThemeSetting('cursor-theme', cursorTheme);
    }

    _captureAppearance() {
        this._previousAppearance = {
            gtkTheme: this._themeSettings.get_string('gtk-theme'),
            colorScheme: this._themeSettings.get_string('color-scheme'),
        };
        try {
            writeFile(APPEARANCE_STATE_FILE, `${JSON.stringify(this._previousAppearance)}\n`);
        } catch (error) {
            logError(error, 'Forge Core: failed to save the previous appearance');
        }
    }

    _syncThemeMode() {
        if (!this._themeSettings || this._themeSyncing)
            return;

        const previousForgeActive = this._forgeActive;
        const persistedTheme = readThemeMode();
        if (persistedTheme)
            this._selectedTheme = persistedTheme;

        this._themeSyncing = true;
        try {
            const iconTheme = this._themeSettings.get_string('icon-theme');
            const activeTheme = iconTheme === FORGE_ICON_THEME
                ? FORGE_ICON_THEME
                : YARU_ICON_THEME;
            if (this._selectedTheme !== activeTheme) {
                this._selectedTheme = activeTheme;
                writeThemeMode(activeTheme);
            }

            const forgeActive = this._selectedTheme === FORGE_ICON_THEME;
            if (forgeActive && !this._forgeActive) {
                if (!this._previousAppearance)
                    this._captureAppearance();
            } else if (!forgeActive) {
                this._restoreAppearance();
            }

            this._forgeActive = forgeActive;
            this._setForgeStylesheet(forgeActive);
            this._syncDesktopTheme(forgeActive, previousForgeActive);
            if (forgeActive !== previousForgeActive || previousForgeActive === undefined)
                this._setForgeAutomation(forgeActive, previousForgeActive);
            this._syncThemeControls();

            if (forgeActive) {
                this._setThemeSetting('gtk-theme', FORGE_GTK_THEME);
                this._setThemeSetting('color-scheme', FORGE_COLOR_SCHEME);
            }
        } finally {
            this._themeSyncing = false;
        }
    }

    _restoreAppearance() {
        let previous = this._previousAppearance;
        this._previousAppearance = null;
        if (!previous) {
            try {
                const saved = readFile(APPEARANCE_STATE_FILE);
                previous = saved ? JSON.parse(saved) : null;
            } catch (error) {
                logError(error, 'Forge Core: failed to read the previous appearance');
            }
        }

        removeFile(APPEARANCE_STATE_FILE);
        if (!previous || typeof previous !== 'object')
            return;

        if (typeof previous.gtkTheme === 'string')
            this._setThemeSetting('gtk-theme', previous.gtkTheme);
        if (typeof previous.colorScheme === 'string')
            this._setThemeSetting('color-scheme', previous.colorScheme);
    }

    _syncThemeControls() {
        const forgeActive = this._selectedTheme === FORGE_ICON_THEME;
        this._themeToggle?.set({
            checked: forgeActive,
            subtitle: forgeActive ? FORGE_ICON_THEME : YARU_ICON_THEME,
        });

        if (this._darkModeToggle)
            this._darkModeToggle.visible = this._darkModeInitialVisibility && !forgeActive;
    }

    _stopThemeTracking() {
        if (this._themeSetupId) {
            GLib.source_remove(this._themeSetupId);
            this._themeSetupId = 0;
        }

        for (const signalId of this._themeSignals ?? [])
            this._themeSettings?.disconnect(signalId);

        if (this._darkModeToggle)
            this._darkModeToggle.visible = this._darkModeInitialVisibility;
        this._themeToggle?.destroy();
        this._themeSettings?.run_dispose();
        this._backgroundSettings?.run_dispose();

        this._themeSignals = null;
        this._themeToggle = null;
        this._themeSettings = null;
        this._backgroundSettings = null;
        this._darkModeToggle = null;
        this._darkModeInitialVisibility = false;
        this._selectedTheme = null;
        this._previousAppearance = null;
        this._forgeActive = false;
        this._themeSyncing = false;
    }

    _attachPowerIndicators() {
        if (this._powerIcons)
            return true;

        const quickSettings = Main.panel.statusArea.quickSettings;
        const system = quickSettings?._system;
        const powerToggle = system?._systemItem?.powerToggle;
        const quickSettingsIcon = powerToggle?._icon;
        const panelIcon = system?._indicator;

        if (!powerToggle || !quickSettingsIcon || !panelIcon)
            return false;

        try {
            this._powerToggle = powerToggle;
            this._powerIcons = [quickSettingsIcon, panelIcon];
            this._powerSignals = [];
            this._powerSignals.push([
                powerToggle,
                powerToggle.connect('notify::gicon',
                    () => this._syncBatteryState()),
            ]);
            this._powerSignals.push([
                powerToggle,
                powerToggle.connect('notify::visible',
                    () => this._syncBatteryState()),
            ]);

            this._syncBatteryState();
            this._powerPulseId = GLib.timeout_add(
                GLib.PRIORITY_DEFAULT,
                BATTERY_PULSE_INTERVAL_MS,
                () => this._pulseBatteryIcons());
        } catch (error) {
            logError(error, 'Forge Core: failed to track battery state');
            this._stopPowerTracking();
        }

        return true;
    }

    _syncBatteryState() {
        const charging = Boolean(this._powerToggle?.visible &&
            hasChargingIcon(this._powerToggle?.gicon));

        if (charging === this._batteryCharging)
            return;

        this._batteryCharging = charging;
        this._batteryPulse = false;

        for (const icon of this._powerIcons ?? []) {
            if (charging)
                icon.add_style_class_name(BATTERY_CHARGING_CLASS);
            else
                icon.remove_style_class_name(BATTERY_CHARGING_CLASS);
            icon.remove_style_class_name(BATTERY_PULSE_CLASS);
        }
    }

    _pulseBatteryIcons() {
        if (!this._powerIcons) {
            this._powerPulseId = 0;
            return GLib.SOURCE_REMOVE;
        }

        if (!this._batteryCharging) {
            this._batteryPulse = false;
            for (const icon of this._powerIcons)
                icon.remove_style_class_name(BATTERY_PULSE_CLASS);
            return GLib.SOURCE_CONTINUE;
        }

        this._batteryPulse = !this._batteryPulse;
        for (const icon of this._powerIcons) {
            if (this._batteryPulse)
                icon.add_style_class_name(BATTERY_PULSE_CLASS);
            else
                icon.remove_style_class_name(BATTERY_PULSE_CLASS);
        }

        return GLib.SOURCE_CONTINUE;
    }

    _stopPowerTracking() {
        if (this._powerSetupId) {
            GLib.source_remove(this._powerSetupId);
            this._powerSetupId = 0;
        }

        if (this._powerPulseId) {
            GLib.source_remove(this._powerPulseId);
            this._powerPulseId = 0;
        }

        for (const [object, signalId] of this._powerSignals ?? [])
            object.disconnect(signalId);

        for (const icon of this._powerIcons ?? []) {
            icon.remove_style_class_name(BATTERY_CHARGING_CLASS);
            icon.remove_style_class_name(BATTERY_PULSE_CLASS);
        }

        this._powerSignals = null;
        this._powerIcons = null;
        this._powerToggle = null;
        this._batteryCharging = false;
        this._batteryPulse = false;
    }
}

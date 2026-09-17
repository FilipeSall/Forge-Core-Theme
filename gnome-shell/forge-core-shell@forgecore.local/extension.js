import Shell from 'gi://Shell';
import GLib from 'gi://GLib';
import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';

const EFFECT_NAME = 'forge-core-glass';
const RADIUS = 22;
const BRIGHTNESS = 0.72;
const BATTERY_CHARGING_CLASS = 'forge-core-battery-charging';
const BATTERY_PULSE_CLASS = 'forge-core-battery-charge-pulse';
const BATTERY_PULSE_INTERVAL_MS = 900;
function hasChargingIcon(gicon) {
    const names = (typeof gicon?.get_names === 'function'
        ? gicon.get_names()
        : gicon?.names) ?? [];

    return names.some(name => typeof name === 'string' &&
        name.startsWith('battery-level-') && name.endsWith('-charging-symbolic'));
}

export default class ForgeCoreShellExtension extends Extension {
    enable() {
        this._blurred = [];
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

        this._powerSetupId = GLib.timeout_add(GLib.PRIORITY_DEFAULT, 100, () => {
            if (this._attachPowerIndicators()) {
                this._powerSetupId = 0;
                return GLib.SOURCE_REMOVE;
            }

            return GLib.SOURCE_CONTINUE;
        });

    }

    disable() {
        this._stopPowerTracking();

        for (const box of this._blurred ?? []) {
            if (box.get_effect(EFFECT_NAME))
                box.remove_effect_by_name(EFFECT_NAME);
        }
        this._blurred = null;
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

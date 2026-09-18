import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import System from 'system';
import {planWallpaperRestore} from '../gnome-shell/forge-core-shell@forgecore.local/wallpaperState.js';

const forgeDir = GLib.build_filenamev([GLib.get_user_cache_dir(), 'forge-core-wallpaper']);
const options = {
    forgeDir,
    fileExists: path => GLib.file_test(path, GLib.FileTest.EXISTS),
};

const settings = new Gio.Settings({schema_id: 'org.gnome.desktop.background'});

function applyPlan(previous) {
    for (const [key, value] of planWallpaperRestore(previous, options)) {
        if (value === null)
            settings.reset(key);
        else if (settings.get_string(key) !== value)
            settings.set_string(key, value);
    }
}

let failures = 0;
function check(label, condition, detail) {
    if (condition) {
        print(`ok   ${label}`);
    } else {
        print(`FAIL ${label} — ${detail}`);
        failures += 1;
    }
}

const dangling = `file://${forgeDir}/wallpaper-1789686289.png`;
settings.set_string('picture-uri', dangling);
settings.set_string('picture-uri-dark', dangling);
settings.set_string('picture-options', 'spanned');

applyPlan({
    pictureUri: dangling,
    pictureUriDark: dangling,
    pictureOptions: 'spanned',
});

for (const key of ['picture-uri', 'picture-uri-dark']) {
    const uri = settings.get_string(key);
    const path = GLib.filename_from_uri(uri)[0];
    check(`${key} aponta para arquivo existente`,
        GLib.file_test(path, GLib.FileTest.EXISTS), `${path} nao existe`);
    check(`${key} nao aponta mais para o cache do Forge`,
        !path.startsWith(`${forgeDir}/`), path);
    check(`${key} voltou ao padrao do schema`,
        uri === settings.get_default_value(key).deepUnpack(),
        `${uri} != ${settings.get_default_value(key).deepUnpack()}`);
}
check('picture-options voltou ao padrao do schema',
    settings.get_string('picture-options') ===
        settings.get_default_value('picture-options').deepUnpack(),
    settings.get_string('picture-options'));

print(failures === 0 ? '\nPASSOU' : `\nFALHOU: ${failures}`);
if (failures > 0)
    System.exit(1);

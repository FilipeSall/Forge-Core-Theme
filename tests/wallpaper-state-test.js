import System from 'system';
import {
    isForgeWallpaperUri,
    planWallpaperRestore,
    sanitizeWallpaperState,
} from '../gnome-shell/forge-core-shell@forgecore.local/wallpaperState.js';

const FORGE_DIR = '/home/tester/.cache/forge-core-wallpaper';
const ALIVE = '/usr/share/backgrounds/warty-final-ubuntu.png';
const DEAD = '/home/tester/Imagens/apagado.png';

const options = {
    forgeDir: FORGE_DIR,
    fileExists: path => path === ALIVE,
};

let failures = 0;

function check(label, actual, expected) {
    const got = JSON.stringify(actual);
    const want = JSON.stringify(expected);
    if (got === want) {
        print(`ok   ${label}`);
    } else {
        print(`FAIL ${label}\n       esperado ${want}\n       obtido   ${got}`);
        failures += 1;
    }
}

check('reconhece wallpaper gerado pelo Forge',
    isForgeWallpaperUri(`file://${FORGE_DIR}/wallpaper-1789686289.png`, FORGE_DIR), true);
check('nao confunde outro caminho com o cache do Forge',
    isForgeWallpaperUri(`file://${ALIVE}`, FORGE_DIR), false);
check('nao confunde prefixo parecido',
    isForgeWallpaperUri(`file://${FORGE_DIR}-outro/x.png`, FORGE_DIR), false);

check('nao guarda o proprio wallpaper do Forge como anterior',
    sanitizeWallpaperState({
        pictureUri: `file://${FORGE_DIR}/wallpaper-1789686289.png`,
        pictureUriDark: `file://${FORGE_DIR}/wallpaper-1789686289.png`,
        pictureOptions: 'spanned',
    }, options), null);

check('nao guarda caminho inexistente',
    sanitizeWallpaperState({
        pictureUri: `file://${DEAD}`,
        pictureUriDark: `file://${DEAD}`,
        pictureOptions: 'zoom',
    }, options), null);

check('guarda o wallpaper real do usuario',
    sanitizeWallpaperState({
        pictureUri: `file://${ALIVE}`,
        pictureUriDark: `file://${ALIVE}`,
        pictureOptions: 'zoom',
    }, options), {
        pictureUri: `file://${ALIVE}`,
        pictureUriDark: `file://${ALIVE}`,
        pictureOptions: 'zoom',
    });

check('estado do bug real volta para o padrao do sistema',
    planWallpaperRestore({
        pictureUri: `file://${FORGE_DIR}/wallpaper-1789686289.png`,
        pictureUriDark: `file://${FORGE_DIR}/wallpaper-1789686289.png`,
        pictureOptions: 'spanned',
    }, options), [
        ['picture-uri', null],
        ['picture-uri-dark', null],
        ['picture-options', null],
    ]);

check('arquivo apagado volta para o padrao do sistema',
    planWallpaperRestore({
        pictureUri: `file://${DEAD}`,
        pictureUriDark: `file://${DEAD}`,
        pictureOptions: 'spanned',
    }, options), [
        ['picture-uri', null],
        ['picture-uri-dark', null],
        ['picture-options', null],
    ]);

check('sem estado salvo volta para o padrao do sistema',
    planWallpaperRestore(null, options), [
        ['picture-uri', null],
        ['picture-uri-dark', null],
        ['picture-options', null],
    ]);

check('wallpaper valido do usuario e restaurado',
    planWallpaperRestore({
        pictureUri: `file://${ALIVE}`,
        pictureUriDark: `file://${ALIVE}`,
        pictureOptions: 'zoom',
    }, options), [
        ['picture-uri', `file://${ALIVE}`],
        ['picture-uri-dark', `file://${ALIVE}`],
        ['picture-options', 'zoom'],
    ]);

check('so o claro sobrevive: o escuro reseta',
    planWallpaperRestore({
        pictureUri: `file://${ALIVE}`,
        pictureUriDark: `file://${DEAD}`,
        pictureOptions: 'zoom',
    }, options), [
        ['picture-uri', `file://${ALIVE}`],
        ['picture-uri-dark', null],
        ['picture-options', 'zoom'],
    ]);

print(failures === 0 ? '\nPASSOU' : `\nFALHOU: ${failures}`);
if (failures > 0)
    System.exit(1);

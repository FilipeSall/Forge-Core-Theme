import GLib from 'gi://GLib';

const BACKGROUND_KEYS = [
    ['picture-uri', 'pictureUri'],
    ['picture-uri-dark', 'pictureUriDark'],
];

export function uriToPath(uri) {
    if (typeof uri !== 'string' || uri === '')
        return null;

    try {
        const [path] = GLib.filename_from_uri(uri);
        return path ?? null;
    } catch (error) {
        return null;
    }
}

export function isForgeWallpaperUri(uri, forgeDir) {
    const path = uriToPath(uri);
    if (path === null || typeof forgeDir !== 'string' || forgeDir === '')
        return false;

    return path === forgeDir || path.startsWith(`${forgeDir}/`);
}

export function isRestorableWallpaperUri(uri, {forgeDir, fileExists}) {
    const path = uriToPath(uri);
    if (path === null || isForgeWallpaperUri(uri, forgeDir))
        return false;

    return fileExists(path);
}

export function sanitizeWallpaperState(state, options) {
    if (!state || typeof state !== 'object')
        return null;

    const sanitized = {};
    let restorable = false;
    for (const [, stateKey] of BACKGROUND_KEYS) {
        const uri = state[stateKey];
        if (isRestorableWallpaperUri(uri, options)) {
            sanitized[stateKey] = uri;
            restorable = true;
        } else {
            sanitized[stateKey] = null;
        }
    }

    if (!restorable)
        return null;

    sanitized.pictureOptions = typeof state.pictureOptions === 'string'
        ? state.pictureOptions
        : null;

    return sanitized;
}

export function planWallpaperRestore(previous, options) {
    const sanitized = sanitizeWallpaperState(previous, options);
    if (!sanitized) {
        return [
            ['picture-uri', null],
            ['picture-uri-dark', null],
            ['picture-options', null],
        ];
    }

    const plan = BACKGROUND_KEYS.map(
        ([settingsKey, stateKey]) => [settingsKey, sanitized[stateKey]]);
    plan.push(['picture-options', sanitized.pictureOptions]);
    return plan;
}

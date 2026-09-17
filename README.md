# Forge Core

Tema visual para Ubuntu/GNOME inspirado numa metrópole futurista autossuficiente —
sci-fi, engenharia pesada, metal escuro e iluminação vermelha.

## Identidade

| Token | Valor |
|---|---|
| `--background` | `#1b1b1b` |
| `--surface` | `#252525` |
| `--surface-elevated` | `#303030` |
| `--text-primary` | `#ffffff` |
| `--text-secondary` | `#a6a6a6` |
| `--text-muted` | `#707070` |
| `--accent` | `#fc435a` |
| `--accent-hover` | `#ff6478` |
| `--border` | `#383838` |

Fora do escopo: RGB gamer, excesso de neon, cyberpunk decadente, steampunk vitoriano.

## Estado

| Camada | Status |
|---|---|
| Wallpaper | pronto (fora deste repo) |
| **Icon theme — pastas** | **v0.1 — instalado** |
| Icon theme — Pasta pessoal | v0.1 — instalado |
| Icon theme — Downloads | v0.1 — instalado |
| Icon theme — Documentos / Músicas / Imagens / Vídeos | reservado |
| Icon theme — app `Configurar monitor HDMI` | v0.1 — instalado |
| **Icon theme — apps (Chrome, Warp, VS Code, Postman, Beekeeper, Stitch, Discord, Orca, Nautilus, Editor de Texto, App Center, volume, teclado, Vim, Writer, energia, drivers, Relógios, Ajuda, Firefox, Brave, Safari, Monitor do Sistema, Visualizador de Imagem, lixeira)** | **v0.1 — instalado** |
| **Cursor theme — seta** | **v0.1 — instalado** |
| **Cursor theme — mão, texto, espera, cruz, grab/grabbing** | **v0.2 — instalado** |
| **Cursor theme — redimensionar (lados, cantos, linhas, colunas)** | **v0.3 — instalado** |
| Cursor theme — `help` / `move` / `not-allowed` | falta arte |
| **Notificações do GNOME Shell** | **v0.1 — instalado** |
| **Dropdown de data/hora (calendário + lista)** | **v0.1 — instalado** |
| **Menu de contexto do desktop (DING)** | **v0.1 — instalado** |
| **Dock Forge Core (altura cheia) / Quick Settings / bateria / toggle Yaru ↔ Forge Core** | **v0.4 — instalado** |
| Overview / apps GTK | não iniciado |

## Estrutura

```
forge-core/
├── assets/icons/
│   ├── manifest.json          fonte da verdade: nomes, tamanhos, aliases
│   ├── folders/               artes originais 1254x1254 RGBA
│   └── apps/                  artes de aplicativos
├── assets/cursors/
│   └── manifest.json          fonte da verdade: hotspots e nomes X de cada cursor
├── assets/dock/
│   └── floating-dock-reference/  pacote original do dock flutuante (referência de desenho)
├── icon-theme/Forge-Core/     tema de ícones gerado (versionado)
├── cursor-theme/Forge-Core-Cursor/   tema de cursor gerado (versionado)
├── gnome-shell/
│   └── forge-core-shell@forgecore.local/   extensão: notificações + dropdown + Quick Settings + dock
│       └── assets/                         SVGs do shell; chassi industrial do dock
├── gtk-3.0/
│   └── forge-core-desktop-menu.css         menu de contexto do desktop (DING, GTK3)
├── gtk-4.0/
│   └── forge-core-nautilus-thumbnails.css  pastas com ícone próprio sem fundo xadrez no Nautilus
├── config/
│   └── forge-core-browser-icons.service    template do watcher systemd --user
├── scripts/
│   ├── build-icons.py         assets + manifest -> icon-theme/
│   ├── build-cursors.py       assets + manifest -> cursor-theme/
│   ├── install-cursors.sh     cursor-theme/ -> ~/.local/share/icons + aplica
│   ├── uninstall-cursors.sh   restaura o cursor anterior e remove
│   ├── install-icons.sh       icon-theme/ -> ~/.local/share/icons + aplica
│   ├── uninstall-icons.sh     restaura o tema anterior e remove
│   ├── apply-browser-icons.py launchers com Icon absoluto -> nomes do tema
│   ├── restore-browser-icons.py restaura esses launchers
│   ├── watch-browser-icons.py detecta novos launchers APT/Snap/Flatpak
│   ├── install-shell.sh       extensão + css do menu -> HOME + aplica
│   ├── uninstall-shell.sh     remove e devolve o visual Yaru
│   ├── apply-browser-cursors.py         Google Chrome com o cursor do sistema (Yaru)
│   ├── restore-browser-cursors.py       devolve o cursor Forge Core ao Chrome
│   ├── apply-folder-chooser-icons.py    metadata::custom-icon -> miniaturas do seletor GTK
│   ├── special_folder_icons.py          ícones por nome de pasta, somente no Forge Core
│   └── restore-folder-chooser-icons.py  remove as miniaturas e o timer
└── docs/
    ├── identidade-visual.md   a fonte da verdade da identidade Forge Core
    ├── icons.md               decisões, comportamento e como expandir
    ├── cursors.md             cobertura de cursores, hotspots e spinner animado
    └── gnome-shell.md         notificações, data/hora e menu do desktop
```

## Uso

Ícones:

```bash
python3 scripts/build-icons.py
./scripts/install-icons.sh     # reverter: ./scripts/uninstall-icons.sh
# install-icons.sh também habilita o watcher systemd --user
```

Cursores:

```bash
python3 scripts/build-cursors.py
./scripts/install-cursors.sh   # reverter: ./scripts/uninstall-cursors.sh
./scripts/apply-browser-cursors.py   # Chrome com o cursor do sistema; reverter: ./scripts/restore-browser-cursors.py
```

Notificações, dropdown de data/hora, bateria, Quick Settings, dock e menu do desktop:

```bash
./scripts/install-shell.sh     # reverter: ./scripts/uninstall-shell.sh
```

Ícones customizados de pasta no seletor "Abrir pasta" (portal GNOME, GTK, VS Code):

`./scripts/install-icons.sh` aplica essa integração automaticamente enquanto o
Forge Core está ativo e um sincronizador acompanha a troca para Yaru. Ao
desligar o tema, as miniaturas são removidas. Para operar manualmente:

```bash
./scripts/apply-folder-chooser-icons.py --timer
./scripts/restore-folder-chooser-icons.py
```

Pastas chamadas `documentos`, `downloads`, `home`, `homework` ou `projetos` recebem os
assets dedicados em qualquer localização acessível do sistema, sem diferenciar maiúsculas e
minúsculas. Um ícone manual já existente tem prioridade. O sincronizador roda na ativação do
tema e diariamente:

```bash
python3 scripts/special_folder_icons.py --dry-run
```

A identidade completa (paleta, tipografia, estilo de ícones, cursores, princípios) está em
[`docs/identidade-visual.md`](docs/identidade-visual.md) — é a fonte da verdade do tema.

Detalhes, limitações conhecidas e guia de expansão por camada:
[`docs/icons.md`](docs/icons.md), [`docs/cursors.md`](docs/cursors.md),
[`docs/gnome-shell.md`](docs/gnome-shell.md), [`docs/typography.md`](docs/typography.md) e
[`docs/folder-chooser-icons.md`](docs/folder-chooser-icons.md).

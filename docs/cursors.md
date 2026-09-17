# Forge Core — Cursor Theme

Tema de cursor `Forge-Core-Cursor`, gerado a partir de `assets/cursors/manifest.json`.
Só o HOME é tocado; `/usr/share/icons` fica intacto.

## Arte de origem

| Arquivo | Papel | Origem |
|---|---|---|
| `arrow-24/32/48.png` | seta padrão | frames já renderizados (não há master em alta) |
| `pointer.png` | mão apontando (link) | master 1254x1254 |
| `grap.png` | mão aberta (grab) | master 1254x1254 |
| `grabbing.png` | punho fechado | master 1254x1254 |
| `text.png` | I-beam | master 1254x1254 |
| `crosshair.png` | cruz | master 1254x1254 |
| `wait.png` | spinner de 3 pontos | master 1254x1254 |
| `resize.png` | seta dupla diagonal | master 1254x1254, usada nas 4 direções por rotação |

Cursor exige **alfa real**: um PNG sem transparência vira um quadrado opaco na tela. A arte de
`resize.png` chegou em RGB com fundo preto sólido, e o alfa foi derivado da própria imagem —
preenchimento conectado a partir da borda sobre o preto (`max(R,G,B) <= 60`), o que preserva o
interior escuro da seta, fechado pelo contorno metálico, e converte o brilho vermelho em alfa
parcial (`alfa = (v - 6) / 44`). Resultado conferido sobre fundo claro e escuro, sem halo.
Se a arte nova já vier com transparência, nada disso é necessário.

Tamanhos gerados: **24, 32, 48, 64**. A seta sai só até 48 — o master em alta resolução
não está no repositório, e fazer upscale de 48 para 64 deixaria o cursor borrado. Quando a
arte original aparecer, basta trocar os `arrow-*.png` por um `master` no manifest e o build
passa a gerar 64 também.

## Cobertura

O agrupamento veio do próprio Yaru: cursores com conteúdo idêntico foram agrupados com
`md5sum` em `/usr/share/icons/Yaru/cursors`, o que revela os papéis reais usados neste
sistema. Cada grupo foi mapeado para uma arte Forge Core.

| Arte | Nomes X cobertos |
|---|---|
| seta | `left_ptr` `default` `arrow` `top_left_arrow` `wayland-cursor` `wayland_cursor` |
| mão apontando | `hand2` `hand` `pointer` `pointing_hand` + hashes `9d800788…` `e29285e6…` |
| mão aberta | `grab` `hand1` `openhand` |
| punho | `grabbing` `closedhand` `dnd-none` `size_all` |
| I-beam | `xterm` `text` `ibeam` |
| cruz | `crosshair` `cross` `cross_reverse` `diamond_cross` `tcross` `plus` `cell` `target` `dotbox` `dot_box_mask` `draped_box` `icon` |
| spinner | `watch` `wait` `progress` `half-busy` `left_ptr_watch` + hashes `00000000…` `08e8e1c9…` `3ecb610c…` |
| seta dupla horizontal (`rotate: 315`) | `ew-resize` `sb_h_double_arrow` `h_double_arrow` `size_hor` `size-hor` `col-resize` `split_h` `left_side` `right_side` `w-resize` `e-resize` + hash `02800603…` |
| seta dupla vertical (`rotate: 45`) | `ns-resize` `sb_v_double_arrow` `v_double_arrow` `double_arrow` `size_ver` `size-ver` `row-resize` `split_v` `top_side` `bottom_side` `n-resize` `s-resize` + hashes `00008160…` `2870a090…` |
| diagonal `\` (`rotate: 0`) | `nwse-resize` `size_fdiag` `size-fdiag` `bd_double_arrow` `top_left_corner` `nw-resize` `bottom_right_corner` `se-resize` + hash `c7088f0f…` |
| diagonal `/` (`rotate: 90`) | `nesw-resize` `size_bdiag` `size-bdiag` `fd_double_arrow` `top_right_corner` `ne-resize` `bottom_left_corner` `sw-resize` + hash `fcf1c3c7…` |

**86 nomes**, todos verificados resolvendo pela pilha real do GTK/Xcursor.

Os hashes hexadecimais não são enfeite: Firefox, Chromium e apps GTK pedem o cursor por
esses nomes. Sem eles, o cursor do link em página web continuaria Yaru.

### Contra a lista de estados prioritários

`docs/identidade-visual.md` seção 7 lista dez estados prioritários. Situação:

| Estado | Status |
|---|---|
| `default` `pointer` `text` `wait` `progress` `grab` `grabbing` | Forge Core |
| redimensionar (lados, cantos, linhas e colunas) | Forge Core |
| `help` `move` `not-allowed` | **ainda Yaru** — não existe arte |

Todo o resto (copiar, alias, proibido, lápis, zoom, texto vertical…) herda
Yaru via `Inherits=Yaru` no `index.theme`. Isso é proposital: transformar a arte de uma mão
em cursor de redimensionamento seria decorativo antes de funcional, o oposto da regra da
seção 7.

## Hotspots

Definidos em coordenadas do master e convertidos na hora do build.

| Cursor | Hotspot | Por quê |
|---|---|---|
| seta | `0,0` | ponta da seta |
| mão apontando | ponta do indicador | é o ponto que "clica" |
| I-beam, cruz, spinner | centro | simetria |
| mão aberta e punho | mesmo ponto relativo (centro) | o cursor troca de aberta para punho durante o arrasto; hotspots diferentes fariam a arte pular |

O build recorta cada master num quadrado centrado no conteúdo (com 3% de folga) e
reescala; o hotspot é transformado junto, então nunca sai do lugar.

## Uma arte, quatro direções (`rotate`)

Redimensionar precisa de quatro orientações, e a arte existe só na diagonal `\`. O manifesto
aceita `rotate` em graus por cursor, e o `build-cursors.py` gira o master antes de recortar:

| `rotate` | Resultado |
|---|---|
| `0` | `\` — canto superior-esquerdo / inferior-direito |
| `45` | vertical — redimensionar linha, borda de cima e de baixo |
| `90` | `/` — canto superior-direito / inferior-esquerdo |
| `315` | horizontal — redimensionar coluna, borda esquerda e direita |

A rotação acontece em volta do **hotspot**, num canvas ampliado o suficiente para a diagonal
caber (a seta mede ~1250 px de ponta a ponta num master de 1254 px; girar no canvas original
cortaria as pontas). Só depois o recorte quadrado é calculado, agora sobre a arte já girada —
diferente do spinner, que reaproveita o recorte do quadro zero para não trepidar.

Como o hotspot fica no centro da seta, ele cai no mesmo ponto em todas as direções.

Verificado ao vivo: numa janela de 800x600, com a borda visível calculada por
`_GTK_FRAME_EXTENTS`, a lateral dá a seta horizontal, a borda de baixo a vertical e os cantos
as diagonais certas. Hover 1 px fora da janela **não** serve para testar: em janelas com
decoração do cliente a zona de resize fica na margem de sombra, dentro da janela X.

## Spinner animado

`wait.png` é estático, mas o cursor é gerado **animado**: 24 quadros girando 360°, 40 ms
cada (uma volta por segundo). A rotação é feita em torno do hotspot, e o recorte é calculado
uma vez no quadro zero e reaproveitado — sem isso a animação trepidaria.

São 96 imagens em um arquivo só (24 quadros x 4 tamanhos), por isso `watch` tem ~750 KB
contra ~32 KB dos estáticos. É normal para cursor animado.

## Construir

```bash
python3 scripts/build-cursors.py
```

Gera `cursor-theme/Forge-Core-Cursor/` (versionado, pronto para instalar). Precisa de
`xcursorgen` (pacote `x11-apps`) e Pillow.

## Instalar

```bash
./scripts/install-cursors.sh          # --no-apply instala sem trocar o cursor ativo
```

O script instala em `~/.local/share/icons/Forge-Core-Cursor`, cria o link legado
`~/.icons/Forge-Core-Cursor`, aponta `~/.icons/default/index.theme` para o tema e seta
`org.gnome.desktop.interface cursor-theme`.

O `~/.icons/default/index.theme` existe para os apps que não leem gsettings — Electron,
Java, alguns jogos. Sem ele, "substituir todos" valeria só para o que é GTK.

## Restaurar

```bash
./scripts/uninstall-cursors.sh        # --keep-files só desliga
```

Volta ao tema registrado em `~/.local/share/forge-core/previous-cursor-theme` (Yaru como
fallback), restaura ou remove o `~/.icons/default/index.theme` e apaga o tema do HOME.

Apps já abertos seguem com o cursor antigo até serem reiniciados — vale para instalar e para
desinstalar.

## Exceção: Google Chrome com o cursor do sistema

```bash
./scripts/apply-browser-cursors.py     # reverter: ./scripts/restore-browser-cursors.py
```

No X11 o Chrome carrega os cursores pelo nome do tema que vem do GTK
(`Forge-Core-Cursor`) e **ignora** `XCURSOR_THEME` — testado: com
`XCURSOR_THEME=Yaru` a mão e o I-beam continuam Forge Core. O que ele respeita é
`XCURSOR_PATH`.

O script prefixa cada `Exec=` dos atalhos do Chrome em `~/.local/share/applications`
(inclusive PWAs) com:

```
env XCURSOR_PATH=~/.local/share/forge-core/browser-cursors:/usr/share/icons:/usr/share/pixmaps
```

Sem `~/.icons` e `~/.local/share/icons` no caminho, o Chrome não acha o
`Forge-Core-Cursor` e cai no tema `default`. O `default` de `/usr/share/icons` herda
`DMZ-White` (mão branca), por isso o script cria `browser-cursors/default/index.theme`
herdando o tema de `previous-cursor-theme` (Yaru).

- Se `google-chrome.desktop` ou `com.google.Chrome.desktop` só existem em
  `/usr/share/applications`, são copiados com `X-Forge-Core-Browser-Cursors=copied`; o
  restore apaga essas cópias e só tira o prefixo das demais.
- Vale só para Chrome aberto pelos atalhos. Se ele já estiver rodando, feche por completo
  (`Ctrl+Shift+Q`); uma instância iniciada pelo terminal sem o `env` mantém o Forge Core.
- O Chrome recria o `.desktop` de PWA ao atualizar o app; rode o apply de novo se o
  prefixo sumir.

## Adicionar um cursor novo

1. Colocar o PNG em `assets/cursors/` (quanto maior melhor; os masters são 1254x1254).
2. Adicionar uma entrada em `manifest.json` com `master`, `hotspot` em pixels do master e a
   lista de `names`.
3. Para descobrir quais nomes o papel usa neste sistema:

```bash
cd /usr/share/icons/Yaru/cursors
md5sum $(find . -maxdepth 1 -type f ! -name "*.cur" ! -name "*.ani" -printf "%f\n") \
  | awk '{a[$1]=a[$1]" "$2} END{for(k in a) print a[k]}' | sort
```

Nomes na mesma linha são o mesmo cursor — é o grupo inteiro que precisa entrar em `names`.

4. `python3 scripts/build-cursors.py && ./scripts/install-cursors.sh`

## Testar

```bash
gsettings get org.gnome.desktop.interface cursor-theme
```

Verificar que todos os nomes resolvem de fato (não só que o arquivo existe):

```bash
python3 -c "
import json
m=json.load(open('assets/cursors/manifest.json'))
print('\n'.join(n for c in m['cursors'] for n in c['names']))" > /tmp/names.txt
xargs -a /tmp/names.txt gjs /tmp/cursor-check.js --
```

Na prática: passar o mouse sobre um link (mão), sobre um campo de texto (I-beam), arrastar
um ícone do desktop (mão aberta virando punho) e abrir algo pesado (spinner girando).

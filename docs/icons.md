# Forge Core — Icon Theme

Tema de ícones do Forge Core. Os assets próprios cobrem pastas, aplicativos selecionados e
ícones simbólicos do GNOME; qualquer nome não listado continua vindo da cadeia de herança.

## Ambiente alvo (detectado em 2026-09-15)

| Item | Valor |
|---|---|
| Distro | Ubuntu 24.04.4 LTS (noble) |
| Desktop | `ubuntu:GNOME` — GNOME Shell 46.0, Nautilus 46.4, sessão X11 |
| Icon theme anterior | `Yaru` |
| GTK theme | `Yaru-dark`, `color-scheme = prefer-dark` |
| HiDPI | não (scaling-factor 0) → diretórios `@2x` **não** são necessários |
| Instalação | `~/.local/share/icons/Forge-Core` (XDG, sem `sudo`) |

## Cadeia de herança

```
Forge-Core
   ├── ícones próprios (places/)
   └── Inherits = Yaru → Humanity → Adwaita → hicolor
```

`Yaru,Humanity,hicolor` é a cadeia real do Yaru nesta máquina; `Adwaita` entra antes do
`hicolor` como rede de segurança para ícones que o Yaru não cobre.

Qualquer nome de ícone que o Forge Core não define cai automaticamente nessa cadeia.

## O que está implementado

| Nome do ícone | Origem | Observação |
|---|---|---|
| `folder` | `assets/icons/folders/forge-folder-network.png` | pasta padrão do Forge Core |
| `inode-directory` | symlink → `folder.png` | **obrigatório** (ver abaixo) |
| `folder-open` | `assets/icons/folders/forge-folder-network.png` | fallback Forge Core para a pasta aberta |
| `folder-drag-accept` | symlink → `folder-open.png` | estado de arrastar-para-dentro |
| `user-home` | `assets/icons/folders/home-forge-core.png` | Pasta pessoal; mesmo asset do nome especial `home` |
| `folder-download` | `assets/icons/folders/downloads-forge-core.png` | pasta Downloads do XDG |
| `preferences-desktop-display` | `assets/icons/apps/forge-display-setup.png` | launcher "Configurar monitor HDMI" |
| `preferences-desktop-display-settings`, `video-display` | symlinks → `preferences-desktop-display.png` | nomes alternativos do mesmo conceito |
| `snap-store_snap-store`, `snap-store_show-updates`, `snap-store_packagekit-session-installer` | `assets/icons/apps/app-center.png` | App Center do Snap — overrides para o ícone absoluto |
| `multimedia-volume-control` | `assets/icons/apps/volume-control.png` | PulseAudio Volume Control |
| `input-keyboard` | `assets/icons/apps/input-keyboard.png` | launcher local “Alternar Teclado” |
| `gvim` | `assets/icons/apps/vim.png` | Vim |
| `libreoffice-writer` | `assets/icons/apps/libreoffice-writer.png` | LibreOffice Writer |
| `org.gnome.PowerStats` | `assets/icons/apps/power-stats.png` | Estatística de energia |
| `jockey` | `assets/icons/apps/additional-drivers.png` | Drivers adicionais |
| `google-chrome` | `assets/icons/apps/chrome.png` | dock |
| `dev.warp.Warp` | `assets/icons/apps/warp.png` | dock |
| `vscode` | `assets/icons/apps/vscode.png` | dock (`code.desktop` e `code-url-handler.desktop`) |
| `postman` | `assets/icons/apps/postman.png` | dock (snap) |
| `beekeeper-studio` | `assets/icons/apps/beekeeper.png` | dock (snap) |
| `chrome-kpkpmmpeainfoiplppkjdnclpakaldhf-Profile_1` | `assets/icons/apps/stitch.png` | dock — PWA Stitch do Chrome |
| `discord` | `assets/icons/apps/discord.png` | dock |
| `orca-stably` | `assets/icons/apps/orca.png` | dock |
| `org.gnome.Nautilus` | `assets/icons/folders/forge-folder-network.png` | dock |
| `org.gnome.TextEditor` | `assets/icons/apps/bloco-notas.png` | dock |
| `org.gnome.clocks` | `assets/icons/apps/clock.png` | Relógios do GNOME |
| `org.gnome.eog` | `assets/icons/apps/finder.png` | visualizador de imagens |
| `org.gnome.SystemMonitor` | `assets/icons/apps/monitor-do-sistema.png` | Monitor do Sistema |
| `firefox`, `firefox_firefox`, `firefox-esr`, `org.mozilla.firefox`, `org.mozilla.Firefox` | `assets/icons/apps/firefox.png` | Firefox — APT, Snap e Flatpak |
| `brave` | `assets/icons/apps/brave.png` | Brave; aliases para APT, Snap e Flatpak |
| `safari` | `assets/icons/apps/safari.png` | Safari; aliases para launchers compatíveis |
| `user-trash`, `user-trash-full` | `assets/icons/apps/lixeira.png` | lixeira do dock e do Nautilus |
| `view-app-grid-user-symbolic` | herdado do tema base | botão Mostrar aplicativos; a rotação é aplicada pelo GNOME Shell |
| `org.gnome.Yelp` | `assets/icons/apps/ajuda.png` | Ajuda do GNOME |

### Pastas especiais por nome

O tema inclui os assets `documentos-forge-core.png`, `downloads-forge-core.png`,
`home-forge-core.png`, `homework-forge-core.png` e `projetos-forge-core.png`. Eles são
registrados como ícones `places` e aplicados pelo sincronizador a qualquer diretório acessível
do sistema cujo nome seja, sem diferenciar maiúsculas/minúsculas, `documentos`, `downloads`,
`home`, `homework` ou `projetos`.

O sincronizador preserva `metadata::custom-icon` manual. Ele remove somente os metadados que
ele próprio registrou, é executado na ativação do Forge Core e possui um timer diário para
encontrar pastas novas ou renomeadas. `/proc`, `/sys`, `/dev`, `/run`, `/tmp`, caches e árvores
de dependências são ignorados. Diretórios sem permissão são ignorados sem interromper a
sincronização.

Os nove assets de projetos (`claude`, `codex`, `forge-core`, `gdf-cluster-2`, `gemini`, `hjlog`,
`negocia-df`, `papelito` e `sea`) usam a mesma comparação sem diferenciar maiúsculas/minúsculas,
mas são
aplicados somente dentro de `/home/sea/projetos`. `negocia` também é aceito como alias da
pasta `negocia-df` existente. Um `metadata::custom-icon` escolhido manualmente sempre tem
prioridade quando o arquivo apontado existe; se um URI `file://` manual ficar quebrado, o
asset Forge correspondente é usado como fallback.

Os nomes de app são o `Icon=` do `.desktop`, conferido com
`Gio.DesktopAppInfo.new('<id>.desktop').get_string('Icon')`. O tema não edita launchers do
sistema. Quando Firefox, Brave ou Safari usam um `Icon=/caminho/absoluto`,
`install-icons.sh` cria uma cópia marcada em `~/.local/share/applications` com `Icon=<nome>`;
`uninstall-icons.sh` remove a cópia ou restaura um arquivo local anterior.
O nome do PWA inclui o id do app e o perfil do Chrome; se o app for reinstalado em outro
perfil, o nome muda e o manifesto precisa acompanhar.

O nome do launcher local precisa ser **igual ao basename** do launcher instalado:
`firefox_firefox.desktop` sombreia o arquivo do Snap com o mesmo desktop ID. Um nome
diferente criaria um segundo aplicativo. `update-desktop-database` atualiza o índice do
diretório, mas não invalida sozinho os objetos já carregados pelo GNOME Shell. Os scripts fazem
uma transição de tema, mas não executam `gnome-shell --replace` automaticamente: essa operação
pode derrubar o Shell em algumas sessões X11. Quando a mudança não aparecer imediatamente, use
logout/login.

Tamanhos gerados: `16, 22, 24, 32, 48, 64, 96, 128, 256`.
O diretório `256x256` é declarado `Type=Scalable` (`MinSize=192`, `MaxSize=512`) para
atender pedidos acima de 256 px sem precisar de um arquivo dedicado.

### Por que `inode-directory` é obrigatório

O GIO pede uma **lista** de nomes por pasta, e para uma pasta comum a lista é:

```
['inode-directory', 'folder', 'inode-directory-symbolic', 'folder-symbolic']
```

`inode-directory` vem **antes** de `folder`. Sem esse alias, o tema poderia resolver a pasta
comum pelo Yaru. O próprio Yaru faz o mesmo symlink.

## Comportamento conhecido: pastas especiais

O GTK resolve ícones **tema por tema**, e dentro de cada tema testa **todos** os nomes da lista.
Como o Forge Core define `folder`, ele vence antes de o Yaru ser consultado:

| Pasta | Nomes pedidos | Resultado atual |
|---|---|---|
| pasta comum | `inode-directory, folder` | Forge Core ✅ |
| Downloads | `folder-download, folder` | Forge Core ✅ (seta de download) |
| Documentos / Músicas / Imagens / Vídeos | `folder-<tipo>, folder` | **Forge Core genérico** |
| Pasta pessoal | `user-home` | Forge Core ✅ |
| Área de trabalho | `user-desktop` | Yaru (herdado) |

`user-home-symbolic` continua vindo do Yaru — ícones simbólicos são monocromáticos de traço,
onde a arte detalhada não funciona. Por isso a barra lateral do Nautilus mantém o traço do Yaru.

Ou seja: as pastas XDG perdem a diferenciação colorida do Yaru e passam a usar a pasta genérica
do Forge Core. Isso é inerente ao algoritmo de lookup — não há como sobrescrever `folder` e ao
mesmo tempo manter `folder-documents` do Yaru sem copiar arte do Yaru para dentro do tema.

Três caminhos possíveis (nenhum aplicado ainda):

1. **Manter assim** — visual homogêneo, todas as pastas no chassi Forge Core.
2. **Criar as variantes Forge Core** para `folder-documents`, `folder-music`,
   `folder-pictures`, `folder-videos` trocando o módulo central (arte já existe em `assets/`).
3. **Copiar os PNGs do Yaru** para dentro do Forge-Core com esses nomes (funciona, mas mistura
   arte azul do Yaru com o chassi escuro — visualmente pior).

## Escala ancorada em um asset de referência

`manifest.json` define `referenceSource: "folders/forge-folder-network.png"`. O `build-icons.py` calcula
a escala **uma única vez**, a partir da largura de conteúdo desse asset (992 px), e aplica a
mesma escala a todos os ícones — depois centraliza cada um pelo próprio bounding box.

Os assets dedicados usam `fill: 1.0` e a mesma arte de `home-forge-core.png` é usada por
`user-home` e pelo nome especial `home`, mantendo o estilo da pasta pessoal consistente.

### Exceção: `fill` por ícone (dock)

Um ícone com `"fill": 1.0` no manifesto ignora a âncora e escala pelo próprio bounding box,
ocupando 100% do lado maior. Usado nos ícones do dock, que ficavam ~6 % menores que os de
antes com a margem das pastas. `folder` continua ancorado; `user-home`, `folder-download` e as
pastas especiais usam o próprio enquadramento por serem assets de 512×512.

**Ao adicionar uma arte nova**, mantenha o chassi no mesmo enquadramento das existentes
(canvas 1254×1254, chassi ~1164 px de largura). Se uma arte futura precisar de um enquadramento
diferente, ajuste `contentFill` — os valores atuais (`0.96` até 32 px, `0.94` acima) já deixam
folga para o halo da home não ser cortado em 16 px.

## Legibilidade em tamanhos pequenos

A arte é fotorrealista e densa. Reduzida por LANCZOS:

| Tamanho | `folder` | `user-home` |
|---|---|---|
| 96, 128, 256 | excelente | excelente |
| 48, 64 | bom | bom, casa legível |
| 32 | bom — o painel vazio sobrevive bem | a casa começa a borrar |
| 16, 22, 24 | aceitável — lê-se como pasta escura com traço `#fc435a` | a casa vira borrão, mas o halo vermelho continua distinguindo a home da pasta comum |

A arte de `folder` sem módulo central (v0.2) reduz consideravelmente melhor que a versão
anterior com o módulo de mira, que virava um borrão abaixo de 32 px.

Isso afeta a barra lateral, a visão em lista e o zoom `small` do Nautilus
(`org.gnome.nautilus.icon-view default-zoom-level`, atualmente `small`).

**Nenhum redesenho automático foi feito.** Se `user-home` incomodar em ≤24 px, a correção
adequada é uma arte simplificada específica para essa faixa, registrada no manifesto como um
asset separado por faixa de tamanho.

## Ícones de aplicativo

O `.desktop` de `Configurar monitor HDMI` declara `Icon=preferences-desktop-display` — um nome
padrão do freedesktop. Por isso o override é feito **dentro do tema**, sem editar o `.desktop`:

```
~/Área de trabalho/configurar-monitor-hdmi.desktop   (intocado)
        Icon=preferences-desktop-display
                    ↓
Forge-Core/48x48/apps/preferences-desktop-display.png ✅
```

Vantagem: `uninstall-icons.sh` reverte tudo, nada fica órfão no `.desktop`.

Nesta máquina esse nome só é usado pelos dois `.desktop` do próprio launcher
(`~/Área de trabalho/` e `~/.local/share/applications/`); o painel Telas do GNOME Settings 46
usa `org.gnome.Settings-display-symbolic`, então não é afetado.

Se no futuro for preciso limitar um ícone a **um único** launcher sem tocar num nome
compartilhado, troque o `Icon=` do `.desktop` por um nome exclusivo (ex.: `forge-display-setup`)
e registre esse nome no manifesto.

### Refresh do cache da extensão Desktop Icons

O Nautilus e o GTK recarregam o tema ao vivo, mas a extensão *Desktop Icons* (`gjs`/ding) cacheia
os ícones da área de trabalho. Para forçar:

```bash
gsettings set org.gnome.desktop.interface icon-theme 'Yaru'
gsettings set org.gnome.desktop.interface icon-theme 'Forge-Core'
```

## Como expandir

Tudo passa por `assets/icons/manifest.json`. O campo `context` define a pasta dentro do tema
(`places` para pastas e locais, `apps` para aplicativos) e o `build-icons.py` monta a linha
`Directories=` do `index.theme` sozinho. Para adicionar um ícone:

```json
{
  "source": "folders/home-forge-core.png",
  "context": "places",
  "name": "user-home",
  "aliases": []
}
```

Depois:

```bash
python3 scripts/build-icons.py
./scripts/install-icons.sh
```

O `build-icons.py` recria `icon-theme/Forge-Core/` do zero e regenera o `index.theme`
(incluindo a linha `Directories=`) a partir do manifesto.

### Descobrindo o nome certo de um ícone de aplicativo

Nunca presuma — APT, Snap e Flatpak usam identificadores diferentes:

```bash
grep -h '^Icon=' ~/.local/share/applications/*.desktop \
                 /usr/share/applications/*.desktop \
                 /var/lib/snapd/desktop/applications/*.desktop 2>/dev/null | sort -u
```

Para descobrir o que o GIO pede para um caminho específico:

```bash
python3 -c "
import gi; gi.require_version('Gio','2.0')
from gi.repository import Gio
print(Gio.File.new_for_path('/caminho').query_info('standard::icon',0,None).get_icon().get_names())
"
```

Para confirmar de qual tema um ícone está vindo:

```bash
python3 -c "
import gi; gi.require_version('Gtk','4.0')
from gi.repository import Gtk, Gdk
Gtk.init()
t = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
print(t.lookup_icon('folder', None, 48, 1, Gtk.TextDirection.NONE, 0).get_file().get_path())
"
```

### Launchers com ícone absoluto

Snap e alguns empacotamentos gravam um caminho absoluto no campo `Icon=`, o que
ignora completamente o tema de ícones. O instalador procura launchers instalados de Firefox,
Brave, Safari e App Center em APT, Snap, Flatpak e no diretório do usuário. Só cria overrides quando o
launcher existe e só altera entradas cujo `Icon=` começa com `/`, portanto um tema instalado
em outra máquina não cria aplicativos fantasma. O arquivo original continua intocado em
`/usr/share/applications`, `/var/lib/snapd/desktop/applications` ou nos exports Flatpak.

O GIO consulta primeiro `~/.local/share/applications` e depois os diretórios de sistema. Assim,
para o Firefox Snap, o resultado esperado é:

```
Gio.DesktopAppInfo.new('firefox_firefox.desktop').get_filename()
  -> ~/.local/share/applications/firefox_firefox.desktop
get_string('Icon')
  -> firefox
Gtk.IconTheme.lookup_icon('firefox', ...)
  -> ~/.local/share/icons/Forge-Core/<tamanho>x<tamanho>/apps/firefox.png
```

Para reaplicar depois de instalar um navegador ou o App Center:

```bash
./scripts/apply-browser-icons.py
```

O `install-icons.sh` também instala e habilita o serviço
`forge-core-browser-icons.service` em `~/.config/systemd/user`. O watcher verifica a cada dois
segundos os diretórios de aplicativos APT, Snap, Flatpak e usuário. Quando um novo launcher
aparece, aplica o override e atualiza o índice. O watcher não reinicia o GNOME Shell; se o Shell
mantiver um `GFileIcon` antigo em memória, a atualização visual ocorre na próxima sessão. Se um
navegador ou o App Center for removido, um override criado pelo tema também é removido para não
deixar aplicativo fantasma.

Em X11, uma recarga manual continua disponível, mas é opcional e pode derrubar o Shell:

```bash
FORGE_CORE_ALLOW_GNOME_SHELL_REPLACE=1 python3 -c \
  "import sys; sys.path.insert(0, 'scripts'); import browser_icons; browser_icons.refresh_gnome_shell()"
```

O serviço pode ser consultado com:

```bash
systemctl --user status forge-core-browser-icons.service
```

O restore e a remoção do watcher são executados automaticamente por
`./scripts/uninstall-icons.sh` e o restore também pode ser chamado diretamente:

```bash
./scripts/restore-browser-icons.py
```

## Assets em reserva

Já versionados em `assets/icons/folders/`, ainda **não** incluídos no tema:

| Arquivo | Módulo central | Destino sugerido |
|---|---|---|
| `forge-folder-power.png` | tomada / plug | — (`folder-download` já usa arte própria) |
| `forge-folder-code.png` | `</>` | `folder-development`, `folder-projects` |

Todos compartilham o mesmo chassi metálico, o que mantém a consistência do conjunto.

## Instalar / desinstalar

```bash
python3 scripts/build-icons.py      # regenera icon-theme/Forge-Core
./scripts/install-icons.sh          # instala em ~/.local/share/icons e aplica
./scripts/install-icons.sh --no-apply   # instala sem trocar o tema ativo
./scripts/uninstall-icons.sh        # restaura o tema anterior e remove os arquivos
./scripts/uninstall-icons.sh --keep-files
```

O tema anterior fica registrado em `~/.local/share/forge-core/previous-icon-theme`.
O estado dos overrides e os backups ficam em
`~/.local/share/forge-core/browser-icon-overrides.json`; o uninstall restaura arquivos locais
anteriores e remove somente overrides ainda marcados pelo Forge Core.

Reversão manual, sem os scripts:

```bash
gsettings set org.gnome.desktop.interface icon-theme 'Yaru'
systemctl --user disable --now forge-core-browser-icons.service
rm -rf ~/.local/share/icons/Forge-Core
```

Nada em `/usr/share/icons` é lido para escrita, nenhum `sudo` é usado e nenhum tema do sistema
é modificado. Logout **não** é necessário: o GTK recarrega o tema de ícones ao vivo.

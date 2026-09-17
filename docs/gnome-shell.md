# Forge Core — GNOME Shell e menu do desktop

Cobre três componentes: o **banner de notificação**, o **dropdown de data/hora**
(calendário + lista de notificações) e o **menu de contexto do desktop** (botão direito na
área de trabalho, e também sobre um ícone). Nada mais do shell é tocado.

## Ambiente alvo (detectado em 2026-09-15)

| Item | Valor |
|---|---|
| Distribuição | Ubuntu 24.04.4 LTS (noble) |
| GNOME Shell | 46.0 |
| Sessão | X11 (`XDG_SESSION_TYPE=x11`, `XDG_CURRENT_DESKTOP=ubuntu:GNOME`) |
| Shell theme ativo | `resource:///org/gnome/shell/theme/Yaru/gnome-shell-dark.css` |
| GTK theme | `Yaru-dark` |
| Icon theme | `Forge-Core` |
| Ícones do desktop | `ding@rastersoft.com` (Desktop Icons NG 47.0.9), extensão de sistema |
| Wallpaper | vídeo, via `hanabi-extension@jeffshee.github.io` |

O shell theme **não** vem de `/usr/share/themes/Yaru-dark/gnome-shell/`. O modo de sessão
`/usr/share/gnome-shell/modes/ubuntu.json` declara `stylesheetName: Yaru/gnome-shell.css`
e, como `color-scheme` é `prefer-dark` e o GTK theme termina em `-dark`,
`_getYaruStyleSheet()` resolve para a variante `gnome-shell-dark.css` dentro de
`/usr/share/gnome-shell/theme/Yaru/gnome-shell-theme.gresource`. Para inspecionar:

```bash
gresource extract /usr/share/gnome-shell/theme/Yaru/gnome-shell-theme.gresource \
  /org/gnome/shell/theme/Yaru/gnome-shell-dark.css > /tmp/yaru-dark.css
```

## Quem desenha o quê

### Notificação — GNOME Shell (St / CSS do shell)

`messageTray.js` cria o banner como um `Calendar.NotificationMessage` e adiciona a classe
`notification-banner` sobre a classe `message` que o widget já traz:

```js
this._banner = new Calendar.NotificationMessage(this._notification);
this._banner.add_style_class_name('notification-banner');
```

Hierarquia real na série 46 (`messageList.js`, `calendar.js`):

```
.message.notification-banner          St.Button
└── St.BoxLayout
    ├── .message-header
    │   ├── .message-source-icon
    │   ├── .message-header-content
    │   │   ├── .message-source-title
    │   │   └── .event-time
    │   ├── .message-expand-button
    │   └── .message-close-button
    ├── .message-box
    │   ├── .message-icon  (+ .message-themed-icon quando simbólico)
    │   └── .message-content
    │       ├── .message-title
    │       └── .message-body  (dentro de .url-highlighter)
    └── St.Bin da área de ações
        └── .notification-buttons-bin
            └── .notification-button
```

`message-banner` **não existe** nesta versão — é nome de versões antigas. Confirmado com
`grep -a message-banner /usr/lib/gnome-shell/libshell-14.so` (sem resultado).

Para reler o JS real da versão instalada:

```bash
gresource extract /usr/lib/gnome-shell/libshell-14.so /org/gnome/shell/ui/messageList.js
gresource extract /usr/lib/gnome-shell/libshell-14.so /org/gnome/shell/ui/messageTray.js
```

### Dropdown de data/hora — GNOME Shell (St / CSS do shell)

`dateMenu.js` marca a caixa do popover com uma classe exclusiva:

```js
this.menu.box.add_style_class_name('datemenu-popover');
```

Essa é a única âncora segura. O container é um `PopupMenu` comum, então a classe
`popup-menu-content` que carrega fundo, borda e sombra é **compartilhada com todos os menus
do painel**, inclusive o Quick Settings. Como `datemenu-popover` está no mesmo ator, o
composto `.popup-menu-content.datemenu-popover` isola o dropdown sem tocar em nenhum outro.

Estrutura real na série 46:

```
.popup-menu-content.datemenu-popover
└── #calendarArea
    ├── .message-list                       lista de notificações
    │   ├── .message-list-placeholder
    │   ├── .message-list-sections > .message-list-section > .message
    │   └── .message-list-controls
    │       ├── .dnd-button > .toggle-switch
    │       └── .message-list-clear-button
    └── .datemenu-calendar-column
        ├── .datemenu-today-button  (.day-label, .date-label)
        ├── .calendar
        │   ├── .calendar-month-header  (.pager-button, .calendar-month-label)
        │   ├── .calendar-day-heading
        │   ├── .calendar-week-number
        │   └── .calendar-day  (+ .calendar-weekend, .calendar-other-month,
        │                         .calendar-today, .calendar-day-with-events)
        └── .datemenu-displays-section
            ├── .events-button        (.events-title, .event-box, .event-time…)
            ├── .world-clocks-button  (.world-clocks-city, .world-clocks-time…)
            └── .weather-button       (.weather-header, .weather-forecast-temp…)
```

`.message-list-section-title` **não existe** nesta versão — foi verificado no JS extraído
antes de escrever qualquer regra.

Três coisas do Yaru aqui só são vencíveis com `!important`, porque o próprio Yaru usa
`!important`: `.calendar-month-label` (cor), `.calendar-today.calendar-day-with-events`
(imagem do ponto) e os anéis de foco laranja (`box-shadow: inset … !important`).

A linguagem industrial do dropdown é desenhada em SVG, não em cor de CSS: o St não tem
`clip-path`, então chanfros, colchetes e placas só existem como imagem. Tudo mora em `assets/`:

| Arquivo | Onde | Como entra |
|---|---|---|
| `datemenu-chassis.svg` | `.popup-menu-content.datemenu-popover` | `border-image … 16` — chanfros de 12/4 px, parede dupla, linhas de energia `#fc435a` só nos cantos superior-esquerdo e inferior-direito, rebites |
| `datemenu-module.svg` (+ `-hover`, `-active`) | calendário, eventos, relógios, tempo | `border-image … 8` — placa `#252525` com chanfro de 6 px em dois cantos; hover `#303030`, ativo com contorno `#fc435a` |
| `datemenu-reticle.svg` (+ `-active`) | `.datemenu-today-button` | `border-image … 8` — colchetes de HUD `#707070`, vermelhos no hover |
| `calendar-today.svg` (+ `-hover`, `-events`, `-events-hover`) | `.calendar-today` | `background-image` — placa octogonal vermelha; número em `#1b1b1b` (branco sobre `#fc435a` dá 3,5:1) |
| `calendar-day-mark.svg` | `.calendar-day-with-events` | barra vermelha de 8 px no pé da célula |
| `switch-off.svg`, `switch-on.svg` | `.dnd-button .toggle-switch` | chave retangular chanfrada com trava de metal |
| `notification-standby.svg` | `.message-list-placeholder > StIcon` | sino em módulo octogonal, LEDs em standby |

O sino do estado vazio é um `St.Icon` simbólico (`no-notifications-symbolic`) criado em JS. Sem
lógica na extensão, o ícone recebe `color: transparent` (a recoloração simbólica some) e o SVG
entra como `background-image` do próprio ícone, com `icon-size: 96px`.

Com `border-image`, o fundo do widget fica `transparent` e o `border-radius` em `0`: qualquer
cor de fundo seria pintada como retângulo por baixo e vazaria nos chanfros. Por isso o
`:hover`/`:active` do Yaru em `.calendar` também é zerado.

Duas armadilhas do St confirmadas nesta versão:

- **`font-family`**: só o primeiro nome pode vir entre aspas; os seguintes precisam ser
  palavras soltas (`font_family_from_terms`). `"Oxanium", "IBM Plex Sans", sans-serif` falha
  com `Couldn't parse family in font property` no journal e cai na fonte padrão. Usar
  `Oxanium, IBM Plex Sans, sans-serif`.
- **`letter-spacing`** não entra no cálculo de largura de `StLabel`: "quarta" saiu cortado como
  "quar…". Só é usado no `.calendar-month-label`, que tem largura fixa de 10em.

URLs relativas em `stylesheet.css` de extensão resolvem a partir da pasta da extensão.

### Menu do desktop — DING (GTK **3**, processo separado)

O menu do botão direito **não** é do GNOME Shell. O DING roda como processo próprio
(`gjs .../ding@rastersoft.com/app/ding.js`) forçando `imports.gi.versions.Gtk = '3.0'`,
e monta um `Gtk.Menu` clássico em `desktopManager.js`:

```js
this._menu = new Gtk.Menu();
this._menu.get_style_context().add_class('desktopmenu');
```

Isso dá um gancho de CSS exclusivo: **`.desktopmenu`**. `fileItemMenu.js` usa a mesma
classe mais `fileitemmenu` no menu de clique direito sobre um ícone.

Consequência: o menu é estilizado por **CSS GTK3**, não por CSS do shell.

### Espaçamento e superfície do dock — Ubuntu Dock (St / CSS do shell)

Dock à esquerda, `custom-theme-shrink` ligado, ícones de 56 px. **Espaço entre ícones: 14 px**
(passo de 70 px, medido no print do dock).

O Ubuntu Dock com shrink põe `margin: 2px 0` em cada `.dash-item-container`; o padding de 6 px
do `.overview-icon` (Yaru) fica em volta do ícone. A extensão troca só a margem vertical do
container para `1px`: 56 + 12 + 2 = 70 px. O padding do `.overview-icon` fica no padrão para o
destaque de hover/foco não colar no ícone.

Medições que levaram a esse valor: margem `0` deu passo de 68 px (12 px de espaço) e padding
do ícone em 3 px deixou o dock apertado demais. Zerar o padding vertical do tile não mudou o
passo, por isso a regra foi removida.

O seletor do Ubuntu Dock tem especificidade (2,3,0); o da extensão acrescenta o tipo
(`StWidget.dash-item-container`, conferido em `dash.js` do `libshell-14.so`) para vencer sem
depender da ordem de carga das folhas. As regras `:first-child`/`:last-child` do Ubuntu Dock
(2,4,0) continuam zerando as pontas.

A superfície do dock é deliberadamente reta: as regras geral e específica de `.dash-background`
usam fundo contínuo `#1b1b1b`, `border: none`, `border-image: none` e `border-radius: 0`.
O dock usa agora `assets/dock-chassis.svg`: uma superfície retangular escura com laterais neutras
e brilho escuro discreto. Os pontos de execução junto aos ícones ficam ocultos; os acentos de
hover/foco permanecem somente nos ícones. O painel e os fundos dos ícones permanecem com
`border-radius: 0`; a linha contínua anterior não é aplicada.

O estado de carregamento da bateria é sincronizado nos dois ícones criados pelo GNOME Shell:
o `StIcon.quick-toggle-icon` do `.power-item` e o `StIcon.system-status-icon` do `.power-status`.
A extensão observa o `Gio.ThemedIcon` do `powerToggle`; nomes com sufixo `-charging-symbolic`
recebem o raio vermelho e um pulso de opacidade de 900 ms, sem alterar layout ou interação.

Para medir de novo, capture a tela e compare o topo de ícones consecutivos que ocupam 100% da
altura (Chrome, VS Code, Editor de Texto): a diferença é o passo, e passo − 56 é o espaço.

## Estratégia de aplicação

Duas camadas separadas, ambas dentro do HOME. Nenhum arquivo de `/usr/share` é tocado e
nenhum tema original é sobrescrito.

| Componente | Mecanismo | Instalado em |
|---|---|---|
| Notificação | extensão própria do shell com `stylesheet.css` | `~/.local/share/gnome-shell/extensions/forge-core-shell@forgecore.local/` |
| Dropdown de data/hora | mesma extensão, mesmo `stylesheet.css` | idem |
| Menu do desktop | CSS de usuário GTK3 importado pelo `gtk.css` | `~/.config/gtk-3.0/forge-core-desktop-menu.css` |

### Por que uma extensão e não um shell theme

Trocar o shell theme exigiria a extensão *User Themes* e substituiria o Yaru inteiro —
blast radius enorme para três componentes. O GNOME Shell carrega automaticamente o
`stylesheet.css` de qualquer extensão ativa (`extensionSystem.js::_loadExtensionStylesheet`),
**somando** ao tema em vez de substituí-lo, e descarrega ao desabilitar. É o único caminho
que é aditivo, reversível por switch e restrito ao usuário.

A extensão concentra apenas o blur dos popovers e o feedback do estado de carregamento; o dock
permanece somente em CSS, sem lógica ou overlay decorativo.

A ordem de busca é `ubuntu-dark.css` → `stylesheet-dark.css` → `ubuntu.css` → `stylesheet.css`.
Usamos só `stylesheet.css`: o Forge Core é uma identidade escura por definição e vale
igual nas duas variantes.

### Especificidade contra o Yaru

Folhas de extensão entram depois do tema, mas empate de especificidade é frágil. Por isso
todo seletor de notificação usa o composto `.notification-banner.message` (e, no dropdown,
o prefixo `.datemenu-popover`), que soma um ponto de classe a mais que o equivalente no Yaru:

| Yaru | Forge Core | Resultado |
|---|---|---|
| `.message .message-header` (0,2,0) | `.notification-banner.message .message-header` (0,3,0) | vence sem `!important` |

Único `!important` do arquivo: `.notification-button:focus`, porque o Yaru usa
`box-shadow: ... !important` no anel de foco laranja.

### Por que CSS de usuário GTK3 para o menu

O DING carrega o próprio CSS com `Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION` (600, dentro do
processo dele). `~/.config/gtk-3.0/gtk.css` entra com `GTK_STYLE_PROVIDER_PRIORITY_USER` (800),
que é maior que o do tema e do app — logo as regras Forge Core vencem por prioridade de
provider, independentemente de especificidade.

O `gtk.css` é global aos apps GTK3, mas **todo seletor é ancorado em `.desktopmenu`**, que só
o DING aplica. Menus de outros apps GTK3 continuam Yaru. Isso foi verificado (ver Testes).

O `gtk.css` recebe apenas um bloco delimitado:

```css
/* forge-core:begin */
@import url("forge-core-desktop-menu.css");
/* forge-core:end */
```

O `@import` fica no topo porque CSS exige `@import` antes de qualquer regra. O desinstalador
remove só esse bloco; se o arquivo já existia antes, ele é restaurado de backup.

## Desenho

Tokens usados (iguais aos do resto do Forge Core):

| Token | Valor | Uso |
|---|---|---|
| surface | `#252525` | fundo da notificação e do menu |
| surface-elevated | `#303030` | botões de fechar/expandir, estado `:active` |
| border | `#383838` | borda e separadores |
| text-primary | `#ffffff` | título, itens do menu |
| text-secondary | `#a6a6a6` | app de origem, corpo da notificação |
| text-muted | `#707070` | horário, itens desabilitados |
| accent | `#fc435a` | barra lateral, traços, hover |
| accent-hover | `#ff6478` | ícone simbólico, link, check marcado em hover |

### Notificação

- Barra vermelha de 3px na lateral esquerda (`border-left`), borda `#383838` nos outros lados.
- Cantos de 10px, sombra escura com viés vermelho: `0 6px 20px 2px rgba(36, 2, 8, 0.62)`.
  St aceita **uma** sombra por elemento — não dá para somar sombra escura + glow vermelho.
  O viés no RGB da sombra resolve os dois em uma declaração só.
- Hover do banner sobe para `#2b2b2b`, `:active` para `#303030`.
- Botões de ação: fundo branco 5%, hover translúcido `rgba(252, 67, 90, 0.2)`.
- Ícone simbólico ganha disco `rgba(252, 67, 90, 0.16)` com glifo `#ff6478`.

### Dropdown de data/hora

- Chassi: placa `#1b1b1b` chanfrada com parede dupla (`#383838` + `#252525`); o vermelho aparece
  só como duas linhas de energia nos cantos opostos. Mesma sombra da notificação.
- Módulos (calendário, eventos, relógios, tempo): placas `#252525` com chanfro assimétrico,
  hover `#303030`, ativo com contorno `#fc435a`. Sem vermelho em repouso.
- Data de hoje: leitura de HUD entre colchetes — dia da semana em Oxanium 600 1.5em branco,
  data em IBM Plex Sans 500 `#a6a6a6`. O estado `:insensitive` (hoje já selecionado) mantém
  as cores; só perde o hover.
- Tipografia: Oxanium em títulos de HUD (dia, mês com `letter-spacing: 2px`, títulos dos
  módulos, estado vazio); JetBrains Mono em dados numéricos (dias, cabeçalho dos dias, semanas,
  horários, temperaturas); IBM Plex Sans no resto, inclusive ações como
  "Adicionar relógios mundiais…".
- Calendário: células quadradas (raio 2px), hover `rgba(252, 67, 90, 0.16)`, selecionado com
  contorno interno `#fc435a` de 1px; **hoje** é a placa octogonal vermelha e não recebe o
  contorno de selecionado.
- Contraste: texto legível em `#a6a6a6` ou branco; `#707070` só nos dias de outro mês.
- Notificações da lista usam exatamente as mesmas regras do banner — os seletores são
  escritos em lista dupla (`.notification-banner.message` e `.datemenu-popover .message`)
  para não existirem duas fontes de verdade. Não foram alteradas nesta rodada.

### Menu do desktop

- Fundo `#252525`, borda `#383838`, raio 6px, padding 7px.
- Traços `#fc435a` de 1px: L nos quatro cantos (13px por braço) e um traço vertical de 18px
  no meio das bordas esquerda e direita a 50% de opacidade — mesma linguagem dos frames
  dos ícones do tema.
  Implementados como 10 camadas de `background-image` com `background-size` e
  `background-position` por camada. `background-origin` é `padding-box` (padrão CSS), então
  `left top` cai logo dentro da borda, e o raio de 6px é pequeno o bastante para os dois
  braços do L se encontrarem sem serem cortados pelo arco.
- Item: raio 6px, padding 6px/12px.
- Hover: `rgba(252, 67, 90, 0.18)` + barra `inset 2px 0 0 #fc435a` via `box-shadow`
  (inset dentro do item não desloca o texto, ao contrário de `border-left`).
- Desabilitado: `#707070`, sem fundo e sem barra.
- Separador: `#383838`, 1px, margem lateral de 8px.
- Check/radio marcados: `#fc435a` (`#ff6478` em hover).
- Estados `:backdrop` são declarados explicitamente. O Yaru pinta menu em backdrop com
  `#303030` e mata o hover; como o desktop raramente é a janela focada, sem isso o menu
  apareceria cinza e sem realce.

## Instalar

```bash
~/projetos/forge-core/scripts/install-shell.sh
```

O script: registra o estado anterior, copia a extensão, adiciona o UUID em
`enabled-extensions`, instala o CSS GTK3, insere o `@import` e reinicia o processo do DING.

Na **primeira** instalação o GNOME Shell precisa ser recarregado: ele varre o diretório de
extensões só na inicialização (`extensionSystem.js::_loadExtensions`), sem monitor de
arquivos. Em X11: `Alt+F2`, `r`, Enter. Em Wayland: logout/login.

## Atualizar

Editou o CSS? Rode o mesmo `install-shell.sh`. Ele é idempotente.

Para recarregar sem reiniciar o shell (a extensão já existe):

```bash
gnome-extensions disable forge-core-shell@forgecore.local
gnome-extensions enable  forge-core-shell@forgecore.local
```

Desabilitar descarrega o `stylesheet.css` e habilitar recarrega do disco.

Para o menu, o GTK3 lê `gtk.css` uma única vez, na inicialização do processo. Reinicie o DING:

```bash
pkill -f "ding@rastersoft.com/app/ding.js"
```

A extensão DING relança o processo sozinho em ~100ms.

## Restaurar

```bash
~/projetos/forge-core/scripts/uninstall-shell.sh
```

Volta ao Yaru-dark puro: desabilita e remove a extensão, tira o UUID de `enabled-extensions`,
remove o bloco do `gtk.css` (ou restaura o backup, se havia arquivo antes), apaga o CSS
instalado e reinicia o DING. `--keep-files` mantém os arquivos e só desliga.

Desligar sem desinstalar:

```bash
gnome-extensions disable forge-core-shell@forgecore.local   # notificação
```

Estado anterior fica em `~/.local/share/forge-core/shell-state.env` e o backup do `gtk.css`,
se existia, em `~/.local/share/forge-core/backup/gtk.css`.

## Desenvolver

Fontes no repositório:

```
gnome-shell/forge-core-shell@forgecore.local/
├── metadata.json
├── extension.js
├── stylesheet.css          <- notificação, dropdown, Quick Settings e dock
└── assets/
    ├── dock-chassis.svg     <- chassi retangular glossy do dock esquerdo
    └── dock-energy-rail.svg <- asset arquivado, não aplicado
gtk-3.0/
└── forge-core-desktop-menu.css   <- menu do desktop
```

Regra: **nunca confie em seletor de tutorial**. Confirme na versão instalada antes de usar,
com `gresource extract` no `libshell-14.so` (shell) ou lendo
`/usr/share/gnome-shell/extensions/ding@rastersoft.com/app/` (menu).

## Testar

### Notificação

```bash
notify-send "Forge Core" "Teste visual das notificações"
notify-send -i dialog-information "Forge Core" "Notificação com ícone"
notify-send "Forge Core" "$(printf 'Linha longa para verificar quebra de texto e altura do banner %.0s' 1 2 3)"
```

Conferir: fundo `#252525`, barra vermelha à esquerda, título branco, corpo `#a6a6a6`,
horário `#707070`, contraste sobre o wallpaper escuro, hover no banner e nos botões.

Erros de CSS do shell aparecem em:

```bash
journalctl --user -f -o cat | grep -iE "st-theme|css|stylesheet"
```

### Dropdown de data/hora

Clique no relógio no painel. Conferir: fundo do popover, cartão de hoje, hoje em vermelho no
calendário, hover nos dias, setas de mês, chave Não Perturbe em vermelho quando ligada,
botão `Limpar`, e as notificações da lista com a mesma barra vermelha do banner.

Com o dropdown aberto, o Quick Settings (canto superior direito) deve manter a moldura e os
controles Forge Core; o ícone de bateria deve mostrar o raio vermelho quando o notebook estiver
carregando.

### Quick Settings, bateria e dock

Abra o Quick Settings no canto superior direito. Conferir: o ícone de bateria com raio vermelho
quando o estado for `charging`, pulso suave sem deslocamento de layout e retorno ao estado normal
quando o carregador for removido. A barra superior e o ícone dentro do Quick Settings devem
permanecer sincronizados.

No dock à esquerda, conferir uma superfície vertical contínua, sem moldura, chanfros ou cantos
arredondados. Hover, foco, separador e espaçamento entre ícones devem continuar funcionando.

### Menu do desktop

Clique direito em área vazia do desktop. Conferir fundo, traços nos cantos, hover com barra
vermelha, item desabilitado (`Colar` sem nada na área de transferência), separadores e o
submenu `Ordenar por...`.

### Verificação sem mexer na tela

Dois utilitários em GJS validam a cascata GTK3 sem abrir menu nenhum: eles montam a mesma
estrutura de widget do DING e leem o estilo resolvido, e renderizam o menu numa superfície
cairo offscreen. Útil para confirmar isolamento — um `Gtk.Menu` sem a classe `desktopmenu`
deve continuar com os valores do Yaru.

Ponto mais importante confirmado por esse caminho: **o submenu herda a classe**. O widget
path resolvido é

```
window.popup menu.desktopmenu menuitem window.popup menu
```

porque `set_submenu()` chama `gtk_menu_attach_to_widget()`, e a janela do submenu herda o
path do item que a ancora. Por isso `menu.desktopmenu menu` casa.

## Escopo e efeitos colaterais

Fora de escopo e não tocados: overview, apps GTK, Nautilus e tela de login. Quick Settings,
bateria, dock e painel superior são estilizados pela extensão; o menu de contexto do desktop
continua na camada GTK3 do DING.

Dois pontos de compartilhamento merecem registro:

1. **`.desktopmenu` cobre os dois menus do desktop, de propósito.** `fileItemMenu.js` aplica
   `desktopmenu` + `fileitemmenu` no menu de clique direito sobre um ícone, então ele herda
   o mesmo visual do menu de fundo — que é o comportamento desejado: é o mesmo widget, da
   mesma extensão, no mesmo contexto. Verificado: `.desktopmenu.fileitemmenu` resolve para
   os mesmos valores. Se um dia for preciso separar os dois,
   `menu.desktopmenu:not(.fileitemmenu)` isola o menu de fundo.

2. **`.popup-menu-content` é compartilhado com todos os menus do painel** — Quick Settings
   inclusive. Nunca estilizar essa classe sozinha. Todas as regras do dropdown usam o
   composto `.popup-menu-content.datemenu-popover` ou o prefixo `.datemenu-popover`, que só
   existem no menu de data/hora. O mesmo vale para `.message` e `.toggle-switch`, que são
   usados também fora do dropdown.

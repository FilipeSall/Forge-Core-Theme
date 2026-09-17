# Forge Core — GNOME Shell e menu do desktop

Cobre quatro componentes: o **banner de notificação**, o **dropdown de data/hora**
(calendário + lista de notificações), o **menu de contexto do desktop** (botão direito na
área de trabalho, e também sobre um ícone) e o **toggle de tema Yaru ↔ Forge Core** no
Quick Settings.

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

### Chassi flutuante do dock — Ubuntu Dock (St / CSS do shell)

Dock à esquerda, `dock-fixed`, altura cheia, ícones de 48 px, encostado na borda. A extensão não
toca nos ícones: troca apenas o chassi em volta deles, o espaçamento e os estados.

Chaves do `org.gnome.shell.extensions.dash-to-dock` aplicadas pelo `install-shell.sh`:

| Chave | Valor | Motivo |
|---|---|---|
| `dash-max-icon-size` | `56` | medida-base do desenho |
| `extend-height` | `true` | o dock ocupa 100% da área de trabalho; o trilho central estica e empurra o launcher para a base |
| `custom-theme-shrink` | `false` | elimina o bloco `.left.shrink`, que duplicaria toda a matriz de seletores |
| `height-fraction` | `1.0` | ignorado com `extend-height`, mantido coerente |
| `running-indicator-style` | `DEFAULT` | `DOTS` desenha os pontos numa `St.DrawingArea` e não pode ser escondida por CSS |

**Geometria**, em coordenadas do monitor primário:

| Elemento | Valor |
|---|---|
| chassi | 88 px de largura, `[0, 88]`, encostado na borda esquerda |
| altura | 100% da área de trabalho (abaixo do painel, até a base da tela) |
| `.overview-icon` | 60x60 (`padding: 2px` em volta do ícone de 56) |
| `.overview-tile` | 88x60 (`padding: 0 14px`) |
| gap vertical | 16 px (`margin: 8px 0` no `.dash-item-container`) |
| acabamento do topo | 8 px (`padding-top` do `#dashtodockDashContainer`) |
| base do launcher | 88x88 (`padding: 14px` no `.show-apps`) |

**A largura do chassi é derivada, não escolhida.** Ela sai de
`.overview-icon + 2 × padding do tile`, mais a folga que a cadeia do `StScrollView` às vezes
acrescenta entre o `#dashtodockDashContainer` e os tiles — que já foi de 4 px com ícones de 48 px e
é zero com os atuais de 56 px. Todo arquivo do dock tem que ter exatamente a largura do nó em que é
aplicado, então **ao mexer no tamanho do ícone, meça o chassi de novo** (perfil de pixel numa linha
do trilho: as bordas `#383838` marcam as extremidades) e reajuste a largura dos SVGs.

Regra de composição que evita o problema se espalhar: **só o `border-image` do chassi desenha
borda, cantos e canais**, e ele mora no `.dash-background`, que ocupa a largura inteira. Os
arquivos aplicados sobre nós menores desenham apenas o miolo — a placa da base
(`dock-cap-bottom.svg`) é só o alojamento circular, sem borda nem cantos próprios.

**Três regiões.** O topo é fixo, o centro é elástico e a base é fixa:

1. `.dash-background` carrega `assets/dock-chassis-frame.svg` como `border-image` com fatias
   `8 10 120 10`. A fatia de topo (8 px: a borda `#383838` e os emissores vermelhos onde os canais
   de energia começam) é desenhada uma vez no topo, sem deformar; o resto do arquivo é a seção do
   trilho, uniforme no eixo Y, e o St a estica/repete até o fim do dock — o centro cresce com a
   quantidade de ícones sem distorcer nada. O topo é reto e o acabamento ocupa só 8 px, para o
   primeiro ícone ficar colado no alto.
2. A base é `assets/dock-cap-bottom.svg` aplicado como `background-image` do único
   `.dash-item-container` filho direto do `#dashtodockDashContainer` — o botão Mostrar
   aplicativos. Esse nó tem 88x88 fixos, exatamente o tamanho do arquivo, e desenha só o
   alojamento circular em volta do ícone do Ubuntu. Como o dock tem altura cheia, o `StScrollView`
   absorve a folga e essa base fica colada na borda de baixo da tela; entre o último ícone e
   ela sobra o trilho esticado, com os canais de energia correndo até embaixo.
3. Os estados (`dock-hover-plate.svg`, `dock-indicator-running.svg`,
   `dock-indicator-focused.svg`, `dock-trash-separator.svg`) também são `background-image` em nós
   de tamanho fixo e idêntico ao do arquivo.

**Separador preso à lixeira.** O separador do próprio Ubuntu Dock (`.dash-separator`) é zerado,
porque ele fica entre os grupos "favoritos/em execução" e "volumes montados + lixeira" — quando um
volume é montado, o traço deixa de ficar em cima da lixeira. No lugar dele, o traço é
`background-image` do `.dash-item-container:last-child` do `#dashtodockBoxContainer`, e a lixeira é
sempre o último item (`dash.js` faz `newApps.push(trashApp)` depois dos volumes). Assim o traço
acompanha a lixeira qualquer que seja a quantidade de ícones.

O arquivo tem 88x94, a altura exata do nó: 14 px de `padding-top` mais os 80 px que o
`.dash-item-container` da lixeira reserva para um tile de 60 px. Como imagem de fundo é
centralizada, **essa altura precisa bater**; ao mexer no tamanho do ícone, meça o nó de novo
(uma `background-color` de depuração na mesma regra mostra a caixa) e refaça o arquivo. Se
`show-trash` for desligado, o traço passa a ficar sobre o último item existente.

**Como o St trata imagem de fundo** (verificado nesta máquina, GNOME Shell 46, com folhas de
teste e medição de pixel; vale para qualquer CSS da extensão):

- `background-repeat` é ignorado. Toda `background-image` repete nos dois eixos.
- A imagem é **centralizada** no nó, não ancorada no canto. Num nó de 84 px com imagem de 80 px
  a imagem cai em `+2` e as bordas do arquivo aparecem duplicadas por causa da repetição.
- Consequência: `background-image` só serve quando o nó tem tamanho fixo e igual ao do arquivo.
  Para região elástica, use `border-image` (fatias em px; porcentagem não é aceita).
- `background-size` aceita `auto`, `contain` e `cover`; percentuais (`100% 100%`) não.
- `border-image` **é** 9-slice padrão: os quatro cantos saem em tamanho natural, as bordas
  esticam ao longo do próprio eixo e o miolo estica nos dois. Medido em 2026-09-17 com um SVG
  de bandas coloridas aplicado no `#panel` e perfil de pixel.
- **Use sempre a forma de um valor só** (`border-image: url(x.svg) 16`). Com quatro valores
  (`4 16 4 16`) a fatia da **esquerda** sai esticada — num `#panel` de 1920 px uma fatia de
  16 px foi desenhada com 104 px. Topo, direita e base saíram corretos. Medido no mesmo teste.
  Como os arquivos do Forge são uniformes no eixo que não tem detalhe, um valor único basta.
- O `border-width` **não** entra na conta: as fatias são desenhadas no tamanho natural mesmo com
  `border: none`. Logo o `border-image` não reserva espaço de layout.
- Truque das duas linhas de folga: para um nó cuja altura pode mudar (o painel é `2.2em`), o
  arquivo tem 34 px e as fatias 16/16. Com o painel em 32 px o miolo tem altura zero e o desenho
  sai 1:1; se a altura mudar, só as duas linhas centrais — deliberadamente uniformes — esticam.

**Seletor com duas classes encadeadas mais pseudo-classe não casa.** `StWidget.panel-button.clock-display`
funciona, `StWidget.panel-button.clock-display:hover` **não** — a regra é simplesmente ignorada.
Confirmado trocando por `StWidget.clock-display:hover`, que passou a valer no mesmo instante.
Quando precisar de estado num nó que já é alvo de uma regra genérica, use **uma** classe e
`!important` (qualquer `!important` vence qualquer regra sem `!important`, independente de
especificidade) em vez de encadear classes.

**Especificidade.** O bloco `.left` do Ubuntu Dock tem (2,3,0) e (2,4,0); o Yaru usa
`box-shadow: ... !important` no anel de foco. As regras de geometria do dock usam `!important`
(o Ubuntu Dock não usa nenhum), o que também resolve o empate com a extensão
`forge-core-dock-spacing@sea`, que ainda põe `margin: 6px 0` no `.dash-item-container`.
As regras ancoradas em `#dashtodockDashContainer >` vencem por id, sem `!important`.

**O dock não tem mais cap no topo.** `dock-chassis-frame.svg` virou um trilho uniforme no eixo Y:
paredes `#383838`, rebaixos `#111111`, canais `#fc435a` e corpo, e nada mais. Quem fecha a coluna
em cima agora é o **header** — a cabeça da coluna é desenhada dentro da barra superior e a seção
atravessa a fronteira sem emenda (ver *Barra superior*). Por isso as fatias caíram para
`border-image: … 10` (um valor só) e os emissores vermelhos que ficavam no topo do dock foram
movidos para dentro da cabeça, no header.

O botão Atividades continua deslocado (`margin-left: 10px`) para ficar centralizado na coluna de
88 px. O valor é medido — se a largura do chassi mudar, refaça a conta.

**Estados.** Normal: só o chassi, sem placa atrás do ícone. Hover: `.overview-icon` em `#303030`
com a placa `dock-hover-plate.svg` (borda `#383838` e dois ganchos vermelhos), transição de
150 ms. Rodando: barra vermelha curta no canal de energia esquerdo. Foco: barra mais longa e
mais clara, e `.overview-icon` em `#252525` — o vermelho nunca envolve o ícone. Os pontos de
execução do GNOME ficam zerados e invisíveis.

O estado de carregamento da bateria é sincronizado nos dois ícones criados pelo GNOME Shell:
o `StIcon.quick-toggle-icon` do `.power-item` e o `StIcon.system-status-icon` do `.power-status`.
A extensão observa o `Gio.ThemedIcon` do `powerToggle`; nomes com sufixo `-charging-symbolic`
recebem o raio vermelho e um pulso de opacidade de 900 ms, sem alterar layout ou interação.

Para medir de novo, capture a tela e compare o topo de ícones consecutivos que ocupam 100% da
altura (Chrome, VS Code, Editor de Texto): a diferença é o passo, e passo − 56 é o espaço.

### Barra superior — GNOME Shell (St / CSS do shell)

O header é a **peça horizontal do mesmo chassi do dock**. Não é "barra preta com linha vermelha":
é a mesma seção industrial do trilho vertical, girada, com a cabeça da coluna desenhada dentro
dela. Olhando a tela inteira lê-se **uma estrutura em L**, não um dock mais uma top bar.

**Geometria medida** (monitor primário, 96 dpi, fonte 11 pt):

| Elemento | Valor |
|---|---|
| altura do painel | 32 px (`height: 2.2em` do Yaru; o `border-bottom` antigo somava 1 px e foi removido) |
| junção (`#panelLeft`) | 96 px: 88 px de cabeça de coluna + 8 px de trilho |
| coluna do dock | 88 px, começando em `y = 32` |
| fatia direita do trilho | 16 px |

**Seção do trilho** (32 linhas, de cima para baixo). É a mesma gramática do dock — parede,
canal de energia, rebaixo, corpo — só que o header tem uma borda livre (a de baixo) e a de cima
é a borda da tela, por isso o empilhamento é assimétrico:

| Linha | Cor | Papel |
|---|---|---|
| 0 | `#383838` | parede externa (topo) |
| 1–2 | `#2b2b2b` / `#222222` | chanfro de luz |
| 3 | `#111111` | rebaixo interno |
| 4–26 | gradiente `#262626` → `#1d1d1d` → `#212121` | corpo; é aqui que ficam texto e ícones |
| 27–28 | `#111111` | rebaixo interno |
| 29–30 | `#5f272e` | canal de energia |
| 31 | `#383838` | parede externa (base) |

O corpo do trilho foi calibrado contra o dock: a média do gradiente tem que ficar perto da média
da seção transversal do dock (≈ 32), senão a viga horizontal lê mais escura que o montante e as
duas param de parecer a mesma peça. Foi medido nos dois — dock em `y` livre de ícone, header em
`x` livre de módulo.

O canal é uma **cor sólida**, não `#fc435a` com opacidade: `#5f272e` é exatamente o que o filamento
do dock produz na tela (`rgb(94,42,48)`, medido). Declarar a mistura pronta garante paridade de
brilho entre o canal horizontal e os verticais sem depender de como o rsvg antialiasa a fatia.
Se mexer num, refaça a medida do outro.

**Junção.** `header-junction.svg` tem 96 px e é aplicado no `#panelLeft` com `min-width: 96px`.
Como a largura do nó é igual à do arquivo, o 9-slice sai **1:1** e cada pixel cai no lugar. Os
88 px da esquerda repetem a seção transversal do dock **na mesma coordenada** — paredes em
`x 0–1` e `x 86–87`, rebaixos em `x 7–8` e `x 79–80`, canais em `x 3–6`/`x 81–84` com filamento
em `x 4,3` e `x 82,3`. O resultado é que a emenda header/dock **não existe em pixel**: uma coluna
de imagem lida em `y = 30` é idêntica à mesma coluna em `y = 34`.

A coluna é **aberta embaixo** (não tem parede de base entre `x 0` e `x 88`) e **fechada em cima**
pela parede `#383838` da linha 0: a estrutura nasce na borda da tela e desce até o fim do dock.
O rebaixo da cabeça forma um colchete com cantos chanfrados a 3,5 px, e os canais vermelhos só
começam em `y = 8` com uma cabeça mais clara (o emissor que antes ficava no topo do dock).

Nos 8 px restantes (`x 88–95`) começa o trilho horizontal, e é ali que mora o único detalhe
vermelho da conexão: o canal entra em `#8c2f3b` encostado na parede da coluna e cai para
`#5f272e` até `x = 96`. Energia entrando na viga a partir do montante.

**Módulos.** Relógio e área de status são a **mesma peça** (`header-bay.svg`), uma baia rebaixada
encaixada no chassi: placa `#131313` → `#191919` com chanfro de 6 px nas pontas, contorno
`#383838`, sombra interna `#0e0e0e` no lábio de cima, luz `#2c2c2c` no de baixo e um filamento
vermelho vertical de 1,4 px em cada extremidade — o mesmo traço dos canais do dock.

| Nó | Arquivo | Quando |
|---|---|---|
| `#panelRight` | `header-bay.svg` | sempre (agrupa appindicators, teclado e Quick Settings) |
| `StWidget.clock-display` | `header-bay.svg` / `-hover` / `-active` | relógio, por estado |
| `.panel-button` | `header-cell.svg` | `:hover` |
| `.panel-button` | `header-cell-active.svg` | `:focus`, `:active` (menu aberto), `:checked` |

A célula (`header-cell*.svg`) é menor que a baia de propósito: um botão em hover acende **dentro**
do módulo, sem competir com ele. A variante ativa ganha uma barra `#fc435a` na base — é o indicador
de "menu aberto" e também o anel de foco de teclado, já que o anel laranja do Yaru foi zerado.

Todos os arquivos de módulo têm 48×34 e usam `border-image: … 16`: as pontas saem em tamanho
natural e o miolo — uniforme no eixo X — estica. Por isso a baia do relógio (168 px) e a da
bandeja (224 px) saem do mesmo arquivo sem distorção, e a barra funciona em qualquer largura.

**Nada vira imagem.** Todos os controles continuam sendo os widgets do GNOME; os SVGs entram só
como `border-image`. Clique, menus, tooltips, navegação por teclado e os ícones de rede, áudio,
bateria e Bluetooth ficam intactos — nenhum ícone de status é recolorido.

**Tela de bloqueio.** Em `unlock-screen`/`login-screen` o `#panelLeft` perde a junção
(`min-width: 0; border-image: none`): sem dock embaixo, uma cabeça de coluna solta não faria
sentido. O trilho e as baias continuam.

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

### Alternância completa Yaru ↔ Forge Core

O toggle `Tema` controla a identidade inteira, não apenas o `icon-theme`:

| Forge Core ativo | Yaru ativo |
|---|---|
| `stylesheet.css` do Forge carregado no GNOME Shell | stylesheet do Forge descarregado; Yaru volta a desenhar menus e dropdowns |
| `gtk.css` importa `forge-core-desktop-menu.css` | import do menu Forge removido |
| ícones do painel/Quick Settings (bateria, rede, volume e Bluetooth) e cursor `Forge-Core` | ícones do painel/Quick Settings e cursor `Yaru` |
| rotator de wallpaper, watcher de launchers e timer de pastas ativos | autostart, watcher e timer desabilitados e parados |
| background Forge preservado | background anterior restaurado (ou default do GNOME se não houver backup) |

Ao voltar para Forge, o background atual do Yaru é salvo, o estado de rotação anterior é
invalidado e uma nova imagem é aplicada imediatamente. O rotator também verifica o modo e
o background atual antes de cada ciclo; portanto, mesmo se for iniciado pelo autostart durante
o login, ele encerra imediatamente em Yaru e corrige um fundo Yaru residual ao entrar no Forge.

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
├── stylesheet.css          <- notificação, dropdown, Quick Settings, header e dock
└── assets/
    ├── header-rail.svg             <- seção horizontal do chassi (border-image do #panel)
    ├── header-junction.svg         <- cabeça da coluna + entrada do trilho (#panelLeft, 96 px)
    ├── header-bay.svg              <- baia rebaixada: relógio e área de status
    ├── header-bay-hover.svg        <- baia do relógio em hover
    ├── header-bay-active.svg       <- baia do relógio com o menu aberto
    ├── header-cell.svg             <- célula de hover de um panel-button
    ├── header-cell-active.svg      <- célula de foco / menu aberto, com barra vermelha
    ├── dock-chassis-frame.svg      <- border-image do chassi: trilho uniforme, sem cap
    ├── dock-cap-bottom.svg         <- base mecânica com alojamento do launcher
    ├── dock-hover-plate.svg        <- placa de hover atrás do ícone
    ├── dock-indicator-running.svg  <- barra do app em execução
    ├── dock-indicator-focused.svg  <- barra do app em foco
    ├── dock-trash-separator.svg    <- traço acima da lixeira
    └── dock-energy-rail.svg        <- asset arquivado, não aplicado
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

O primeiro item é o toggle `Tema`. Desligado, ele usa o Yaru completo; ligado, usa o Forge
Core, força `Yaru-dark` + `prefer-dark` e oculta o toggle nativo `Dark Style`. Ao voltar para
Yaru, a aparência anterior é restaurada, o background Forge e suas automações são parados,
e `Dark Style` reaparece. A escolha fica registrada em
`~/.local/share/forge-core/icon-theme-mode`, para que uma troca externa de aparência não
desative o Forge Core silenciosamente.

No dock à esquerda, conferir: chassi encostado na borda ocupando toda a altura, cap superior com a alça branca
sem deformação, canais vermelhos discretos nas laterais, barra vermelha à esquerda dos apps em
execução, placa de hover, separador acima da lixeira e o botão do Ubuntu encaixado no alojamento
circular da base. Abrir e fechar aplicativos: o centro cresce e encolhe sem esticar os caps.
Clique, clique direito, arrastar e soltar e tooltip continuam funcionando.

### Barra superior

Olhe a quina onde o dock encontra a barra: a emenda não pode existir. Confirme por pixel, não a
olho — recorte a coluna `x = 4` (o filamento vermelho) e compare `y = 30` com `y = 34`; os dois
têm que dar `rgb(94,42,48)`. O mesmo vale para `x = 0/1`, `x = 7/8`, `x = 79/80` e `x = 86/87`.

Depois: passe o mouse no relógio (a baia clareia), clique (a baia acende e ganha barra vermelha na
base), abra o Quick Settings (a célula acende **dentro** da baia da bandeja), e confira que rede,
áudio, bateria e Bluetooth continuam com a cor e a forma de sempre. Abra a Visão geral — o chassi
continua igual e a junção segue alinhada.

Para largura diferente sem trocar de máquina, mova o monitor primário e volte:

```bash
xrandr --output HDMI-A-0 --primary   # painel vai para a tela menor
xrandr --output eDP --primary        # volta
```

A junção tem que sair nos mesmos 96 px e a emenda continuar invisível; só o trilho do meio muda
de comprimento.

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

Fora de escopo e não tocados: tela de login e o tema global do sistema. Quick Settings, bateria,
dock e barra superior são estilizados pela extensão — na Visão geral o chassi do header é mantido
de propósito, para a estrutura em L não sumir ao abrir o overview; o menu de contexto do
desktop continua na camada GTK3 do DING. A alternância também remove o overlay GTK3 do Forge
e controla os automatismos de wallpaper, launchers e pastas.

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

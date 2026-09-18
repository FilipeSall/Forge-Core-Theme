# Forge Core — interior do Nautilus

Redesenho do interior da janela do Nautilus (GNOME 46 / GTK 4.14 / libadwaita 1.5):
chassi, barra lateral, área de arquivos e ícones simbólicos da lateral.

A identidade completa está em [`identidade-visual.md`](identidade-visual.md).

## Conceito

A janela é **uma máquina dividida em dois módulos**. O trilho superior é o mesmo
trilho da barra do GNOME Shell (`assets/header-rail.svg` da extensão): topo com
fio metálico `#383838`, corpo `#262626 → #1d1d1d → #212121` e, na base, a junta
`#111111` + `#5f272e` + `#383838`. Abaixo dele, dois módulos encaixados —
a barra lateral e a área de conteúdo — separados por um trilho vertical de três
fios (`#121212` / `#2b2b2b` / `#383838`), a mesma junta que o
`header-junction.svg` desenha no Shell.

### Regra do vermelho

> O vermelho marca **onde o sistema está**, não o que está selecionado.

- item ativo da lateral, aba ativa, botão `:checked`, `current-dir`: `#fc435a`;
- seleção de arquivos: placa `#303030` + fio `#525252`, **sem vermelho** —
  selecionar 200 arquivos não acende 200 luzes;
- foco de teclado: contorno `#fc435a` a 70%;
- detalhe vermelho dos ícones da lateral: `#a83e4b` parado, `#c8404e` no hover,
  `#fc435a` no item ativo. O acento só atinge energia plena onde há atividade.

### Camadas

| Camada | Valor |
|---|---|
| chassi da janela | `#1b1b1b` |
| trilho / cabeçalho | `#262626 → #1d1d1d → #212121` |
| junta (seam) | `#111111` · `#5f272e` · `#383838` |
| placa da lateral | `#272727 → #202020` |
| baia de conteúdo | `#232323 → #1f1f1f` (≈ `#212121`) |
| hover | `#2b2b2b` (lateral) · `#292929` (grade) |
| selecionado / elevado | `#303030` |
| baia embutida (pathbar, entry) | `#131313 → #191919` |
| acento | `#fc435a` |

Raio de canto: `2px` em toda a janela (mesma medida do menu de contexto do
desktop em `gtk-3.0/`), no lugar dos 6–12 px do Adwaita.

## Mecanismo

`gtk-4.0/forge-core-nautilus.css` é embutido no `gtk.css` do usuário pelo mesmo
caminho já usado pelas miniaturas de pasta — `folder_chooser_icons.install_nautilus_css()`,
descrito em [`folder-chooser-icons.md`](folder-chooser-icons.md). Instalar e
remover acompanham o tema ativo: sair do `Forge-Core` apaga o bloco do `gtk.css`.

**Escopo.** `~/.config/gtk-4.0/gtk.css` vale para todo aplicativo GTK 4. Por isso
toda regra é ancorada em `window.view` — o `NautilusWindow` é o único `window`
com a classe `.view` (ele a declara no próprio template). Diálogos de arquivo de
outros aplicativos usam os mesmos nós (`placessidebar`, `.sidebar-row`,
`gridview`) e **não** são afetados. Verificado com o Editor de Texto e com o
seletor "Abrir arquivo" do portal.

**Sem assets.** Todo o desenho é CSS (gradientes com paradas em px e
`box-shadow` inset), não SVG. Fios de 1 px ficam nítidos em qualquer altura de
linha e em qualquer escala de tela; um `border-image` esticado não fica.

Duas armadilhas do GTK 4.14 encontradas no caminho:

- `box-shadow` inset é pintado na **ordem inversa** do CSS: a última sombra fica
  por cima. O trilho vertical lista a mais larga primeiro.
- `letter-spacing` não entra na medição do rótulo: o `AdwWindowTitle` corta o
  texto. O título "ARQUIVOS" usa Oxanium sem `letter-spacing`.

O GTK só lê o `gtk.css` na inicialização do processo — depois de editar, rode
`nautilus -q` e reabra a janela. Não há recarga a quente.

## Ícones simbólicos da lateral

Gerados por `scripts/build-symbolic-icons.py` junto com o resto da família
simbólica (formas preenchidas, porque o GTK só recolore `fill`; o vermelho entra
pela classe `error`, tingida via `-gtk-icon-palette`):

| Linha | Nome freedesktop | Contexto |
|---|---|---|
| Recentes | `document-open-recent-symbolic` | `actions` |
| Favoritos | `starred-symbolic` | `status` |
| Pasta pessoal | `user-home-symbolic` | `places` |
| Área de trabalho | `user-desktop-symbolic` | `places` |
| Documentos | `folder-documents-symbolic` | `places` |
| Downloads | `folder-download-symbolic` | `places` |
| Imagens | `folder-pictures-symbolic` | `places` |
| Músicas | `folder-music-symbolic` | `places` |
| Vídeos | `folder-videos-symbolic` | `places` |
| Lixeira | `user-trash-symbolic`, `user-trash-full-symbolic` | `places` |

Desenhados em 16×16 com polígonos chanfrados, como o resto da família. Como são
nomes padrão do freedesktop, valem também para a lateral do seletor de arquivos
GTK enquanto o `Forge-Core` estiver ativo — é a consistência desejada.

**"Outros locais" continua com o `+` do sistema.** A linha usa
`list-add-symbolic`, o mesmo nome de todo botão "adicionar" do GNOME.
Sobrescrevê-lo no tema trocaria o `+` de todos os aplicativos. A identidade
Forge Core chega nessa linha pela cor (`color` e `-gtk-icon-palette` da lateral),
não por troca de arte.

Depois de mexer no gerador:

```bash
python3 scripts/build-symbolic-icons.py   # -> assets/icons/symbolic/
python3 scripts/build-icons.py            # -> icon-theme/Forge-Core/scalable/
./scripts/install-icons.sh                # -> ~/.local/share/icons
```

## Separar arquivos ocultos — não implementado

O pedido era quebrar a grade em duas regiões quando "mostrar arquivos ocultos"
está ligado: conteúdo normal acima, dotfiles abaixo, com um divisor.

Não há caminho sustentável no Nautilus 46:

- **CSS não serve.** O GTK não expõe nenhuma classe, estado ou pseudo-classe
  para "arquivo oculto" — `standard::is-hidden` fica no `GFileInfo`, nunca chega
  ao nó CSS. Não há como sequer esmaecer os dotfiles, muito menos reordená-los.
- **Extensão não serve.** `libnautilus-extension4` oferece
  `ColumnProvider`, `InfoProvider`, `MenuProvider` e `PropertyPageProvider`.
  Nenhuma delas alcança o modelo (`NautilusViewModel`), o `GtkSorter` ou o
  cabeçalho de seção da view.
- **Seções do GTK não estão em uso.** `GtkGridView`/`GtkListView` suportam
  `GtkSectionModel` desde o GTK 4.12, mas o Nautilus 46 não usa cabeçalho de
  seção nem expõe o modelo.
- **Preferência não existe.** `org.gnome.nautilus.preferences` tem
  `show-hidden-files` e `default-sort-order`; nada sobre agrupar dotfiles.

Restariam duas opções tecnicamente corretas, ambas fora do escopo de um tema:

1. **Patch no Nautilus** (`NautilusViewModel` + `GtkSectionModel` + factory de
   cabeçalho) e distribuir um pacote próprio — quebra a cada atualização do
   `nautilus`.
2. **Extensão com `NautilusColumnProvider`** publicando um atributo de seção e
   deixando o usuário ordenar por essa coluna. Funciona só na visão em lista,
   adiciona uma coluna e não desenha divisor nenhum.

Nada foi implementado. `hidden-section-divider.svg` do pacote de assets fica sem
uso enquanto isso. O restante do redesenho não depende disso.

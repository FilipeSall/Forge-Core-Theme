# Forge Core — Floating Dock Asset Pack

Este pacote contém os assets necessários para reproduzir o conceito de dock/menu lateral flutuante Forge Core sem substituir os ícones dos aplicativos.

## Arquivos

- `01-dock-top-cap.svg` — peça superior fixa.
- `02-dock-center-rail.svg` — chassis central; pode repetir no eixo Y.
- `03-dock-bottom-cap.svg` — peça inferior fixa, com alojamento do botão Ubuntu/launcher.
- `04-active-indicator.svg` — indicador de aplicativo ativo.
- `05-separator.svg` — separador opcional.
- `06-hover-plate.svg` — placa de hover/foco opcional atrás de um ícone.
- `07-reference-preview.svg` — preview estrutural sem ícones de aplicativos.
- `forge-core-dock-tokens.css` — tokens sugeridos.
- `CLAUDE-CODE-IMPLEMENTATION-PROMPT.md` — prompt pronto para implementação.

## Medidas-base

- largura do dock: 80 px;
- ícones: 48 px;
- gap vertical: 8 px;
- padding horizontal: 10 px;
- top cap: 118 px de altura;
- bottom cap: 138 px de altura.

As medidas devem ser tratadas como referência, não como valores rígidos. A implementação deve respeitar escala do GNOME, resolução e quantidade de ícones.

## Regra estrutural

Não use uma imagem PNG única como fundo do dock.

Monte o visual em três regiões:

1. topo fixo;
2. centro elástico/repetível;
3. base fixa.

O centro pode crescer sem deformar os detalhes mecânicos do topo e da base.

## Paleta

- `#1b1b1b` background;
- `#252525` surface;
- `#303030` elevated;
- `#383838` border;
- `#fc435a` accent;
- `#ff6478` accent hover.

O vermelho é energia/estado ativo, nunca a superfície dominante.

## Ícones

Os ícones existentes não devem ser substituídos nem redesenhados. O dock apenas cria chassis, espaçamento, hover, estados e indicadores ao redor deles.

# Forge Core — carregamento da bateria e dock reto

## Contexto

O estado de carregamento do notebook não tem feedback visual suficiente: o ícone atual pode ser confundido com bateria baixa. O dock lateral também está usando uma moldura chanfrada, mas deve ser uma superfície reta, sem bordas.

## Design aprovado

## Refinamento visual aprovado

- Manter o dock sem `border`, `border-radius` e `border-image`.
- Adicionar `assets/dock-energy-rail.svg` como um trilho interno de energia: núcleo vermelho fino,
  halo médio translúcido e pequenas terminações luminosas.
- Aplicar o asset apenas ao dock vertical esquerdo, usando `background-image` no fundo que
  acompanha os itens; dimensionar o trilho de ponta a ponta para começar no primeiro item e
  terminar no último. Não criar uma moldura ao redor da superfície e não alterar os ícones,
  hover ou espaçamento.
- Usar a paleta Forge Core existente (`#fc435a`, `#ff6478`, `#1b1b1b`) sem introduzir neon
  ciano, roxo ou gradientes CSS.

## Refinamento do trilho retirado

O trilho neon foi removido da instalação atual a pedido do usuário. O dock permanece reto,
sem bordas, sem separadores extras e sem `dock-energy-rail.svg` aplicado. Novas direções visuais
serão escolhidas em uma rodada de brainstorming antes de qualquer novo código.

## Novo refinamento aprovado — cápsula industrial sem fundos arredondados

- Usar uma superfície vertical escura glossy com `assets/dock-chassis.svg`, sem `border-radius` no
  painel e sem fundos arredondados nos ícones.
- Remover qualquer acento vermelho da borda externa do chassi; manter as laterais neutras e um
  brilho escuro discreto.
- Manter os acentos de hover/foco somente nos ícones, sem tinta vermelha colada nas laterais.
- Manter um separador metálico reto entre grupos e aumentar o tamanho do dock para 56px, alinhando
  a densidade visual à referência fornecida.
- Preservar hover, foco, interação e o indicador de carregamento da bateria.

### Estado de carregamento

- Manter o ícone simbólico `battery-level-*-charging-symbolic` como sinal primário.
- Usar um raio vermelho Forge Core visível dentro da bateria.
- Localizar no GNOME Shell 46 `Main.panel.statusArea.quickSettings._system._systemItem.powerToggle` e o indicador irmão `_system._indicator`.
- Observar `notify::gicon` em `powerToggle` e considerar carregando quando um nome retornado por `powerToggle.gicon.get_names()` terminar em `-charging-symbolic`.
- Aplicar `forge-core-battery-charging` ao `powerToggle._icon` (nó `StIcon.quick-toggle-icon` dentro de `.power-item`) e ao indicador `quickSettings._system._indicator` (nó `StIcon.system-status-icon` dentro de `.power-status`).
- Iniciar o carregamento sem a classe de pulso e alternar `forge-core-battery-charge-pulse` a cada 900 ms, com `transition-duration: 900ms` e opacidade reduzida para aproximadamente 0,68 durante o pulso.
- Manter no máximo um temporizador por ciclo da extensão; ao recarregar, remover o temporizador anterior antes de criar outro.
- Ao sair de carregando, remover as duas classes de estado e restaurar opacidade total; ao ficar sem bateria, fazer o mesmo. `battery-level-100-charged-symbolic` é estado carregado, não pulsante; `battery-missing-symbolic` não recebe classes.
- Limpar conexões e temporizador ao desabilitar a extensão.

### Dock lateral

- Sobrescrever as regras geral e específica do dock (`#dashtodockContainer #dash .dash-background` e `#dashtodockContainer.left #dash .dash-background`) com `background-color: #1b1b1b`, `border: none`, `border-image: none` e `border-radius: 0`.
- O dock ativo não possui overlay ou asset decorativo: a regra específica mantém somente a
  superfície Forge Core reta e sem moldura.
- Deixar de referenciar `dock-plate.svg`; manter o arquivo de asset no projeto para preservar reversibilidade e não apagar arte não utilizada nesta rodada.
- Remover as bordas de início/fim que referenciam `dock-separator.svg`, para que não sobrem linhas
  pretas acima do primeiro item ou abaixo do último; preservar o separador entre grupos, estados
  de hover/foco dos aplicativos e espaçamento existentes.
- Não alterar o menu de contexto do desktop nem a moldura dos Quick Settings.

## Arquivos e fluxo

1. `scripts/build-symbolic-icons.py` é a fonte dos SVGs de bateria, incluindo os níveis efetivamente gerados `0, 10, 20, ..., 100`, com e sem `-charging`; a instalação executa o gerador antes de copiar o tema.
2. A geração atualiza `assets/icons/symbolic/status/` e `icon-theme/Forge-Core/scalable/status/` quando necessário.
3. `gnome-shell/.../extension.js` preserva a lógica existente de blur e observa o `Gio.ThemedIcon` já escolhido pelo GNOME Shell; não abre uma segunda conexão com UPower.
4. `gnome-shell/.../stylesheet.css` define os seletores `.quick-settings .quick-settings-system-item .power-item StIcon.forge-core-battery-charging` e `#panel .power-status StIcon.forge-core-battery-charging`, além do pulso e do dock reto, sem aplicar um trilho decorativo.
5. `scripts/install-icons.sh` e `scripts/install-shell.sh` aplicam as mudanças no ambiente do usuário.

## Falhas e reversibilidade

- Se o caminho do objeto de energia ou o `Gio.ThemedIcon` não estiver disponível, a extensão mantém o tema visual sem instalar observadores parciais.
- A fonte de verdade é o nome do ícone produzido pelo GNOME Shell: sem o sufixo `-charging-symbolic`, o estado é normal; com ele, é carregando. Isso mantém os dois pontos visuais sincronizados sem divergência entre duas fontes de energia.
- Eventos repetidos de `notify::gicon` apenas sincronizam o estado; não criam temporizadores extras nem reiniciam o pulso quando o estado não mudou.
- Se a conexão ou a sincronização falhar depois de parcialmente instalada, o caminho de limpeza remove conexões, temporizador e classes já adicionadas.
- Ao desabilitar a extensão, o temporizador é removido, as conexões são desconectadas e as classes adicionadas são limpas; o efeito de blur original também é mantido e removido pelo fluxo existente.
- O dock permanece com a superfície reta Forge Core durante a extensão e, ao desabilitar, a folha da extensão deixa de aplicar toda a regra dedicada ao dock; o asset `dock-plate.svg` permanece intacto.

## Validação

- Verificar a sintaxe de `extension.js`.
- Confirmar que os 11 SVGs para os níveis `0, 10, 20, ..., 100` de `battery-level-*-charging-symbolic` existem.
- Confirmar que existe no máximo um ID de temporizador de pulso enquanto a extensão está ativa.
- Recarregar a extensão e o DING.
- Conferir bateria normal, carregando, Quick Settings, barra superior, dock reto e hover dos aplicativos.
- Confirmar que o raio vermelho continua visível em todos os níveis de bateria e que o pulso não altera tamanho, alinhamento ou interação.
- Confirmar que nenhum trilho ou separador decorativo aparece no dock e que o fundo continua reto nos quatro lados.
- Se não houver estado CHARGING disponível durante o teste, validar a estrutura e nomes dos estados e deixar a instalação pronta para a próxima emissão do UPower.

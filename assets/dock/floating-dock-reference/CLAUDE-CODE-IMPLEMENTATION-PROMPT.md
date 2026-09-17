# Implementar dock/menu lateral flutuante Forge Core

<role>
Você é um engenheiro Linux/GNOME especializado em GNOME Shell, extensões, temas GTK/Shell, CSS e integração visual de desktop.
Seu objetivo é implementar, e não apenas sugerir, um novo dock/menu lateral flutuante para o projeto Forge Core.
</role>

<context>
Estou personalizando meu Linux com a identidade visual Forge Core.

O dock atual já possui os ícones corretos e eles NÃO devem ser substituídos, redesenhados ou alterados.
Quero alterar somente o chassis/menu que envolve os ícones: background, bordas, tamanho, padding, gap, hover, indicador de app ativo e acabamento superior/inferior.

A referência visual é um dock vertical estreito, flutuante, industrial e futurista:
- chassis preto/grafite;
- metal escuro;
- cantos e chanfros discretos;
- pequenos canais de energia vermelha;
- base mecânica ao redor do launcher/Ubuntu;
- acabamento superior com um pequeno detalhe branco;
- centro limpo e escalável;
- sem aparência RGB gamer;
- sem grandes superfícies vermelhas.

Paleta oficial:
- background: #1b1b1b
- surface: #252525
- surface-elevated: #303030
- border: #383838
- accent: #fc435a
- accent-hover: #ff6478

O vermelho representa energia/estado ativo e deve ser usado com moderação.
</context>

<assets>
Use os assets fornecidos neste diretório:

- 01-dock-top-cap.svg
- 02-dock-center-rail.svg
- 03-dock-bottom-cap.svg
- 04-active-indicator.svg
- 05-separator.svg
- 06-hover-plate.svg
- 07-reference-preview.svg
- forge-core-dock-tokens.css

Não rasterize os SVGs sem necessidade.

Arquitetura visual obrigatória:
1. top cap fixo;
2. região central elástica/repetível;
3. bottom cap fixo.

O centro deve poder aumentar/diminuir verticalmente sem deformar topo e base.
</assets>

<task>
Primeiro investigue como o dock/menu lateral atual está implementado nesta máquina/projeto.

Descubra:
- se é Ubuntu Dock, Dash to Dock, Dash to Panel, uma extensão própria ou CSS do GNOME Shell;
- qual extensão/tema controla o dock;
- quais arquivos realmente devem ser alterados;
- como os estilos atuais são carregados;
- como preservar atualizações/reversibilidade;
- se a customização pode ser feita no projeto Forge Core sem editar arquivos de sistema diretamente.

Depois implemente o novo design.

Não pare na investigação e não entregue apenas instruções: faça as alterações necessárias quando identificar a arquitetura correta.
</task>

<implementation_requirements>
A implementação deve:

- manter os ícones existentes exatamente como estão;
- manter funcionalidade de clique, drag/drop, badges, tooltips, menu de contexto e indicadores do GNOME;
- manter o dock vertical;
- deixar o dock visualmente flutuante, com pequeno afastamento das bordas da tela;
- usar largura-base de aproximadamente 80 px;
- usar ícones na faixa de 44–50 px, preferencialmente 48 px quando compatível com a configuração atual;
- usar gap vertical por volta de 8 px;
- evitar padding excessivo;
- permitir que o centro cresça conforme quantidade de ícones;
- manter top cap e bottom cap sem deformação;
- aplicar `04-active-indicator.svg` à esquerda do app ativo/rodando, ou reproduzir o mesmo efeito em CSS caso seja tecnicamente mais correto;
- usar `06-hover-plate.svg` apenas se não interferir com hitbox, animações ou legibilidade; caso contrário, reproduza o efeito por CSS;
- reservar o alojamento circular da base para o launcher/Show Applications/Ubuntu quando essa estrutura existir;
- usar o separador somente quando houver uma separação semântica real no dock;
- usar glow vermelho discreto, nunca bloom intenso;
- manter contraste suficiente em wallpapers claros e escuros;
- preservar performance do GNOME Shell;
- não adicionar animações pesadas.
</implementation_requirements>

<preferred_visual_behavior>
Estado normal:
- chassis escuro;
- ícone sem placa chamativa;
- bordas e linhas vermelhas quase imperceptíveis.

Hover:
- leve elevação visual;
- surface-elevated (#303030);
- borda #383838;
- pequeno accent vermelho;
- transição curta, aproximadamente 120–180 ms.

Aplicativo ativo:
- indicador vertical vermelho pequeno na lateral esquerda;
- glow suave;
- não envolver o ícone inteiro em vermelho.

Launcher:
- deve parecer encaixado na peça mecânica inferior;
- deve continuar totalmente clicável;
- não alterar o ícone do Ubuntu/launcher.
</preferred_visual_behavior>

<constraints>
Não:
- substitua os ícones;
- copie a referência como uma imagem única;
- use um PNG gigante como fundo;
- estique topo/base;
- crie grandes áreas vermelhas;
- use RGB, azul/roxo neon dominante ou estética gamer;
- edite arquivos de sistema antes de identificar uma alternativa segura;
- quebre suporte a diferentes escalas;
- esconda estados funcionais do GNOME;
- remova acessibilidade ou interação do dock.
</constraints>

<implementation_strategy>
Prefira esta ordem:

1. inspecionar a implementação real;
2. identificar a menor superfície de customização;
3. criar backup/versionamento dos arquivos alterados;
4. montar top/center/bottom de forma modular;
5. aplicar tokens e espaçamento;
6. integrar estados active/hover;
7. ajustar launcher;
8. recarregar de forma segura;
9. validar visualmente e funcionalmente;
10. documentar como reverter.

Se o GNOME/Ubuntu Dock não permitir inserir diretamente os SVGs como três regiões, reproduza o mesmo design com pseudo-elementos, background-image, múltiplas camadas CSS ou estrutura equivalente. Preserve a aparência e a modularidade, não a técnica exata.
</implementation_strategy>

<validation>
Antes de considerar concluído, valide:

- dock aparece corretamente após reload/login;
- não há erro no GNOME Shell;
- ícones continuam os mesmos;
- todos os ícones continuam clicáveis;
- hover funciona;
- app ativo é reconhecível;
- launcher funciona;
- menu de contexto funciona;
- dock não corta ícones;
- com mais/menos ícones, o centro adapta sem deformar topo/base;
- visual continua legível com escala do sistema atual;
- o vermelho permanece accent e não dominante;
- nenhuma alteração depende de caminho temporário.

Se houver logs do GNOME Shell disponíveis, verifique por erros após a implementação.
</validation>

<deliverables>
Ao finalizar:

1. implemente o dock;
2. deixe os assets em uma pasta permanente dentro do projeto Forge Core;
3. documente os arquivos modificados;
4. documente como recarregar/aplicar;
5. documente como desfazer;
6. mostre uma lista curta das mudanças efetuadas;
7. informe qualquer limitação técnica real encontrada.

Mantenha sua resposta final curta e objetiva.
</deliverables>

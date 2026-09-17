# Forge Core — Identidade Visual

## 1. Visão geral

**Forge Core** é uma identidade visual para Linux inspirada em uma metrópole futurista autossuficiente, poderosa e organizada.

A direção estética combina:

- sci-fi;
- engenharia industrial;
- steampunk futurista reinterpretado;
- tecnologia avançada;
- superfícies escuras;
- metal grafite;
- iluminação vermelha;
- sensação de sistema robusto, preciso e altamente tecnológico.

A proposta não é parecer “gamer RGB” nem um cyberpunk decadente. O universo visual deve transmitir **controle, poder, precisão, tecnologia e sofisticação**.

---

## 2. Conceito do universo

Forge Core representa um mundo onde tecnologia e engenharia evoluíram de forma limpa, funcional e monumental.

A estética pode remeter a:

- cidades futuristas autossuficientes;
- reatores centrais;
- centros de processamento;
- engrenagens;
- cabos e condutores;
- máquinas industriais avançadas;
- arquitetura tecnológica monumental;
- exércitos e máquinas futuristas;
- robôs e criaturas mecânicas;
- interfaces de alta tecnologia;
- centros de comando.

### Direção conceitual

O Forge Core deve parecer:

> uma infraestrutura tecnológica avançada criada para operar com precisão, força e autonomia.

---

## 3. Paleta principal

```css
:root {
  --background: #1b1b1b;
  --surface: #252525;
  --surface-elevated: #303030;

  --text-primary: #ffffff;
  --text-secondary: #a6a6a6;
  --text-muted: #707070;

  --accent: #fc435a;
  --accent-hover: #ff6478;

  --border: #383838;
}
```

### Uso das cores

| Token | Cor | Uso |
|---|---|---|
| `background` | `#1b1b1b` | Fundo principal |
| `surface` | `#252525` | Cards, menus, painéis |
| `surface-elevated` | `#303030` | Elementos destacados |
| `text-primary` | `#ffffff` | Texto principal |
| `text-secondary` | `#a6a6a6` | Texto secundário |
| `text-muted` | `#707070` | Informação discreta |
| `accent` | `#fc435a` | Energia, foco, estado ativo |
| `accent-hover` | `#ff6478` | Hover e realce |
| `border` | `#383838` | Bordas e divisões |

### Regra principal

O vermelho é **accent**, não superfície principal.

Deve representar:

- energia;
- ativação;
- foco;
- estado ativo;
- pulso;
- feedback;
- tecnologia viva.

Evitar grandes áreas totalmente vermelhas.

---

## 4. Tipografia

O Forge Core utiliza três famílias tipográficas.

### IBM Plex Sans

**Função:** interface principal.

Usar em:

- GNOME;
- menus;
- configurações;
- Nautilus;
- notificações;
- labels;
- textos comuns;
- títulos funcionais.

Pesos:

- 400 Regular
- 500 Medium
- 600 SemiBold

### Oxanium

**Função:** identidade visual e accent tipográfico.

Usar em:

- branding Forge Core;
- títulos especiais;
- HUDs;
- indicadores;
- headings;
- labels tecnológicas.

Evitar em:

- parágrafos;
- nomes de arquivos;
- textos longos;
- menus inteiros.

### JetBrains Mono

**Função:** conteúdo técnico.

Usar em:

- Warp;
- VS Code;
- terminal;
- código;
- logs;
- snippets;
- informações técnicas.

Pesos:

- 400 Regular
- 500 Medium

### Hierarquia

```text
Forge Core
├── IBM Plex Sans
│   └── UI principal
├── Oxanium
│   └── branding / HUD / títulos especiais
└── JetBrains Mono
    └── terminal / código / informações técnicas
```

---

## 5. Estilo de ícones

### Direção geral

Os ícones devem misturar:

- metal escuro;
- grafite;
- bordas claras discretas;
- neon vermelho;
- pequenos traços das cores originais do aplicativo;
- formas simples;
- boa leitura em tamanhos pequenos.

### Regra de identidade

**Forma:** priorizar reconhecimento do aplicativo.  
**Acabamento:** aplicar Forge Core.

Referência:

```text
70% identidade formal do app
30% Forge Core

70% acabamento Forge Core
30% cor original do app
```

### Evitar

- excesso de microdetalhes;
- texturas que desaparecem em 32–48 px;
- ícones quase totalmente pretos;
- excesso de volume 3D;
- perda da silhueta original;
- neon fino demais.

### Prioridade

Os ícones devem continuar legíveis em:

- 32×32;
- 48×48;
- 64×64.

---

## 6. Pastas

As pastas Forge Core devem parecer módulos industriais de armazenamento.

Características:

- base grafite;
- detalhes metálicos;
- linhas vermelhas;
- aparência robusta;
- contraste suficiente contra wallpapers escuros.

### Pasta padrão

Sem símbolo central quando possível.

### Pasta Home

Pode possuir um símbolo de casa grande e claramente reconhecível.

### Regra de contraste

A pasta não pode desaparecer sobre o wallpaper.

Priorizar:

- bordas mais claras;
- silhueta perceptível;
- vermelho visível;
- diferença clara entre `#1b1b1b`, `#252525` e o fundo.

---

## 7. Cursores

O Cursor Theme Forge Core usa:

- preto;
- grafite;
- metal;
- detalhes vermelhos;
- desenho simples;
- alto contraste;
- transparência real.

Estados prioritários:

- `default`
- `pointer`
- `text`
- `wait`
- `progress`
- `help`
- `move`
- `not-allowed`
- `grab`
- `grabbing`

Outros estados podem ser adicionados posteriormente.

### Regra

Cursores devem ser funcionais antes de decorativos.

Cada cursor precisa ter:

- hotspot correto;
- formato fácil de reconhecer;
- boa leitura em fundos escuros e claros.

---

## 8. Wallpapers

### Direção

Wallpapers Forge Core devem ser predominantemente escuros.

Características:

- centro visual forte;
- bordas mais escuras;
- vinheta/shadow nas extremidades;
- pouca informação nas laterais;
- vermelho concentrado no centro ou em poucos pontos;
- composição adequada para desktop.

### Temas aprovados

- desenvolvedor mascarado usando tecnologia avançada;
- interior de um PC futurista com engrenagens e cabos;
- reator central;
- exército futurista marchando;
- dragão robótico;
- centros de comando;
- alta tecnologia industrial;
- arquitetura Forge Core;
- máquinas e sistemas energéticos.

### Regras

- evitar poluição visual;
- evitar excesso de elementos pequenos;
- não encher as laterais;
- preservar áreas de respiro;
- manter bom contraste com dock e ícones;
- usar vermelho de forma controlada.

---

## 9. Movimento e animação

Se houver wallpapers animados:

Preferir:

- loop curto;
- câmera estática;
- poucas regiões animadas;
- código rolando;
- cursor piscando;
- neon pulsando;
- reator “respirando”;
- névoa leve;
- luzes discretas.

Evitar:

- movimento excessivo;
- deformação de elementos;
- movimentos de câmera agressivos;
- loops perceptíveis;
- ruído visual.

### Formato

Preferir:

- WebM
- MP4

GIF apenas como preview/teste quando necessário.

---

## 10. GNOME Shell

Componentes do sistema podem ser estilizados seguindo a mesma identidade:

- notificações;
- menus de contexto;
- barra superior;
- Quick Settings;
- overview;
- dock;
- tela de bloqueio.

### Notificações

Direção:

- fundo `#252525`;
- borda `#383838`;
- texto branco;
- texto secundário `#a6a6a6`;
- accent `#fc435a`;
- glow discreto;
- boa legibilidade;
- aparência de “módulo de sistema”.

### Menus de contexto

Direção:

- superfícies escuras;
- bordas discretas;
- hover vermelho translúcido;
- texto branco;
- separadores sutis;
- cantos moderadamente arredondados.

---

## 11. Linguagem visual

### Palavras-chave

- poderoso
- tecnológico
- preciso
- industrial
- futurista
- elegante
- robusto
- modular
- energético
- autossuficiente

### Evitar

- gamer RGB;
- neon exagerado;
- cyberpunk decadente;
- poluição visual;
- steampunk vitoriano clássico;
- bronze e marrom predominantes;
- excesso de engrenagens decorativas;
- excesso de detalhes;
- interfaces pouco legíveis.

---

## 12. Princípios de design

### 1. Funcional antes de decorativo

Toda customização deve continuar fácil de usar.

### 2. Vermelho como energia

O vermelho indica atividade e poder.

### 3. Escuro como estrutura

Preto e grafite formam o chassis do sistema.

### 4. Metal como linguagem

Bordas e detalhes metálicos reforçam a estética industrial.

### 5. Identidade sem destruir reconhecimento

Apps e elementos do sistema devem continuar fáceis de reconhecer.

### 6. Simplicidade em tamanhos pequenos

Quanto menor o elemento, menos detalhes deve possuir.

### 7. Coerência

Pastas, cursores, ícones, menus e wallpapers devem parecer parte do mesmo universo.

---

## 13. Arquitetura visual sugerida

```text
Forge-Core/
│
├── assets/
│   ├── icons/
│   ├── cursors/
│   ├── folders/
│   ├── wallpapers/
│   └── fonts/
│
├── icon-theme/
│
├── cursor-theme/
│
├── gnome-shell/
│
├── gtk/
│
├── scripts/
│
└── docs/
    └── visual-identity.md
```

---

## 14. Resumo rápido para outras IAs

Use este bloco quando precisar passar contexto rapidamente:

> Forge Core é um tema visual para Linux com estética sci-fi + industrial/steampunk futurista.  
> A interface é predominantemente escura, usando `#1b1b1b`, `#252525`, `#303030`, `#383838`, branco e vermelho `#fc435a`.  
> O vermelho funciona como energia/estado ativo, nunca como cor dominante da superfície.  
> O visual deve ser tecnológico, poderoso, preciso, elegante e modular.  
> Evitar RGB gamer, cyberpunk decadente, excesso de neon e excesso de detalhes.  
> Ícones devem manter a identidade funcional do app, mas receber acabamento Forge Core com metal escuro, bordas e detalhes vermelhos.  
> Wallpapers devem ter foco central, bordas escuras e composição simples.  
> Tipografia: IBM Plex Sans para UI, Oxanium para branding/HUD e JetBrains Mono para terminal/código.  
> Toda customização deve manter legibilidade e usabilidade.

---

## 15. Status atual

Direções já definidas:

- nome: **Forge Core**
- paleta: definida
- wallpapers: definida
- pastas: direção definida
- icon theme: direção definida
- cursor theme: direção definida
- tipografia: definida
- notificações/menu de contexto: direção definida

Este arquivo deve ser tratado como a **fonte da verdade visual do Forge Core**.

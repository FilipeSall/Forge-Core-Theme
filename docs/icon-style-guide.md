# Forge Core — Icon Style Guide

> Fonte de verdade para criação, revisão e manutenção dos ícones do projeto **Forge Core**.

## 1. Objetivo

Este documento define como os ícones do Forge Core devem ser desenhados.

O objetivo é manter uma família visual coerente sem transformar todos os aplicativos no mesmo ícone.

A regra central é:

> **preservar o reconhecimento do aplicativo e aplicar o Forge Core no acabamento, material, luz, estrutura e composição.**

Os ícones devem parecer parte do mesmo sistema, mas cada app precisa continuar imediatamente reconhecível.

---

## 2. Direção atual aprovada

A direção visual aprovada para os ícones é:

- sci-fi industrial;
- grafite/preto;
- metal escuro fosco;
- formas grandes e simples;
- profundidade 3D controlada;
- vermelho Forge Core como energia;
- brilho discreto;
- identidade original do aplicativo preservada;
- acabamento premium;
- poucos detalhes;
- forte leitura em tamanhos pequenos.

O visual deve parecer:

> **um componente tecnológico avançado integrado ao Forge Core.**

Não deve parecer:

- skin gamer antiga;
- interface de 2006;
- Winamp skin;
- steampunk ornamentado;
- RGB gamer;
- ícone excessivamente detalhado;
- placa metálica idêntica aplicada em todos os aplicativos.

---

## 3. Princípio principal

### Reconhecimento primeiro

O símbolo principal do aplicativo deve continuar reconhecível.

Exemplos:

- Chrome continua usando a identidade circular e suas cores;
- VS Code continua usando o símbolo azul característico;
- Discord continua azul/índigo;
- ORCA usa a marca real do ORCA;
- um terminal continua sendo representado por prompt/linha de comando;
- Lixeira continua sendo uma lixeira;
- Pastas continuam sendo pastas.

### Forge Core no acabamento

A identidade Forge Core deve aparecer em:

- material;
- chassis;
- recortes;
- luz;
- energia vermelha;
- sombras;
- profundidade;
- acabamento industrial;
- composição.

Não é necessário pintar todo aplicativo de vermelho.

---

## 4. Paleta

Paleta principal:

```css
:root {
  --background: #1b1b1b;
  --surface: #252525;
  --surface-elevated: #303030;

  --border: #383838;

  --text-primary: #ffffff;
  --text-secondary: #a6a6a6;

  --accent: #fc435a;
  --accent-hover: #ff6478;
}
```

### Distribuição visual recomendada

```text
65–80%  preto / grafite
10–20%  metal / cinza
5–10%   vermelho Forge Core
restante: cor original do aplicativo
```

A cor original pode ultrapassar esses valores quando for essencial para reconhecimento.

Exemplo: Chrome, VS Code, Discord.

---

## 5. Vermelho Forge Core

O vermelho representa:

- energia;
- atividade;
- núcleo;
- circuito;
- iluminação;
- estado ativo;
- integração com o sistema.

### Usar em

- linhas internas;
- recortes;
- fendas;
- bordas parciais;
- rim light;
- pequenos halos;
- regiões de energia.

### Evitar

- fundo inteiro vermelho;
- glow cobrindo todo o ícone;
- moldura vermelha em todos os lados;
- excesso de neon.

Regra:

> O vermelho deve parecer energia dentro da estrutura, e não tinta aplicada sobre ela.

---

## 6. Estrutura dos ícones

Não existe uma moldura única obrigatória.

Isso é importante.

A versão antiga do tema usava estruturas muito parecidas ao redor de todos os ícones, o que tornava a interface pesada e datada.

A nova regra é:

> **coerência de material e iluminação, não uniformidade de silhueta.**

### Formatos possíveis

Dependendo do app:

- círculo;
- quadrado arredondado;
- hexágono;
- objeto independente;
- pasta;
- documento;
- módulo técnico;
- símbolo sem chassis completo.

O formato deve seguir a identidade do aplicativo.

---

## 7. Chassis / base

Quando houver uma base Forge Core:

### Características

- grafite muito escuro;
- acabamento fosco;
- leve profundidade;
- bordas discretamente metálicas;
- recortes geométricos simples;
- 1 ou 2 regiões vermelhas;
- sem microparafusos;
- sem dezenas de painéis.

### Evitar

- bordas extremamente grossas;
- muitos segmentos;
- moldura mecânica ornamentada;
- rebites;
- parafusos decorativos;
- aparência de HUD gamer.

O chassis deve funcionar como suporte visual.

Ele nunca deve competir com a marca do aplicativo.

---

## 8. Profundidade e 3D

O Forge Core pode usar 3D, mas de forma controlada.

### Permitido

- bevel muito sutil;
- sombra curta;
- material fosco;
- pequena separação de camadas;
- luz direcional suave;
- relevo suficiente para separar símbolo e base.

### Evitar

- plástico brilhante;
- reflexo espelhado;
- bevel exagerado;
- volume cartunesco;
- sombra longa;
- glossy estilo anos 2000.

O ícone deve parecer um objeto tecnológico premium, não um botão de interface antiga.

---

## 9. Símbolo principal do app

O símbolo principal deve ter:

- silhueta clara;
- contraste alto;
- tamanho grande;
- poucos detalhes;
- boa leitura em 32–64 px.

### Regra de escala

O símbolo central deve ocupar aproximadamente:

```text
55–75% da área útil do ícone
```

A proporção pode variar conforme o formato.

Não diminuir excessivamente a marca apenas para mostrar mais chassis.

---

## 10. Cor original dos aplicativos

As cores originais devem ser preservadas quando ajudam a reconhecer o aplicativo.

### Exemplos

**Chrome**
- vermelho;
- amarelo;
- verde;
- azul.

**VS Code**
- azul.

**Discord**
- azul/índigo.

**ORCA**
- branco ou a cor oficial adequada da marca.

### Regra

Forge Core não significa monocromatizar tudo.

A aparência Forge Core vem da estrutura em volta, iluminação e acabamento.

---

## 11. Ícones funcionais do sistema

Ícones que não representam aplicativos comerciais podem usar a identidade Forge Core de forma mais intensa.

Exemplos:

- Pastas;
- Documentos;
- Todos os Apps;
- Lixeira;
- Downloads;
- Home;
- Configurações do sistema;
- categorias.

Nestes casos, o desenho pode ser criado especificamente para Forge Core.

---

## 12. Pastas

Pastas devem parecer módulos de armazenamento.

### Direção

- grafite escuro;
- construção simples;
- 1 elemento vermelho interno;
- bordas discretas;
- forma reconhecível imediatamente;
- sem símbolo central quando a pasta for genérica.

Pastas especiais podem ter símbolos.

Exemplos:

- Home;
- Downloads;
- Projetos;
- Documentos.

---

## 13. Documentos

Documentos devem ser visualmente diferentes de pastas.

Direção aprovada:

- uma ou duas folhas;
- grafite/preto;
- canto dobrado;
- linhas simples;
- pequeno accent vermelho;
- composição clara;
- sem excesso de texto.

Não transformar documentos em uma pasta.

---

## 14. Todos os Apps

O ícone de **Todos os Apps** não deve parecer configurações.

Direção aprovada:

- matriz/grid de módulos;
- células simples;
- 3×3 ou composição equivalente;
- uma célula ou núcleo com destaque Forge Core;
- geometria clara;
- leitura imediata como “coleção de aplicativos”.

Evitar:

- engrenagem;
- sliders;
- chave inglesa;
- qualquer símbolo associado a configurações.

---

## 15. ORCA

O ORCA deve usar a marca correta como símbolo central.

Referência estrutural:

- preservar a silhueta real da marca;
- contraste alto;
- símbolo branco ou conforme a identidade oficial;
- base/chassis Forge Core discreto;
- vermelho apenas em elementos de energia do chassis.

Nunca substituir a marca por um símbolo genérico.

---

## 16. Terminal

O Terminal deve ser simples.

Direção:

- prompt claramente reconhecível;
- fundo grafite;
- símbolo branco;
- pequeno accent vermelho;
- geometria limpa.

Exemplo conceitual:

```text
>_
```

Evitar código pequeno, múltiplas linhas ou excesso de texto.

---

## 17. Estados pequenos

Os ícones devem continuar funcionando em:

- 32×32;
- 48×48;
- 64×64;
- 128×128;
- 256×256.

### Quanto menor o tamanho

- menos textura;
- menos glow;
- menos recortes;
- mais contraste;
- linhas mais grossas;
- símbolo central maior.

Regra:

> quanto menor o ícone, mais simples ele deve parecer.

---

## 18. Glow

Glow deve ser pequeno e localizado.

### Bom

```text
linha vermelha
+
halo curto
+
reflexo discreto
```

### Ruim

```text
bloom em todo o ícone
+
vermelho vazando por toda a composição
```

O glow deve ajudar a indicar energia.

---

## 19. Material

Materiais recomendados:

- grafite;
- metal preto;
- aço escuro;
- superfícies foscas;
- vidro fumê muito discreto;
- materiais compostos futuristas.

Evitar:

- plástico;
- cromo espelhado;
- ouro como estrutura principal;
- bronze;
- madeira;
- acabamento excessivamente brilhante.

---

## 20. Iluminação

A iluminação deve ser funcional.

Preferir:

- rim light;
- red light interno;
- luz lateral;
- highlights metálicos suaves;
- sombras profundas.

Evitar:

- iluminação plana;
- glow em todos os lados;
- excesso de highlights;
- branco estourado.

---

## 21. Consistência entre ícones

Ícones não precisam ter exatamente o mesmo formato.

Eles precisam compartilhar:

- intensidade de sombra;
- acabamento;
- materiais;
- nível de profundidade;
- quantidade de vermelho;
- qualidade de borda;
- escala óptica;
- iluminação.

### Escala óptica

Dois ícones com 64×64 px podem parecer de tamanhos diferentes.

Ajustar visualmente até que tenham peso semelhante no dock.

Não confiar apenas nas dimensões do canvas.

---

## 22. Fundo e transparência

Assets finais devem preferencialmente ser exportados com:

- fundo transparente;
- símbolo centralizado;
- margem consistente;
- sem sombra cortada.

### Margem segura

Manter aproximadamente:

```text
8–12% de margem externa
```

Isso evita cortes em docks e launchers.

---

## 23. Exportação

Entregar preferencialmente:

```text
32x32
48x48
64x64
128x128
256x256
512x512
```

Arquivo principal:

```text
PNG transparente
```

Quando houver versão vetorial:

```text
SVG
```

---

## 24. Nomenclatura

Usar nomes previsíveis.

Exemplo:

```text
google-chrome-forge-core.png
vscode-forge-core.png
discord-forge-core.png
orca-forge-core.png
terminal-forge-core.png
documentos-forge-core.png
todos-os-apps-forge-core.png
```

Evitar:

```text
image1.png
icon-new-final2.png
teste.png
```

---

## 25. Checklist de aprovação

Antes de aprovar um ícone:

- [ ] O aplicativo continua reconhecível?
- [ ] O símbolo principal é grande o suficiente?
- [ ] O Forge Core aparece no acabamento?
- [ ] O vermelho está controlado?
- [ ] Não existe excesso de moldura?
- [ ] Não parece uma skin gamer antiga?
- [ ] Não possui microdetalhes inúteis?
- [ ] Funciona em 48×48?
- [ ] Funciona sobre wallpaper escuro?
- [ ] A escala óptica combina com os outros ícones?
- [ ] O glow está discreto?
- [ ] A silhueta continua clara?
- [ ] O ícone parece premium e moderno?
- [ ] O formato escolhido faz sentido para aquele aplicativo?

---

## 26. Prompt base para gerar novos ícones

```text
Create a Forge Core application icon.

Goal:
preserve the original app identity and recognizable silhouette,
while applying the Forge Core visual language to the material,
lighting, chassis and finishing.

Style:
minimal futuristic industrial sci-fi,
premium dark technology,
matte graphite metal,
deep black surfaces,
subtle dimensional depth,
clean geometry,
controlled Forge Core red energy accents (#fc435a),
small red internal glow,
high contrast,
simple readable silhouette,
few details,
professional Linux desktop icon.

Important:
the original application logo must remain immediately recognizable.
Preserve its characteristic colors when they are important for recognition.

Forge Core integration:
use graphite / black material,
subtle industrial cuts,
small red illuminated seams or energy lines,
soft short shadows,
controlled bevel,
clean premium construction.

Do NOT force every icon into the same frame.
Choose a circular, rounded-square, hexagonal or object-based structure
according to the original application's visual identity.

Composition:
large central symbol,
balanced optical size,
8–12% safe margin,
transparent background,
readable at 32px, 48px and 64px.

Avoid:
generic identical metallic frame on every icon,
2000s glossy UI,
Winamp skin aesthetics,
RGB gamer look,
excessive cyberpunk,
too many mechanical details,
bolts,
screws,
heavy bevel,
plastic shine,
large neon areas,
excessive red,
tiny details,
clutter.
```

---

## 27. Prompt negativo rápido

```text
no generic identical frame,
no gamer RGB,
no glossy 2000s UI,
no plastic,
no excessive bevel,
no bolts,
no screws,
no visual clutter,
no excessive glow,
no red-dominant icon,
no tiny details,
no unreadable logo,
no steampunk ornament,
no bronze-dominant palette,
no cartoon style
```

---

## 28. Regra final

A aparência Forge Core não deve vir de colocar a mesma moldura em todos os ícones.

Ela deve vir de uma linguagem compartilhada:

> **grafite + metal fosco + profundidade controlada + energia vermelha + símbolo original preservado.**

O resultado ideal é:

```text
aplicativos diferentes
+
mesmo universo visual
```

e não:

```text
mesma moldura
+
logos diferentes
```

---

## 29. Relação com a identidade geral do Forge Core

Este guia complementa a identidade visual principal do projeto.

Em caso de dúvida, aplicar esta prioridade:

1. usabilidade;
2. reconhecimento do aplicativo;
3. legibilidade em tamanhos pequenos;
4. coerência Forge Core;
5. detalhe decorativo.

O ícone deve funcionar primeiro como ícone.

Depois como peça estética.

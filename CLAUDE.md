# Forge Core — regras para agentes

## PROIBIDO criar branch

**Nunca crie branch neste repositório.** Nada de `git checkout -b`, `git switch -c`,
`git branch <nome>`, nem worktree com branch nova — **a não ser que eu peça
explicitamente naquele momento**.

- Commite sempre na branch que já está ativa (`main`).
- Vale também para o remoto: `git push -u origin <nome>` **cria** a branch no servidor.
  Antes de empurrar, cheque `git status -sb`; sem upstream, pergunte para onde vai.
- Se alguma orientação padrão mandar "crie uma branch antes de commitar na principal",
  **ela não vale aqui** — esta regra vence.
- Se achar que uma branch separada é mesmo necessária, **explique o motivo e espere
  resposta**.

## Comentários no código

Não adicione comentários (`//`, `#`, docstrings avulsas) por conta própria. O *porquê*
vai na mensagem de commit. Exceção: o projeto já usa docstring de módulo/função em
Python — siga essa convenção, curta, e nunca comentário solto dentro do corpo.
Não remova comentários pré-existentes.

## Depois de mexer no manifesto de ícones

`assets/icons/manifest.json` é a fonte da verdade. Toda alteração exige:

```bash
python3 scripts/build-icons.py     # manifesto -> icon-theme/
./scripts/install-icons.sh         # icon-theme/ -> ~/.local/share/icons + aplica
```

Sem o `install-icons.sh`, `special_folder_icons.load_special_folders()` não encontra
o asset instalado e pula o ícone.

## Escopo dos ícones por nome de pasta

Todo ícone com `folderNames` **precisa** de `matchRoots` (aceita `~`) e usa
`matchDepth` (padrão 2). Sem isso o ícone é ignorado.

Isso existe porque uma varredura ampla marcava centenas de diretórios irrelevantes
(pacotes Java, `build/`, dot-dirs, `/home`). A varredura é limitada por raiz, com
`-xdev` e `-maxdepth`; caminhos com componente oculto são descartados.

## Não desmonte o desktop no `disable()`

`disable()` da extensão roda **a cada bloqueio de tela** e em todo reload do shell.
Ele só pode soltar o que `enable()` criou. Trocar tema, mexer em GSettings, parar
units ou limpar metadata pertence ao toggle do Quick Settings e ao
`uninstall-shell.sh`.

## Os assets de pasta sao SO para pastas

Os arquivos de `assets/icons/folders/` valem apenas para pastas reais, via
`metadata::custom-icon` + miniatura. **Nao** os injete em outras superficies:

- **Barra lateral do GTK/Nautilus** — ela usa os nomes padrao do freedesktop
  (`user-home-symbolic`, `user-desktop-symbolic`, `folder-download-symbolic`...).
  Esses nomes ja tem arte propria, gerada por `scripts/build-symbolic-icons.py`
  em `assets/icons/symbolic/`. Nao crie entradas no `manifest.json` com esses
  nomes so para reaproveitar um asset de pasta.
- **VS Code** — `scripts/apply-vscode-folder-icons.py` altera o Material Icon Theme
  do usuario. Nao rode como parte de instalacao nenhuma; reverta com
  `scripts/restore-vscode-folder-icons.py`.

O VS Code ainda ganhara assets proprios (SVG) no futuro.

## Purga de cache a cada troca de tema

Trocar o tema dispara `folder_chooser_icons.purge_asset_caches()`. O alvo e
deliberadamente estreito:

- miniaturas marcadas com `Software = forge-core-folder-chooser-icons`;
- miniaturas cujo `Thumb::URI` aponta para um **diretorio** (so o Forge cria
  miniatura de pasta), incluindo os marcadores em `~/.cache/thumbnails/fail/`;
- o `icon-theme.cache` do tema instalado, via `gtk-update-icon-cache`.

**Nunca** apague `~/.cache` inteiro nem miniaturas de arquivo: as de foto/video sao
do usuario e regenerar tudo e caro. Miniaturas cujo alvo nao existe mais tambem ficam
— podem ser de midia em disco externo desmontado.

## Launchers NAO sao reescritos na troca de tema

O `Icon=` dos launchers gerenciados guarda um **nome** (`Icon=firefox`), fixo. Quem
decide a arte e o tema ativo:

- `Forge-Core` tem `firefox.png` -> arte do Forge;
- qualquer outro tema cai no `hicolor` do usuario, onde `browser_icons` publica a
  **arte original** do app (`install_icon_fallback`).

Assim o `.desktop` nunca muda ao trocar de tema, e o GNOME resolve o icone
nativamente. Nao volte a reescrever launcher por tema: era isso que deixava app com
engrenagem quando o servico estava atrasado ou o Shell com cache velho.

O `~/.local/share/icons/hicolor/` do usuario precisa de um `index.theme`, senao o
GTK ignora a pasta inteira. `ensure_hicolor_index()` cuida disso.

## Cache em memoria do Nautilus

Recarregar a janela (acao `reload` via D-Bus) basta para o Nautilus **pegar** arte
nova, mas nao para ele **esquecer** arte apagada: o cache e do processo inteiro e
sobrevive ao reload. Por isso `refresh_nautilus(removed=True)` reinicia o servico
(`nautilus -q`). Comprovado: uma pasta sem metadata e sem miniatura continuou
desenhada 90 s apos o reload.

## Testar funcao em processo NAO prova que o sistema funciona

Editar um script e chamar a funcao num `python3 -c` passa, mas os servicos
continuam com o codigo antigo carregado — e ha ainda uma **copia** em
`~/.local/share/forge-core/browser-icons-watcher/` feita na instalacao.

Depois de editar qualquer coisa sob `scripts/`, antes de dar por resolvido:

```bash
./scripts/install-icons.sh                                    # atualiza a copia runtime
systemctl --user restart forge-core-folder-chooser-icons-theme.service
```

E valide trocando o tema de verdade (`gsettings set ... icon-theme`), deixando os
servicos agirem, em vez de chamar `apply()`/`restore()` na mao.

## Serialização

`folder_chooser_icons` e `special_folder_icons` escrevem nos mesmos thumbnails,
manifestos e metadata. Toda entrada pública passa por `forge_locks.folder_icons_lock()`
(reentrante). Não adicione um caminho de escrita fora dele.

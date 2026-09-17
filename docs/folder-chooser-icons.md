# Forge Core — ícones de pastas no seletor "Abrir pasta" (GTK / portal)

O Nautilus exibe `metadata::custom-icon`. O seletor de arquivos do GTK (GTK 3 e
GTK 4) não lê essa metadata — `libgtk-3` e `libgtk-4` não contêm a string
`custom-icon`. Esse seletor é o do `xdg-desktop-portal-gnome` (GTK 4), o do
`xdg-desktop-portal-gtk` (GTK 3) e o que o VS Code/Electron abre (portal ou
GTK 3 direto).

O seletor, porém, consulta `thumbnail::path` e desenha a miniatura **antes** de
`standard::icon`, e o GLib resolve `thumbnail::path` também para diretórios
(`~/.cache/thumbnails/{normal,large}/<md5 da URI>.png`, padrão freedesktop).
Esta integração gera essa miniatura para cada pasta que tem
`metadata::custom-icon`. A metadata continua sendo a fonte da verdade; nada do
sistema, do tema Forge-Core ou do Yaru/Adwaita é alterado.

| Alternativa | Resultado no seletor |
|---|---|
| `metadata::custom-icon` (GVfs) | ignorado pelo GTK |
| `standard::icon` | não gravável (`gio set` recusa); derivado do tipo `inode/directory` |
| `.directory` (KDE) | lido só pelo KIO; o GIO não interpreta |
| emblemas (`metadata::emblems`) | exclusivos do Nautilus |
| portal (`gnome` × `gtk`) | ambos usam `GtkFileChooser`; mesma regra |
| **miniatura freedesktop** | **exibida** (GTK 3, GTK 4 e portal) |

## Aplicar ou reaplicar

```bash
./scripts/apply-folder-chooser-icons.py            # varre $HOME até profundidade 6
./scripts/apply-folder-chooser-icons.py --dry-run  # só lista
./scripts/apply-folder-chooser-icons.py --timer    # + timer systemd --user semanal
```

Aceita raízes e `--depth N`. É idempotente: reescreve as miniaturas próprias e
remove as de pastas que perderam o ícone customizado. Uma miniatura
pré-existente que não seja do Forge Core é movida para
`~/.local/share/forge-core/backups/folder-chooser-icons/`. O manifesto fica em
`~/.local/share/forge-core/folder-chooser-icons/manifest.json`, e cada PNG gerado
leva `tEXt Software=forge-core-folder-chooser-icons`.

O efeito é imediato na próxima abertura do seletor.

## Efeito colateral no Nautilus

O Nautilus 46 também lê `thumbnail::path` de pastas e marca o ícone com a classe
`.thumbnail`, que o `style.css` interno desenha com fundo xadrez
(`/org/gnome/nautilus/Checkerboard.png`) e contorno. Sem correção, toda pasta
com ícone customizado aparece num quadrado xadrez em vez de transparente.

Por isso o `apply` instala `gtk-4.0/forge-core-nautilus-thumbnails.css` em
`~/.config/gtk-4.0/` e adiciona o `@import` no topo do `gtk.css` do usuário
(prioridade USER, acima da APPLICATION do Nautilus). O `restore` remove a
linha e o arquivo; o resto do `gtk.css` fica intacto.

O GTK só lê o `gtk.css` na inicialização: após o primeiro `apply`, rode
`nautilus -q` e reabra. A regra vale para toda miniatura do Nautilus — imagens
com transparência também passam a aparecer sem o xadrez.

## Restaurar

```bash
./scripts/restore-folder-chooser-icons.py
```

Remove timer, miniaturas (pelo manifesto e por varredura da marca), manifesto e
devolve os backups. Não toca em `metadata::custom-icon`.

## Validar

```bash
gio info -a thumbnail::path,metadata::custom-icon ~/projetos/sea/negocia
# thumbnail::path: /home/sea/.cache/thumbnails/large/<md5>.png
systemctl --user list-timers forge-core-folder-chooser-icons.timer
```

## Limitações

- O `gsd-housekeeping` apaga miniaturas com mais de 180 dias
  (`org.gnome.desktop.thumbnail-cache maximum-age`); o timer semanal renova.
- A miniatura é presa ao caminho: pasta renomeada ou ícone novo só aparece após
  reaplicar (manual ou pelo timer).
- Barra lateral (Pasta pessoal, favoritos) usa ícones simbólicos — não muda.
- Na visão em lista o ícone aparece em 16 px; na grade do portal GNOME, grande.
- Só ícones `file://`; `metadata::custom-icon-name` (nome de tema) é ignorado.
- Pastas ocultas (`.claude`) só aparecem com arquivos ocultos visíveis (Ctrl+H).
- Diálogos Qt/KDE não usam o seletor GTK.

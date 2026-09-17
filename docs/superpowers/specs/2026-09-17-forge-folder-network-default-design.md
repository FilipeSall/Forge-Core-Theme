# Forge Core — pasta padrão com asset network

## Objetivo

Usar `assets/icons/folders/forge-folder-network.png` como a pasta genérica do
tema Forge Core. Pastas sem personalização específica devem resolver para esse
asset através dos nomes `folder` e `inode-directory`.

## Escopo

- Alterar `assets/icons/manifest.json` para apontar `folder` para
  `folders/forge-folder-network.png`.
- Usar o mesmo asset como `referenceSource`, preservando a escala do novo
  padrão.
- Regenerar os PNGs derivados de `folder`; manter `inode-directory` como alias
  para `folder.png`.
- Atualizar `docs/icons.md`.

Ficam fora do escopo `folder-open`, `user-home`, `folder-download`, ícones
personalizados por pasta, a integração do VS Code e temas externos. A entrada
`org.gnome.Nautilus`, que já usa esse asset, permanece igual.

## Validação

- Validar o manifesto como JSON.
- Executar a geração do tema sem substituir alterações não relacionadas do
  worktree.
- Conferir que cada tamanho do tema contém `places/folder.png` gerado a partir
  do novo asset e `places/inode-directory.png` apontando para ele.
- Confirmar que não houve mudança em arquivos fora do manifesto, documentação e
  artefatos do ícone padrão.

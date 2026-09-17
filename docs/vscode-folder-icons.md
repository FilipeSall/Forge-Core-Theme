# Forge Core — ícones de pastas no VS Code

O Nautilus usa `metadata::custom-icon`; o Explorer do VS Code usa o seu
próprio tema de ícones e, por isso, não lê essa metadata. Esta integração
preserva o Material Icon Theme e substitui somente os ícones de:

- `.claude`
- `.codex`
- `.gemini`

Os assets vêm de `assets/icons/folders/`. A cópia original do manifesto do
Material Icon Theme é guardada em
`~/.local/share/forge-core/backups/vscode-material-icon-theme/`.

## Aplicar ou reaplicar

```bash
./scripts/apply-vscode-folder-icons.py
```

Depois, no VS Code, use **Developer: Reload Window**. Reaplique após uma
atualização da extensão Material Icon Theme, pois atualizações substituem os
arquivos da extensão.

## Restaurar

```bash
./scripts/restore-vscode-folder-icons.py
```

Depois recarregue a janela do VS Code.

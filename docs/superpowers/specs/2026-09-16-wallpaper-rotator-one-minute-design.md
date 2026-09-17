# Forge Core wallpaper rotator: correção e intervalo de um minuto

## Objetivo

Corrigir a comparação de topologia que atualmente considera cada leitura do `xrandr` uma mudança, alterar o intervalo normal de rotação para 60 segundos e impedir crescimento ilimitado do cache.

## Causa

`active` é uma lista de tuplas. Depois de persistida em JSON, a topologia retorna como uma lista de listas. A comparação direta entre esses valores nunca é igual, portanto `topology_changed` permanece verdadeiro e uma nova imagem é renderizada a cada consulta.

## Solução

- Representar a topologia em um formato canônico JSON: lista de listas com nome, largura, altura, x e y.
- Usar essa representação tanto ao comparar quanto ao salvar o estado.
- Definir `ROTATION_SECONDS = 60`.
- Ao iniciar e depois de salvar e ativar uma nova imagem, manter no máximo três wallpapers gerados.
- Considerar elegíveis apenas arquivos regulares, não simbólicos, que correspondam diretamente a `CACHE_DIR/wallpaper-*.png`. O conjunto preservado será o arquivo referenciado pelo estado atual mais os dois arquivos elegíveis de maior `mtime` distintos dele. Se o arquivo atual não existir ou não for elegível, preservar somente os três elegíveis de maior `mtime`. Remover os demais.
- Nunca excluir `state.json` nem `rotator.lock` durante a retenção.
- Encerrar somente o processo antigo do rotator e lançar explicitamente uma nova instância, pois a entrada XDG Autostart não supervisiona nem reinicia processos. Verificar que existe exatamente um PID e que ele mantém a trava.

## Tratamento de falhas

- A limpeza ignora arquivos que desaparecerem durante a operação e não segue links simbólicos.
- O wallpaper referenciado pelo estado atual é sempre preservado, mesmo que seu `mtime` não esteja entre os três mais recentes.
- Uma falha real de renderização continua visível, sem atualizar falsamente o estado.
- A trava existente impede duas instâncias simultâneas.

## Verificação

- Testar que uma topologia recarregada de JSON é igual à topologia ativa equivalente.
- Confirmar que não há nova renderização antes de 60 segundos quando a topologia não muda.
- Confirmar uma nova renderização no primeiro poll a partir de 60 segundos; com polling de 15 segundos, a janela nominal é de 60 a menos de 75 segundos, acrescida do tempo de renderização.
- Confirmar no máximo três arquivos `wallpaper-*.png` após a limpeza.
- Imediatamente após o lançamento, medir o processo por 80 segundos com `pidstat -u -p PID 5 16`. Como o estado foi atualizado pelo processo antigo pouco antes da troca, deve ocorrer exatamente uma sequência de renderização nessa janela. Fora das amostras que cruzarem essa sequência, o processo deve consumir no máximo 1% de CPU. Confirmar também pelos `mtime` que foi criado exatamente um novo wallpaper.

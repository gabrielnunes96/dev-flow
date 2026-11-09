---
name: video
description: Gera um vídeo-resumo animado (1080p, ~3 min) de uma entrega — o que foi feito, como está, testes e próximos passos — a partir de um roteiro JSON, com narração (voz do Windows, ElevenLabs pela API ou MP3 gerado à mão), cenas sincronizadas com a fala, transições, trilha e efeitos. Use quando o usuário pedir um vídeo, um resumo em vídeo ou uma apresentação narrada de um relatório/documentação.
argument-hint: "[relatório ou documento de origem]"
---

# Vídeo-resumo

Scripts em `../../scripts/` (rodar com `python -I`). Dependências do motor: `pip install -r ../../requirements.txt` (Pillow, numpy, imageio-ffmpeg). Exemplo completo: `exemplos/video/migracao-ponte.json` do marketplace.

## Passos
1. **Roteiro** em `.claude/local/video/<nome>/roteiro.json` a partir do material (relatório, cards, testes). 8 a 11 cenas, ~3 min de fala. Tipos de cena (`roteiro.py`, `TIPOS`): `abertura`, `manchete`, `antes_depois`, `numeros`, `lista`, `grade`, `aneis`, `terminal`, `antes_agora`, `linha_tempo`, `encerramento`. Cada elemento visual tem `quando` = trecho literal da `fala` (ou `[trecho, segundos]`): ele aparece quando a narração chega ali.
2. **Fala para voz**: números por extenso, siglas como se lêem ("vê seis", "quinhentos e um", "cinco ponto um"); frases curtas. Sem imitar voz de pessoa real.
3. `roteiro.py validar <roteiro>` até sair `ok`.
4. **Narração** — perguntar ao usuário qual:
   - `voz.py windows <roteiro>` (Maria pt-BR; robótica, só para rascunho);
   - `voz.py eleven <roteiro> --voice-id <id>` — chave em `ELEVENLABS_API_KEY` definida pelo próprio usuário (`setx`); nunca ler, imprimir ou pedir a chave. Plano gratuito: API não usa vozes da biblioteca (402) e PCM exige Pro;
   - manual: `voz.py texto <roteiro> falas.md` → o usuário gera e salva `<id>.mp3` → `voz.py mp3 <roteiro> <pasta>`.
   Se o usuário editar uma fala na ferramenta, atualizar a `fala` no roteiro (os `quando` dependem dela) e validar de novo.
5. `render.py <roteiro> folha` e **olhar a imagem** (um quadro do fim de cada cena): texto cortado, sobreposição, seta sobre rótulo. Para checar sincronia, `previa <segundos>` no meio das cenas.
6. `render.py <roteiro> video <saida.mp4>` em segundo plano (~1,5× a duração). Extrair 2 quadros do MP4 para conferir e entregar com `SendUserFile`. Dizer que o áudio não foi ouvido por você.

## Armadilhas conhecidas
- `ImageDraw.text` do Pillow ignora o alfa numa imagem RGB: o motor usa `Pincel` (máscara) — não desenhar texto com `ImageDraw` direto.
- Ao ler arquivos de áudio/JSON no Windows, forçar UTF-8; não regravar nada a partir de saída do `az`/console em cp1252.
- Vídeo e áudios ficam em `.claude/local/` (não versionar).

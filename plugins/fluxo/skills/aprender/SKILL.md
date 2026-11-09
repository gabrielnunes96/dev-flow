---
name: aprender
description: Retrospectiva que transforma correções e descobertas da sessão em regra durável no lugar certo (perfil, rules do projeto, CLAUDE.md, skill de stack ou o próprio plugin). Use ao fim de uma demanda, quando o usuário corrigir uma premissa ("o sandbox não tem essa regra"), ou quando pedir para "registrar o aprendizado".
argument-hint: "[o que aprendemos, opcional]"
---

# Registrar aprendizado

Para cada aprendizado (do argumento ou levantado na conversa: correções do usuário, comportamentos do ambiente, armadilhas que custaram tempo, padrões que funcionaram):

1. **Classificar onde mora** — o mesmo critério que separa as peças do plugin:
   | É... | Vai para |
   | --- | --- |
   | Fato do projeto (arquitetura, convenção, armadilha) | `CLAUDE.md` do projeto |
   | Comportamento de ambiente / dados de teste | arquivo de `validacao.dados` |
   | Comando, caminho, proteção, situação de parar | `.claude/projeto.json` |
   | Algo que nunca pode acontecer | `protecao` no perfil (o guard aplica) — não só texto |
   | Jeito de trabalhar que vale para qualquer projeto daquela stack | skill do plugin `stack-*` |
   | Jeito de trabalhar que vale para qualquer projeto | skill do plugin `fluxo` |
   | Preferência pessoal do usuário | memória do Claude |
2. **Conferir** se já existe algo que cobre: atualizar em vez de duplicar; remover o que ficou errado (ex.: um "impedimento" que não era).
3. **Aplicar** as mudanças no projeto. Mudança em plugin (repositório `dev-flow`) → fazer no repositório do plugin, com commit próprio, e lembrar o usuário de atualizar (`claude plugin marketplace update dev-flow`).
4. **Responder** com uma linha por aprendizado: o que foi registrado e onde.

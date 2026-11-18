---
name: depurar
description: Corrige um bug pela causa raiz — registra o sintoma, reproduz, investiga por hipóteses (subagente depurador), escreve o teste de regressão que falha, aplica a correção mínima, revisa, valida e commita com permissão. Use quando o usuário relatar um erro, um comportamento errado, um teste ou pipeline quebrado, ou pedir "corrige esse bug" / "por que isso acontece".
argument-hint: "[descrição do bug, mensagem de erro ou id]"
---

# Bug → causa raiz → correção provada

Método: `../../referencias/raciocinio.md` (seção 6), relativo a esta skill. Scripts: `../../scripts/` (`S`), sempre `python -I`.

## 1. Registrar
- `python -I S/perfil.py mostrar`. Slug `bug-<resumo-curto>`; pasta `{docs}/{slug}/`, com `bug.md` pelo modelo `../../templates/bug.md`: sintoma literal (mensagem, stack trace, esperado × obtido), como reproduzir, ambiente, desde quando.
- Faltou dado essencial (passo a passo, mensagem exata, ambiente) → perguntar uma vez, com o que já se sabe.
- Bug em produção com impacto (dado sendo corrompido, indisponibilidade): dizer ao usuário que a mitigação (rollback, feature flag, desligar job) vem antes da correção, e que ela é decisão dele.

## 2. Investigar
- Causa óbvia e local (erro de digitação, import faltando, com stack trace apontando a linha) → seguir direto ao passo 3.
- Senão, disparar o especialista `../../agents/depurador.md` com: sintoma, reprodução, stacks, versão boa conhecida (se houver) e o caminho dos scripts `S`. Ele devolve causa raiz com evidência e a correção mínima proposta. Como disparar: `../../referencias/hosts.md`.
- Registrar em `bug.md`: hipóteses testadas, causa raiz (`arquivo:linha`) e gatilho.

## 3. Teste de regressão primeiro
- Escrever o teste que reproduz o bug no padrão do projeto (skill da stack). Rodar e **ver falhar** pelo motivo certo. Teste que passa antes da correção não prova nada.
- Bordas vizinhas da mesma causa (seção 3 do método) → casos no mesmo teste/arquivo.

## 4. Corrigir
- Correção mínima na causa, não no sintoma: nada de `try` que engole, `if` especial para o caso relatado ou `sleep` para "resolver" corrida.
- O mesmo padrão em outros lugares (o depurador lista) → corrigir junto se for a mesma causa; senão, listar como tarefa à parte.
- `comandos.teste` (e `build`/`lint`) verdes. Teste novo passando.

## 5. Revisar, validar, commitar
- Especialista `../../agents/revisor.md` com o bug, a causa e o diff (critério de aceite = "o sintoma não ocorre e o teste de regressão passa").
- Validação no ambiente pelo especialista `../../agents/validador.md` quando `validacao.tipo` ≠ `nenhuma`, reproduzindo o cenário original.
- Commit como no ciclo da tarefa (skill `task`, passo 6): stage só dos arquivos da correção, pedir permissão, mensagem `Corrige <sintoma>` no `git.formato_commit`. Nunca push.

## 6. Fechar
- `bug.md` completo: causa, correção (hash), teste, validação, como evitar (regra nova?).
- Aprendizado que vale além deste bug (armadilha da stack, do ambiente, do projeto) → sugerir a skill `aprender`.

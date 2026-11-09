---
name: task
description: Executa o ciclo completo de uma tarefa do plano (escolher a próxima pronta, implementar pela skill da stack, testes, revisão, validação no ambiente, commit, atualizar tarefas.json e o card, marcar feito). Use quando o usuário pedir para seguir para a próxima tarefa/task, fazer uma tarefa pelo id, ou continuar até terminar a fila.
argument-hint: "[id da tarefa | todas] [demanda]"
---

# Ciclo da tarefa

Argumento: `$ARGUMENTS` — vazio = próxima pronta da demanda ativa; um id (`T3` ou número do WI) = aquela tarefa; `todas` = repetir até a fila acabar ou surgir um bloqueio. Um segundo argumento escolhe a demanda (slug) quando há mais de uma.

**Scripts**: `../../scripts/` a partir do diretório desta skill (o hook de início de sessão também imprime o caminho). Sempre `python -I`. Abaixo, `S` = esse diretório.

## 0. Pré-condições
1. `python -I S/perfil.py validar` — erro → parar e mostrar. Ler o perfil (`perfil.py mostrar`) e os arquivos de `convencoes`.
2. `git status --short`: limpo. Alteração pendente que não é sua → parar e perguntar.
3. Se `validacao.token.script` existir, rodar (`fluxo:x.py` = `S/x.py`; sem prefixo = relativo à raiz do projeto). Código 2 (sem VPN) → avisar e seguir implementando; a validação espera. Código 3 → parar.
4. Carregar a skill de cada stack do perfil (`stack-dotnet:dotnet`, `stack-sql:sql`, `stack-front:front`). Sem o plugin da stack → seguir só com as convenções do projeto e avisar no fechamento.

## 1. Escolher e abrir a tarefa
- Fila = `{docs}/{demanda}/tarefas.json`. `python -I S/plano.py proxima <arq>` (ou a do argumento). Código 1 → a mensagem diz por quê (fila concluída, dependência, protegida); reportar e parar.
- Nunca pegar tarefa `protegida` nem item listado em `rastreador.protegidos`.
- `plano.py marcar <arq> <id> andamento`. Com `rastreador.tipo = azure-boards`, mover o WI para `estados.andamento` (skill `azure-boards:boards`).
- Reler na funcional os critérios (`criterios`) e na técnica a seção do componente. A tarefa implementa **só** isso.

## 2. Implementar
- Seguir a skill da stack e as convenções do projeto (padrão para adicionar uma operação, nomes, erros).
- Antes de escolher API/SDK/tabela, ler o código real; não inventar membros.
- Não editar arquivo gerado (o guard bloqueia); alterar a fonte e regerar.
- Edição por script: ler o conteúdo inteiro antes de abrir o arquivo para escrita e conferir que o trecho a trocar existe (`assert`). Abrir em modo escrita antes de ler zera o arquivo se o script falhar no meio.
- Monorepo: rodar os `comandos` do perfil a partir da raiz do projeto, não da pasta em que o último comando parou.
- Sem regra que a funcional não pediu. Ambiguidade de regra → parar e perguntar.

## 3. Testes
- Cada critério da tarefa tem pelo menos um teste. Siga o padrão de testes que o projeto já tem.
- Derrubar a aplicação antes de compilar (`python -I S/servico.py derrubar`, se houver `servico`), então `comandos.teste`. Tudo verde antes de seguir.

## 4. Revisão
- Delegar ao subagente `fluxo:revisor` com: id e critérios da tarefa, stacks, e o que mudou. Corrigir os achados procedentes e rodar os testes de novo. Achado que você descarta → dizer por quê no fechamento.

## 5. Validação no ambiente
- Conforme `validacao.tipo`, delegar ao subagente `fluxo:validador` com o lote: os `casos_obrigatorios` do perfil + o que os critérios pedem. Dados de teste em `validacao.dados`.
- Instabilidade conhecida do ambiente → repetir uma vez e registrar. Falha do código → voltar ao passo 2. Sem acesso (VPN) → registrar "não validado: motivo" e seguir; não marcar a demanda como entregue sem validar depois.

## 6. Commit (só com permissão)
- `git add` só dos arquivos da tarefa (`{git.escopo_add}`, na pasta do repositório da tarefa) e **parar** e pedir permissão, listando o que está no stage (a mensagem proposta só se o usuário pedir). Mensagem no `git.formato_commit` (pt-BR no presente, `{id}` = WI se houver, senão o id da tarefa); linha `Co-Authored-By` só se `git.coautor` estiver preenchido no perfil (padrão: sem). Commit só depois do "pode commitar" do usuário, a cada tarefa; uma permissão não vale para a próxima.
- Até o commit, a tarefa fica `andamento` e o card cita "commit pendente". Nunca push. Correção depois = novo commit com o mesmo id.

## 7. Registro
- `plano.py marcar <arq> <id> feito --commit <hash curto> [--wi N]`.
- Card: descrição original + Implementação (com hash) + Testes + Validação, no modelo `../../templates/card.html` (ou `rastreador.modelo_card`). Salvar em `{docs}/{demanda}/cards/{id}.html`. Com Boards, publicar a descrição e mudar para `estados.feito` numa só atualização (skill `azure-boards:boards`).

## 8. Fechamento
- Resumo curto: tarefa, commit, testes (total), validação por variante, estado, próxima pronta (`plano.py proxima`).
- `todas` → voltar ao passo 0. Parar ao esgotar a fila ou em: sem acesso ao ambiente para validar, falha sem causa clara, regra ambígua, algo fora do escopo da demanda, ou qualquer item de `pare_e_pergunte` do perfil.
- **Paralelo** (opcional, quando o usuário pedir pressa): `plano.py prontas` lista as que não dependem entre si; cada uma pode ir para um subagente com `isolation: worktree`, e você integra os commits na ordem do plano.

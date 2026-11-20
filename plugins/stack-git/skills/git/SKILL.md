---
name: git
description: Convenções para usar, revisar e diagnosticar Git no fluxo — commits pequenos e atômicos, branch a partir da base atualizada, rebase só em branch própria, conflito resolvido entendendo os dois lados e com teste, histórico publicado intocável, .gitattributes de fim de linha (CRLF/LF), .gitignore, segredos e arquivos grandes fora do histórico, hooks, bisect, blame e reflog. Use ao preparar commits, resolver conflitos, revisar o que vai para o histórico ou investigar quando e por que algo mudou num projeto com stack git.
---

# Git no fluxo

A política de Git do **perfil** (`git.branch_base`, `git.commit_por_task`, `git.formato_commit`, `git.coautor`, `git.escopo_add`, `git.push`) e as convenções do projeto vencem estas quando conflitarem. Esta skill cobre o método: o commit acontece só com a permissão do usuário, como manda o ciclo da tarefa (`fluxo:task`), e push, merge e publicação são do humano.

Versões com suporte, LTS e mudanças recentes: `../../referencias/atual.md` (veja a data de revisão). Antes de usar API ou recurso, siga o procedimento *projeto primeiro* do fluxo (`referencias/conhecimento.md` do plugin `fluxo`): padrão do projeto → versão em uso → documentação daquela versão → novidade como sugestão.

## Commits e branches
- Branch nova a partir de `git.branch_base` **atualizada**; nome no padrão do projeto (ver `git branch -r` e o histórico).
- **Commit atômico**: uma intenção por commit, que compila e passa nos testes sozinho. Refatoração separada de mudança de comportamento; formatação em massa em commit próprio.
- Mensagem no formato do perfil, dizendo **o que e por quê** (o diff já mostra o como). Seguir o idioma e o estilo do `git log` do projeto.
- Antes de commitar: `git status` e `git diff --cached` lidos inteiros — nada de arquivo gerado, temporário, `.env`, dump, binário de build ou mudança de outra tarefa. Adicionar por caminho (`git add <arquivos>`), não `git add -A` às cegas.
- Respeitar arquivos protegidos e gerados do perfil (`protecao`).

## Histórico
- **Histórico publicado não se reescreve** (`rebase`, `commit --amend`, `reset` em commits que já estão no remoto compartilhado). Corrigir com commit novo ou `git revert`.
- `rebase` (inclusive `--autosquash` com `fixup!`) só em branch própria ainda não compartilhada. Atualizar branch com a base: o que o projeto usa (merge ou rebase); na dúvida, merge.
- Operações que **a sessão prepara e o humano executa**: `push` (conforme `git.push`), `push --force`/`--force-with-lease`, `reset --hard`, `clean -fdx`/`-fdX` (apaga também ignorados: `.env`, `.claude/local/`, dependências), `checkout -- .`/`restore .` com mudança não commitada, `branch -D`, apagar tag, `filter-repo`, merge na base. Para guardar ou ver o que sairia, a sessão usa `git stash` e `git clean -n` (simulação).
- Perdeu algo? `git reflog` antes de qualquer conclusão: commit "sumido" quase sempre está lá.

## Conflitos
- Entender os dois lados antes de escolher: `git log --merge -p <arquivo>`; marcadores com a base (`merge.conflictStyle=zdiff3` configurado antes do merge, ou recriados com `git checkout --conflict=zdiff3 -- <arquivo>`; versão mínima no `atual.md`). Nunca "aceitar tudo de um lado" sem ler.
- Lockfile (`package-lock.json`, `poetry.lock`, `*.lock`) em conflito: aceitar o da base e **regenerar** com o gerenciador; não editar à mão.
- Depois de resolver: build e testes de novo; `git diff --check` e `git diff --cached --check` sem marcador `<<<<<<<` sobrando.

## Arquivos e configuração do repositório
- **Fim de linha**: `.gitattributes` versionado decide, não o `core.autocrlf` de cada máquina. Base: `* text=auto`; `*.sh text eol=lf` (script com CRLF quebra no Linux); `*.bat`/`*.cmd`/`*.ps1` `eol=crlf` quando o projeto exige; imagens, zips e binários `binary`. Mudança de fim de linha em massa = commit próprio (`git add --renormalize .`).
- Editar arquivo existente **preservando** o fim de linha dele (CRLF continua CRLF); diff com todas as linhas alteradas é sinal de fim de linha trocado.
- **`.gitignore`**: dependências, saídas de build, `.env*` (com `.env.example` versionado), segredos locais e pastas do host (ex.: `.claude/local/`). Arquivo já rastreado não sai pelo ignore: `git rm --cached` em commit próprio. Ignore pessoal em `.git/info/exclude`, não no do projeto.
- **Arquivo grande/binário** (modelos, mídia, dumps): Git LFS ou armazenamento externo, decidido com o humano; nunca dump de banco no repositório.
- **Hooks** do projeto (pre-commit, husky, lefthook): rodam sempre; não usar `--no-verify` para passar. Hook falhou → corrigir a causa.
- Submódulos: atualizar o ponteiro só quando a tarefa pede, em commit separado, citando a versão.

## Segredos
- Segredo commitado é segredo vazado, mesmo que o commit seja desfeito: **revogar/rotacionar primeiro** (pelo humano), depois limpar o histórico se o time decidir (`git filter-repo`, com push forçado coordenado).
- Varredura antes do commit quando o projeto tem (`gitleaks`, `trufflehog`, `git-secrets`); sem ferramenta, ler o `git diff --cached` procurando chave, token, senha, string de conexão.

## Investigar
- Quando quebrou: `git bisect` com um comando de teste (`git bisect run <comando>`), entre uma versão boa e uma ruim conhecidas.
- Por que essa linha existe: `git log -L <ini>,<fim>:<arquivo>`, `git blame -w -C -C` (ignora espaço e acha código movido), `git log -S'<texto>'`/`-G'<regex>'` para achar quando apareceu/sumiu; ler o commit e a mensagem antes de mudar.
- `.git-blame-ignore-revs` para commits de formatação em massa, se o projeto usa.

## Validar
- `git status` só com os arquivos da tarefa; `git diff --check` e `git diff --cached --check` limpos (espaço sobrando, marcador de conflito).
- `git diff --cached --stat` coerente com a tarefa; nenhum arquivo acima do tamanho combinado; `git ls-files --eol <arquivos>` sem fim de linha trocado.
- `git log -1` no formato do perfil, com coautor quando configurado.

## Checklist de revisão
1. Commit atômico e no formato do perfil; mensagem diz o que e por quê.
2. Nada de gerado, temporário, `.env`, dump ou mudança de outra tarefa no commit.
3. Nenhum segredo no diff (nem em commit anterior da branch); se houve, rotação pedida ao humano.
4. Fim de linha preservado e coerente com o `.gitattributes`; scripts de shell em LF.
5. Conflitos resolvidos lendo os dois lados, lockfile regenerado, testes rodados depois.
6. Nenhum histórico publicado reescrito; operação destrutiva ou push deixado para o humano.
7. Binário grande fora do Git (ou em LFS combinado); `.gitignore` cobre o que a tarefa gerou.

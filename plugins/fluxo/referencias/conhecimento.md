# Conhecimento atual: projeto primeiro

Vale para todo especialista e toda skill de stack. O que você sabe de uma tecnologia pode estar desatualizado — ou adiantado demais para o projeto. Antes de recomendar ou escrever código, nesta ordem:

## 1. O projeto manda
- Ler as convenções (`CLAUDE.md`, `convencoes` do perfil, regras do host) e **o código mais parecido** com o que vai mudar: estrutura, nomes, tratamento de erro, testes, bibliotecas já usadas.
- O padrão do projeto vence o seu, mesmo que exista um jeito "mais moderno". Copie o estilo existente; não introduza segundo estilo.

## 2. Versão em uso
- Descobrir a versão real antes de escolher API: `global.json`/`*.csproj` (`TargetFramework`), `.nvmrc`/`engines`/lockfile, `pyproject.toml`/`requires-python`, `pom.xml`/`build.gradle` (`java.version`, Spring Boot), `go.mod` (`go`), imagens base do `Dockerfile`, `required_version`/providers do Terraform, versão do banco no compose/infra.
- Recurso que não existe nessa versão não entra, por melhor que seja.

## 3. Documentação daquela versão
- Para API, sintaxe ou comportamento que você não tem certeza **naquela versão**, confirmar numa fonte, nesta preferência:
  1. ferramenta de documentação do host, se houver (ex.: um MCP de documentação por biblioteca/versão);
  2. busca na web pela documentação oficial da versão;
  3. o próprio código-fonte/tipos do pacote instalado (`node_modules`, `site-packages`, `~/.m2`, `go/pkg/mod`, `obj/project.assets.json`);
  4. se nada disso estiver disponível, dizer explicitamente "não confirmei na documentação da versão X".
- Versões suportadas, LTS, fim de suporte e mudanças recentes da stack: `referencias/atual.md` do plugin da stack (tem data de revisão; se estiver velha, confirme na fonte).

## 4. Novidade
- Conforme `conhecimento.novidades` no perfil:
  - `sugerir` (padrão): novidade que o projeto não usa vira **sugestão** no fechamento (ou ADR proposta), com ganho, custo e risco. Não muda o código por conta própria.
  - `aplicar`: projeto novo ou que pediu para acompanhar novidades — pode usar a versão suportada mais recente (LTS quando houver), registrando a escolha.
- Em qualquer caso: só versão estável e com suporte. Versão sem suporte (fim de vida) no projeto → apontar como risco, não "atualizar de carona" numa tarefa que não pediu.
- A demanda pediu explicitamente a novidade → aplicar, seguindo os passos 1 a 3.

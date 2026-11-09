---
name: dotnet
description: Convenções e armadilhas de .NET/ASP.NET Core para implementar, testar e revisar tarefas do fluxo — build e testes, API em memória para testes de contrato, compatibilidade de rotas, Nullable em DTOs, SDKs gerados, pacotes vulneráveis e binários travados no Windows. Use ao implementar ou revisar código C#/.NET num projeto com stack dotnet.
---

# .NET no fluxo

As convenções do **projeto** (CLAUDE.md) vencem estas quando conflitarem.

## Implementar
- Siga a operação existente mais parecida, de ponta a ponta (DTO → mapper → service → application → controller → registro no IoC). Registro de dependências explícito: se o projeto não usa scan, toda classe nova é registrada.
- Ler o SDK/cliente gerado antes de escolher método e modelo; não supor membros. Construtores de modelos gerados podem lançar sem argumentos (OpenAPI Generator) — passar os campos.
- Enums de SDK: converter pelo valor serializado (`[EnumMember]`), não `Enum.Parse` (pode dar um número que não é membro).
- **Nullable em DTOs de request**: com `<Nullable>enable</Nullable>`, o MVC trata `string` não anulável como `[Required]` implícito. Campo opcional (ou obrigatório só numa variante) = `string?`, validado no service da variante, com 400 que nomeia os campos no JSON.
- Resposta de API externa: devolver o que veio (campo do DTO com o modelo cru e `[JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]`), sem regra do consumidor.
- Rotas: explícitas (`[Route("api/dominio")]` + `[HttpPost("acao")]`), sem o token `[controller]`. Rota antiga mudou → action própria `[Obsolete]` com a rota absoluta e o verbo antigo, delegando à nova (aparece deprecated no Swagger, consumidor não quebra).
- Comentários XML em controllers e DTOs quando o Swagger lê o XML (`GenerateDocumentationFile`).
- Código gerado (`Connected Services`, SDK de OpenAPI): não editar; alterar a spec/o script de geração e regerar. Exceção só com autorização registrada no CLAUDE.md.

## Testar
- `comandos.teste` do perfil. **Windows**: a aplicação rodando trava os binários — derrubar (`servico.py derrubar`) antes de compilar/testar.
- Unidade: mapeamento por variante, serviço contra um servidor HTTP fake local (`HttpListener`/Kestrel em porta 0) conferindo rota, método e corpo enviados, erro preservando o status, roteamento/501.
- **Contrato** (vale muito ao mexer em rotas/DTOs): subir a API inteira em memória (`../../templates/ApiEmMemoria.cs`, relativo a esta skill) e conferir que rota antiga e nova caem na mesma action, que o Swagger marca as obsoletas e que os nomes do JSON de cada response não mudaram (snapshot usando o mesmo `JsonOptions` da API).
- Pacotes: `dotnet list <sln> package --vulnerable --include-transitive` sem achados ao mexer em dependências. Atualizar pacote só onde ele é referenciado diretamente; não espalhar referência por todos os projetos.
- Atualização de pacote que quebra API de outro pacote (ex.: RestSharp 111+ trocou `MaxTimeout` por `Timeout` `TimeSpan`) → corrigir a origem (template/geração), não o gerado.

## Checklist de revisão
1. Registro no IoC de tudo que é novo; nenhum `new` de serviço com dependência.
2. `string?` + validação na variante para campo opcional; sem `[Required]` implícito acidental.
3. Exceção do cliente externo capturada no service e convertida em resposta com o status certo; nada propagando 500 sem querer.
4. `async` até o fim (sem `.Result`/`.Wait()`), `CancellationToken` repassado quando a cadeia já usa.
5. Rota/verbo conforme a convenção; rota antiga preservada quando mudou.
6. Nenhum arquivo gerado alterado; nenhum segredo em `appsettings.*` fora dos que o projeto declara intencionais.
7. Testes cobrem sucesso por variante, erro e validação; fakes do contrato alterado atualizados.

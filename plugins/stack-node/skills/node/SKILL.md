---
name: node
description: Convenções e armadilhas de back-end Node.js/TypeScript para implementar, testar e revisar tarefas do fluxo — Express, Fastify e NestJS, TypeScript estrito, validação com zod/class-validator, Prisma/TypeORM/Drizzle, async e tratamento de erro, Jest/Vitest com supertest, npm/pnpm/yarn e auditoria de pacotes. Use ao implementar ou revisar código de servidor, API, worker ou CLI em Node num projeto com stack node.
---

# Node.js (back-end) no fluxo

As convenções do **projeto** (CLAUDE.md, `tsconfig.json`, ESLint) vencem estas quando conflitarem. Front-end (React/Angular/Vue) é da skill `stack-front:front`.

## Implementar
- Gerenciador pelo lock: `pnpm-lock.yaml` → pnpm; `yarn.lock` → yarn; `package-lock.json` → npm; `bun.lockb` → bun. Instale com o comando de lock congelado (`npm ci`, `pnpm i --frozen-lockfile`). Versão do Node em `.nvmrc`/`engines`.
- Siga a operação existente mais parecida (rota → validação → controller/handler → serviço → repositório). NestJS: módulo, provider registrado, DTO com `class-validator`; Fastify: schema JSON na rota; Express: middleware de validação (zod) e um handler de erro central.
- TypeScript estrito: sem `any` novo (use `unknown` + estreitamento), tipos de entrada derivados do schema (`z.infer`).
- Async: toda promise com `await` ou retornada; nada de `forEach` com `async` (use `for...of` ou `Promise.all` com limite). Erro em handler Express 4 assíncrono precisa ir para `next(err)` (ou wrapper); Express 5/Fastify/Nest tratam.
- Erros: classe de erro de domínio → status HTTP no handler central; nunca stack trace na resposta em produção.
- ORM: Prisma (`select`/`include` explícitos, transação com `$transaction`), TypeORM/Drizzle conforme o projeto; migrations versionadas e revisadas. Evite N+1 (`include`/join, `IN`).
- Configuração por variável de ambiente validada na inicialização (zod/envalid); falta de variável derruba o boot com mensagem clara. Segredo nunca no repositório.
- Event loop: nada de CPU pesada ou I/O síncrono (`fs.readFileSync`, `crypto.pbkdf2Sync`) no caminho da requisição.
- Graceful shutdown: tratar `SIGTERM` (fechar servidor, conexões de banco e fila) quando o projeto roda em container.
- ESM × CommonJS: siga o `"type"` do `package.json`; não misture `require` e `import` no mesmo módulo.

## Testar
- `comandos.lint`, `comandos.teste` e `comandos.build` (`tsc --noEmit` ou o build do projeto) verdes.
- Jest/Vitest conforme o projeto. API com `supertest` (Express/Nest) ou `fastify.inject`, conferindo status, corpo e nomes dos campos.
- HTTP externo: `nock`/`msw` conferindo método, URL e corpo; nada de chamada real em teste.
- Tempo: fake timers (`vi.useFakeTimers`/`jest.useFakeTimers`) em vez de `setTimeout` real.
- Banco: o padrão do projeto (container de teste via Testcontainers ou banco de teste); limpe o estado entre testes.
- Vulnerabilidades: `comandos.vulnerabilidades` (ex.: `npm audit --omit=dev --audit-level=high`) ao mexer em dependências.

## Checklist de revisão
1. Toda promise aguardada; sem `async` em `forEach`; erros assíncronos chegam ao handler central.
2. Entrada validada por schema na fronteira; tipo derivado do schema; sem `any` novo.
3. Erro de domínio mapeado para o status certo; sem stack trace ou mensagem interna na resposta.
4. Sem N+1; transação onde há mais de uma escrita dependente.
5. Sem I/O síncrono ou CPU pesada no caminho da requisição.
6. Variáveis de ambiente validadas; nenhum segredo no código ou log.
7. Dependência nova justificada, no lock, sem vulnerabilidade alta.
8. Testes com supertest/inject cobrindo sucesso, validação (400) e erro da dependência.

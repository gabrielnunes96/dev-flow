---
name: go
description: Convenções e armadilhas de Go para implementar, testar e revisar tarefas do fluxo — layout de módulo, tratamento de erro com wrap, context em toda chamada de I/O, goroutines sem vazamento, interfaces pequenas, net/http e roteadores, database/sql/pgx/sqlc, testes de tabela, race detector, golangci-lint e govulncheck. Use ao implementar ou revisar código Go num projeto com stack go.
---

# Go no fluxo

As convenções do **projeto** (CLAUDE.md, `.golangci.yml`, layout de pacotes) vencem estas quando conflitarem.

## Implementar
- Siga o layout existente (`cmd/`, `internal/`, pacotes por domínio). Pacote novo só quando há responsabilidade nova; nada de `utils`/`common` genérico.
- Erros: devolva, não entre em pânico. Envolva com contexto: `fmt.Errorf("buscar pedido %d: %w", id, err)`; compare com `errors.Is`/`errors.As`, nunca pela string. Erro tratado uma vez: ou loga ou devolve.
- `context.Context` como primeiro parâmetro em tudo que faz I/O, repassado até o driver/cliente HTTP; respeite cancelamento e prazo.
- Goroutines: toda goroutine tem dono e fim (cancelamento por context, `errgroup`, `WaitGroup`). Canal fechado só por quem escreve. Estado compartilhado com `sync.Mutex` ou por canal — nunca os dois sem motivo.
- Interfaces pequenas, definidas por quem **consome**; aceite interfaces, devolva structs concretas.
- HTTP: `http.Server` com `ReadHeaderTimeout`/timeouts; cliente com `Timeout`, `resp.Body.Close()` sempre (com `defer` depois de checar o erro). JSON com tags explícitas; `DisallowUnknownFields` se o contrato for estrito.
- Banco: `database/sql`/pgx/sqlc conforme o projeto; `rows.Close()` e `rows.Err()`; transação com `defer tx.Rollback()` e `Commit` explícito; parâmetros (`$1`), nunca `fmt.Sprintf` em SQL.
- Dinheiro em inteiros na menor unidade (centavos) ou decimal de biblioteca; nunca `float64`.
- Armadilhas: variável de laço capturada em goroutine (antes do Go 1.22), `defer` dentro de laço longo, slice compartilhando array (`append` em subslice), map não é seguro para escrita concorrente, `nil` de interface com valor tipado nulo.

## Testar
- `comandos.teste` (tipicamente `go test ./... -race -count=1`), `comandos.lint` (`golangci-lint run` ou `go vet ./...`) e `gofmt -l .` vazio.
- Testes de tabela (`[]struct{nome string; ...}` com `t.Run`), `t.Helper()` em auxiliares, `t.Parallel()` quando o teste não compartilha estado.
- HTTP: `httptest.NewRecorder`/`httptest.NewServer` para handler e para fake de dependência externa.
- Banco: Testcontainers ou banco de teste do projeto; sem mock de `database/sql` para regra que depende de SQL.
- Tempo injetado (função `now` ou interface de relógio), sem `time.Sleep` para sincronizar.
- Vulnerabilidades: `govulncheck ./...` ao mexer em dependências; `go mod tidy` sem diferença.

## Checklist de revisão
1. Nenhum erro ignorado (`_ =` só com comentário do motivo); wrap com `%w` e contexto.
2. `context` repassado em todo I/O; timeouts em servidor e cliente HTTP.
3. Toda goroutine termina; sem corrida (`-race` verde); canais fechados pelo escritor.
4. `Body.Close`, `rows.Close`, `rows.Err`, `tx.Rollback` deferido.
5. SQL parametrizado; nada de `Sprintf` com entrada.
6. Interfaces pequenas no consumidor; sem pacote genérico novo.
7. Testes de tabela cobrindo sucesso, borda e erro; `gofmt`/`vet`/lint limpos.

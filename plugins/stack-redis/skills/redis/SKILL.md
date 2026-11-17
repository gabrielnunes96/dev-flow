---
name: redis
description: Convenções para usar, testar e revisar Redis no fluxo — cache-aside com TTL e invalidação, nomes de chave, estruturas certas (hash, set, sorted set, stream), operações atômicas e Lua, locks distribuídos com expiração, rate limiting, filas/streams, pub/sub, comandos proibidos (KEYS, FLUSHALL), memória e política de evicção. Use ao implementar ou revisar cache, sessão, fila, contador, lock ou rate limit com Redis num projeto com stack redis.
---

# Redis no fluxo

As convenções do **projeto** (prefixo de chaves, cliente, configuração) vencem estas quando conflitarem.

## Implementar
- **Redis não é fonte da verdade** (a menos que a técnica diga e a persistência AOF/RDB esteja configurada para isso). Toda leitura de cache tem caminho de fallback para a fonte.
- Chaves: `app:dominio:entidade:id[:campo]` (ex.: `loja:pedido:123:resumo`), com o prefixo do projeto. Versão no nome (`:v2`) quando o formato do valor muda — evita ler formato antigo.
- **TTL em toda chave de cache** (`SET k v EX 300`), com variação aleatória (jitter) para não expirar tudo junto. Chave sem TTL só com motivo registrado.
- Cache-aside: lê cache → miss → lê fonte → grava com TTL. Escrita na fonte → **apaga** a chave (não atualiza), depois do commit. Proteja contra estampido (muitos misses simultâneos) com lock curto ou "stale-while-revalidate" se a carga justificar.
- Estrutura certa: hash para objeto com campos, set para pertinência, sorted set para ranking/janela de tempo, list/stream para fila, HyperLogLog para contagem aproximada.
- Atomicidade: `INCR`/`HINCRBY`, `SET NX EX`, `MULTI/EXEC` ou script Lua quando ler-e-escrever precisa ser atômico. Nunca `GET` + `SET` para contador.
- Lock distribuído: `SET lock:x <token-único> NX PX <ttl>` e liberação com Lua que confere o token. O lock expira: a operação protegida precisa caber no TTL ou renová-lo; para correção forte, use fencing token na fonte.
- Rate limit: janela fixa com `INCR` + `EXPIRE` na primeira chamada, ou janela deslizante com sorted set/Lua.
- Filas: Streams (`XADD`/`XREADGROUP`/`XACK`, com tratamento de pendentes via `XAUTOCLAIM`) quando a mensagem não pode se perder; pub/sub é "dispara e esquece" (assinante desconectado perde).
- **Proibidos em código**: `KEYS *` (bloqueia o servidor; use `SCAN`), `FLUSHALL`/`FLUSHDB`, `MONITOR`, valores enormes (> ~100 KB) e coleções sem limite.
- Cliente com pool, timeout de conexão e de comando, e reconexão; falha do Redis em cache **degrada** (vai à fonte), não derruba a requisição.
- Dados sensíveis: não cachear token/dado pessoal sem necessidade; se cachear, TTL curto e sem log do valor. TLS e senha/ACL vêm da configuração, nunca do código.

## Testar
- `comandos.teste` com Redis real de teste (Testcontainers ou `compose`); fake em memória só para lógica que não depende de semântica do Redis (TTL, atomicidade, Lua).
- Casos: hit, miss, expiração (TTL curto no teste ou relógio do Redis), invalidação após escrita, Redis indisponível (degrada), concorrência no lock/contador.

## Checklist de revisão
1. TTL (com jitter) em chave de cache; nome com prefixo e versão.
2. Invalidação por remoção após o commit da fonte.
3. Operações atômicas; nenhum `GET`+`SET` para contador ou lock.
4. Lock com token e liberação condicional; operação cabe no TTL.
5. Nenhum `KEYS`, `FLUSH*`, valor gigante ou coleção sem limite.
6. Timeout no cliente; falha do Redis degrada em vez de derrubar.
7. Sem dado sensível desnecessário no cache.

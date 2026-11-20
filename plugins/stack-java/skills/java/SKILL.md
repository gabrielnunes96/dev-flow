---
name: java
description: Convenções e armadilhas de Java/Kotlin na JVM para implementar, testar e revisar tarefas do fluxo — Spring Boot (web, data JPA, validation, security), Maven e Gradle, JUnit 5, Mockito, MockMvc/WebTestClient, Testcontainers, Flyway/Liquibase, transações, N+1 do JPA e dependências vulneráveis. Use ao implementar ou revisar código Java ou Kotlin num projeto com stack java.
---

# Java / Kotlin (JVM) no fluxo

As convenções do **projeto** (CLAUDE.md, checkstyle/spotless, arquitetura de pacotes) vencem estas quando conflitarem.

Versões com suporte, LTS e mudanças recentes: `../../referencias/atual.md` (veja a data de revisão). Antes de usar API ou recurso, siga o procedimento *projeto primeiro* do fluxo (`referencias/conhecimento.md` do plugin `fluxo`): padrão do projeto → versão em uso → documentação daquela versão → novidade como sugestão.

## Implementar
- Build pelo wrapper do projeto: `./mvnw` ou `./gradlew` (nunca o Maven/Gradle global). Versão do JDK em `pom.xml`/`toolchain`/`.sdkmanrc`.
- Siga o fluxo existente mais parecido (controller → DTO/record → service → repository → entidade). Injeção por construtor (campos `final`), sem `@Autowired` em campo.
- DTOs de entrada e saída separados da entidade JPA; nunca exponha entidade na API (lazy loading e atribuição em massa). `record` para DTO quando o JDK permitir.
- Validação na fronteira com Bean Validation (`@Valid`, `@NotNull`, `@Size`) e um `@RestControllerAdvice` que devolve 400 nomeando os campos (ProblemDetail no Spring 6).
- `@Transactional` no serviço (não no controller), `readOnly = true` em leitura. Lembre: chamada interna (`this.metodo()`) não passa pelo proxy — a transação/anotação não se aplica.
- JPA: `FetchType.LAZY` por padrão; consultas com `JOIN FETCH`/`@EntityGraph` onde a tela precisa da coleção (N+1); paginação com `Pageable`. `equals`/`hashCode` de entidade pelo id de negócio ou id não nulo.
- Migrations com Flyway/Liquibase, uma por mudança, nunca editar migração já aplicada.
- `BigDecimal` para dinheiro (com `compareTo`, não `equals`), `java.time` com fuso (`Instant`, `OffsetDateTime`), nunca `Date`.
- `Optional` só em retorno; não em campo nem parâmetro. Nada de `Optional.get()` sem verificação.
- Kotlin: null-safety de verdade (sem `!!` novo), `data class` para DTO, plugin `kotlin-spring`/`kotlin-jpa` para entidades.
- Configuração em `application.yml` por profile; segredos por variável de ambiente/cofre.

## Testar
- `comandos.teste` (ex.: `./mvnw -q verify` ou `./gradlew test`) e `comandos.lint` verdes.
- Unidade: JUnit 5 + AssertJ + Mockito; `@ParameterizedTest` para a matriz de casos.
- Web: `@WebMvcTest` + `MockMvc` (ou `WebTestClient`) conferindo status, JSON (`jsonPath`) e validação.
- Persistência: `@DataJpaTest` com **Testcontainers** do mesmo banco de produção (H2 esconde diferença de dialeto).
- Integração externa: WireMock/MockWebServer conferindo método, URL e corpo.
- Vulnerabilidades: `comandos.vulnerabilidades` (OWASP dependency-check, `./gradlew dependencyCheckAnalyze`) ao mexer em dependências.

## Checklist de revisão
1. Injeção por construtor; nenhuma entidade exposta na API.
2. `@Valid` na entrada e advice que devolve 400 com campos.
3. `@Transactional` no lugar certo; sem autochamada esperando proxy.
4. Sem N+1 (fetch/entity graph) e com paginação em listas.
5. `BigDecimal` com `compareTo`; `java.time` com fuso; sem `Optional.get()` cego.
6. Migração nova, não edição de migração aplicada; rollback/estratégia descrita.
7. Exceções não engolidas; log com contexto e sem dado sensível.
8. Testes de controller, de repositório com Testcontainers quando há consulta nova, e de serviço com casos de erro.

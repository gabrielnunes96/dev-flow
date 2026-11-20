# Conhecimento atual: Java/Kotlin
<!-- dev-flow:conhecimento revisado_em=2026-11-19 produtos=eclipse-temurin,spring-boot -->

> Parte volátil da stack, separada do método (a skill). A tabela de versões é gerada por `scripts/atualizar_conhecimento.py` no repositório do dev-flow; as mudanças a observar entram pela revisão periódica (skill `atualizar-conhecimento`), sempre com aprovação humana. Antes de usar qualquer item, siga o procedimento *projeto primeiro* (`referencias/conhecimento.md` do plugin `fluxo`): a versão do projeto manda.

## Fontes oficiais
- https://adoptium.net/support/
- https://spring.io/projects/spring-boot#support
- https://openjdk.org/projects/jdk/
- https://endoflife.date/eclipse-temurin (suporte e fim de vida; fonte da tabela abaixo)
- https://endoflife.date/spring-boot (suporte e fim de vida; fonte da tabela abaixo)

## Versões
<!-- versoes:inicio -->
Gerado em 2026-11-19 por `scripts/atualizar_conhecimento.py` a partir de endoflife.date (ciclos com suporte e os 2 últimos sem suporte). Não editar à mão.

| Produto | Ciclo | Situação | Lançado | Suporte ativo até | Fim de suporte | Última |
| --- | --- | --- | --- | --- | --- | --- |
| eclipse-temurin | 27 | suportado | 2026-09-22 | — | 2027-03-23 | 27.0.1.0.2+1 |
| eclipse-temurin | 25 | LTS | 2025-09-22 | — | 2031-09-30 | 25.0.5+8 |
| eclipse-temurin | 21 | LTS | 2023-10-10 | — | 2029-12-31 | 21.0.13+9 |
| eclipse-temurin | 17 | LTS | 2021-09-22 | — | 2027-10-31 | 17.0.21+9 |
| eclipse-temurin | 11 | LTS | 2021-08-01 | — | 2027-10-31 | 11.0.33+10 |
| eclipse-temurin | 8 | LTS | 2021-07-29 | — | 2030-12-31 | 8u512-b09 |
| eclipse-temurin | 26 | sem suporte | 2026-03-23 | — | 2026-09-22 | 26.0.2.1+1 |
| eclipse-temurin | 24 | sem suporte | 2025-03-20 | — | 2025-09-22 | 24.0.2+12 |
| spring-boot | 4.1 | suportado | 2026-06-30 | — | 2027-07-31 | 4.1.2 |
| spring-boot | 4.0 | suportado | 2025-11-30 | — | 2026-12-31 | 4.0.9 |
| spring-boot | 3.5 | sem suporte | 2025-05-31 | — | 2026-06-30 | 3.5.16 |
| spring-boot | 3.4 | sem suporte | 2024-11-30 | — | 2025-12-31 | 3.4.13 |
<!-- versoes:fim -->

## O que acompanhar
- JDK LTS novo e fim de suporte; `java.version`/toolchain e imagem base.
- Linha do Spring Boot com suporte (OSS) e a versão mínima de Java que ela exige.

## Mudanças a observar
Nenhuma registrada ainda. Cada item entra com data, fonte e a partir de que versão vale.

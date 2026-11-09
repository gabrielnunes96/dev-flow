# {Título da demanda} — Especificação técnica

> Demanda: `{slug}` · Base: funcional v{n} · {dd/mm/aaaa} · Situação: **rascunho | aprovada em dd/mm/aaaa**

## 1. Visão da solução
Um parágrafo e, se ajudar, um diagrama do fluxo entre componentes em texto (bloco ```text```, com setas). Não usar mermaid: não renderiza no anexo do Boards nem em todo visualizador.

## 2. Componentes afetados
| Repositório / projeto | Stack | O que muda | Arquivos-chave (existentes) |
| --- | --- | --- | --- |
| | | | `caminho/arquivo:linha` |

## 3. Contratos
Rotas, DTOs, eventos, tabelas, procedures — com nomes reais seguindo as convenções do projeto.

| Contrato | Antes | Depois | Compatibilidade |
| --- | --- | --- | --- |
| `POST api/{dominio}/{acao}` | — | request/response | nova rota; antiga mantida como obsoleta |

## 4. Dados
Modelo, migrations/scripts (com rollback), volume, índices, retenção.

## 5. Integrações externas
APIs de terceiros, SDKs, limites conhecidos, ambiente de teste (sandbox) e o que ele aceita.

## 6. Segurança
Autenticação, autorização, segredos (onde ficam, quem lê), dados sensíveis (mascaramento, LGPD/PCI).

## 7. Observabilidade
Logs, métricas, healthcheck, como diagnosticar em produção.

## 8. Estratégia de testes
| Critério de aceite | Teste unitário | Teste de contrato/integração | Validação no ambiente |
| --- | --- | --- | --- |
| CA-1 | `Classe.Metodo` | | chamada X → 200 |

## 9. Riscos e decisões
| # | Risco / decisão | Opções | Escolha e motivo |
| --- | --- | --- | --- |
| R-1 | | | |

## 10. Implantação e rollback
Ordem de deploy entre componentes, feature flag, migração de dados, como desfazer.

## 11. CI/CD
Pipelines afetadas ou novas, ambientes, aprovações.

> Portão: o plano só começa com esta especificação aprovada (registrada no topo).

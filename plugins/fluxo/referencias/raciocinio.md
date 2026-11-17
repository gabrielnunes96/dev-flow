# Método de raciocínio do fluxo

Referência comum a todas as skills e agentes do `fluxo`. Não é teoria: é a sequência de perguntas que separa uma mudança que "parece certa" de uma que **está** certa. Use a parte que o problema pede — um ajuste de texto não precisa de análise de complexidade; um cálculo de saldo precisa de tudo.

## 1. Modelar antes de mexer
1. **Entrada → transformação → saída.** Diga em uma frase o que entra (tipos, origem, volume), o que sai e quem consome. Se não cabe numa frase, o problema ainda não está entendido.
2. **Estado.** O que persiste entre chamadas (banco, cache, arquivo, memória, fila)? Quem mais escreve nele? Mudança de estado é onde mora quase todo bug.
3. **Fronteiras.** Onde o código confia (dentro do processo) e onde não pode confiar (entrada do usuário, API externa, arquivo, fila, outro serviço)? Toda fronteira valida, converte e trata erro.
4. **Decomposição.** Quebre em passos que se testam sozinhos. Passo que faz duas coisas (decide **e** executa efeito colateral) separe: a decisão vira função pura, o efeito fica na borda.

## 2. Contrato de cada unidade
Para a função/rota/procedure que você cria ou altera, escreva (mentalmente ou no teste):
- **Pré-condição**: o que precisa ser verdade na entrada (não nulo, lista não vazia, usuário autenticado, registro existe).
- **Pós-condição**: o que é verdade na saída (status, registro criado, soma preservada, evento publicado uma vez).
- **Invariante**: o que nunca muda, antes e depois (saldo nunca negativo, total = soma dos itens, id único, ordem mantida).
- **Erro**: o que acontece quando a pré-condição falha — exceção tipada, 4xx com campo, retorno vazio? Nunca "depende".

Uma pós-condição ou invariante que você não sabe escrever é um critério de aceite faltando: volte à funcional.

## 3. Casos de borda (lista de verificação)
Para cada entrada, percorra a lista e descarte conscientemente o que não se aplica:

| Categoria | Pergunte |
| --- | --- |
| Cardinalidade | 0, 1, 2, muitos, o máximo permitido, máximo + 1 |
| Ausência | `null`/`None`/`undefined`, campo ausente vs. vazio vs. só espaços |
| Limites numéricos | zero, negativo, overflow, divisão por zero, arredondamento (dinheiro em decimal, nunca float) |
| Texto | Unicode/acentos, emoji, maiúsculas, tamanho máximo, injeção (SQL, HTML, shell, path) |
| Tempo | fuso horário, horário de verão, fim de mês/ano bissexto, relógio de servidores diferentes, `now()` em teste |
| Ordem | entrada fora de ordem, duplicada, repetida (idempotência), reprocessamento |
| Concorrência | duas requisições iguais ao mesmo tempo, leitura-modificação-escrita, lock, retry que duplica efeito |
| Falha parcial | o passo 2 de 3 falhou — o que ficou gravado? Existe transação ou compensação? |
| Dependência externa | timeout, 4xx, 5xx, resposta lenta, resposta fora do contrato, indisponível |
| Permissão | sem login, outro usuário (IDOR), papel sem acesso, token expirado |
| Volume | 10× e 1000× o volume de hoje: memória, tempo, paginação, N+1 |

## 4. Custo
- **Complexidade**: diga o O() do caminho principal em função do que cresce (linhas da tabela, itens do pedido, usuários). Laço dentro de laço sobre dados que crescem, consulta dentro de laço (N+1) e carregar tudo em memória são os suspeitos de sempre.
- **I/O vence CPU**: uma ida ao banco ou à rede custa mais que milhares de operações em memória. Agrupe, pagine, use índice.
- Otimize só com número na mão (medida, plano de execução, perfil). Sem número, prefira o código mais claro.

## 5. Raciocinar sobre o código existente
- **Leia antes de supor.** Nome de método, campo, rota e tabela vêm do código real (grep, leitura), nunca da memória ou do "deveria ser".
- **Siga o dado.** Do ponto de entrada até a persistência e de volta: quem chama, quem é chamado, quais transformações acontecem.
- **Execute na cabeça.** Para a mudança, simule pelo menos três entradas: o caminho feliz, uma borda e um erro. Escreva o valor de cada variável relevante em cada passo. Diferença entre o esperado e o simulado é bug antes de existir.
- **Raio de impacto.** Quem mais usa o que você mudou? Busque todos os chamadores. Mudança de assinatura, contrato ou esquema sem olhar consumidores é a maior fonte de regressão.

## 6. Depurar por hipóteses
1. **Reproduza** com o menor caso possível. Sem reprodução, não há correção — há palpite.
2. **Observe** o sintoma exato (mensagem, stack trace, valor errado, linha). Copie, não parafraseie.
3. **Liste hipóteses** (2–4), cada uma com a evidência que a confirmaria ou derrubaria.
4. **Teste a mais barata de derrubar primeiro.** Um log, uma consulta, um teste unitário, `git bisect` entre a versão boa e a ruim.
5. **Ache a causa raiz**, não o sintoma: pergunte "por quê?" até chegar numa decisão de código ou de dado. Corrigir o sintoma (um `if` a mais, um `try` que engole) esconde o bug.
6. **Prove** com um teste que falha antes da correção e passa depois. Procure o mesmo padrão em outros lugares.

## 7. Decidir entre alternativas
Para cada decisão relevante, registre: opções reais (no mínimo duas), critério (correção, simplicidade, custo, desempenho, risco, reversibilidade), escolha e motivo. Prefira a opção **reversível** e **mais simples que atende os critérios**; complexidade só com requisito que a exija (seção 8). Decisão que é de produto, custo ou prazo é do usuário: pergunte.

## 8. Simplicidade: sem overengineering
O código certo é o **menor que atende os critérios de aceite** e segue o padrão do projeto. Complexidade é custo pago em toda leitura, teste e mudança futura; só entra com um requisito que a exija **hoje**.

Não faça sem um requisito escrito (funcional, técnica ou ADR) que peça:
- **Abstração especulativa**: interface com uma implementação só, fábrica, strategy, classe base, genérico ou plugin "para o futuro". Duas ocorrências ainda não são padrão; extraia na terceira.
- **Camada nova**: serviço que só repassa a chamada, DTO idêntico à entidade, mapper de um campo, wrapper de biblioteca sem regra própria.
- **Configuração no lugar de código**: flag, parâmetro ou arquivo de configuração para um valor que nunca muda.
- **Infraestrutura antecipada**: fila, cache, microsserviço, event sourcing, CQRS, retry/circuit breaker onde não há falha nem volume medidos.
- **Dependência nova** para o que a biblioteca padrão ou uma função de 10 linhas resolve.
- **Tratamento de caso impossível**: validação repetida dentro do domínio que já foi feita na fronteira, `try` em volta do que não lança.
- **Generalizar o pedido**: a funcional pede exportar CSV; não nasce um "motor de exportação" com formatos plugáveis.

Teste rápido antes de criar algo: *se eu apagar isto, qual critério de aceite falha?* Nenhum → não crie. Prefira duplicação pequena e óbvia a uma abstração errada; código simples é fácil de generalizar depois, abstração errada é cara de desfazer.

Isso não é licença para atalho: validação na fronteira, tratamento de erro real, testes, segurança e as regras da stack continuam obrigatórios. Simples é **pouca coisa, bem feita**.

## 9. Verificar antes de dizer pronto
- Cada critério de aceite tem um teste que falharia se o critério quebrasse (troque o operador mentalmente: o teste pega?).
- Testes cobrem caminho feliz, bordas relevantes da seção 3 e pelo menos um erro.
- Build, lint e testes do perfil verdes **nesta** execução, não numa anterior.
- Validação no ambiente feita, ou registrada como pendente com o motivo.
- Diga o que **não** verificou. "Funciona" sem evidência não é resultado.

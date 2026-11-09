---
name: front
description: Convenções para implementar, testar e revisar front-end no fluxo (React, Angular, Vue ou HTML) — componentes, estado e chamadas à API, lint/testes/build, verificação visual no navegador embutido em desktop e mobile, acessibilidade. Use ao criar ou revisar telas e componentes num projeto com stack front.
---

# Front-end no fluxo

As convenções do **projeto** (CLAUDE.md, lint, design system) vencem estas quando conflitarem.

## Implementar
- Copie o padrão da tela/componente existente mais parecido (estrutura de pastas, estado, chamada à API, tratamento de erro, design system). Não introduza biblioteca nova sem a técnica prever.
- Contrato da API: tipar a resposta a partir do contrato real do back (DTO/Swagger), não do que "deveria" vir. Tratar loading, vazio, erro (4xx com mensagem do back, 5xx genérico) e 401 (sessão).
- Textos visíveis no idioma do projeto; sem texto fixo onde o projeto usa i18n.
- Formulários: validação no cliente espelhando a do back (mesmos obrigatórios), mensagens por campo, botão desabilitado durante o envio.
- Segredos nunca no bundle (chaves só no back; variáveis `VITE_`/`NG_`/`NEXT_PUBLIC_` são públicas).

## Testar
- `comandos.lint`, `comandos.teste` e `comandos.build` do perfil — os três verdes.
- Teste de componente para a regra (renderiza o estado certo para loading/vazio/erro/sucesso; envia o payload certo).
- E2E (Playwright etc.): esperar o estado observável (um item, um texto, um status na tela) em vez de um tempo fixo (`setTimeout`); a espera fixa passa sozinha e falha com a suíte inteira rodando.
- **Verificação visual** (validacao.tipo = navegador): subir o dev server (`servico.py subir` ou `preview_start`), abrir no navegador embutido, executar o critério de aceite, conferir em desktop e mobile (`resize_window` preset mobile), sem erro no console (`read_console_messages`) e sem requisição falhando (`read_network_requests`). Registrar o que viu, não opinião.

## Checklist de revisão
1. Estados loading/vazio/erro tratados; 401 leva ao fluxo de sessão do projeto.
2. Tipos batem com o contrato real do back.
3. Acessibilidade: `label` em campo, `alt` em imagem, foco visível, navegação por teclado no fluxo principal, contraste do design system.
4. Responsivo: nada estoura em 375px; sem rolagem horizontal.
5. Sem chave/segredo no código do cliente; sem `console.log` sobrando; sem `any` novo onde o projeto é tipado.
6. Sem dependência nova não prevista; bundle não cresce sem motivo.

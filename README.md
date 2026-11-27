# CSSDeals → Telegram

Monitor separado de qualquer outro projeto. Token Telegram somente em GitHub Actions Secrets.

## Estado verificado em 27/11/2026

- Varredura completa: sucesso, base inicial de 190 anúncios, envio Telegram e cache validados.
- Consulta filtrada: sucesso em modo sem envio, 183 correspondências no instante do teste;
  calçados em 8,6 segundos e camisetas em 12,9 segundos. Não é comparação simultânea de cobertura.
- Teste rápido: https://github.com/augustosergiobauru-lgtm/Cssdeals-bot/actions/runs/45947576228
- Filtros: EU 45/46; camisetas 2XL/XXL, 3XL/XXXL e 4XL/XXXXL.
- O filtro depende do tamanho publicado, não garante estoque, e a categoria Shoes pode conter outros itens.

## Agendamento e custo

Repositório público após autorização explícita do proprietário em 27/11/2026.
Consulta rápida habilitada a cada cinco minutos (cron `2-59/5 * * * *`).
A varredura completa complementar continua a cada três horas. Se o repositório voltar
para privado, os eventos do cron rápido são ignorados sem iniciar runner.

Teste real após publicação: execução 45948157170 concluída com sucesso, 187
correspondências, 29 avisos de anúncios ainda não registrados enviados, cache anterior
recuperado e novo cache salvo. Leitura do catálogo: 10,0s para calçados e 13,8s para camisetas;
a execução completa inclui preparação do navegador e tempo de envio Telegram.
https://github.com/augustosergiobauru-lgtm/Cssdeals-bot/actions/runs/45948157170

O GitHub oferece runners padrão gratuitos para repositórios públicos.
Runners maiores não são usados. No privado, as consultas completas consomem a franquia
mensal da conta. Não foi alterado plano, faturamento, limite de gastos ou visibilidade.
Não há garantia de pontualidade ou de aviso instantâneo: o agendamento GitHub pode atrasar.
Não foi validada uma alternativa gratuita 24h com intervalo de segundos.

A consulta rápida usa os controles normais de tamanho do site e percorre todas as páginas
desses filtros. Não faz chamadas HTTP diretas fora do navegador. Tamanhos em texto livre
que não aparecem nos controles podem depender da varredura completa complementar.
A consulta direta de teste recebeu 403 e não é utilizada.

## Configuração

O token fica em `TELEGRAM_BOT_TOKEN` nos segredos do repositório.
O chat confirmado está configurado no workflow; `TELEGRAM_CHAT_ID` nos segredos permite
substituir esse destino. O ID do chat não é token, mas aparece na configuração e no histórico.

Actions → CSSDeals Telegram → Run workflow:
- `monitor`: consulta filtrada.
- `full-scan`: varredura completa.
- `chat-id`: lista IDs privados que enviaram /start; não envia mensagens.

Nenhum token está nos arquivos versionados. Os segredos não são publicados junto com o código.
Antes de tornar o repositório público, revise também histórico, logs e dados de configuração.

## Comportamento

A primeira execução registra a base e envia uma confirmação; não envia todos os anúncios.
As próximas execuções enviam novos anúncios ou novos tamanhos com preço em yuan, link e
foto quando disponível. Não monitora redução de preço.
Ambos os coletores compartilham a mesma base SQLite e a mesma fila de execução para evitar duplicados.
O cache é salvo mesmo após falha parcial de envio. Se expirar ou for removido, uma nova base
será criada e as novidades daquele intervalo não serão enviadas retroativamente.
Interrupção entre envio e gravação pode excepcionalmente repetir um aviso.

## Desenvolvimento

Python 3.12:

```sh
pip install -r requirements.txt
python -m playwright install --with-deps chromium
python -m unittest -v
python fast_monitor.py --dry-run
python fast_monitor.py
```

`--dry-run` não envia Telegram nem marca anúncios como vistos.
`MAX_PAGES` (padrão 100) limita as páginas por filtro; a varredura completa usa esse limite por categoria.
Os testes locais cobrem tamanhos, números fracionados, exclusões, base inicial, duplicados e reenvio após falha.

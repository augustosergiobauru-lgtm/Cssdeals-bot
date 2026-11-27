# CSSDeals → Telegram do Augusto

Código preparado em 27/11/2026. O monitor fica inativo até configurar os segredos e validar o primeiro envio.

Filtros: tênis EU 45 e 46; camisetas 2XL/XXL, 3XL/XXXL e 4XL/XXXXL.
O filtro usa o tamanho anunciado, nunca preço ou números no título.
Chinelos e sandálias com nomes reconhecidos são excluídos. Títulos genéricos
ou em outros idiomas podem precisar de revisão: a categoria Shoes contém outros calçados.

O monitor abre o catálogo público com Chromium, percorre as páginas e envia
texto, preço em yuan, tamanho, link e, quando acessível, foto para um único chat privado.
Na primeira execução registra os itens existentes e envia apenas uma confirmação.
Nas seguintes envia anúncios novos ou novos tamanhos, sem repetir os já registrados.
Não monitora queda de preço nem garante estoque: o tamanho é o publicado no anúncio.

## Configuração

1. Crie um repositório GitHub **privado e separado do Nexus Play** e envie estes arquivos,
   incluindo `.github/workflows/monitor.yml`.
2. Em Settings → Secrets and variables → Actions, adicione `TELEGRAM_BOT_TOKEN`.
   O token não está incluído neste pacote; nunca o coloque em commits ou arquivos públicos.
3. Para descobrir o ID do chat, abra Actions → CSSDeals Telegram → Run workflow e escolha
   `chat-id`. Abra os logs da etapa “Descobrir ID privado”. Alternativamente, em um ambiente confiável
   configure o token como variável de ambiente e execute `python monitor.py --chat-id`.
   Se nenhum ID aparecer, envie `/start` de novo ao bot e repita. O comando não envia mensagens.
4. Adicione o ID privado confirmado em `TELEGRAM_CHAT_ID` nos segredos do repositório.
5. Execute Actions → CSSDeals Telegram → Run workflow e escolha `monitor`. Confira a confirmação no Telegram
   e o resultado da execução. Só então considere o serviço ativado.

Após validar o primeiro envio, descomente `schedule` e a linha `cron` do workflow para
ativar a consulta a cada aproximadamente 30 minutos, sujeita a atrasos do GitHub.
Verifique a franquia de Actions da conta antes de ativar; Chromium e varreduras completas
consomem minutos e não há garantia de custo zero. Nenhuma assinatura paga é necessária no código.
Sem o celular ligado após a hospedagem. O estado usa cache do GitHub: se o cache expirar
ou for removido, a próxima execução cria nova base e não alerta sobre os itens daquele intervalo.
Para serviço definitivo, substitua cache por armazenamento persistente.

## Execução e validação

Python 3.12:

```sh
pip install -r requirements.txt
python -m playwright install --with-deps chromium
python -m unittest -v
python monitor.py --dry-run
python monitor.py
```

`--dry-run` não envia alertas nem grava anúncios como vistos.
`MAX_PAGES` limita páginas por categoria (padrão 100); atingir o limite interrompe a execução
para evitar uma base incompleta. Falhas no catálogo não substituem o estado anterior.
Falhas de envio mantêm o anúncio pendente para a próxima execução. Uma interrupção entre
envio e gravação pode excepcionalmente repetir um alerta.

Validação realizada: estrutura real dos cards e tamanhos lida no navegador; testes de
tamanhos, exclusão de numeração fracionada, duplicação, primeira execução e reenvio após falha.
A consulta HTTP direta do ambiente retornou 403. A varredura completa via Chromium
na hospedagem e o envio real ao Telegram ainda precisam de validação.

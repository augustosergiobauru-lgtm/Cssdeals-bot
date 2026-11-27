"""Monitor pessoal CSSDeals. Credenciais somente em variáveis de ambiente."""
import argparse
import asyncio
import hashlib
import json
import os
import re
import sqlite3
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = 'https://www.cssdeals.com'
EXTRACT = """() => Array.from(document.querySelectorAll('.mn-product-card'))
 .filter(c => c.querySelector('a[href*="itemid="]'))
 .map(c => {const a=c.querySelector('a[href*="itemid="]'); return {
 id: new URL(a.href).searchParams.get('itemid'), url:a.href,
 title:c.querySelector('h5')?.innerText || 'Produto',
 price:c.querySelector('.mn-price-new')?.innerText || '',
 sku:c.querySelector('.mn-sku')?.innerText || '',
 image:c.querySelector('img.main-img')?.src || ''};})"""


def matches(category, sku, title=''):
    text = sku.upper().strip()
    if category == 'camisetas':
        return bool(re.search(r'(?<![A-Z0-9])(?:[234]XL|XXL|XXXL|XXXXL)(?![A-Z0-9])', text))
    # Nunca confundir US, preços ou EU 45.5 com EU 45.
    if re.search(r'(?i)slipper|sandal|flip.flop|拖鞋|凉鞋|chinelo', title):
        return False
    explicit = re.findall(r'(?:EUR?|欧洲码)\s*[:=]?\s*(\d+(?:[.,]\d+)?)', text)
    if explicit:
        return any(n in ('45', '46') for n in explicit)
    if re.search(r'(?<![A-Z])(?:US|UK)(?=\s|\d|$)', text):
        return False
    return bool(re.search(r'(?<![\d.,])(?:45|46)(?![\d.,])', text))


def telegram(method, payload):
    token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    if not token:
        raise RuntimeError('Configure TELEGRAM_BOT_TOKEN como segredo.')
    request = urllib.request.Request(
        f'https://api.telegram.org/bot{token}/{method}',
        data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.load(response)
    except (urllib.error.URLError, TimeoutError):
        # Não imprimir exceções de rede: elas podem conter a URL com token.
        raise RuntimeError('Falha de conexão com Telegram; credencial omitida.') from None
    if not result.get('ok'):
        raise RuntimeError('Telegram recusou a solicitação; confira a configuração.')
    return result['result']


def notify(item):
    chat = os.environ.get('TELEGRAM_CHAT_ID')
    if not chat:
        raise RuntimeError('Configure TELEGRAM_CHAT_ID.')
    text = (f"Novidade CSSDeals · {item['category']}\n{item['title']}\n"
            f"Preço: {item['price']}\nTamanho anunciado: {item['sku']}\n{item['url']}")
    # Texto e link sempre entregues; imagem é opcional para não perder alertas.
    telegram('sendMessage', {'chat_id': chat, 'text': text[:4096]})
    if item.get('image'):
        try:
            telegram('sendPhoto', {'chat_id': chat, 'photo': item['image']})
        except RuntimeError:
            print('Foto indisponível; aviso com link já entregue.')


async def collect(category, category_id, max_pages):
    from playwright.async_api import async_playwright
    result = {}
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        page = await browser.new_page()
        try:
            response = await page.goto(f'{BASE}/shop-left-sidebar.html?id={category_id}',
                                       wait_until='domcontentloaded', timeout=60000)
            if response and response.status >= 400:
                raise RuntimeError(f'CSSDeals retornou HTTP {response.status}; consulta interrompida.')
            await page.locator('.mn-product-card a[href*="itemid="]').first.wait_for(timeout=60000)
            for number in range(1, max_pages + 1):
                rows = await page.evaluate(EXTRACT)
                if not rows:
                    raise RuntimeError('Catálogo vazio ou estrutura alterada; estado anterior preservado.')
                for item in rows:
                    if matches(category, item['sku'], item['title']):
                        item['category'] = category
                        result[item['id']] = item
                next_page = page.locator('#pagination a').filter(has_text=re.compile(f'^{number+1}$'))
                if not await next_page.count():
                    break
                if number == max_pages:
                    raise RuntimeError('Limite de páginas atingido; aumente MAX_PAGES antes de ativar.')
                previous = [r['id'] for r in rows]
                await next_page.click()
                await page.wait_for_function(
                    "previous => {const ids=Array.from(document.querySelectorAll('.mn-product-card a.image[href*=\"itemid=\"]')).map(a=>new URL(a.href).searchParams.get('itemid'));return ids.length>0 && JSON.stringify(ids)!==JSON.stringify(previous)}",
                    arg=previous, timeout=60000)
                await page.wait_for_timeout(1500)
        finally:
            await browser.close()
    return list(result.values())


def process(db, items, dry_run=False):
    db.execute('CREATE TABLE IF NOT EXISTS seen (key TEXT PRIMARY KEY)')
    db.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)')
    initialized = db.execute("SELECT value FROM settings WHERE key='initialized'").fetchone()
    sent = 0
    for item in items:
        key = hashlib.sha256(f"{item['id']}|{item['sku']}".encode()).hexdigest()
        if db.execute('SELECT 1 FROM seen WHERE key=?', (key,)).fetchone():
            continue
        if dry_run:
            print(json.dumps(item, ensure_ascii=False))
            continue
        if initialized:
            notify(item)
            sent += 1
        db.execute('INSERT INTO seen VALUES (?)', (key,))
        db.commit()
    if not dry_run:
        db.execute("INSERT OR REPLACE INTO settings VALUES ('initialized','1')")
        db.commit()
    return sent, bool(initialized)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--chat-id', action='store_true')
    args = parser.parse_args()
    if args.chat_id:
        updates = telegram('getUpdates', {'allowed_updates': ['message'], 'timeout': 0})
        chats = {u['message']['chat']['id'] for u in updates if u.get('message', {}).get('text') == '/start'
                 and u['message']['chat']['type'] == 'private'}
        print('IDs privados que enviaram /start:', ', '.join(map(str, sorted(chats))) or 'Nenhum. Envie /start novamente.')
        return
    if not args.dry_run and not all(os.environ.get(k) for k in ('TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID')):
        raise RuntimeError('Configure os dois segredos Telegram antes de executar.')
    items = []
    for category, category_id in [('tenis', 11), ('camisetas', 14)]:
        items.extend(await collect(category, category_id, int(os.environ.get('MAX_PAGES', '100'))))
    path = Path(os.environ.get('STATE_PATH', 'data/state.sqlite'))
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as db:
        sent, initialized = process(db, items, args.dry_run)
    print(f'Correspondências: {len(items)}. Novos avisos: {sent}.')
    if not initialized and not args.dry_run:
        telegram('sendMessage', {'chat_id': os.environ['TELEGRAM_CHAT_ID'], 'text':
            f'Monitor CSSDeals iniciado. Registrei {len(items)} anúncios existentes. Próximos avisos: tênis EU 45/46 e camisetas 2XL/3XL/4XL.'})


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as error:
        print(f'Execução interrompida ({type(error).__name__}). Confira acesso ao catálogo, segredos e limites; nenhum token será exibido.')
        raise SystemExit(1)

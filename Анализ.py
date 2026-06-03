# ==============================================================================
# 1. НАСТРОЙКА ОКРУЖЕНИЯ
# ==============================================================================
import re
import requests
import pandas as pd
from datetime import datetime
from google.colab import files

# ==============================================================================
# 2. ВХОДНЫЕ ДАННЫЕ (ОБНОВЛЕННЫЙ ID ПРИЛОЖЕНИЯ)
# ==============================================================================
# Прямая ссылка на приложение Альфа-Банка по его ID
app_url = "https://apps.apple.com/ru/app/id570060128"

# ==============================================================================
# 3. АВТОМАТИЧЕСКИЙ РАЗБОР ССЫЛКИ
# ==============================================================================
def parse_app_url(url):
    # Универсальное регулярное выражение, обрабатывающее ссылки как с именем, так и только с ID
    pattern = r"apps\.apple\.com/([a-z]{2})/app/(?:[^/]+/)?id(\d+)"
    match = re.search(pattern, url)
    if not match:
        raise ValueError("Не удалось распознать ссылку. Проверьте формат URL.")
    return match.group(1), match.group(2)

country, app_id = parse_app_url(app_url)
print(f"Парсинг приложения по запросу...")
print(f" -> ID приложения: {app_id}")
print(f" -> Регион поиска: {country.upper()}\n")

# ==============================================================================
# 4. СБОР ОТЗЫВОВ ЧЕРЕЗ ГЛОБАЛЬНЫЙ RSS-ШЛЮЗ
# ==============================================================================
print("Загрузка последних отзывов (лимит: 500 штук)...")
reviews_list = []

# Эмулируем заголовки реального устройства, чтобы избежать блокировок Apple
headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7"
}

# Цикл по 10 доступным страницам RSS-фида
for page in range(1, 11):
    rss_url = f"https://itunes.apple.com/{country}/rss/customerreviews/page={page}/id={app_id}/sortby=mostrecent/json"
   
    try:
        response = requests.get(rss_url, headers=headers, timeout=10)
       
        # Если страница вернула ошибку, значит, мы достигли лимита
        if response.status_code != 200:
            break
           
        data = response.json()
        feed = data.get('feed', {})
        entries = feed.get('entry', [])
       
        if not entries:
            break
           
        # Если отзыв на странице всего один, Apple пришлет словарь вместо списка
        if isinstance(entries, dict):
            entries = [entries]
           
        for entry in entries:
            # Пропускаем технический элемент с метаданными самого приложения
            if 'im:name' in entry:
                continue
               
            try:
                author = entry.get('author', {}).get('name', {}).get('label', 'Аноним')
                rating = entry.get('im:rating', {}).get('label', '0')
                title = entry.get('title', {}).get('label', '')
                content = entry.get('content', {}).get('label', '')
                date_raw = entry.get('updated', {}).get('label', '')[:10] # Формат YYYY-MM-DD
               
                reviews_list.append({
                    'Дата': date_raw,
                    'Имя пользователя': author,
                    'Рейтинг': int(rating),
                    'Заголовок': title,
                    'Отзыв': content
                })
            except Exception:
                continue
               
    except Exception as e:
        print(f"Ошибка при обработке страницы {page}: {e}")
        break

# ==============================================================================
# 5. СОХРАНЕНИЕ В CSV И АВТОМАТИЧЕСКОЕ СКАЧИВАНИЕ
# ==============================================================================
if not reviews_list:
    print("\n[!] Не удалось собрать отзывы. Приложение может быть временно скрыто в данном регионе или у него нет текстовых отзывов.")
else:
    # Удаляем возможные дубликаты по автору и тексту
    df_result = pd.DataFrame(reviews_list).drop_duplicates(subset=['Имя пользователя', 'Отзыв'])
    df_result = df_result.head(500)
   
    print(f"\nУспешно собрано отзывов: {len(df_result)}")
   
    # Сохраняем файл
    output_filename = 'reviews_570060128.csv'
    df_result.to_csv(output_filename, index=False, encoding='utf-8-sig')
    print(f"Данные сохранены в файл: {output_filename}")
   
    # Скачиваем на локальный компьютер
    print("Запуск скачивания...")
    files.download(output_filename)
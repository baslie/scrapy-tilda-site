import requests
from bs4 import BeautifulSoup, NavigableString, Comment
import re

# Теги, которые мы полностью игнорируем (не содержат текстовой информации)
IGNORE_TAGS = {"script", "style", "noscript", "iframe", "input", "img", "link"}

def process_node(node):
    """
    Рекурсивно обрабатывает узел и возвращает строку с его смысловой текстовой информацией.
    
    - Комментарии игнорируются.
    - Для NavigableString возвращается его очищенный текст.
    - Для тега <meta> с name="description" или property="og:description" возвращается <Description>content</Description>.
    - Для тега <title> возвращается <Title>content</Title>.
    - Теги из IGNORE_TAGS полностью пропускаются.
    - Для остальных тегов, если они входят в список разрешённых (например, html, head, body, div, span, p, h1–h6, li, ul, ol, a, button, nav, form), оборачиваем полученное содержимое в открывающий и закрывающий тег.
    - Если тег не входит в список, его содержимое просто возвращается без обёртки.
    - Если после обработки детей ничего не осталось – возвращается пустая строка.
    """
    # Удаляем комментарии
    if isinstance(node, Comment):
        return ""
    
    # Если это текст, возвращаем очищенный вариант
    if isinstance(node, NavigableString):
        text = str(node).strip()
        return text if text else ""
    
    # Если узел не имеет имени – пропускаем
    if not hasattr(node, 'name'):
        return ""
    
    tag = node.name.lower()
    
    # Игнорируем нежелательные теги
    if tag in IGNORE_TAGS:
        return ""
    
    # Специальная обработка для meta
    if tag == "meta":
        name_attr = node.get("name", "").lower()
        prop_attr = node.get("property", "").lower()
        if name_attr == "description" or prop_attr == "og:description":
            content = node.get("content", "").strip()
            if content:
                return f"<Description>{content}</Description>"
        return ""
    
    # Обработка для title
    if tag == "title":
        content = "".join(process_node(child) for child in node.children).strip()
        return f"<Title>{content}</Title>" if content else ""
    
    # Список тегов, для которых сохраняем обёртку
    allowed_wrap = {
        "html", "head", "body", "div", "span", "p",
        "h1", "h2", "h3", "h4", "h5", "h6",
        "li", "ul", "ol", "a", "button", "nav", "form"
    }
    
    # Рекурсивно обрабатываем детей
    children_content = "".join(process_node(child) for child in node.children).strip()
    if not children_content:
        return ""
    
    if tag in allowed_wrap:
        return f"<{tag}>{children_content}</{tag}>"
    else:
        # Если тег не входит в список, возвращаем только детей
        return children_content

def minify_html(html_str):
    """Минифицирует строку, заменяя все последовательности пробельных символов одним пробелом."""
    return re.sub(r'\s+', ' ', html_str).strip()

def main():
    url = "https://digitum.tilda.ws/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/110.0.0.0 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Ошибка при выполнении запроса: статус {response.status_code}")
        return
    html_text = response.text

    # Парсинг HTML
    soup = BeautifulSoup(html_text, "html.parser")
    
    # Удаляем все HTML-комментарии
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()
    
    # Начинаем обработку с тега <html>, если он есть, иначе всего документа
    root = soup.html if soup.html else soup
    extracted = process_node(root)
    minified = minify_html(extracted)
    
    output_file = "extracted_text_structure.html"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(minified)
    
    print(f"Файл с текстовой структурой сохранен как '{output_file}'")

if __name__ == "__main__":
    main()

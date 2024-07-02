import requests
from newspaper import Article
import re
from ebooklib import epub
import time
from newspaper.article import ArticleException
import pypandoc

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}


class CustomHTTPError(Exception):
    def __init__(self, status_code, url, message=""):
        self.status_code = status_code
        self.url = url
        self.message = message
        super().__init__(self.message)


def get_final_url(url):
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an HTTPError on bad status
        final_url = response.url
        return final_url
    except requests.exceptions.RequestException as e:
        if e.response.status_code == 429:
            raise CustomHTTPError(429, url, f"Too Many Requests: {e}")
        else:
            print(f"Error resolving URL {url}: {e}")
            raise e


def extract_content(url):
    try:
        final_url = get_final_url(url)
        article = Article(final_url)
        article.download()
        article.parse()
        return article.title, article.text
    except ArticleException as e:
        if "Status code 429" in str(e):
            raise CustomHTTPError(429, url, f"Too Many Requests: {e}")
        else:
            raise e
    except Exception as e:
        print(f"An error occurred while extracting content from {url}: {e}")
        raise e


def extract_chapters(base_url, start_chapter, end_chapter):
    chapters_content = []
    for chapter in range(start_chapter, end_chapter + 1):
        while True:
            try:
                url = re.sub(r'chapter-\d+', f'chapter-{chapter}', base_url)
                print(f"Extracting content from {url}")
                title, content = extract_content(url)
                if content:
                    chapters_content.append((chapter, title, content))
                time.sleep(2)  # Sleep for 1 second to avoid rate limiting
                break
            except CustomHTTPError as e:
                if e.status_code == 429:
                    print(f"Received 429 Too Many Requests for {e.url}. Waiting for 10 seconds before retrying...")
                    time.sleep(15)
                else:
                    print(f"HTTP error occurred: {e}")
                    raise e
            except Exception as e:
                print(f"An error occurred: {e}")
                raise e
    return chapters_content


def save_as_epub(chapters_content, epub_filename):
    book = epub.EpubBook()

    # Set metadata
    book.set_title("Extracted Webnovel")
    book.set_language("en")

    # Create chapters
    epub_chapters = []
    for chapter, title, content in chapters_content:
        epub_chapter = epub.EpubHtml(title=title, file_name=f'chap_{chapter}.xhtml', lang='en')
        epub_content = content.replace("\n", "<br />")
        epub_chapter.content = f'<h1>{title}</h1><p>{epub_content}</p>'
        book.add_item(epub_chapter)
        epub_chapters.append(epub_chapter)

    # Define Table Of Contents
    book.toc = (epub_chapters)

    # Add default NCX and Nav files
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # Define CSS style
    style = 'body { font-family: Times, serif; }'
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(nav_css)

    # Basic spine
    book.spine = ['nav'] + epub_chapters

    # Write to the file
    epub.write_epub(epub_filename, book, {})

def main():
    base_url = "https://www.lightnovelworld.com/novel/a-returners-magic-should-be-special-493/chapter-1"
    start_chapter = 1
    end_chapter = 3  # Specify the end chapter number here

    chapters_content = extract_chapters(base_url, start_chapter, end_chapter)
    epub_filename = "returners_magic.epub"
    pdf_filename = "returners_magic.pdf"

    save_as_epub(chapters_content, epub_filename)

    print(f"Extraction complete. Content saved to {epub_filename} and {pdf_filename}")


if __name__ == "__main__":
    main()

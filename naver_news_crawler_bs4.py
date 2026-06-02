import json
import re
import time
from typing import List, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

SEARCH_URL = (
    "https://search.naver.com/search.naver?where=nexearch&sm=top_hty&fbm=0&ie=utf8"
    "&query=%EB%B0%98%EB%8F%84%EC%B2%B4&ackey=gq8aptcy"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}



def fetch_html(url: str, timeout: int = 10) -> Optional[str]:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        if not resp.encoding or resp.encoding.lower() == "iso-8859-1":
            resp.encoding = resp.apparent_encoding
        return resp.text
    except requests.RequestException as exc:
        print(f"[ERROR] 요청 실패: {url}\n        이유: {exc}")
        return None



def extract_news_links(search_html: str) -> List[str]:
    soup = BeautifulSoup(search_html, "html.parser")
    links: List[str] = []

    def add_link_if_article(href: str):
        href = href.strip()
        if not href.startswith("http"):
            return

        lowered = href.lower()
        # 언론사 프로필/섹션/정적 페이지는 제외
        block_keywords = [
            "media.naver.com/press",
            "news.naver.com/main/static",
            "channelpromotion",
            "keep.naver.com",
            "search.naver.com",
        ]
        if any(keyword in lowered for keyword in block_keywords):
            return

        if href not in links:
            links.append(href)

    # 1) 질문에서 제공한 신규 구조(뉴스 카드 제목 링크) 우선
    for a_tag in soup.select(".fender-news-portal-container-desk a[data-heatmap-target='.tit']"):
        href = a_tag.get("href") or ""
        add_link_if_article(href)

    # 2) 일부 카드에서 제목 대신 본문/이미지 링크만 노출되는 경우 보완
    if not links:
        for selector in [
            ".fender-news-portal-container-desk a[data-heatmap-target='.body']",
            ".fender-news-portal-container-desk a[data-heatmap-target='.img']",
        ]:
            for a_tag in soup.select(selector):
                href = a_tag.get("href") or ""
                add_link_if_article(href)

    # 3) 백업: 네이버 뉴스 검색의 구형 선택자 대응
    if not links:
        for selector in ["a.news_tit", "a.title_link", "a[href*='n.news.naver.com/mnews/article']"]:
            for a_tag in soup.select(selector):
                href = a_tag.get("href") or ""
                add_link_if_article(href)

    # 4) 최후 fallback: 기사 패턴 URL만 수집
    if not links:
        article_url_patterns = [
            "n.news.naver.com/mnews/article",
            "news.naver.com",
            "/article/",
            "/news/",
            "?sid=",
        ]
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].strip()
            lowered = href.lower()
            if any(pattern in lowered for pattern in article_url_patterns):
                add_link_if_article(href)

    return links



def clean_text(raw_text: str) -> str:
    text = re.sub(r"\s+", " ", raw_text)
    return text.strip()



def extract_article_content(article_html: str, url: str) -> str:
    soup = BeautifulSoup(article_html, "html.parser")

    # 도메인별 우선 선택자
    parsed = urlparse(url)
    host = parsed.netloc.lower()

    priority_selectors: List[str] = []
    if "naver.com" in host:
        priority_selectors.extend(["#dic_area", "#newsct_article", "#articeBody"])

    # 일반 뉴스 사이트 대응 선택자
    priority_selectors.extend(
        [
            "article",
            "div[itemprop='articleBody']",
            "#articleBody",
            ".article_body",
            ".news_end",
            ".article_txt",
        ]
    )

    for selector in priority_selectors:
        node = soup.select_one(selector)
        if not node:
            continue

        for trash in node.select("script, style, noscript, iframe"):
            trash.decompose()

        text = clean_text(node.get_text(separator=" "))
        if len(text) >= 120:
            return text

    # 최후 fallback: 페이지 전체 텍스트에서 최소 길이 이상만 반환
    page_text = clean_text(soup.get_text(separator=" "))
    return page_text if len(page_text) >= 120 else ""



def crawl_news_articles(search_url: str, max_articles: int = 10, delay_sec: float = 0.4):
    search_html = fetch_html(search_url)
    if not search_html:
        return []

    links = extract_news_links(search_html)
    if not links:
        print("[INFO] 뉴스 링크를 찾지 못했습니다.")
        return []

    results = []
    for idx, link in enumerate(links[:max_articles], start=1):
        print(f"[INFO] ({idx}/{min(len(links), max_articles)}) 수집 중: {link}")

        article_html = fetch_html(link)
        if not article_html:
            continue

        article_text = extract_article_content(article_html, link)
        if not article_text:
            continue

        title = ""
        soup = BeautifulSoup(article_html, "html.parser")
        if soup.title and soup.title.string:
            title = clean_text(soup.title.string)

        results.append(
            {
                "title": title,
                "url": link,
                "content": article_text,
            }
        )

        time.sleep(delay_sec)

    return results



def save_to_json(data, output_path: str = "news_articles.json"):
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)



if __name__ == "__main__":
    articles = crawl_news_articles(SEARCH_URL, max_articles=10, delay_sec=0.3)

    print(f"\n총 수집 기사 수: {len(articles)}")
    if articles:
        save_to_json(articles)
        print("news_articles.json 파일로 저장했습니다.")

        # 콘솔에서 앞부분 미리보기
        preview_count = min(3, len(articles))
        for i in range(preview_count):
            item = articles[i]
            print(f"\n[{i + 1}] {item['title']}")
            print(f"URL: {item['url']}")
            print(f"본문 미리보기: {item['content'][:180]}...")
    else:
        print("수집된 기사가 없습니다.")

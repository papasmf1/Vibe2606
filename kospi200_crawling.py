import requests
from bs4 import BeautifulSoup
import pandas as pd

def get_kospi200_top_stocks(page=1):
    """
    네이버 금융 코스피200 편입종목상위 크롤링
    :param page: 페이지 번호 (기본값: 1, 페이지당 10개 종목)
    :return: 편입종목상위 데이터 리스트
    """
    # 편입종목상위 iframe URL (page 파라미터로 페이지 이동)
    url = f"https://finance.naver.com/sise/entryJongmok.naver?type=KPI200&page={page}"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Referer": "https://finance.naver.com/sise/sise_index.naver?code=KPI200",
    }

    response = requests.get(url, headers=headers)
    response.encoding = "euc-kr"  # 네이버 금융은 EUC-KR 인코딩 사용

    if response.status_code != 200:
        print(f"[오류] HTTP 상태 코드: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    # 테이블 탐색
    table = soup.find("table")
    if not table:
        print("[오류] 테이블을 찾을 수 없습니다.")
        return []

    stocks = []
    rows = table.find_all("tr")

    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 7:
            continue

        # 종목명 링크만 대상 (헤더, 빈 행 제외)
        name_tag = cols[0].find("a", href=lambda h: h and h.startswith("/item"))
        if not name_tag:
            continue
        name = name_tag.get_text(strip=True)
        if not name:
            continue

        # 종목 링크에서 종목 코드 추출
        href = name_tag.get("href", "")
        code = href.split("code=")[-1].strip() if "code=" in href else ""

        current_price = cols[1].get_text(strip=True).replace(",", "")
        change_raw    = cols[2].get_text(strip=True).replace(",", "")
        change_rate   = cols[3].get_text(strip=True)
        volume        = cols[4].get_text(strip=True).replace(",", "")
        trade_value   = cols[5].get_text(strip=True).replace(",", "")
        market_cap    = cols[6].get_text(strip=True).replace(",", "")

        # 등락 방향 추출 (이미지 alt 속성: 상승 / 하락 / 보합)
        direction_img = cols[2].find("img")
        direction = direction_img["alt"] if direction_img else ""

        stocks.append({
            "종목코드":      code,
            "종목명":        name,
            "현재가":        current_price,
            "전일비":        f"{direction} {change_raw}".strip(),
            "등락률":        change_rate,
            "거래량":        volume,
            "거래대금(백만)": trade_value,
            "시가총액(억)":   market_cap,
        })

    return stocks


def crawl_all_pages(max_pages=10):
    """
    여러 페이지의 편입종목상위 데이터를 수집합니다.
    :param max_pages: 최대 페이지 수 (기본값: 10)
    :return: 전체 데이터 DataFrame
    """
    all_stocks = []
    for page in range(1, max_pages + 1):
        print(f"[{page}/{max_pages}] 페이지 수집 중...")
        stocks = get_kospi200_top_stocks(page=page)
        if not stocks:
            print(f"  → 데이터 없음, 수집 종료")
            break
        all_stocks.extend(stocks)
        print(f"  → {len(stocks)}개 종목 수집")

    return pd.DataFrame(all_stocks)


if __name__ == "__main__":
    print("=" * 60)
    print("  네이버 금융 - 코스피200 편입종목상위 크롤링")
    print("=" * 60)

    # 1페이지만 수집
    print("\n[1페이지 데이터 조회]")
    stocks = get_kospi200_top_stocks(page=1)

    if stocks:
        df = pd.DataFrame(stocks)
        print(df.to_string(index=False))

        # 전체 페이지 수집 여부 선택
        print("\n전체 페이지를 모두 수집하시겠습니까? (y/n): ", end="")
        answer = input().strip().lower()
        if answer == "y":
            df_all = crawl_all_pages(max_pages=20)
            print(f"\n총 {len(df_all)}개 종목 수집 완료")
            print(df_all.to_string(index=False))

            # CSV 저장
            df_all.to_csv("kospi200_top_stocks.csv", index=False, encoding="utf-8-sig")
            print("\n[저장 완료] kospi200_top_stocks.csv")
    else:
        print("데이터를 가져오지 못했습니다.")

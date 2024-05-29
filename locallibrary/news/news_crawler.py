import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin
import schedule
import time
import threading

def crawl_and_save():
    # 기본 URL 설정
    base_url = "http://www.mediwelfare.com/news/articleList.html"
    article_base_url = "http://www.mediwelfare.com"
    params = {
        'sc_section_code': 'S1N8',
        'view_type': 'sm',
        'page': 1
    }

    # 모든 기사 정보를 담을 리스트
    all_articles = []

    # 페이지 순회
    while True:
        # 현재 페이지 URL
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # 요청이 성공했는지 확인

        # BeautifulSoup을 사용하여 페이지 파싱
        soup = BeautifulSoup(response.text, 'html.parser')

        # 기사 리스트를 담고 있는 HTML 요소를 찾기
        articles = soup.find_all('div', class_='list-block')

        if not articles:
            # 더 이상 기사가 없으면 종료
            break

        for article in articles:
            try:
                # 상세 페이지 URL
                div_tag = article.find('div', class_='list-titles')
                a_tag = div_tag.find('a') if div_tag else None
                relative_article_url = a_tag['href'] if a_tag else None
                article_url = urljoin(article_base_url, relative_article_url) if relative_article_url else None

                # 기사 상세 페이지 방문
                img_url = None
                if article_url:
                    article_response = requests.get(article_url)
                    article_response.raise_for_status()

                    article_soup = BeautifulSoup(article_response.text, 'html.parser')

                    # article-view-content-div id 안의 두 번째 div의 figure 안의 img 태그의 src 속성을 찾기
                    content_div = article_soup.find(id='article-view-content-div')
                    if content_div:
                        inner_divs = content_div.find_all('div')
                        if len(inner_divs) >= 2:
                            figure_tag = inner_divs[1].find('figure')
                            if figure_tag:
                                img_tag = figure_tag.find('img')
                                if img_tag and 'src' in img_tag.attrs:
                                    img_url = urljoin(article_base_url, img_tag['src'])
                                    print(f"Found image URL: {img_url}")
                                else:
                                    print("Image tag or src attribute not found")
                            else:
                                print("Figure tag not found")
                        else:
                            print("Not enough inner divs found")
                    else:
                        print("Content div not found")

                # 제목
                strong_tag = a_tag.find('strong') if a_tag else None
                title = strong_tag.get_text(strip=True) if strong_tag else "No Title"

                # 내용
                content_tag = article.find('p', class_='list-summary')
                content = content_tag.get_text(strip=True) if content_tag else "No Content"

                # 기자
                reporter_tag = article.find('div', class_='list-dated')
                reporter = reporter_tag.get_text(strip=True) if reporter_tag else "No Reporter"

                # 기사 정보를 리스트에 추가
                all_articles.append({
                    'url': article_url,
                    'img_url': img_url,
                    'title': title,
                    'content': content,
                    'reporter': reporter
                })
            except Exception as e:
                print(f"An error occurred while processing an article: {e}")

        # 다음 페이지로 이동
        params['page'] += 1

    # DataFrame으로 변환
    df = pd.DataFrame(all_articles)

    # CSV 파일로 저장
    df.to_csv('all_articles.csv', index=False, encoding='utf-8-sig')

    print("All data has been saved to all_articles.csv")

# 크롤링 및 저장 함수 실행
def job():
    print("Starting the crawling job...")
    crawl_and_save()

# 스케줄 설정
schedule.every().day.at("10:00").do(job)
schedule.every().day.at("22:00").do(job)

# 스케줄러 실행 루프를 백그라운드 스레드에서 실행
def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

# 스케줄러 실행을 위한 스레드 시작
schedule_thread = threading.Thread(target=run_schedule, daemon=True)
schedule_thread.start()

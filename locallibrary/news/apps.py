from django.apps import AppConfig
import threading
import time


class NewsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'news'

class NewsCrawler(AppConfig):
    name = 'myproject'

    def ready(self):
        import news.news_crawler  # 스케줄러를 불러옵니다

        # CSV 로드를 위한 스레드 시작
        def load_csv_on_start():
            from news.load_csv import load_csv
            load_csv('all_articles.csv')
        
        csv_thread = threading.Thread(target=load_csv_on_start, daemon=True)
        csv_thread.start()
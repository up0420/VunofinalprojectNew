import csv
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'locallibrary.settings')
django.setup()

from news.models import NewsArticle

def load_csv(file_path):
    with open(file_path, encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        for row in reader:
            NewsArticle.objects.create(
                url=row['url'],
                img_url=row['img_url'],
                title=row['title'],
                content=row['content'],
                reporter=row['reporter']
            )

if __name__ == "__main__":
    load_csv('all_articles.csv')

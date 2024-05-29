from django.core.paginator import Paginator
from django.shortcuts import render
from .models import NewsArticle

def news_list(request):
    articles = NewsArticle.objects.all().order_by('-pub_date')
    paginator = Paginator(articles, 10)  # 페이지 당 10개의 기사

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'news/news_list.html', {'page_obj': page_obj})

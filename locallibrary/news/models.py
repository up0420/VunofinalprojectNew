from django.db import models

class NewsArticle(models.Model):
    url = models.URLField(max_length=200)
    img_url = models.URLField(max_length=200, blank=True, null=True)
    title = models.CharField(max_length=200)
    content = models.TextField()
    reporter = models.CharField(max_length=100)
    pub_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

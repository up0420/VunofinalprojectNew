from django.urls import path
from catalog import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('', views.main, name = 'main'),
    path('main', views.main, name = 'main'),
    path('x-ray-2', views.xray, name = 'x-ray'),
    path('upload_image/', views.upload_image, name='upload_image'),
    path('get_patient_images/', views.get_patient_images, name ='get_patient_images'),
    path('board', views.board, name = 'board'),
    path('board_all', views.boardAll, name = 'board_all'),
    path('get_patient_data/', views.get_patient_data, name='get_patient_data'),
    path('get_allpatient_data/', views.get_allpatient_data, name='get_allpatient_data'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout_view'),
    path('analyze/', views.analyze_image, name='analyze_image'), 
    path('login/', views.login_view, name='login_view'),
    path('save_mir/', views.save_mir, name='save_mir'),
    path('mir_view/', views.mir_view, name='mir_view'),
    path('get_mir_data/', views.get_mir_data, name='get_mir_data'),
    path('get_ximage_id/', views.get_ximage_id, name='get_ximage_id'),
    path('contact', views.contact, name = 'contact'),
    path('qna', views.qna, name = 'qna'),
    path('chestMateRunner/', views.chestMateRunner, name = 'chestMateRunner'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


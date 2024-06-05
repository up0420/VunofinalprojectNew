from django.shortcuts import render
from django.views import generic
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from .models import XImage, Patient
import os
from .inference import run_inference, ChestMateRunner  # 여기서 main 함수를 불러옵니다
from django.conf import settings
from datetime import datetime
import logging
import cv2
import base64


# def patient_xrays(request, pat_id):
#     patient = get_object_or_404(Patient, PAT_ID=pat_id)
#     xrays = XImage.objects.filter(PAT_ID=patient)
#     return render(request, 'patient_xrays.html', {'patient': patient, 'xrays': xrays})


# 이미지 업로드
@csrf_exempt
def upload_image(request):
    if request.method == 'POST' and request.FILES.get('image'):
        image = request.FILES['image']
        patient_id = request.POST.get('patient_id', '')

        # XImage 모델의 인스턴스 생성
        ximage = XImage(PAT_ID_id=patient_id, XIMAGE_PATH=image)

        try:
            # 데이터베이스에 저장
            ximage.save()
            return JsonResponse({'success': True})
        except Exception as e:
            # 저장 실패 시 에러 응답
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        # POST 요청이 아니거나 이미지 파일이 없는 경우
        return JsonResponse({'success': False, 'error': 'No image file provided.'})
    
    
# 이미지 불러오기
# def get_patient_images(request):
#     if request.method == 'GET':
#         patient_id = request.GET.get('patient_id')
#         try:
#             # 해당 환자의 이미지 경로 불러오기
#             images = XImage.objects.filter(PAT_ID=patient_id).values_list('XIMAGE_PATH', flat=True)
#             # 이미지 경로들을 리스트로 변환하여 반환
#             image_urls = [image.url for image in images]
#             return JsonResponse({'success': True, 'images': image_urls})
#         except Exception as e:
#             return JsonResponse({'success': False, 'error': str(e)})
#     else:
#         return JsonResponse({'success': False, 'error': 'Invalid method'})


# 모델링 부분    

# views.py


# 경로를 이스케이프 문자로 수정
path_weight_cmptx = r'C:\VunofinalprojectNew\locallibrary\catalog\model_cmptx.pth'
path_weight_eff_atel = r'C:\VunofinalprojectNew\locallibrary\catalog\model_eff_atel.pth'

# ChestMateRunner 초기화
runner = ChestMateRunner(path_weight_cmptx, path_weight_eff_atel)



logger = logging.getLogger(__name__)

# 히트맵 이미지를 생성하는 함수
def generate_heatmap_image(image_path):
    # URL을 로컬 파일 경로로 변환
    if image_path.startswith('http://') or image_path.startswith('https://'):
        image_path = image_path.replace('http://127.0.0.1:8000/catalog/', '')
    
    if image_path.startswith('media/'):
        image_path = os.path.join(r'C:\VunofinalprojectNew\locallibrary', image_path)
    
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found at path: {image_path}")
    
    # ChestMateRunner를 사용하여 히트맵 생성
    result = runner.run(image_path)
    
    score_cm = result['cardiomegaly']['score']
    score_ptx = result['pneumothorax']['score']
    if score_cm > score_ptx:
        heatmap = result['cardiomegaly']['heatmap']
    else:
        heatmap = result['pneumothorax']['heatmap']

    # 히트맵 이미지가 올바르게 생성되었는지 확인
    if heatmap is None:
        raise ValueError("Heatmap generation failed: heatmap is None")

    _, buffer = cv2.imencode('.png', heatmap)
    if buffer is None or len(buffer) == 0:
        raise ValueError("Image encoding failed: buffer is None or empty")

    heatmap_base64 = base64.b64encode(buffer).decode('utf-8')
    return heatmap_base64

# 히트맵을 생성하는 뷰 함수
@csrf_exempt
def generate_heatmap(request):
    if request.method == 'POST':
        image_path = request.POST.get('image_path')
        logger.debug(f'Received image path: {image_path}')
        if image_path:
            try:
                heatmap = generate_heatmap_image(image_path)
                logger.debug('Heatmap generated successfully')
                if heatmap:
                    return JsonResponse({'heatmap': heatmap})
                else:
                    logger.error('Heatmap generation failed')
                    return JsonResponse({'error': 'Heatmap generation failed'}, status=400)
            except FileNotFoundError as e:
                logger.error(f'File not found: {e}')
                return JsonResponse({'error': str(e)}, status=404)
            except Exception as e:
                logger.error(f'Unexpected error: {e}')
                return JsonResponse({'error': str(e)}, status=500)
        logger.error('No image path provided')
        return JsonResponse({'error': 'No image path provided'}, status=400)
    logger.error('Invalid request method')
    return JsonResponse({'error': 'Invalid request method'}, status=405)

def analyze_image(request):
    image_path = request.GET.get('image_path')
    if image_path:
        # 이미지의 상대 경로 생성 및 절대 경로로 변환
        static_image_path = os.path.join(settings.MEDIA_ROOT, 'ximages', os.path.basename(image_path))
        print('경로' , static_image_path)
        
        model_path = os.path.join(settings.BASE_DIR, 'catalog', 'age.onnx')
        result = run_inference(model_path, static_image_path)
        return JsonResponse({'result': result})
    else:
        return JsonResponse({'error': 'No image path provided'}, status=400)

def chestMateRunner(request):
    Model = ChestMateRunner(path_weight_cmptx=path_weight_cmptx, 
                            path_weight_eff_atel=path_weight_eff_atel)
    
    image_path = request.GET.get('image_path')
    if image_path:
        # 이미지의 상대 경로 생성 및 절대 경로로 변환
        static_image_path = os.path.join(settings.MEDIA_ROOT, 'ximages', os.path.basename(image_path))
        print('경로:', static_image_path)
        
        result = Model.run(path_image=static_image_path)
        
        # 두 모델의 결과를 병합하여 직렬화 준비
        serialized_result = {
            'cardiomegaly': {'score': float(result['cardiomegaly']['score'])},
            'pneumothorax': {'score': float(result['pneumothorax']['score'])},
            'effusion': {'score': float(result['effusion']['score'])},
            'atelectasis': {'score': float(result['atelectasis']['score'])},
            # 'heatmap_image': result['heatmap']          
            }
        
        print("this is a json test:", serialized_result)
        return JsonResponse({'result': serialized_result})
    else:
        return JsonResponse({'error': 'No results provided'}, status=400)          

def get_patient_images(request):
    if request.method == 'GET' or request.method == 'POST':
        print("Request GET data:", request.GET)
        patient_id = request.GET.get('patient_id')
        print("Patient ID:", patient_id)
        if patient_id is None:
            return JsonResponse({'success': False, 'error': 'No patient_id provided'})
        try:
             # 해당 환자의 이미지 경로 불러오기
            images = XImage.objects.filter(PAT_ID=patient_id).values_list('XIMAGE_PATH', flat=True)
            # 이미지 경로들을 리스트로 변환하여 반환
            image_urls = [image for image in images]
            return JsonResponse({'success': True, 'images': image_urls})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid method'})






def xray(request) :
    patient_id = request.GET.get('patient_id')  # URL에서 patient_id 쿼리 매개변수 가져오기
   
    if patient_id:
        try:
            # patient_id를 사용하여 해당 환자를 가져옴
            patient = get_object_or_404(Patient, PAT_ID=patient_id)
            # 환자 정보를 가져와서 사용합니다.
            return render(request, 'X-ray-2.html', {'patient': patient})
        except Patient.DoesNotExist:
            # 해당 환자를 찾을 수 없을 때의 예외 처리
            return render(request, 'X-ray-2.html', {'error': '환자를 찾을 수 없습니다.'})
    else:
        # patient_id가 제공되지 않은 경우에 대한 예외 처리
        return render(request, 'X-ray-2.html', {'error': '환자 ID가 제공되지 않았습니다.'})

# from django.utils.decorators import method_decorator
# @method_decorator(csrf_exempt, name='dispatch')
def saveMIR(request):
    if request.method == 'POST':
        doc_id = request.session.get('doc_id')
        doctor = get_object_or_404(Doctor, DOC_ID=doc_id)
        ai_opinion = request.POST.get('ai_opinion')
        doctor_opinion = request.POST.get('doctor_opinion')
        ximage_id = request.POST.get('ximage_id')
        ximage = get_object_or_404(XImage, pk=ximage_id)
        
        print('doc_id: ', doc_id, 'doctor: ', doctor, 'ai_op: ' , ai_opinion, 'doc_op: ', doctor_opinion, 'ximage_id: ', ximage_id, 'ximage: ', ximage)

        try:
            ximage = XImage.objects.get(pk=ximage_id)
            doctor = Doctor.objects.first()

            mir, created = MIR.objects.update_or_create(
                XIMAGE_ID=ximage,
                defaults={
                    'MIR_RESULT': ai_opinion,
                    'MIR_MIR': doctor_opinion,
                    'DOC_ID': doctor,
                }
            )

            return JsonResponse({'status': 'success'})
        except XImage.DoesNotExist:
            return JsonResponse({'error': 'XImage not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=400)
    

def main(request):
    return render(request, 'main.html')

def board(request):
    return render(request, 'board.html')
def boardAll(request):
    return render(request, 'board_all.html')
def contact(request):
    return render(request, 'contact.html')
def qna(request):
    return render(request, 'qna.html')

# 비동기 게시판 구현
""" from django.http import JsonResponse
from .models import Patient

def get_patient_data(request):
    patients = Patient.objects.all()
    data = [{'id': patient.PAT_ID, 'name': patient.PAT_NAME, 'birthdate': patient.PAT_BIRTH} for patient in patients]
    return JsonResponse(data, safe=False) """


from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import Patient, XImage, Doctor, MIR

# def get_patient_data(request):
#     patients = Patient.objects.all()
#     paginator = Paginator(patients, 5)  # 페이지당 5개 테스트
#     page_number = request.GET.get('page')
#     page_obj = paginator.get_page(page_number)
    
#     data = {
#         'patients': [{'id': patient.PAT_ID, 'name': patient.PAT_NAME, 'birthdate': patient.PAT_BIRTH} for patient in page_obj],
#         'total_pages': paginator.num_pages
#     }

    
   
 
def get_patient_data(request):
    doc_id = request.session.get('doc_id')
    if doc_id is None:
        return JsonResponse({'error': 'No doc_id found in session'}, status=400)

    search_date_start = request.GET.get('search_date_start')
    search_date_end = request.GET.get('search_date_end')
    search_name = request.GET.get('search_name')
  
    patients = Patient.objects.filter(DOC_ID=doc_id)
    
    if search_name:
        patients = patients.filter(PAT_NAME__icontains=search_name)
    
    if search_date_start and search_date_end:
        patients = patients.filter(PAT_BIRTH__range=[search_date_start, search_date_end])
    
    paginator = Paginator(patients, 5)  # 페이지당 5개의 항목
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    patient_data = []
    for patient in page_obj:
        ximage = XImage.objects.filter(PAT_ID=patient).first()
        mir_data = None
        if ximage:
            mir = MIR.objects.filter(XIMAGE_ID=ximage).first()
            if mir:
                mir_data = {
                    'result': mir.MIR_RESULT,
                    'mir': mir.MIR_MIR,
                    'date': mir.MIR_DATE.strftime('%Y-%m-%d')
                }

        patient_data.append({
            'id': patient.PAT_ID,
            'name': patient.PAT_NAME,
            'birthdate': patient.PAT_BIRTH,
            'mir_data': mir_data
        })

    data = {
        'patients': patient_data,
        'total_pages': paginator.num_pages
    }
    return JsonResponse(data, safe=False)


 


def get_allpatient_data(request):
    search_date_start = request.GET.get('search_date_start')
    search_date_end = request.GET.get('search_date_end')
    search_name = request.GET.get('search_name')
    search_major = request.GET.get('search_major')

    patients = Patient.objects.all()
    
    if search_name:
        patients = patients.filter(PAT_NAME__icontains=search_name)
    
    if search_date_start and search_date_end:
        patients = patients.filter(PAT_BIRTH__range=[search_date_start, search_date_end])
    if search_major:
        try:
            # 검색한 진료 과목에 해당하는 의사들의 doc_major 값을 가져옴
            doctor_major_list = Doctor.objects.filter(DOC_ID__in=patients.values_list('DOC_ID', flat=True)).values_list('DOC_MAJOR', flat=True)
            
            # search_major와 일치하는 환자들만 필터링
            filtered_patients = patients.filter(DOC_ID__DOC_MAJOR=search_major)
    
            if filtered_patients:
                patients = filtered_patients
            else:
                # 검색 결과가 없는 경우 처리
                return JsonResponse({'error': 'No patients found with the given major'}, status=400)
        except Doctor.DoesNotExist:
            return JsonResponse({'error': 'No doctor found with the given major'}, status=400)
        

        
        
    paginator = Paginator(patients, 5)  # 페이지당 5개의 항목
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    

    logging.basicConfig(
    level=logging.DEBUG,  # 로그 레벨 설정 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(levelname)s - %(message)s',  # 로그 포맷 설정
    filename='debug.log',  # 로그 파일명 설정
)
    print('check_patient:' , patients)
    
    patient_data = []
    for patient in page_obj:
        print('page_object', page_obj)
        print('check_patient after check:' , patient)
        ximage = XImage.objects.filter(PAT_ID=patient.PAT_ID).first()
        print('check_ximage:' , ximage)
        if ximage:
            mir = MIR.objects.filter(XIMAGE_ID=ximage).order_by('MIR_DATE').first()
            print('check_mir:' , mir)
            if mir:
                mir_data = {
                    'result': mir.MIR_RESULT,
                    'mir': mir.MIR_MIR,
                    'date': mir.MIR_DATE.strftime('%Y-%m-%d')
                }
            else: mir_data = None
        else: mir_data = None          
        #logging.debug("Mir_data: %s", mir)  # 로그 기록
        patient_data.append({
            'id': patient.PAT_ID,
            'name': patient.PAT_NAME,
            'birthdate': patient.PAT_BIRTH,
            'mir_data': mir_data
        })
        
    data = {
        'patients': patient_data,
        'total_pages': paginator.num_pages
    }
    return JsonResponse(data, safe=False)




from django.core.exceptions import ValidationError
from django.utils.dateparse import parse_date

# def board(request):
#     search_name = request.GET.get('search_name', '')
#     search_date_start = request.GET.get('search_date_start', '')
#     search_date_end = request.GET.get('search_date_end', '')
#     page_number = request.GET.get('page')

#     filters = {}
    
#     if search_name:
#         filters['PATIENT__PAT_NAME__icontains'] = search_name

#     if search_date_start:
#         try:
#             start_date = parse_date(search_date_start)
#             if start_date is None:
#                 raise ValidationError("Invalid date format")
#             filters['mir__MIR_DATE__gte'] = start_date
#         except ValidationError:
#             pass

#     if search_date_end:
#         try:
#             end_date = parse_date(search_date_end)
#             if end_date is None:
#                 raise ValidationError("Invalid date format")
#             filters['mir__MIR_DATE__lte'] = end_date
#         except ValidationError:
#             pass

#     results = XImage.objects.select_related('PATIENT', 'MIR').filter(**filters).values(
#         'XIMAGE_ID', 'PATIENT__PAT_NAME', 'PATIENT__PAT_BIRTH', 'mir__MIR_DATE'
#     )
    
#     paginator = Paginator(results, 5)  # 페이지당 5개씩
#     page_obj = paginator.get_page(page_number)





#회원가입
from django.contrib import messages
from django.shortcuts import render, redirect
from .forms import DoctorForm

def register(request):
    if request.method == "POST":
        form = DoctorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('main')  
    else:
        form = DoctorForm()
    return render(request, 'main.html', {'form': form})


# 로그인
from django.shortcuts import render, redirect
from .models import Doctor

def login_view(request):
    if request.method == 'POST':
        doc_id = request.POST.get('id')
        doc_pw = request.POST.get('password')
        
        try:
            doctor = Doctor.objects.get(DOC_ID=doc_id)
            if doctor.DOC_PW == doc_pw:
                # 세션에 doc_id와 doc_name 저장
                request.session['doc_id'] = doctor.DOC_ID
                request.session['doc_name'] = doctor.DOC_NAME
                request.session['doc_major'] = doctor.DOC_MAJOR
                return redirect('board')
            else:
                return render(request, 'main.html', {'error': '아이디 또는 비밀번호가 올바르지 않습니다.'})
        except Doctor.DoesNotExist:
            return render(request, 'main.html', {'error': '아이디 또는 비밀번호가 올바르지 않습니다.'})
            
    else:
        return render(request, 'main.html')
    
# 로그아웃
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import logout
# def logout_view(request):
#     auth_logout(request)
#     request.session.flush()
#     return redirect('main')


@csrf_exempt
def logout_view(request):

    if request.method in ['POST', 'GET']:
        auth_logout(request)
        request.session.flush()
        response = redirect('main')
        response.delete_cookie('sessionid')
        return response
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=400)



#mir에 저장하기
import json
from django.http import JsonResponse
from .models import XImage, Doctor, MIR

def save_mir(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            ai_result = data.get('ai_result')
            doctor_opinion = data.get('doctor_opinion')
            patient_id = data.get('patient_id')
            image_url = data.get('image_url')  # Assuming image_url is passed in the request

            # Find the XImage object using the image path (URL)
            ximage = XImage.objects.get(PAT_ID=patient_id, XIMAGE_PATH=image_url)
            doc_id = request.session.get('doc_id')
            doctor = get_object_or_404(Doctor, DOC_ID=doc_id)
            mir = MIR.objects.create(
                XIMAGE_ID=ximage,
                MIR_RESULT=ai_result,
                MIR_MIR=doctor_opinion,
                DOC_ID=doctor
            )
            mir.save()
            return JsonResponse({'success': True})
        except XImage.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'XImage not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        print("Invalid request method:", request.method)
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

#mir_view
def mir_view(request):
    patient_id = request.GET.get('patient_id')
    if not patient_id:
        # patient_id가 없을 경우에 대한 처리
        return render(request, 'error.html', {'message': 'No patient ID provided.'})

    patient = get_object_or_404(Patient, PAT_ID=patient_id)
    return render(request, 'mir_view.html', {'patient': patient})

# mir data 가져오기
from django.http import JsonResponse
from .models import XImage, MIR
def get_mir_data(request):
    ximage_id = request.GET.get('ximage_id')
    if not ximage_id:
        return JsonResponse({'success': False, 'error': 'No ximage_id provided'})
    
    try:
        ximage = XImage.objects.get(XIMAGE_ID=ximage_id)
        mir_data = MIR.objects.get(XIMAGE_ID=ximage)
        return JsonResponse({
            'success': True,
            'ai_opinion': mir_data.MIR_RESULT,
            'doctor_opinion': mir_data.MIR_MIR
        })
    except XImage.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'XImage not found'})
    except MIR.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'MIR data not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def get_ximage_id(request):
    image_path = request.GET.get('image_path')
    if not image_path:
        return JsonResponse({'success': False, 'error': 'No image_path provided'})
    
    try:    
        ximage = XImage.objects.get(XIMAGE_PATH=image_path)
        return JsonResponse({'success': True, 'ximage_id': ximage.XIMAGE_ID})
    except XImage.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'XImage not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


// AI Analysis
document.getElementById('analysis').addEventListener('click', function() {
    var imagePath = document.getElementById('main-image').getAttribute('src');
    console.log('imagePath' + imagePath)
    fetch(`/catalog/analyze/?image_path=${imagePath}`)
        .then(response => response.json())
        .then(data => {
            if (data.result) {
                document.getElementById('ai-opinion').textContent = `AI 소견: ${data.result}`;
                document.getElementById('ai-opinion').classList.remove('hidden');
            } else {
                console.error('AI 분석 결과가 없습니다.');
            }
        })
        .catch(error => {
            console.error('오류 발생:', error);
        });
});



document.addEventListener('DOMContentLoaded', (event) => {
    // 초기 썸네일 이미지에 이벤트 리스너 추가 
    // 메인 <-> 썸네일 이미지 전환 
    initializeThumbnails();
}); 


// 썸네일 비우는 함수
function clearThumbnails() {
    const thumbnailImagesDiv = document.querySelector('.thumbnail-images');
    thumbnailImagesDiv.innerHTML = ''; // 비워주기
}


// 메인 이미지를 설정하는 함수
function setMainImage(imageUrl) {
    var mainImage = document.getElementById('main-image');
   
    mainImage.src = `media/${imageUrl}`;
    console.log('mainImage: ' + mainImage);
    console.log('imgurl: ' + imageUrl);
    console.log('mainImage.src : ' + mainImage.src);


    // // main-container 요소를 가져옵니다.
    // var mainContainer = document.querySelector('.main-container');
    
    // // mainImage를 main-container에 추가합니다.
    // mainContainer.appendChild(mainImage);
}

// 이미지를 썸네일에 추가하는 함수
function addThumbnail(imageUrl) {
    var newImage = document.createElement('img');
    newImage.src = `media/${imageUrl}`
    newImage.className = 'thumbnail';
    newImage.alt = 'X-Ray Thumbnail';

    var thumbnailImagesDiv = document.querySelector('.thumbnail-images');
    thumbnailImagesDiv.appendChild(newImage);

    // 새로 추가된 썸네일에 이벤트 리스너 추가
    newImage.addEventListener('click', function() {
        setMainImage(imageUrl); // 이미지 클릭시 메인이미지로 변경
    });
}


// 썸네일 클릭 시, 메인 이미지로 변경하는 이벤트 리스너를 초기화하는 함수
function initializeThumbnails() {
    const thumbnails = document.querySelectorAll('.thumbnail');
    thumbnails.forEach(thumbnail => {
        thumbnail.addEventListener('click', function() {
            setMainImage(thumbnail.src.replace(window.location.origin + '/', ''));
        });
    });
}


// add 버튼 클릭 시 이미지 추가 
document.getElementById('add-image').addEventListener('click', function() {
    document.getElementById('image-input').click();
});

// 썸네일 + 메인이미지 변경
document.getElementById('image-input').addEventListener('change', function(event) {
    var file = event.target.files[0];

    if (file) {
        var reader = new FileReader(); // 선택된 파일을 FileReader 를 통해 읽기
        
        reader.onload = function(e) {
            var newImage = document.createElement('img');
            newImage.src = e.target.result ;  // e.target은 FileReader 객체이고, result는 읽은 파일의 데이터 URL
            newImage.className = 'thumbnail';
            newImage.alt = 'New X-Ray Thumbnail';
            console.log('add image 경로 : ' + newImage.src);
            var thumbnailImagesDiv = document.querySelector('.thumbnail-images');
            thumbnailImagesDiv.appendChild(newImage.cloneNode());  

            var mainImage = document.getElementById('main-image');
            mainImage.src = e.target.result;


            // 새로 추가된 썸네일에 이벤트 리스너 추가
            newImage.addEventListener('click', function() {
                setMainImage(newImage.src);
            });
        }
        
        reader.readAsDataURL(file);  // 파일의 데이터를 Base64 인코딩된 데이터 URL로 변환
    } else {
        alert("Please select an image file.");
    }
});

// 이미지 저장

// board.html에서 가져온 patient_id를 x-ray-2.html의 js부분에서 사용할 수 있게끔 구현하는 방법
// 원래는 String형태로 반환이 되었는데 이렇게 하니까 int형으로 반환해줌
const queryString = window.location.search;
const urlParams = new URLSearchParams(queryString);
const patientId = urlParams.get('patient_id');

console.log(patientId); // patientId 값을 확인
document.getElementById('save-image').addEventListener('click', () => {
    const fileInput = document.getElementById('image-input');
    const file = fileInput.files[0];
    if (file) {
        const formData = new FormData();
        formData.append('image', file);
        formData.append('patient_id', patientId);

        fetch('upload_image/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data && data.success) {
                console.log(data)
                alert('Image saved successfully!');
            } else {
                console.log(data)
                console.log(patientId)
                alert('Failed to save image.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error occurred while saving the image.');
        });
    } else {
        alert('No image selected.');
    }
});

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// 페이지가 로드될 때 실행되는 함수
window.addEventListener('DOMContentLoaded', function() {
    loadPatientImages(); // 환자의 이미지를 불러오는 함수 호출
});

// 환자의 이미지를 불러오는 함수
function loadPatientImages() {
    const patientId = new URLSearchParams(window.location.search).get('patient_id'); // URL에서 patient_id 값을 가져옵니다.
    if (!patientId) {
        console.error('No patient_id found in URL');
        return;
    }

    console.log(`Fetching images for patient_id: ${patientId}`);
    
    // AJAX 요청을 보냅니다.
    fetch(`get_patient_images/?patient_id=${patientId}`)
        .then(response => response.json())
        .then(data => {
            // 데이터 형태확인
            console.log('Received data:', data, 'patientId:', patientId); 
            // data가 배열인지 확인 (환자 한명당 사진이 여러개인지 확인)
            if (Array.isArray(data.images) && data.images.length > 0) {
                // 이미지 목록 로드
                const mainImageUrl = data.images[0];
                setMainImage(mainImageUrl);

                // 썸네일 비우기
                clearThumbnails();

                // 나머지 이미지가 있으면 썸네일로 추가
                if (data.images.length > 1) {
                    data.images.slice(1).forEach(imageUrl => {
                        addThumbnail(imageUrl);
                    });
                }
            } else {
                console.error('Error: Data is not an array or empty.');
            }
        })
        .catch(error => {
            console.error('Error fetching patient images:', error);
        });
}

// 전 페이지로 이동하는 함수
function goBack() {
    window.location.href = 'board'; // 'board' 페이지로 이동
}

// Analysis 버튼 클릭 시 분석 시작 
function updateBar() {
    // hidden 해놓은 ai 소견 내역을 visible로 변경하기
    var hiddenElements = document.querySelectorAll('.hidden');
    
    hiddenElements.forEach(function(element) {
        element.classList.remove('hidden');
    });

    // 일단 임의 데이터
    const data = [
        { name: 'Effusion', percentage: Math.floor(Math.random() * 100) },
        { name: 'Cardiomegaly', percentage: Math.floor(Math.random() * 100) },
        { name: 'Fibrosis', percentage: Math.floor(Math.random() * 100) }
    ];

    // 각 데이터 항목 업데이트
    data.forEach((item, index) => {
        const findingName = document.getElementById(`finding${index + 1}`);
        const bar = document.getElementById(`bar${index + 1}`);
        const percentageText = document.getElementById(`percentageText${index + 1}`);

        findingName.textContent = item.name;
        bar.style.width = item.percentage + '%';
        percentageText.textContent = item.percentage + '%';
    });
}


// 이미지 확대 축소 
document.addEventListener("DOMContentLoaded", function() {
    const zoomInIcon = document.getElementById("zoom-in-icon");
    const zoomOutIcon = document.getElementById("zoom-out-icon");
    const zoomRange = document.getElementById("zoom-range");
    const mainImage = document.getElementById("main-image");
    let currentScale = 1;
    let initialX = 0;
    let initialY = 0;
    let xOffset = 0;
    let yOffset = 0;
    let isMouseDown = false;

    zoomInIcon.addEventListener("click", function() {
        if(zoomRange.style.visibility == "visible"){
            zoomRange.style.visibility = "hidden";
        }else{
            zoomRange.style.visibility = "visible";
        }

        if (currentScale < 2) { // 최대 확대 배율 설정
            currentScale += 0.1;
            applyTransform();
        }
    });

    zoomOutIcon.addEventListener("click", function() {
        if (currentScale > 0.5) { // 최소 축소 배율 설정
            currentScale -= 0.1;
            applyTransform();
        }
    });

    zoomRange.addEventListener("input", function() {
        currentScale = parseFloat(zoomRange.value) / 100;
        applyTransform();
    });

    // 마우스로 이미지 이동
    mainImage.addEventListener("mousedown", function(event) {
        isMouseDown = true;
        initialX = event.clientX - xOffset;
        initialY = event.clientY - yOffset;
    });

    // 마우스로 이미지 이동
    mainImage.addEventListener("mouseup", function() {
        isMouseDown = false;
    });

    // 마우스로 이미지 이동
    mainImage.addEventListener("mousemove", function(event) {
        if (isMouseDown) {
            const mouseX = event.clientX - initialX;
            const mouseY = event.clientY - initialY;
            xOffset = mouseX;
            yOffset = mouseY;
            applyTransform();
        }
    });
    

    function applyTransform() {
        mainImage.style.transform = `scale(${currentScale})  translate(${xOffset}px, ${yOffset}px)`;
    } /* 이미지 위치 : translate(${xOffset}px, ${yOffset}px) */
});



// 새로고침 버튼
document.addEventListener("DOMContentLoaded", function() {
    const returnButton = document.getElementById("return");
    const mainImage = document.getElementById("main-image");
    let currentScale = 1;

    const canvas = document.getElementById('drawing-canvas');
    const ctx = canvas.getContext('2d');
    
    returnButton.addEventListener("click", function() {
        // 이미지 크기 되돌리기
        currentScale = 1;
        mainImage.style.transform = `scale(${currentScale})`;
        mainImage.style.transformOrigin = "center center";
        
        // 그림 있다면 지우기
        if (canvas.style.pointerEvents === 'auto') {
            canvas.style.pointerEvents = 'none';
            ctx.clearRect(0, 0, canvas.width, canvas.height); // 그려져 있다면 지워버리기
        }
    });
});



// 그리기 활성화
document.addEventListener('DOMContentLoaded', () => {
    const penIcon = document.querySelector('.fi.fi-sr-pen-nib');
    const mainImage = document.getElementById('main-image');
    const canvas = document.getElementById('drawing-canvas');
    const ctx = canvas.getContext('2d');

    // 캔버스를 이미지 크기에 맞춤
    function resizeCanvas() {
        canvas.width = mainImage.width;
        canvas.height = mainImage.height;
        canvas.style.pointerEvents = 'none'; // 기본적으로 그리기 비활성화
    }

    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    let isDrawing = false;

    // 마우스 이벤트 핸들러 함수
    function startDrawing(event) {
        isDrawing = true;
        ctx.beginPath();
        ctx.moveTo(event.offsetX, event.offsetY);
    }

    function draw(event) {
        if (!isDrawing) return;
        ctx.lineTo(event.offsetX, event.offsetY);
        ctx.stroke();
    }

    function stopDrawing() {
        isDrawing = false;
        ctx.closePath();
    }

    // 아이콘 클릭 시 캔버스 활성화/비활성화
    penIcon.addEventListener('click', () => {
        if (canvas.style.pointerEvents === 'none') {
            canvas.style.pointerEvents = 'auto';
            ctx.strokeStyle = 'red'; // 선 색상
            ctx.lineWidth = 2; // 선 두께
        } else {
            canvas.style.pointerEvents = 'none';
            ctx.clearRect(0, 0, canvas.width, canvas.height); // 그려져 있다면 지워버리기
        }
    });

    // 캔버스에 마우스 이벤트 리스너 추가
    canvas.addEventListener('mousedown', startDrawing);
    canvas.addEventListener('mousemove', draw);
    canvas.addEventListener('mouseup', stopDrawing);
    canvas.addEventListener('mouseout', stopDrawing);
});


document.addEventListener('DOMContentLoaded', () => {
    const svgIcon = document.querySelector('.fi');
    const mainImage = document.getElementById('main-image');
    let brightness = 1;

    svgIcon.addEventListener('click', () => {
        // 명암을 조절하는 로직 (값을 토글)
        brightness = brightness === 1 ? 0.5 : 1; // 예시: 1과 0.5 사이를 토글
        mainImage.style.filter = `brightness(${brightness})`;
    });
});



// 대비 조절  
document.addEventListener('DOMContentLoaded', () => {
    const contrastSlider = document.getElementById('contrast-slider');
    const mainImage = document.getElementById('main-image');

    contrastSlider.addEventListener('input', () => {
        const contrastValue = contrastSlider.value;
        mainImage.style.filter = `contrast(${contrastValue}%)`;
    });
});


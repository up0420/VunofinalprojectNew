


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
    if (mainImage) {
        mainImage.src = `/media/${imageUrl}`;
        console.log('mainImage:', mainImage);
        console.log('imgurl:', imageUrl);
        console.log('mainImage.src:', mainImage.src);
    } else {
        console.error('Main image element not found.');
    }
}

function setMainImage(imageUrl) {
    var mainImage = document.getElementById('main-image');
    if (mainImage) {
        mainImage.src = `/media/${imageUrl}`;
        console.log('mainImage:', mainImage);
        console.log('imgurl:', imageUrl);
        console.log('mainImage.src:', mainImage.src);
        
        // imageUrl을 이용하여 MIR 데이터를 가져오는 함수 호출
        fetchMIRData(imageUrl);
    } else {
        console.error('Main image element not found.');
    }
}



function addThumbnail(imageUrl) {
    var newImage = document.createElement('img');
    newImage.src = `/media/${imageUrl}`;
    newImage.className = 'thumbnail';
    newImage.alt = 'X-Ray Thumbnail';

    var thumbnailImagesDiv = document.querySelector('.thumbnail-images');
    if (thumbnailImagesDiv) {
        thumbnailImagesDiv.appendChild(newImage);

        // 새로 추가된 썸네일에 이벤트 리스너 추가
        newImage.addEventListener('click', function() {
            setMainImage(imageUrl); // 이미지 클릭시 메인이미지로 변경
        });
    } else {
        console.error('Thumbnails container not found.');
    }
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



// board.html에서 가져온 patient_id를 x-ray-2.html의 js부분에서 사용할 수 있게끔 구현하는 방법
// 원래는 String형태로 반환이 되었는데 이렇게 하니까 int형으로 반환해줌
const queryString = window.location.search;
const urlParams = new URLSearchParams(queryString);
const patientId = urlParams.get('patient_id');

console.log(patientId); // patientId 값을 확인

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

function loadPatientImages() {
    const patientId = new URLSearchParams(window.location.search).get('patient_id');
    if (!patientId) {
        console.error('No patient_id found in URL');
        return;
    }

    console.log(`Fetching images for patient_id: ${patientId}`);

    fetch(`/catalog/get_patient_images/?patient_id=${patientId}`)
        .then(response => response.json())
        .then(data => {
            console.log('Received data:', data);
            if (data.success && Array.isArray(data.images) && data.images.length > 0) {
                const mainImageUrl = data.images[0];
                setMainImage(mainImageUrl);

                clearThumbnails();

                if (data.images.length > 1) {
                    data.images.slice(1).forEach(imageUrl => {
                        addThumbnail(imageUrl);
                    });
                }
            } else {
                console.error('Error: Data is not an array or is empty.');
            }
        })
        .catch(error => {
            console.error('Error fetching patient images:', error);
        });
}

document.addEventListener('DOMContentLoaded', function() {
    loadPatientImages();
});


// 전 페이지로 이동하는 함수
function goBack() {
    window.location.href = '/catalog/board_all';
}


function fetchMIRData(imagePath) {
    fetch(`/catalog/get_ximage_id/?image_path=${imagePath}`)
        .then(response => response.json())
        .then(data => {
            console.log('ximage_id:', data);
            if (data.success) {
                const ximageId = data.ximage_id;
                fetch(`/catalog/get_mir_data/?ximage_id=${ximageId}`)
                    .then(response => response.json())
                    .then(data => {
                        console.log('ai/doctor opinion:', data);
                        if (data.success) {
                            // ai-opinion 값에 toFixed(2) 적용하여 소수점 이하 두 자리까지 표시
                            const aiOpinion = parseFloat(data.ai_opinion).toFixed(2);
                            document.getElementById('ai-opinion').innerHTML = aiOpinion;
                            document.getElementById('doctor-opinion').value = data.doctor_opinion;
                        } else {
                            console.error('Error fetching MIR data:', data.error);
                        }
                    })
                    .catch(error => {
                        console.error('Error fetching MIR data:', error);
                    });
            } else {
                console.error('Error fetching XImage ID:', data.error);
            }
        })
        .catch(error => {
            console.error('Error fetching XImage ID:', error);
        });
}






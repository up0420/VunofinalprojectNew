import torch
from torchvision import transforms, models
from PIL import Image
import torch.nn as nn
import pandas as pd

# GPU 사용 설정
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# 모델 설정 (ResNet18)
def initialize_model(num_classes):
    model = models.resnet18(weights='DEFAULT')
    num_ftrs = model.fc.in_features
    model.fc = nn.Linear(num_ftrs, num_classes)
    model = model.to(device)
    return model

# 모델과 가중치 로드
def load_model_weights(model, weights_path):
    model.load_state_dict(torch.load(weights_path))
    model.eval()
    return model

# 예측
def predict(image_path, model, transform):
    # 이미지 로드 및 전처리
    image = Image.open(image_path).convert('RGB')
    image = transform(image).unsqueeze(0)  # 배치 차원 추가
    image = image.to(device)

    # 모델 예측
    with torch.no_grad():
        outputs = model(image)
        preds = (outputs > 0.5).float()

    #예측값 nparr 형태로 반환 
    return preds.cpu().numpy()

# 데이터 변환 설정 (평가용)
data_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

def main(image_path, weights_path, num_classes):
    # Initialize and load model
    model = initialize_model(num_classes)
    model = load_model_weights(model, weights_path)

    # Predict
    predictions = predict(image_path, model, data_transform)
    print("Predictions:", predictions)

if __name__ == "__main__":
    # 예측할 이미지 경로 설정
    image_path = 'path_to_new_image.jpg'  # 예측할 이미지 경로
    weights_path = 'chest_xray_model.pth'  # 모델 가중치 경로
    num_classes = 2  # 클래스 수 (변경 필요 시 수정)

    # Run main function
    main(image_path, weights_path, num_classes)

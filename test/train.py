import os
import pandas as pd
from PIL import Image
import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms, models
import torch.nn as nn
import torch.optim as optim

# 데이터셋 경로 설정
image_dir = 'c:/nih/images'
csv_file = 'c:/nih/nih.csv'

# CSV 파일 읽기
df = pd.read_csv(csv_file)

# 흉부 X-ray 데이터셋 클래스 정의
class ChestXrayDataset(Dataset):
    def __init__(self, csv_file, image_dir, transform=None):
        self.labels_df = pd.read_csv(csv_file)
        self.image_dir = image_dir
        self.transform = transform

    def __len__(self):
        return len(self.labels_df)

    def __getitem__(self, idx):
        img_name = os.path.join(self.image_dir, self.labels_df.iloc[idx, 0])
        image = Image.open(img_name).convert('RGB')
        label = self.labels_df.iloc[idx, 1:].values
        label = label.astype('float')

        if self.transform:
            image = self.transform(image)

        return image, torch.tensor(label)

# 데이터 변환 설정
data_transforms = {
    'train': transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ]),
    'val': transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ]),
}

# 데이터셋 및 데이터 로더 설정
train_dataset = ChestXrayDataset(csv_file, image_dir, transform=data_transforms['train'])
val_dataset = ChestXrayDataset(csv_file, image_dir, transform=data_transforms['val'])

train_loader = DataLoader(train_dataset, batch_size=128, shuffle=True, num_workers=4)
val_loader = DataLoader(val_dataset, batch_size=128, shuffle=False, num_workers=4)

dataloaders = {'train': train_loader, 'val': val_loader}
dataset_sizes = {'train': len(train_dataset), 'val': len(val_dataset)}

# GPU 사용 설정
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# 모델 설정
model = models.resnet18(weights='DEFAULT')
num_ftrs = model.fc.in_features
model.fc = nn.Linear(num_ftrs, len(df.columns) - 1)  # 라벨의 수에 맞게 출력 차원 설정

model = model.to(device)

# 손실 함수 및 옵티마이저 설정
criterion = nn.BCEWithLogitsLoss()  # 다중 라벨 분류를 위한 손실 함수
optimizer = optim.SGD(model.parameters(), lr=0.001, momentum=0.9)

# 학습 함수 정의
def train_model(model, criterion, optimizer, dataloaders, dataset_sizes, device, num_epochs=25, checkpoint_interval=5):
    best_model_wts = model.state_dict()
    best_loss = float('inf')

    for epoch in range(num_epochs):
        print(f'Epoch {epoch}/{num_epochs - 1}')
        print('-' * 10)

        for phase in ['train', 'val']:
            if phase == 'train':
                model.train()  # 모델을 학습 모드로 설정
            else:
                model.eval()   # 모델을 평가 모드로 설정

            running_loss = 0.0
            running_corrects = 0

            for inputs, labels in dataloaders[phase]:
                inputs = inputs.to(device)
                labels = labels.to(device)

                optimizer.zero_grad()

                with torch.set_grad_enabled(phase == 'train'):
                    outputs = model(inputs)
                    preds = (outputs > 0.5).float()
                    loss = criterion(outputs, labels)

                    if phase == 'train':
                        loss.backward()
                        optimizer.step()

                running_loss += loss.item() * inputs.size(0)
                running_corrects += torch.sum(preds == labels.data)

            epoch_loss = running_loss / dataset_sizes[phase]
            epoch_acc = running_corrects.double() / dataset_sizes[phase]

            print(f'{phase} Loss: {epoch_loss:.4f} Acc: {epoch_acc:.4f}')

            # best model 저장
            if phase == 'val' and epoch_loss < best_loss:
                best_loss = epoch_loss
                best_model_wts = model.state_dict()

        # 체크포인트 저장
        if (epoch + 1) % checkpoint_interval == 0:
            checkpoint_path = f'checkpoint_epoch_{epoch+1}.pth'
            torch.save(model.state_dict(), checkpoint_path)
            print(f'Checkpoint saved: {checkpoint_path}')

    # 최상의 모델 가중치를 로드
    model.load_state_dict(best_model_wts)
    return model

if __name__ == "__main__":
    # 모델 학습
    model = train_model(model, criterion, optimizer, dataloaders, dataset_sizes, device, num_epochs=25, checkpoint_interval=5)

    # 최종 모델 저장
    torch.save(model.state_dict(), 'chest_xray_model.pth')

    print("학습 끝")

from pathlib import Path
import warnings
warnings.filterwarnings("ignore", category=UserWarning)


import torch
import torch.nn as nn
from PIL import Image

from ai.aimodel import AIModel

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def ConvBlock(in_channels, out_channels, pool=False):
    layers = [nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1),
              nn.BatchNorm2d(out_channels),
              nn.ReLU(inplace=True)]
    if pool:
        layers.append(nn.MaxPool2d(4))
    return nn.Sequential(*layers)


class ResNet9(nn.Module):
    def __init__(self, in_channels, num_diseases):
        super().__init__()

        self.conv1 = ConvBlock(in_channels, 64)
        self.conv2 = ConvBlock(64, 128, pool=True)  # out_dim : 128 x 64 x 64
        self.res1 = nn.Sequential(ConvBlock(128, 128), ConvBlock(128, 128))

        self.conv3 = ConvBlock(128, 256, pool=True)  # out_dim : 256 x 16 x 16
        self.conv4 = ConvBlock(256, 512, pool=True)  # out_dim : 512 x 4 x 44
        self.res2 = nn.Sequential(ConvBlock(512, 512), ConvBlock(512, 512))

        self.classifier = nn.Sequential(nn.MaxPool2d(4),
                                        nn.Flatten(),
                                        nn.Linear(512, num_diseases))

    def forward(self, xb):  # xb is the loaded batch
        out = self.conv1(xb)
        out = self.conv2(out)
        out = self.res1(out) + out
        out = self.conv3(out)
        out = self.conv4(out)
        out = self.res2(out) + out
        out = self.classifier(out)
        return out


import torchvision.transforms as transforms


class PlantDiseaseModel(AIModel):
    disease_class_labels = ['Apple___Apple_scab', 'Apple___Black_rot', 'Apple___Cedar_apple_rust', 'Apple___healthy',
                            'Blueberry___healthy', 'Cherry_(including_sour)___Powdery_mildew',
                            'Cherry_(including_sour)___healthy',
                            'Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot', 'Corn_(maize)___Common_rust_',
                            'Corn_(maize)___Northern_Leaf_Blight',
                            'Corn_(maize)___healthy', 'Grape___Black_rot', 'Grape___Esca_(Black_Measles)',
                            'Grape___Leaf_blight_(Isariopsis_Leaf_Spot)',
                            'Grape___healthy', 'Orange___Haunglongbing_(Citrus_greening)', 'Peach___Bacterial_spot',
                            'Peach___healthy',
                            'Pepper,_bell___Bacterial_spot', 'Pepper,_bell___healthy', 'Potato___Early_blight',
                            'Potato___Late_blight',
                            'Potato___healthy', 'Raspberry___healthy', 'Soybean___healthy', 'Squash___Powdery_mildew',
                            'Strawberry___Leaf_scorch', 'Strawberry___healthy', 'Tomato___Bacterial_spot',
                            'Tomato___Early_blight',
                            'Tomato___Late_blight', 'Tomato___Leaf_Mold', 'Tomato___Septoria_leaf_spot',
                            'Tomato___Spider_mites Two-spotted_spider_mite',
                            'Tomato___Target_Spot', 'Tomato___Tomato_Yellow_Leaf_Curl_Virus',
                            'Tomato___Tomato_mosaic_virus',
                            'Tomato___healthy']

    def __init__(self):
        self.model = None
        self.transform = transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.ToTensor(),
        ])

    def load_model(self):
        if self.model is not None:
            return
        self.model = ResNet9(3, len(self.disease_class_labels))
        parent_path = Path(__file__).parent
        state_dict = torch.load(parent_path / 'plant-disease-model.pth', device)
        self.model.load_state_dict(state_dict)
        self.model.eval()

    def predict(self, image: Image):
        self.load_model()
        image_tensor = self.transform(image).unsqueeze(0)
        predicted_disease = None
        with torch.no_grad():
            output = self.model(image_tensor)
            _, predicted = torch.max(output.data, 1)
            disease_index = predicted.item()
            predicted_disease = self.disease_class_labels[disease_index]

        return predicted_disease

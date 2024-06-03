# inference.py
from typing import Any

import cv2
import numpy as np
import onnx
import onnxruntime
import torch.nn as nn
import torch.nn.functional as F
import torch
from univdt.utils.image import load_image

from .pymodels import Model


def run_inference(path_weight: str, path_input: str) -> float:
    try:
        # load onnx file
        onnx_model = onnx.load(path_weight)
        onnx.checker.check_model(onnx_model)
        # get input shape
        input_shape = onnx_model.graph.input[0].type.tensor_type.shape.dim
        H, W = input_shape[2].dim_value, input_shape[3].dim_value
        image = load_image(path_input, out_channels=1)  # H W 1
        image = cv2.resize(image, (W, H))  # H W
        image = image.astype(np.float32) / 255.0
        image = np.expand_dims(image, axis=0)  # 1 H W
        image = np.expand_dims(image, axis=0)  # 1 1 H W

        # onnx runtime
        ort_session = onnxruntime.InferenceSession(path_weight)
        input_name = ort_session.get_inputs()[0].name
        output_name = ort_session.get_outputs()[0].name

        # inference
        ort_inputs = {input_name: image}
        ort_outs = float(ort_session.run([output_name], ort_inputs)[0][0])

        return ort_outs
    except Exception as e:
        print(f"Error in run_inference function: {e}")
        return None


_CONFIG_MODEL_CM_PTX = {"encoder": {"name": "convnext_base.fb_in22k_ft_in1k_384",
                                    "pretrained": False, "num_classes": 0,
                                    "features_only": True, "in_chans": 1, "out_indices": [2, 3]},
                        "decoder": {"name": "upsample_concat"},
                        "header": {"name": "singleconv", "num_classes": 2, "dropout": 0.2,
                                   "pool": "avg", "interpolate": False, "return_logits": True}}


class GradCAM:
    def __init__(self, model: nn.Module, target_layer: nn.Module):
        self.model = model
        self.target_layer = target_layer

        self.gradients = None
        self.activations = None
        self.hook_layers()

    def hook_layers(self):
        def forward_hook(module, input, output):
            self.activations = output

        def full_backward_hook(module, grad_input, grad_output):
            self.gradients = grad_output[0]

        self.target_layer.register_forward_hook(forward_hook)
        self.target_layer.register_full_backward_hook(full_backward_hook)

    def forward(self, input_image: torch.Tensor):
        self.model.zero_grad()
        return self.model(input_image)


class ChestMateRunner:
    """
    Run inference for the ChestMate model
    """

    def __init__(self,
                 path_weight_cmptx: str):
        self.path_weight_cmptx = path_weight_cmptx  # cardiomegaly and pneumothorax model path

        model_cmptx = ChestMateRunner.load_model(_CONFIG_MODEL_CM_PTX, path_weight_cmptx)
        self.cm_ptx = GradCAM(model_cmptx, model_cmptx.header.conv)

    @staticmethod
    def unwrap_key(dummy: dict[str, Any], src_key: str, dst_key: str) -> dict[str, Any]:
        updated_dict = {}
        for key, value in dummy.items():
            updated_key = key.replace(src_key, dst_key)
            updated_dict[updated_key] = value
        return updated_dict

    @staticmethod
    def load_weight(path_weight: str) -> dict[str, Any]:
        weight = torch.load(path_weight, map_location='cpu')
        if 'state_dict' in weight:
            weight = weight['state_dict']
        weight = ChestMateRunner.unwrap_key(weight, 'model.', '')
        return weight

    @staticmethod
    def load_model(config_model: dict[str, Any], path_weight: str) -> Model:
        model = Model(**config_model)
        model.load_state_dict(ChestMateRunner.load_weight(path_weight))
        model = model.eval()
        return model

    @staticmethod
    def preprocess(path_image: str) -> torch.Tensor:
        image = load_image(path_image, out_channels=1)
        image = image.astype(np.float32) / 255.0
        image = torch.from_numpy(image)
        image = torch.permute(image, (2, 0, 1)).unsqueeze(0)
        return image

    @torch.no_grad()
    def run(self, path_image: str) -> dict:
        image = ChestMateRunner.preprocess(path_image)

    @torch.no_grad()
    def run_cm_ptx(self, image: torch.Tensor):
        image = F.upsample_bilinear(image, size=(512, 512))
        logits, preds = self.model_cmptx(image)

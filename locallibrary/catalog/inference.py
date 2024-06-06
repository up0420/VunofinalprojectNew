# inference.py
import copy
from typing import Any

import cv2
import numpy as np
import onnx
import onnxruntime
import torch
import torch.nn as nn
import torch.nn.functional as F
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


_CONFIG_MODEL = {"encoder": {"name": "convnext_base.fb_in22k_ft_in1k_384",
                             "pretrained": False, "num_classes": 0,
                             "features_only": True, "in_chans": 1, "out_indices": [2, 3]},
                 "decoder": {"name": "upsample_concat"},
                 "header": {"name": "singleconv", "num_classes": 2, "dropout": 0.2,
                            "pool": "avg", "interpolate": False, "return_logits": True}}


class GradCAM:
    def __init__(self, model: nn.Module, target_layer: nn.Module):
        self.model = model
        self.target_layer = target_layer

        self.gradients: torch.Tensor = None
        self.activations: torch.Tensor = None
        self.hook_layers()

    def hook_layers(self):
        def forward_hook(module, input, output):
            self.activations = output

        def full_backward_hook(module, grad_input, grad_output):
            self.gradients = grad_output[0]

        self.target_layer.register_forward_hook(forward_hook)
        self.target_layer.register_full_backward_hook(full_backward_hook)

    def forward(self, x: torch.Tensor):
        self.model.zero_grad()
        return self.model(x)

    def __call__(self, *args: Any, **kargs: Any) -> Any:
        return self.forward(*args, **kargs)

    def generate_cam(self, target_class: int) -> np.ndarray:
        gradients = self.gradients.cpu().data.numpy()
        activations = self.activations.cpu().data.numpy()
        assert gradients.shape == activations.shape
        assert gradients.shape[0] == 1

        gradients = gradients[0]  # C H W
        activations = activations[0]  # C H W

        weights = np.mean(gradients, axis=(1, 2))
        cam = np.sum(weights[:, np.newaxis, np.newaxis]
                     * activations, axis=0)  # H W
        cam = np.maximum(cam, 0)
        cam = cam - np.min(cam)
        cam = cam / np.max(cam)
        return cam


def ovelay_cam_on_image(image: np.ndarray | torch.Tensor, cam: np.ndarray | torch.Tensor, alpha: float = 0.7) -> np.ndarray:
    if isinstance(image, torch.Tensor):
        image = image.detach().cpu().numpy()
    if isinstance(cam, torch.Tensor):
        cam = cam.detach().cpu().numpy()

    if len(image.shape) == 4:
        image = image[0]

    assert len(image.shape) == 3
    image = np.transpose(image, (1, 2, 0))  # H W C
    if image.shape[-1] == 1:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    image = cv2.resize(image, (512, 512))
    image = (image * 255).astype(np.uint8)

    cam = cv2.resize(cam, (512, 512))
    heatmap = cv2.applyColorMap(np.uint8(255*cam), cv2.COLORMAP_JET)
    heatmap = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)
    # heatmap = heatmap.astype(np.uint8)
    overlay = cv2.addWeighted(image, alpha, heatmap, 1-alpha, 0)
    overlay = cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR)
    return overlay


class ChestMateRunner:
    """
    Run inference for the ChestMate model
    """

    def __init__(self,
                 path_weight_cmptx: str,
                 path_weight_eff_atel: str,
                 path_weight_emp_eda_pt_fib: str,
                 threshold_cm: float = 0.5,
                 threshold_ptx: float = 0.5,
                 threshold_effusion: float = 0.5,
                 threshold_atel: float = 0.5,
                 threshold_empysema: float = 0.5,
                 threshold_edema: float = 0.5,
                 threshold_pleural_thickening: float = 0.5,
                 threshold_fibrosis: float = 0.5,
                 ):
        # cardiomegaly and pneumothorax model path
        self.path_weight_cmptx = path_weight_cmptx
        # effusion and atelectasis model path
        self.path_weight_eff_atel = path_weight_eff_atel
        # emphysema, edema, pleural thickening, and fibrosis model path
        self.path_weight_emp_eda_pt_fib = path_weight_emp_eda_pt_fib

        _CONFIG_MODEL['header']['num_classes'] = 2
        model_cmptx = ChestMateRunner.load_model(_CONFIG_MODEL,
                                                 path_weight_cmptx)
        self.cm_ptx = GradCAM(model_cmptx, model_cmptx.header.conv)

        _CONFIG_MODEL['header']['num_classes'] = 2
        model_eff_atel = ChestMateRunner.load_model(_CONFIG_MODEL,
                                                    path_weight_eff_atel)
        self.eff_atel = GradCAM(model_eff_atel, model_eff_atel.header.conv)

        _CONFIG_MODEL['header']['num_classes'] = 4
        model_emp_eda_pt_fib = ChestMateRunner.load_model(_CONFIG_MODEL,
                                                          path_weight_emp_eda_pt_fib)
        self.emp_eda_pt_fib = GradCAM(model_emp_eda_pt_fib,
                                      model_emp_eda_pt_fib.header.conv)

        # thresholds
        self.threshold_cm = threshold_cm  # threshold for cardiomegaly
        self.threshold_ptx = threshold_ptx  # threshold for pneumothorax
        self.threshold_effusion = threshold_effusion  # threshold for effusion
        self.threshold_atel = threshold_atel  # threshold for atelectasis
        self.threshold_empysema = threshold_empysema  # threshold for emphysema
        self.threshold_edema = threshold_edema  # threshold for edema
        self.threshold_pleural_thickening = threshold_pleural_thickening
        self.threshold_fibrosis = threshold_fibrosis  # threshold for fibrosis

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

    def run(self, path_image: str) -> dict[str, Any]:
        image = ChestMateRunner.preprocess(path_image)

        outputs = {}
        # run cardiomegaly and pneumothorax model
        cm_ptx: dict[str, Any] = self._run_cm_ptx(copy.deepcopy(image))
        outputs.update(cm_ptx)

        # run effusion and atelectasis model
        eff_atel: dict[str, Any] = self._run_effusion_atel(
            copy.deepcopy(image))
        outputs.update(eff_atel)

        # run emphysema, edema, pleural thickening, and fibrosis model
        emp_eda_pt_fib: dict[str, Any] = self._run_emp_eda_pt_fib(
            copy.deepcopy(image))
        outputs.update(emp_eda_pt_fib)

        return outputs

    def _run_model(self, image: torch.Tensor, model: nn.Module) -> torch.Tensor:
        image = F.interpolate(image, size=(384, 384),
                              mode='bilinear', align_corners=True)
        _, preds = model(image)
        preds = preds.squeeze()
        return preds

    def _run_cm_ptx(self, image: torch.Tensor) -> dict[str, Any]:
        preds = self._run_model(image, self.cm_ptx.model)

        scores = preds.detach().squeeze().cpu().numpy()
        score_cm, score_ptx = scores
        outputs = {'cardiomegaly': {'score': 0.0, 'heatmap': None},
                   'pneumothorax': {'score': 0.0, 'heatmap': None}}
        outputs['cardiomegaly']['score'] = score_cm
        outputs['pneumothorax']['score'] = score_ptx

        if score_cm > self.threshold_cm:
            preds[0].backward(retain_graph=True)
            cam: np.ndarray = self.cm_ptx.generate_cam(0)
            overlay = ovelay_cam_on_image(image, cam)
            outputs['cardiomegaly']['heatmap'] = overlay

        if score_ptx > self.threshold_ptx:
            preds[1].backward(retain_graph=True)
            cam: np.ndarray = self.cm_ptx.generate_cam(1)
            overlay = ovelay_cam_on_image(image, cam)
            outputs['pneumothorax']['heatmap'] = overlay
        return outputs

    def _run_effusion_atel(self, image: torch.Tensor) -> dict[str, Any]:
        preds = self._run_model(image, self.eff_atel.model)

        scores = preds.detach().squeeze().cpu().numpy()
        score_effusion, score_atel = scores
        outputs = {'effusion': {'score': 0.0, 'heatmap': None},
                   'atelectasis': {'score': 0.0, 'heatmap': None}}
        outputs['effusion']['score'] = score_effusion
        outputs['atelectasis']['score'] = score_atel

        if score_effusion > self.threshold_effusion:
            preds[0].backward(retain_graph=True)
            cam: np.ndarray = self.eff_atel.generate_cam(0)
            overlay = ovelay_cam_on_image(image, cam)
            outputs['effusion']['heatmap'] = overlay

        if score_atel > self.threshold_atel:
            preds[1].backward(retain_graph=True)
            cam: np.ndarray = self.eff_atel.generate_cam(1)
            overlay = ovelay_cam_on_image(image, cam)
            outputs['atelectasis']['heatmap'] = overlay
        return outputs

    def _run_emp_eda_pt_fib(self, image: torch.Tensor) -> dict[str, Any]:
        preds = self._run_model(image, self.emp_eda_pt_fib.model)

        scores = preds.detach().squeeze().cpu().numpy()
        score_emphysema, score_edema, score_pt, score_fibrosis = scores
        outputs = {'emphysema': {'score': 0.0, 'heatmap': None},
                   'edema': {'score': 0.0, 'heatmap': None},
                   'pleural_thickening': {'score': 0.0, 'heatmap': None},
                   'fibrosis': {'score': 0.0, 'heatmap': None}}
        outputs['emphysema']['score'] = score_emphysema
        outputs['edema']['score'] = score_edema
        outputs['pleural_thickening']['score'] = score_pt
        outputs['fibrosis']['score'] = score_fibrosis

        if score_emphysema > self.threshold_empysema:
            preds[0].backward(retain_graph=True)
            cam: np.ndarray = self.emp_eda_pt_fib.generate_cam(0)
            overlay = ovelay_cam_on_image(image, cam)
            outputs['emphysema']['heatmap'] = overlay

        if score_edema > self.threshold_edema:
            preds[1].backward(retain_graph=True)
            cam: np.ndarray = self.emp_eda_pt_fib.generate_cam(1)
            overlay = ovelay_cam_on_image(image, cam)
            outputs['edema']['heatmap'] = overlay

        if score_pt > self.threshold_pleural_thickening:
            preds[2].backward(retain_graph=True)
            cam: np.ndarray = self.emp_eda_pt_fib.generate_cam(2)
            overlay = ovelay_cam_on_image(image, cam)
            outputs['pleural_thickening']['heatmap'] = overlay

        if score_fibrosis > self.threshold_fibrosis:
            preds[3].backward(retain_graph=True)
            cam: np.ndarray = self.emp_eda_pt_fib.generate_cam(3)
            overlay = ovelay_cam_on_image(image, cam)
            outputs['fibrosis']['heatmap'] = overlay
        return outputs

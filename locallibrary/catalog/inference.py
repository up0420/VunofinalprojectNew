# inference.py
import cv2
import numpy as np
import onnx
import onnxruntime
from univdt.utils.image import load_image

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

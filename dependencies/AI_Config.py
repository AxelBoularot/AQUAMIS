import torch
from ultralytics import YOLO


def _is_no_kernel_image_error(err: BaseException) -> bool:
    msg = str(err)
    return (
        "no kernel image is available for execution on the device" in msg
        or "cudaErrorNoKernelImageForDevice" in msg
    )


def _choose_device() -> str:
    try:
        if not torch.cuda.is_available():
            return "cpu"

        cap = torch.cuda.get_device_capability(0)
        sm = f"sm_{cap[0]}{cap[1]}"

        arch_list = []
        try:
            arch_list = torch.cuda.get_arch_list() or []
        except Exception:
            arch_list = []

        if arch_list and sm not in arch_list:
            print(
                f"CUDA GPU capability {sm} not supported by this PyTorch build ({arch_list}); using CPU."
            )
            return "cpu"

        try:
            x = torch.zeros((1,), device="cuda")
            _ = (x + 1).sum().item()
            torch.cuda.synchronize()
        except Exception as e:
            print(f"CUDA smoke-test failed ({e}); using CPU.")
            return "cpu"

        return "cuda:0"
    except Exception as e:
        print(f"Error selecting CUDA device: {e}")
        return "cpu"


def load_yolo_model(model_path: str = "object_detection_lib/yolo11n.pt"):
    device = _choose_device()
    print(f"Using device: {device}")

    try:
        model = YOLO(model_path)
        if device != "cpu":
            try:
                model = model.to(device)
            except RuntimeError as e:
                if _is_no_kernel_image_error(e):
                    print("CUDA incompatible with this GPU; falling back to CPU.")
                    device = "cpu"
                    model = model.to(device)
                else:
                    raise
        return model, device
    except Exception as e:
        print(f"Error loading YOLO model: {e}")
        return None, device

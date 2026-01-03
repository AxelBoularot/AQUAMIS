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


"""def load_yolo_model(model_path: str = "object_detection_lib/yolo11n.pt"):
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
"""
# --- NOUVELLE CLASSE POUR GÉRER YOLO WORLD ---
class YOLOWorldWrapper:
    def __init__(self, model_path: str, device: str):
        self.model = YOLO(model_path)
        self.device = device
        
        # Déplacer sur le bon device
        if self.device != "cpu":
            try:
                self.model.to(self.device)
            except RuntimeError as e:
                if _is_no_kernel_image_error(e):
                    print("CUDA incompatible fallback CPU")
                    self.device = "cpu"
                    self.model.to("cpu")
                else:
                    raise
        
        # Initialisation par défaut (important pour éviter un état vide)
        # Si c'est un modèle standard, cette ligne sera ignorée sans crash
        try:
            self.model.set_classes(["object"])
        except Exception:
            pass # Ce n'est pas un modèle World, on ignore

    def set_classes(self, classes_list: list):
        """Permet de changer les objets détectés à la volée"""
        try:
            # Nettoyage de la liste
            clean_list = [c.strip() for c in classes_list if c.strip()]
            if clean_list:
                self.model.set_classes(clean_list)
                print(f"-> Modèle mis à jour pour détecter : {clean_list}")
        except Exception as e:
            print(f"Erreur lors du changement de classes (Modèle non compatible ?) : {e}")

    # On redirige les appels standards vers le vrai modèle YOLO
    def track(self, source, **kwargs):
        return self.model.track(source, **kwargs)
    
    def predict(self, source, **kwargs):
        return self.model.predict(source, **kwargs)
    
    @property
    def names(self):
        return self.model.names


# --- LOAD MODIFIÉ ---
# Par défaut on charge un modèle 'world' (plus petit = plus rapide sur CPU)
def load_yolo_model(model_path: str = "object_detection_lib/yolov8s-world.pt"):
    device = _choose_device()
    print(f"Using device: {device}")

    try:
        # On retourne notre Wrapper au lieu de l'objet brut
        # Cela rend 'model.set_classes()' disponible dans ton App
        model_wrapper = YOLOWorldWrapper(model_path, device)
        return model_wrapper, model_wrapper.device
        
    except Exception as e:
        print(f"Error loading YOLO model: {e}")
        return None, device
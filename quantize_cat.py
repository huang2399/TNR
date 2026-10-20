import torch
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
from esp_ppq.api import espdl_quantize_onnx

# --- 1. 配置参数 ---
ONNX_MODEL_PATH = r"D:\cats-vs-notcats\outputs\cat_vs_notcat.onnx"
OUTPUT_DIR = r"D:\cats-vs-notcats\outputs"
VALID_DATA_DIR = r"D:\cats-vs-notcats\valid"
INPUT_SHAPE = [1, 3, 224, 224]

# --- 2. 定义 collate_fn，只返回图像数据 ---
def collate_fn(batch):
    # batch 是一个列表，每个元素是 (image_tensor, label)
    # 我们只需要第一个元素 image_tensor
    images = [item[0] for item in batch]
    # 将列表堆叠成一个批次张量 [B, C, H, W]
    return torch.stack(images, dim=0)

# --- 3. 准备校准集的数据加载器 ---
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])

calib_dataset = datasets.ImageFolder(VALID_DATA_DIR, transform=transform)
calib_loader = DataLoader(
    calib_dataset,
    batch_size=1,
    shuffle=True,
    num_workers=0,
    collate_fn=collate_fn  # 关键：传入我们自定义的 collate_fn
)

# --- 4. 执行量化 ---
print("⏳ 开始量化模型...")
espdl_path = f"{OUTPUT_DIR}/cat_vs_notcat.espdl"

espdl_quantize_onnx(
    onnx_import_file=ONNX_MODEL_PATH,
    espdl_export_file=espdl_path,
    calib_dataloader=calib_loader,
    calib_steps=32,
    input_shape=INPUT_SHAPE,
    target="esp32s3",
    num_of_bits=8,
    device="cpu",
    error_report=True,
    skip_export=False,
    export_test_values=True,
    verbose=1,
)
print(f"✅ 量化完成！模型已保存至: {espdl_path}")
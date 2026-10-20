import argparse
from pathlib import Path
import torch
from torch import nn, optim
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms

def evaluate(model, loader, criterion, device):
    model.eval()
    total_loss, correct, total = 0.0, 0, 0
    with torch.no_grad():
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)
            logits = model(images)
            total_loss += criterion(logits, labels).item() * labels.size(0)
            correct += (logits.argmax(1) == labels).sum().item()
            total += labels.size(0)
    return total_loss / total, correct / total

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default=r"D:\cats-vs-notcats\train")
    parser.add_argument("--valid-data-dir", default=r"D:\cats-vs-notcats\valid")
    parser.add_argument("--output-dir", default=r"D:\cats-vs-notcats\outputs")
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--batch-size", type=int, default=64)
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"🔥 使用设备: {device}")
    if torch.cuda.is_available():
        print(f"🎮 显卡型号: {torch.cuda.get_device_name(0)}")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 图像预处理（部署时必须完全一致）
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])

    train_dataset = datasets.ImageFolder(args.data_dir, transform=transform)
    val_dataset = datasets.ImageFolder(args.valid_data_dir, transform=transform)
    
    # 强制检查类别名称
    print(f"📂 类别顺序: {train_dataset.classes}")
    assert train_dataset.classes == ["cat", "notcat"], "类别目录名必须是 cat 和 notcat！"

    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, num_workers=4, pin_memory=True)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False, num_workers=4, pin_memory=True)

    # 加载预训练的 MobileNetV2（迁移学习）
    print("⏳ 正在加载 MobileNetV2 预训练模型...")
    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.IMAGENET1K_V1)
    model.classifier[1] = nn.Linear(model.last_channel, 2)  # 改成 2 分类
    model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=1e-4)

    print("🚀 开始训练！")
    for epoch in range(args.epochs):
        model.train()
        train_loss = 0.0
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            loss = criterion(model(images), labels)
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * labels.size(0)
        train_loss /= len(train_dataset)
        
        val_loss, val_acc = evaluate(model, val_loader, criterion, device)
        print(f"Epoch {epoch+1:02d}/{args.epochs} | 训练损失: {train_loss:.4f} | 验证损失: {val_loss:.4f} | 验证准确率: {val_acc*100:.2f}%")

    # 保存最终模型
    torch.save(model.state_dict(), output_dir / "cat_vs_notcat.pth")
    (output_dir / "labels.txt").write_text("cat\nnotcat\n")
    print(f"✅ 模型已保存到 {output_dir / 'cat_vs_notcat.pth'}")

    # 导出 ONNX（为你后续对接摄像头或部署到 ESP32 做准备）
    print("⏳ 正在导出 ONNX 模型...")
    model.eval()
    dummy = torch.randn(1, 3, 224, 224).to(device)
    torch.onnx.export(
        model, dummy,
        output_dir / "cat_vs_notcat.onnx",
        opset_version=12,
        input_names=["input"], output_names=["output"]
    )
    print("🎉 ONNX 导出成功！全部任务完成！")

if __name__ == "__main__":
    main()
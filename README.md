# ESP32-S3-EYE 摄像头 → LCD 通用固件 v1.0.0

把这块固件烧进**任意一块 ESP32-S3-EYE**，上电后 LCD 就会显示摄像头实时画面。
不需要装 ESP-IDF，只要一个 Python 和一根 USB 线。

- 目标板：ESP32-S3-EYE（ESP32-S3-WROOM-1-**N8R8**，8MB Flash + 8MB Octal PSRAM，摄像头 OV2640）
- 显示：240x240 RGB565，实测约 **20 fps**
- 控制台：**USB Serial/JTAG**（日志从板上的 USB 口出，115200）

---

## 一、最快路径：整包烧录（推荐，不需要 ESP-IDF）

### 1. 接线
用一根**能传数据**的 USB-C 线，插开发板上的 **USB 口**（板上有两个 Type-C，一个是 USB，一个是 UART）。
插好后设备管理器里会出现一个串口，硬件 ID 是 `VID_303A&PID_1001`（USB 串行设备）。

### 2. 装 esptool
```powershell
pip install -U esptool
```

### 3. 烧录（把 COM5 换成你的实际端口号）
```powershell
python -m esptool --chip esp32s3 -p COM5 -b 460800 write_flash -e --flash_mode dio --flash_size 8MB --flash_freq 80m 0x0 s3eye_camera_universal_full.bin
```
`-e` = 先整片擦除再写，能避免上一块固件残留的分区表/NVS 干扰。**强烈建议保留。**

烧完板子会自动复位，屏幕应立刻出现摄像头画面。

### 4. 懒人版
Windows 下在本目录直接双击 `flash.bat`（自动找串口），或指定端口：
```powershell
.\flash.bat COM5
```

> 只有登录/下载页（0x0 起始）这一个整包文件需要烧。**不要**只烧 app，否则可能没有 bootloader / 分区表。

---

## 二、怎样确认它是正常的

用任意串口工具连 **USB 口**（115200），正常日志是这样：

```
I (592) S3EYE-CAM:  ESP32-S3-EYE  camera -> LCD   v1.0.0
I (736) S3EYE-CAM: [LCD] OK  240x240, backlight on
I (743) ov2640: Detected Camera sensor PID=0x26
I (744) S3EYE-CAM: [CAM] init OK
I (809) app_video: Video Stream Start
I (960) S3EYE-CAM: [OK] streaming camera -> LCD
I (981) S3EYE-CAM: [CAM] first frame: 240x240 RGB565, 115200 bytes
I (5080) S3EYE-CAM: [CAM] 20.0 fps @ 240x240
```

对照要点：

| 看到什么 | 说明 |
| --- | --- |
| `[LCD] OK ... backlight on` | 背光已经点亮 |
| `ov2640: Detected Camera sensor PID=0x26` | 摄像头被识别到了（0x26 = OV2640） |
| `[OK] streaming camera -> LCD` | 视频流已启动 |
| `[CAM] ... fps` | 正在出图，**看到这行就一定是通的** |
| `W ... xclk frequency 16000000 is not equal to 20000000` | **正常**，不影响显示，只是帧率 20fps 而不是 25fps |
| `[CAM] bsp_camera_start FAILED` / `open video device failed` | 摄像头侧问题 → 见第三节 |
| `TG0WDT_SYS_RST` 反复出现 | 固件/烧录方式不对 → 见第四节第 4 点 |

---

## 三、黑屏 / 没画面：按顺序排查

1. **摄像头 FPC 排线**（最常见）
   断电 → 掰开卡扣 → 排线插到底、金色触点朝向正确 → 压紧卡扣。S3-EYE 上摄像头和 LCD 是两根独立排线，都检查。
2. **LCD FPC 排线**：同上。屏幕完全黑、背光都不亮，多半是这根。
3. **USB 线**：必须是数据线（很多线只供电）。尽量直插电脑 USB 口，不要用劣质 Hub。
4. **插口插对**：烧录和看日志都用 **USB 口**；插 UART 口看不到日志（这是设计如此，见第四节）。
5. **屏幕上有提示文字**
   - 显示我们的开机界面（`ESP32-S3-EYE` / `LCD OK`）但没有画面 → 摄像头链路问题，按 1 处理。
   - 显示 `CAMERA ERROR` / `NO CAMERA SIGNAL` → 摄像头没出图，按 1 处理，然后断电重启。
   - 显示 `MEMORY ERROR` → PSRAM 异常（板子不对/坏了）。
6. **刷过别的固件**：整包命令里的 `-e` 已经处理。若想手动彻底清：
   ```powershell
   python -m esptool --chip esp32s3 -p COM5 erase_flash
   ```
   然后再执行第一节第 3 步。

---

## 四、为什么 S3-EYE 容易“莫名其妙黑屏”（原因说明）

1. **控制台抢占 GPIO43/44**
   ESP-IDF 默认把日志放在 UART0，而 UART0 的 TX/RX 正好是 **GPIO43/GPIO44**。
   偏偏 S3-EYE 的 LCD 用的是 **GPIO43 = DC、GPIO44 = CS**。
   两者撞车 → 花屏或黑屏，而且日志还会刷一堆
   `GPIO 44 and 43 are used as console UART I/O pins`。
   **本固件把控制台改到 USB Serial/JTAG**，GPIO43/44 完全让给 LCD。
   → 代价是：日志只能从**USB 口**看，从 UART 口看不到。
2. **背光 GPIO48 是低电平点亮**（LEDC 5kHz/10bit，`duty = 1023*(100-brightness)/100`）。
   固件上电第一件事就是点亮背光并显示开机 UI，绝不会“毫无提示地全黑”。
3. **帧缓冲在 PSRAM**：240x240 RGB565 双缓冲（各 115200 字节）放在 8MB Octal PSRAM。
   分配失败会直接在屏幕上报错。
4. **整包固件的 flash 模式必须是 `dio`**
   本工程 sdkconfig 实际生效的是 `dio`。用 `merge_bin --flash_mode qio` 生成的整包，
   会把 bootloader 头里的 `0x02`(DIO) 改成 `0x00`(QIO)，烧进去就是无限
   `TG0WDT_SYS_RST` 复位循环。本仓库的 `s3eye_camera_universal_full.bin` 已经用 **dio** 生成并实机验证。

---

## 五、关键引脚对照表（官方 BSP 6.0.0）

| 功能 | GPIO | 备注 |
| --- | --- | --- |
| **LCD** SCLK | 21 | |
| **LCD** MOSI | 47 | |
| **LCD** CS | 44 | 与默认 UART0 RX 冲突 |
| **LCD** DC | 43 | 与默认 UART0 TX 冲突 |
| **LCD** RST | NC | 不接 |
| **LCD** 背光 BL | 48 | LEDC，**低电平点亮** |
| **CAM** XCLK | **15** | |
| **CAM** SIOD (SDA) | **4** | SCCB，400kHz |
| **CAM** SIOC (SCL) | **5** | SCCB |
| **CAM** VSYNC | 6 | |
| **CAM** HREF | 7 | |
| **CAM** PCLK | 13 | |
| **CAM** D0–D7 | 11, 9, 8, 10, 12, 18, 17, 16 | |
| **CAM** PWDN / RST | NC | 不接 |

> ⚠️ 网上流传的引脚表有不少是错的，例如把 **XCLK 写成 21**、把 **SIOD/SIOC 写成 26/27**。
> 21 其实是 LCD 的 SCLK；**GPIO26–32 是内部 Flash 专用，GPIO33–37 是 Octal PSRAM 专用，绝对不能外接**。

---

## 六、从源码构建（可选）

需要 **ESP-IDF v5.4+**（本固件在 **v5.4.4** 上验证）。第一次构建会自动下载
`esp32_s3_eye` BSP 6.0.0 等 managed_components。

```powershell
idf.py set-target esp32s3
idf.py build
idf.py -p COM5 flash monitor
```

重新生成可分发整包：
```powershell
python -m esptool --chip esp32s3 merge_bin -o dist/s3eye_camera_universal_full.bin ^
  --flash_mode dio --flash_freq 80m --flash_size 8MB ^
  0x0 build/bootloader/bootloader.bin ^
  0x8000 build/partition_table/partition-table.bin ^
  0x10000 build/s3eye_camera_universal.bin
```
⚠️ `--flash_mode` 只能是 **dio**。

工程内关键改动（相对官方 `display_camera_video` 示例）：
- `sdkconfig.defaults`：`CONFIG_ESP_CONSOLE_USB_SERIAL_JTAG=y`（释放 GPIO43/44）+ 8MB Flash + Octal PSRAM 80MHz
- `main/main.c`：开机先点背光 + 显示 UI，分步自检 LCD/摄像头/缓冲/视频流，失败给屏幕提示，6 秒无画面报 `NO CAMERA SIGNAL`，并输出 fps 统计
- ESP32-S3 **没有 PPA**，240x240 RGB565 直接作为 LVGL canvas 缓冲送到 240x240 LCD，不做缩放

---

## 七、兼容性与已知限制

- 目标板：ESP32-S3-EYE（N8R8：8MB Flash + 8MB Octal PSRAM）。
- Flash 是 16MB 的板子也能用（本固件只用到前 8MB；分区表 app 区 1MB，固件占约 644KB）。
- **PSRAM 必须是 Octal**（官方板就是）。如果对方是自制板 / Quad PSRAM，需要改 `CONFIG_SPIRAM_MODE_*` 重新编译，整包不可通用。
- 摄像头驱动只编入了 **OV2640**（S3-EYE 出厂配置），并对它做了自动识别。换成别的摄像头模组需重新编译。
- 帧率 **20fps**：BSP 把 XCLK 固定为 16MHz，而 OV2640 标称 20MHz ⇒ 20/25 比例。想上 25fps 得改 XCLK，属可选优化，不影响功能。
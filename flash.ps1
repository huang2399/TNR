# ESP32-S3-EYE 一键烧录 (PowerShell)
# 用法:  .\flash.ps1             自动检测串口
#        .\flash.ps1 -Port COM5  指定串口
param([string]$Port)
$ErrorActionPreference = 'Continue'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$bin  = Join-Path $here 's3eye_camera_universal_full.bin'

if (-not (Test-Path $bin)) {
    Write-Host "[错误] 找不到固件: $bin" -ForegroundColor Red
    Read-Host '按回车退出'; exit 1
}

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host '[错误] 没找到 python，请先安装 Python 3 并加入 PATH' -ForegroundColor Red
    Read-Host '按回车退出'; exit 1
}

python -c "import esptool" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host '[提示] 正在安装 esptool ...' -ForegroundColor Yellow
    python -m pip install -U esptool
}

if (-not $Port) {
    Write-Host '[提示] 正在自动检测串口 ...'
    $Port = ([string](python (Join-Path $here 'detect_port.py'))).Trim()
}
if (-not $Port) {
    Write-Host '[错误] 没检测到串口。插好 USB 线，或: .\flash.ps1 -Port COM5' -ForegroundColor Red
    Read-Host '按回车退出'; exit 1
}

Write-Host "固件 : $bin"
Write-Host "串口 : $Port" -ForegroundColor Green
Write-Host '方式 : 整片擦除后烧录（约 10 秒）'
python -m esptool --chip esp32s3 -p $Port -b 460800 write_flash -e --flash_mode dio --flash_size 8MB --flash_freq 80m 0x0 $bin
if ($LASTEXITCODE -eq 0) {
    Write-Host '[完成] 板子会自动复位，LCD 应显示摄像头画面。' -ForegroundColor Green
    Write-Host '       看日志请连板子的 USB 口，115200。' -ForegroundColor Green
} else {
    Write-Host '[失败] 烧录出错：串口被占用 / 串口号不对 / USB 线不支持数据传输。' -ForegroundColor Red
}
Read-Host '按回车退出'
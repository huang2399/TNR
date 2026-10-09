"""列出可用串口，优先返回乐鑫 USB Serial/JTAG (VID 303A)。"""
import sys

def main():
    try:
        from serial.tools import list_ports
    except Exception:
        print("")
        return
    ports = list(list_ports.comports())
    if not ports:
        print("")
        return
    prefer = [p for p in ports if (getattr(p, "vid", None) == 0x303A)
              or ("303A" in (p.hwid or "").upper())]
    pick = (prefer or ports)[0]
    print(pick.device or "")

if __name__ == "__main__":
    main()
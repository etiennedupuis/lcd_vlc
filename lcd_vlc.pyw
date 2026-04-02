import ctypes
import time
import requests
from xml.etree import ElementTree

# ---- LCD SETUP ----
dll = ctypes.cdll.LoadLibrary(r"C:\Program Files\Logitech Gaming Software\SDK\LCD\x64\LogitechLcd.dll")
dll.LogiLcdInit.restype = ctypes.c_bool
dll.LogiLcdMonoSetText.restype = ctypes.c_bool
dll.LogiLcdUpdate.restype = None
dll.LogiLcdShutdown.restype = None

# ---- VLC SETTINGS ----
VLC_URL = "http://localhost:8080/requests/status.xml"
VLC_PASSWORD = "YOUR_ULA_PASSWORD"

lcd_active = False
scroll_index = 0  # global scroll position


# ---- HELPERS ----
def format_time(seconds):
    m = seconds // 60
    s = seconds % 60
    return f"{m}:{s:02d}"


def progress_bar(current, total, length=28):
    if total == 0:
        return "." * length
    filled = int((current / total) * length)
    return ":" * filled + "." * (length - filled)


def scroll_text(text, width=30):
    global scroll_index

    if len(text) <= width:
        return text.ljust(width)

    # Add spacing for smooth loop
    scroll_text = text + "   "
    start = scroll_index % len(scroll_text)
    visible = (scroll_text[start:] + scroll_text[:start])[:width]

    scroll_index += 1
    return visible


def get_vlc_info():
    try:
        r = requests.get(VLC_URL, auth=("", VLC_PASSWORD), timeout=2)
        tree = ElementTree.fromstring(r.content)

        state = tree.findtext("state")

        current_time = int(tree.findtext("time") or 0)
        total_length = int(tree.findtext("length") or 0)

        title, artist, album, track_number = "Unknown", "", "", ""
        for info in tree.findall(".//info"):
            name = info.get("name")
            if name == "title":
                title = info.text or "Unknown"
            elif name == "artist":
                artist = info.text or ""
            elif name == "album":
                album = info.text or ""
            elif name == "track_number":
                track_number = info.text or ""

        return state, title, artist, album, track_number, current_time, total_length

    except:
        return "offline", "", "", "", "", 0, 0


print("Running! Press Ctrl+C to stop.")

try:
    while True:
        state, title, artist, album, track_number, current_time, total_length = get_vlc_info()

        if state in ("playing", "paused"):

            if not lcd_active:
                dll.LogiLcdInit(ctypes.c_wchar_p("VLC Now Playing"), ctypes.c_int(0x00000001))
                lcd_active = True
                print("VLC active — taking LCD.")

            status = "▶" if state == "playing" else "⏸"

            time_str = f"{format_time(current_time)}/{format_time(total_length)}"
            bar = progress_bar(current_time, total_length)

            # ---- DISPLAY ----
            dll.LogiLcdMonoSetText(0, ctypes.c_wchar_p(scroll_text(artist, 30)))
            dll.LogiLcdMonoSetText(1, ctypes.c_wchar_p(scroll_text(album, 30)))
            dll.LogiLcdMonoSetText(2, ctypes.c_wchar_p(scroll_text(f"{track_number}. {title}", 30)))
            dll.LogiLcdMonoSetText(3, ctypes.c_wchar_p(f"{status} {time_str} {bar}"))
            
            dll.LogiLcdUpdate()

        else:
            if lcd_active:
                dll.LogiLcdShutdown()
                lcd_active = False
                print("VLC stopped — releasing LCD.")

        time.sleep(1)  # faster refresh = smoother scroll

except KeyboardInterrupt:
    print("Stopped.")
    if lcd_active:
        dll.LogiLcdShutdown()

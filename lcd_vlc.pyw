import ctypes
import time
import requests
from xml.etree import ElementTree

# ---- LCD SETUP ---- (make sure the path to the DLL is correct)
dll = ctypes.cdll.LoadLibrary(r"C:\Program Files\Logitech Gaming Software\SDK\LCD\x64\LogitechLcd.dll")
dll.LogiLcdInit.restype = ctypes.c_bool
dll.LogiLcdMonoSetText.restype = ctypes.c_bool
dll.LogiLcdUpdate.restype = None
dll.LogiLcdShutdown.restype = None

# ---- VLC SETTINGS ----
VLC_URL = "http://localhost:8080/requests/status.xml"
VLC_PASSWORD = "YOUR_VLC_LUA_PASSWORD"

lcd_active = False  # Track whether we currently own the LCD

def get_vlc_info():
    try:
        r = requests.get(VLC_URL, auth=("", VLC_PASSWORD), timeout=2)
        tree = ElementTree.fromstring(r.content)

        state = tree.findtext("state")  # playing, paused, stopped

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

        return state, title, artist, album, track_number
    except:
        return "offline", "", "", "", ""

print("Running! Press Ctrl+C to stop.")

try:
    while True:
        state, title, artist, album, track_number = get_vlc_info()

        if state in ("playing", "paused"):
            # Claim the LCD if we don't have it yet
            if not lcd_active:
                dll.LogiLcdInit(ctypes.c_wchar_p("VLC Now Playing"), ctypes.c_int(0x00000001))
                lcd_active = True
                print("VLC active — taking LCD.")

            status = "(Playing)" if state == "playing" else "(Paused)"
            dll.LogiLcdMonoSetText(0, ctypes.c_wchar_p(f"  {status}"))
            dll.LogiLcdMonoSetText(1, ctypes.c_wchar_p(f"  {artist[:30]}"))
            dll.LogiLcdMonoSetText(2, ctypes.c_wchar_p(f"  {album[:30]}"))
            dll.LogiLcdMonoSetText(3, ctypes.c_wchar_p(f"  {track_number}. {title[:30]}"))
            dll.LogiLcdUpdate()

        else:
            # Release the LCD back to normal if we were using it
            if lcd_active:
                dll.LogiLcdShutdown()
                lcd_active = False
                print("VLC stopped — releasing LCD.")

        time.sleep(2)

except KeyboardInterrupt:
    print("Stopped.")
    if lcd_active:
        dll.LogiLcdShutdown()

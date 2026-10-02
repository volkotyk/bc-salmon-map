"""Open ../index.html in headless Chrome and fail when the page script does not finish its start.

The page script sets <html data-ready="1"> as its last step. An uncaught error stops the script before that step,
and the map stays empty. The deploy job runs this check, so a broken page does not replace the live one.

  python smoke.py    exit code 0: the page started; 1: the page did not start, or no Chrome found
  CHROME=/path/to/chrome python smoke.py
"""
import os, pathlib, re, shutil, subprocess, sys

PAGE = pathlib.Path(__file__).resolve().parent.parent / "index.html"
NAMES = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome", "msedge"]
WINDOWS = [r"C:\Program Files\Google\Chrome\Application\chrome.exe", r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"]

chrome = os.environ.get("CHROME") or next(filter(None, map(shutil.which, NAMES)), None) \
    or next((p for p in WINDOWS if os.path.exists(p)), None)
if not chrome:
    sys.exit("smoke: no Chrome or Chromium found; set CHROME")

run = subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-sandbox", "--no-first-run",
                      "--enable-logging=stderr", "--v=0", "--virtual-time-budget=10000",
                      "--dump-dom", PAGE.as_uri()], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
if re.search(r'<html[^>]*\sdata-ready="1"', run.stdout):
    print(f"smoke: {PAGE.name} started")
    sys.exit(0)
print(f"smoke: {PAGE.name} did not start (no data-ready mark). Page console:", file=sys.stderr)
for line in run.stderr.splitlines():
    if "CONSOLE" in line or "Uncaught" in line:
        print("  " + line, file=sys.stderr)
sys.exit(1)

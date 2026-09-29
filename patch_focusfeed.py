"""
Usage:  python patch_focusfeed.py your_file.html
Creates index.html with all cleanups + prototype disclaimer applied.
"""
import re, sys, pathlib

src = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "focusfeed.html")
h = src.read_text(encoding="utf-8")
log = []

def step(name, new):
    global h
    log.append(("OK     " if new != h else "SKIPPED", name))
    h = new

# 1. Allow zoom (accessibility)
step("Enable zoom in viewport", h.replace(
    'content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no"',
    'content="width=device-width, initial-scale=1.0"'))

# 2. Remove duplicate "Daily AI Brief" card (first copy)
a = h.find("<!-- \U0001F525 SMART REELS ACCESS CARD")
b = h.find("<!-- Connected Platforms Section")
step("Remove duplicate Daily AI Brief card", h[:a] + h[b:] if 0 <= a < b else h)

# 3. Remove empty leftover comments
new = h
for c in ["<!-- Avatar Evolution Status Bar Component -->",
          "<!-- Time Saved Tracker Card (Gamified Progress Component) -->",
          "<!-- Tab 3: Deep Lock Simulator -->"]:
    new = new.replace(c, "")
step("Remove empty comment blocks", new)

# 4. Repeated icon CSS + extra unpkg script
new = h.replace('<script src="https://unpkg.com/@phosphor-icons/web"></script>', "")
new = re.sub(r'<link href="https://cdn\.jsdelivr\.net/npm/@phosphor-icons/web@2\.1\.2/src/\w+/style\.css" rel="stylesheet" type="text/css">', "", new)
step("Remove duplicate icon links / unpkg script", new)

# 5. Remove unused avatar modal (HTML + JS)
a = h.find("<!-- AVATAR EVOLUTION SYSTEM MODAL -->")
a = h.rfind("<!-- ====", 0, a) if a != -1 else -1
b = h.find("<!-- \U0001F525 SMART REELS LIMIT EXCEEDED MODAL -->")
b = h.rfind("<!-- ====", 0, b) if b != -1 else -1
new = h[:a] + h[b:] if 0 <= a < b else h
new = re.sub(r"// Avatar Evolution Modal.*?(?=// App Customization Selector Modal)", "", new, flags=re.S)
step("Remove unused avatar modal", new)

# 6. Fix dead references in JS
NEW_BUDGET = """function updateReelBudgetUI() {
      const chatIndicator = document.getElementById('chat-budget-indicator');
      if (chatIndicator) chatIndicator.textContent = `${reelBudgetUsed}/${MAX_REELS} Used`;
    }
"""
new = re.sub(r"function updateReelBudgetUI\(\) \{.*?\n    \}\n", lambda m: NEW_BUDGET, h, count=1, flags=re.S)
new = re.sub(r"\s*'screen-chat-lock': 'nav-btn-lock',", "", new)
new = new.replace("'nav-btn-lock', ", "")
step("Remove dead JS references", new)

# 7. innerHTML -> textContent (prevents HTML injection)
SAFE = """const inner = document.createElement('div');
      inner.className = 'bg-sage-500 text-white rounded-3xl rounded-tr-sm p-3.5 shadow-cozy text-xs leading-relaxed';
      inner.textContent = text;
      bubble.appendChild(inner);"""
step("Safe chat bubble (no innerHTML)",
     re.sub(r"bubble\.innerHTML = `.*?`;", lambda m: SAFE, h, count=1, flags=re.S))

# 8. aria-labels on icon-only buttons
LABELS = {"ph-caret-left": "Go back", "ph-arrow-left": "Back to inbox", "ph-funnel": "Filter",
          "ph-paperclip": "Attach", "ph-paper-plane-right": "Send message", "ph-x ": "Close",
          "ph-check": "Save", "ph-play": "Play reel"}
def add_aria(m):
    tag, inner = m.group(1), m.group(2)
    if "aria-label" in tag or re.sub(r"<[^>]+>", "", inner).strip():
        return m.group(0)
    for key, label in LABELS.items():
        if key in inner + " ":
            return f'{tag[:-1]} aria-label="{label}">{inner}</button>'
    return m.group(0)
step("Add aria-labels", re.sub(r"(<button[^>]*>)(.*?)</button>", add_aria, h, flags=re.S))

# 9. Prototype disclaimer (comment + visible footer)
NOTE = ("<!-- FocusFeed AI - UI prototype only. No real app integration, no backend, no user data. "
        "Not affiliated with or endorsed by Instagram, YouTube, Snapchat, Facebook, WhatsApp, X, Reddit or Google. -->\n")
FOOT = ('<p class="fixed bottom-0.5 inset-x-0 text-center text-[10px] text-charcoal-600 px-4 leading-tight" '
        'style="pointer-events:none">It\'s just a prototype (UI demo only, no real app integration). '
        'Not affiliated with or endorsed by Instagram, YouTube, Snapchat, Facebook, WhatsApp, X, Reddit or Google. '
        'All names and logos belong to their owners. Chat names are fictional.</p>\n')
new = h.replace("<!DOCTYPE html>", "<!DOCTYPE html>\n" + NOTE, 1) if "<!DOCTYPE html>" in h else NOTE + h
new = new.replace("</body>", FOOT + "</body>", 1)
step("Add prototype disclaimer", new)

pathlib.Path("index.html").write_text(h, encoding="utf-8")
for status, name in log:
    print(status, name)
print("\nSaved: index.html")

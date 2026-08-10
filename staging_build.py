#!/usr/bin/env python3
"""Build the staging mirror of washington-site.
Copies the BUILT site, then makes it safe to share:
  - base-path rewrite (/x -> /washington-staging/x) for project-Pages hosting
  - noindex meta + robots.txt disallow (prod stays indexable; staging must not be)
  - signup endpoint neutralized (reviewers must not write rows into the real sheet)
  - GA stripped (review traffic is not audience traffic)
  - STAGING ribbon on every page
  - the A2 folder prototype mounted at /a2/ until P1 integrates it as the index
Rerun after every washington-site build:  python3 staging_build.py
"""
import pathlib, re, shutil, subprocess, time

SITE = pathlib.Path.home()/"Documents/GitHub/washington-site"
LAB  = pathlib.Path.home()/"Desktop/washington-design-lab/out/opt-a2-editorial.html"
HERE = pathlib.Path(__file__).resolve().parent
BASE = "/washington-staging"

BRANCH = subprocess.run(["git","-C",str(pathlib.Path.home()/"Documents/GitHub/washington-site"),
    "branch","--show-current"],capture_output=True,text=True).stdout.strip() or "?"
RIBBON = ('<div style="position:fixed;left:0;right:0;top:0;z-index:99999;background:#F74D3A;'
 'color:#fff;font:700 12px/1.4 -apple-system,Helvetica,Arial,sans-serif;letter-spacing:.08em;'
 'text-transform:uppercase;padding:.4rem 1rem;text-align:center">Staging &#183; not the live site '
 '&#183; forms + analytics disabled &#183; branch ' + BRANCH + ' &#183; built ' + time.strftime("%b %d, %H:%M PT") + '</div>'
 '<style>body{margin-top:2rem}</style>')

PAGES = ["index.html","es/index.html","ru/index.html","uk/index.html","loved-ones/index.html"]
for rel in PAGES:
    src = SITE/rel; dst = HERE/rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    h = src.read_text()
    h = h.replace('href="/', f'href="{BASE}/')                      # base rewrite (rooted only)
    h = h.replace(f'href="{BASE}/" ', 'href="/" ') if False else h
    h = re.sub(r'<script async src="https://www\.googletagmanager\.com.*?</script>', "", h, flags=re.S)
    h = re.sub(r'<script>\s*window\.dataLayer.*?</script>', "", h, flags=re.S)
    h = re.sub(r'action="https://script\.google\.com[^"]*"', 'action="#" data-staging-dead', h)
    h = re.sub(r'var ENDPOINT = "https://script\.google\.com[^"]*";', 'var ENDPOINT = "";', h)
    if "script.google.com" in h: raise SystemExit(f"STOPPED: live endpoint survived in {rel}")
    if "noindex" not in h:
        h = h.replace("<head>", '<head><meta name="robots" content="noindex,nofollow">', 1)
    h = h.replace("<body>", "<body>"+RIBBON, 1)
    dst.write_text(h)
    print("staged", rel)

for asset in ["logo.png","og-image.png","paper-blue.jpg"]:
    shutil.copy(SITE/asset, HERE/asset)
(HERE/"robots.txt").write_text("User-agent: *\nDisallow: /\n")
(HERE/"a2").mkdir(exist_ok=True)
shutil.copy(LAB, HERE/"a2/index.html")     # self-contained, noindex + dead forms already
(HERE/"README.md").write_text("# washington-staging\n\n**Staging mirror. NOT the live site.** "
 "noindex, forms dead, GA stripped. Built from washington-site by `staging_build.py`. "
 "The A2 folder prototype is at `/a2/` until integration lands.\n")
print("done")

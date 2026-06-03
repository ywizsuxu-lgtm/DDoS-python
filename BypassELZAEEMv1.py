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
from urllib.parse import urlparse, urlencode
from datetime import datetime
from collections import deque
from typing import Optional, List, Dict, Tuple

try:
    from aiohttp import ClientSession, TCPConnector, ClientTimeout
except ImportError:
    print("[!] aiohttp not installed.  Run:  pip install aiohttp")
    sys.exit(1)

# ======================================================================
#  Constants
# ======================================================================
VERSION       = "4.0"
TOOL_NAME     = "ZAEEM ULTRA"
CONTACT       = "@ZAEEM_S1"
TRIAL_DAYS    = 3
PROXY_TTL     = 3600

PROXY_FILE    = Path.home() / ".zaeem_proxies.json"
ALLOWED_FILE  = Path.home() / ".zaeem_allowed.txt"
STATE_FILE    = Path.home() / ".zaeem_state"
RESULTS_DIR   = Path.home() / ".zaeem_results"

DEFAULT_CONC  = 300
DEFAULT_TOTAL = 3000
DEFAULT_TOUT  = 8.0
WARN_MS       = 600
DEG_5XX       = 0.10
DEG_P95_MS    = 1200

# ======================================================================
#  User-Agent Pool
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

def div(char="=", width=66, color=Color.CYAN):
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
    "  Use ONLY on systems you own or have explicit permission to test.\n"
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

def _save_trial(ts_):
    try:
        STATE_FILE.write_text(str(int(ts_)), "utf-8")
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
    return False, f"Host '{host}' not in allowlist.\nAllowed: {', '.join(sorted(allowed))}"

# ======================================================================
#  Proxy Engine
# ======================================================================
class ProxyEngine:

    def __init__(self):
        self._list       = []
        self._bad        = set()
        self._idx        = 0
        self._lock       = threading.Lock()
        self.fetched_at  = 0.0

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
        conn = TCPConnector(limit=40, ssl=False)
        try:
            async with ClientSession(connector=conn) as s:
                results = await asyncio.gather(
                    *[self._fetch_one(s, u) for u in PROXY_SOURCES],
                    return_exceptions=True
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

    def _run(self, coro):
        try:
            return asyncio.run(coro)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(coro)

    def fetch(self, cb=None):
        if cb:
            cb(paint(f"  [{ts()}] Fetching from {len(PROXY_SOURCES)} sources...", Color.YELLOW))
        lst = self._run(self._fetch_all())
        with self._lock:
            self._list      = lst
            self._bad       = set()
            self._idx       = 0
            self.fetched_at = time.time()
        self._save()
        if cb:
            cb(paint(f"  [{ts()}] Fetched {len(lst)} proxies.", Color.GREEN))
        return len(lst)

    def reset_and_fetch(self, cb=None):
        with self._lock:
            self._list = []
            self._bad  = set()
            self._idx  = 0
            self.fetched_at = 0.0
        try:
            if PROXY_FILE.exists():
                PROXY_FILE.unlink()
        except Exception:
            pass
        self.fetch(cb)

    def load_or_fetch(self, cb=None, force=False):
        if force:
            self.reset_and_fetch(cb)
            return
        if PROXY_FILE.exists():
            try:
                data = json.loads(PROXY_FILE.read_text("utf-8"))
                age  = time.time() - float(data.get("fetched_at", 0))
                lst  = data.get("proxies", [])
                if age < PROXY_TTL and lst:
                    with self._lock:
                        self._list      = lst
                        self.fetched_at = data["fetched_at"]
                    if cb:
                        cb(paint(f"  [{ts()}] Loaded {len(lst)} proxies (cache).", Color.GREEN))
                    return
            except Exception:
                pass
        self.fetch(cb)

    def _save(self):
        try:
            PROXY_FILE.write_text(
                json.dumps({"fetched_at": self.fetched_at, "proxies": self._list}),
                "utf-8"
            )
        except Exception:
            pass

    def next(self):
        with self._lock:
            avail = [p for p in self._list if p not in self._bad]
            if not avail:
                return None
            p = avail[self._idx % len(avail)]
            self._idx += 1
            return f"http://{p}"

    def mark_bad(self, proxy_url):
        with self._lock:
            raw = re.sub(r"^https?://", "", proxy_url)
            self._bad.add(raw)

    def count(self):
        with self._lock:
            return max(0, len(self._list) - len(self._bad))

    def summary(self):
        with self._lock:
            total = len(self._list)
            bad   = len(self._bad)
            good  = max(0, total - bad)
            return f"Proxies: {good} active / {bad} removed / {total} total"


PROXY = ProxyEngine()

# ======================================================================
#  Payload helpers
# ======================================================================
def rand_str(n=12):
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))

def rand_qs():
    pairs = "&".join(f"{rand_str(5)}={rand_str(10)}" for _ in range(random.randint(1, 4)))
    return "?" + pairs

def rand_post_body():
    return urlencode({rand_str(8): rand_str(16) for _ in range(random.randint(3, 8))})

def rand_xff():
    return ".".join(str(random.randint(1, 254)) for _ in range(4))

# ======================================================================
#  Live Stats
# ======================================================================
class Stats:
    def __init__(self, total):
        self.total  = total
        self.ok     = 0
        self.fail   = 0
        self.lat    = deque(maxlen=8000)
        self.codes  = {}
        self.errors = {}
        self._lock  = threading.Lock()
        self.t0     = time.perf_counter()

    def hit(self, ms, code):
        with self._lock:
            self.ok += 1
            self.lat.append(ms)
            self.codes[code] = self.codes.get(code, 0) + 1

    def miss(self, name):
        with self._lock:
            self.fail += 1
            self.errors[name] = self.errors.get(name, 0) + 1

    def sent(self):
        return self.ok + self.fail

    def rps(self):
        elapsed = time.perf_counter() - self.t0
        return self.sent() / elapsed if elapsed > 0 else 0.0

    def pct(self, p):
        lat = sorted(self.lat)
        if not lat:
            return 0.0
        k = max(0, int(round((p / 100) * (len(lat) - 1))))
        return lat[k]

    def avg(self):
        lat = list(self.lat)
        return statistics.mean(lat) if lat else 0.0

# ======================================================================
#  Worker
# ======================================================================
async def worker(session, url, method, sem, stats, timeout,
                 use_proxy, rand_path, verbose):
    async with sem:
        proxy  = PROXY.next() if use_proxy else None
        target = url + (rand_qs() if rand_path else "")
        data   = rand_post_body() if method == "POST" else None
        headers = {
            "User-Agent"      : random.choice(UA_POOL),
            "Accept"          : "text/html,application/xhtml+xml,*/*;q=0.8",
            "Accept-Language" : "en-US,en;q=0.9",
            "Accept-Encoding" : "gzip, deflate",
            "Connection"      : "keep-alive",
            "Cache-Control"   : "no-cache, no-store",
            "Pragma"          : "no-cache",
            "X-Forwarded-For" : rand_xff(),
            "X-Real-IP"       : rand_xff(),
        }
        if method == "POST":
            headers["Content-Type"] = "application/x-www-form-urlencoded"

        t0 = time.perf_counter()
        try:
            async with session.request(
                method, target,
                headers=headers, data=data,
                proxy=proxy,
                timeout=timeout,
                allow_redirects=True,
                max_redirects=5,
            ) as resp:
                await resp.read()
                ms = (time.perf_counter() - t0) * 1000.0
                stats.hit(ms, resp.status)
                if verbose:
                    if resp.status >= 500:
                        print(paint(f"  [{ts()}] x {resp.status}  {ms:7.1f}ms", Color.RED))
                    elif resp.status >= 400 or ms >= WARN_MS:
                        print(paint(f"  [{ts()}] ! {resp.status}  {ms:7.1f}ms", Color.YELLOW))
                    else:
                        print(paint(f"  [{ts()}] + {resp.status}  {ms:7.1f}ms", Color.GREEN))

        except (aiohttp.ClientProxyConnectionError,
                aiohttp.ClientConnectorError):
            stats.miss("ProxyError")
            if proxy:
                PROXY.mark_bad(proxy)
        except asyncio.TimeoutError:
            stats.miss("TimeoutError")
        except Exception as e:
            stats.miss(type(e).__name__)

# ======================================================================
#  Progress bar
# ======================================================================
async def show_progress(tasks, stats):
    W = 36
    while True:
        done   = sum(1 for t in tasks if t.done())
        frac   = done / stats.total if stats.total else 1.0
        filled = int(frac * W)
        bar    = "#" * filled + "-" * (W - filled)
        line   = (
            paint(f"\r  [{ts()}] ", Color.DIM)
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
async def engine(url, method, concurrency, total,
                 timeout_s, verify_tls, use_proxy,
                 rand_path, verbose):
    sem     = asyncio.Semaphore(concurrency)
    stats   = Stats(total)
    ssl_ctx = None

    if urlparse(url).scheme == "https":
        ssl_ctx = ssl.create_default_context()
        if not verify_tls:
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode    = ssl.CERT_NONE

    conn = TCPConnector(
        ssl=ssl_ctx,
        limit=0,
        limit_per_host=0,
        ttl_dns_cache=300,
        use_dns_cache=True,
        enable_cleanup_closed=True,
        keepalive_timeout=30,
    )
    to = ClientTimeout(total=timeout_s, connect=5.0, sock_read=timeout_s)

    async with ClientSession(connector=conn,
                             skip_auto_headers=["User-Agent"]) as session:
        tasks = [
            asyncio.create_task(
                worker(session, url, method, sem, stats, to,
                       use_proxy, rand_path, verbose)
            )
            for _ in range(total)
        ]
        if verbose:
            await asyncio.gather(*tasks, return_exceptions=True)
        else:
            await asyncio.gather(
                asyncio.create_task(show_progress(tasks, stats)),
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
                return {"up": True, "status": r.status,
                        "ms": round(ms, 1), "err": None}
    except Exception as e:
        return {"up": False, "status": None, "ms": None,
                "err": f"{type(e).__name__}: {e}"}

# ======================================================================
#  Save results
# ======================================================================
def save_result(url, dt, stats, rps, hc):
    try:
        RESULTS_DIR.mkdir(exist_ok=True)
        fname = RESULTS_DIR / f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        fname.write_text(json.dumps({
            "url"        : url,
            "duration_s" : round(dt, 2),
            "sent"       : stats.sent(),
            "ok"         : stats.ok,
            "fail"       : stats.fail,
            "rps"        : round(rps, 1),
            "latency"    : {
                "avg": round(stats.avg(), 1),
                "p50": round(stats.pct(50), 1),
                "p95": round(stats.pct(95), 1),
                "p99": round(stats.pct(99), 1),
            },
            "codes"        : stats.codes,
            "health_after" : hc,
            "timestamp"    : datetime.now().isoformat(),
        }, indent=2), "utf-8")
    except Exception:
        pass

# ======================================================================
#  Results screen
# ======================================================================
def print_results(url, dt, stats, method, used_proxy, verify_tls):
    clr()
    sent = stats.sent()
    rps  = sent / dt if dt > 0 else 0.0
    ip   = resolve_ip(url)

    print(div())
    print(paint(f"  TEST COMPLETE  --  {TOOL_NAME} {VERSION}",
                Color.BOLD, Color.GREEN))
    print(div())
    print(paint(f"  Target   : {url}", Color.CYAN))
    print(paint(f"  IP       : {ip}", Color.DIM))
    print(paint(f"  Method   : {method}", Color.CYAN))
    print(paint(f"  Proxy    : {'enabled (' + str(PROXY.count()) + ')' if used_proxy else 'direct'}",
                Color.CYAN))
    print(paint(f"  Duration : {dt:.2f}s", Color.CYAN))
    print(div("-", 66, Color.DIM))

    ok_p   = stats.ok   / sent * 100 if sent else 0.0
    fail_p = stats.fail / sent * 100 if sent else 0.0
    print(paint(f"  Total    : {sent}", Color.WHITE))
    print(paint(f"  Success  : {stats.ok}  ({ok_p:.1f}%)", Color.GREEN))
    print(paint(f"  Failed   : {stats.fail}  ({fail_p:.1f}%)", Color.RED))
    print(paint(f"  RPS      : {rps:.1f} req/s", Color.YELLOW, Color.BOLD))
    print(div("-", 66, Color.DIM))

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
        print(div("-", 66, Color.DIM))

    if stats.codes:
        print(paint("  HTTP Status Codes", Color.BLUE))
        for code in sorted(stats.codes):
            cnt = stats.codes[code]
            bar = "#" * min(30, max(1, cnt * 30 // max(1, sent)))
            if code < 400:
                col = Color.GREEN
            elif code < 500:
                col = Color.YELLOW
            else:
                col = Color.RED
            print(paint(f"    {code}: {cnt:>7}  {bar}", col))
        print(div("-", 66, Color.DIM))

    if stats.errors:
        print(paint("  Errors", Color.RED))
        for e, cnt in sorted(stats.errors.items(), key=lambda x: -x[1])[:8]:
            print(paint(f"    {e}: {cnt}", Color.DIM))
        print(div("-", 66, Color.DIM))

    five_xx  = sum(v for k, v in stats.codes.items()
                   if isinstance(k, int) and k >= 500)
    five_r   = five_xx / sent if sent else 0.0
    degraded = five_r >= DEG_5XX or stats.pct(95) >= DEG_P95_MS

    hc = asyncio.run(health_check(url, 10.0, verify_tls))
    save_result(url, dt, stats, rps, hc)

    print(paint("  Target Status After Test", Color.BLUE))
    if not hc["up"]:
        print(paint("  [DOWN]      No response / connection refused.",
                    Color.RED, Color.BOLD))
        print(paint(f"              {hc['err']}", Color.DIM))
    elif degraded or (hc["status"] and hc["status"] >= 500):
        print(paint("  [DEGRADED]  Server errors or high latency.",
                    Color.YELLOW, Color.BOLD))
        print(paint(f"              HTTP {hc['status']}  |  {hc['ms']}ms",
                    Color.DIM))
    else:
        print(paint("  [UP]        Responding normally.",
                    Color.GREEN, Color.BOLD))
        print(paint(f"              HTTP {hc['status']}  |  {hc['ms']}ms",
                    Color.DIM))

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

# ======================================================================
#  Sub-screens
# ======================================================================
def run_test_screen(target):
    clr()
    print(BANNER)
    print(div())
    print(paint("  TEST CONFIGURATION", Color.CYAN, Color.BOLD))
    print(div("-", 66, Color.DIM))

    ok, msg = validate_target(target)
    if not ok:
        print(paint(f"\n  [ERROR] {msg}", Color.RED))
        print(paint("  Add the domain from menu [A] first.", Color.YELLOW))
        input(paint("  Press Enter...", Color.DIM))
        return

    print(paint(f"  Target  : {target}", Color.GREEN))
    print(paint(f"  IP      : {resolve_ip(target)}", Color.DIM))
    print(div("-", 66, Color.DIM))

    m_raw  = input(paint("  Method  GET/POST/HEAD [GET]: ",
                         Color.YELLOW)).strip().upper()
    method = m_raw if m_raw in ("GET","POST","HEAD","PUT","DELETE") else "GET"
    conc   = ask_int  (paint(f"  Concurrency [{DEFAULT_CONC}]: ",  Color.YELLOW), DEFAULT_CONC)
    total  = ask_int  (paint(f"  Total requests [{DEFAULT_TOTAL}]: ", Color.YELLOW), DEFAULT_TOTAL)
    tout   = ask_float(paint(f"  Timeout seconds [{DEFAULT_TOUT}]: ", Color.YELLOW), DEFAULT_TOUT)
    tls    = ask_yn   (paint( "  Verify TLS? (y/N) [N]: ",           Color.YELLOW), False)
    rpath  = ask_yn   (paint( "  Random query string? (Y/n) [Y]: ",  Color.YELLOW), True)
    verb   = ask_yn   (paint( "  Verbose per-request log? (y/N) [N]: ", Color.YELLOW), False)

    use_proxy = False
    if PROXY.count() > 0:
        use_proxy = ask_yn(
            paint(f"  Use proxies? ({PROXY.count()} available) (Y/n) [Y]: ",
                  Color.YELLOW), True
        )
    else:
        print(paint("  [!] No proxies available -- sending direct.", Color.YELLOW))

    print(div())
    print(paint(f"  Launching: {method} x{total}  concurrency={conc}",
                Color.GREEN, Color.BOLD))
    if use_proxy:
        print(paint(f"  {PROXY.summary()}", Color.DIM))
    print(div())

    t0    = time.time()
    stats = asyncio.run(
        engine(target, method, conc, total, tout, tls, use_proxy, rpath, verb)
    )
    dt    = time.time() - t0

    print_results(target, dt, stats, method, use_proxy, tls)


def proxy_screen():
    while True:
        clr()
        print(BANNER)
        print(div())
        print(paint("  PROXY MANAGEMENT", Color.CYAN, Color.BOLD))
        print(div("-", 66, Color.DIM))
        print(paint(f"  {PROXY.summary()}", Color.DIM))
        print(div("-", 66, Color.DIM))
        print(paint("  [1] Full refresh (wipe + fetch new)", Color.GREEN))
        print(paint("  [2] Fetch only (re-download)", Color.YELLOW))
        print(paint("  [3] Show count", Color.CYAN))
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
            print(paint(f"\n  {PROXY.summary()}", Color.GREEN))
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
    print(paint("  Example:  example.com  (no http/https)", Color.DIM))
    print(div("-", 66, Color.DIM))
    h = input(paint("  Domain: ", Color.GREEN)).strip()
    if add_allowed(h):
        print(paint(f"  [OK] Saved: {h}", Color.GREEN))
    else:
        print(paint("  [ERROR] Invalid domain.", Color.RED))
    time.sleep(0.8)


def help_screen():
    clr()
    print(BANNER)
    print(div())
    lines = [
        f"  {TOOL_NAME} {VERSION}  --  High-Speed Async Load Tester",
        "",
        "  QUICK START:",
        "    1. Run the tool.  Proxies are fetched automatically.",
        "    2. Enter a target IP or URL when prompted.",
        "    3. Select [1] from the menu to start the test.",
        "",
        "  TARGET FORMATS ACCEPTED:",
        "    IP only        192.168.1.10",
        "    IP with port   192.168.1.10:8080",
        "    Domain         example.com  (must be in allowlist)",
        "    Full URL       https://example.com/path",
        "",
        "  PROXY BEHAVIOR:",
        "    - Every run: old proxies wiped, new ones fetched fresh.",
        "    - Proxies rotate per-request (circular, auto-remove bad).",
        "",
        "  BEST PERFORMANCE SETTINGS:",
        "    concurrency=500  |  requests=5000  |  timeout=5",
        "    TLS=N  |  rand_path=Y  |  proxy=Y",
        "",
        "  INSTALL:",
        "    pip install aiohttp",
        "    pip install uvloop    (optional, +50% speed on Linux)",
        "",
        f"  CONTACT: {CONTACT}",
    ]
    for ln in lines:
        print(paint(ln, Color.CYAN if ln.startswith(f"  {TOOL_NAME}") else Color.WHITE))
    print(div())
    input(paint("  Press Enter...", Color.DIM))


def history_screen():
    clr()
    print(BANNER)
    print(div())
    print(paint("  RESULTS HISTORY (last 10 tests)", Color.CYAN, Color.BOLD))
    print(div("-", 66, Color.DIM))
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
                    print(
                        paint(f"  {icon}", col)
                        + paint(f"  {d['timestamp'][:16]}  ", Color.DIM)
                        + paint(f"{d['url'][:38]}", Color.CYAN)
                        + paint(f"  rps={d.get('rps', 0)}", Color.YELLOW)
                    )
                except Exception:
                    pass
    except Exception:
        pass
    print(div())
    input(paint("  Press Enter...", Color.DIM))

# ======================================================================
#  Target input prompt
# ======================================================================
def ask_target():
    print(paint(
        "\n"
        "  Enter the target:\n"
        "    IP address     ->  192.168.1.10\n"
        "    IP with port   ->  192.168.1.10:8080\n"
        "    Domain         ->  example.com\n"
        "    Full URL       ->  https://example.com/page\n",
        Color.DIM
    ))
    while True:
        print(div("-", 66, Color.DIM))
        raw = input(paint("  >> Target (IP / URL): ",
                          Color.GREEN, Color.BOLD)).strip()
        if not raw:
            print(paint("  [!] Input cannot be empty.", Color.RED))
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
            q = input(paint(f"  Add '{host}' to allowlist? (y/N): ",
                            Color.YELLOW)).strip().lower()
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
        print(div("-", 66, Color.DIM))
        print(paint(f"  Target  : {target}", Color.GREEN))
        print(paint(f"  IP      : {resolve_ip(target)}", Color.DIM))
        print(paint(f"  {PROXY.summary()}", Color.DIM))
        print(div())
        print(paint("  [1]  Start stress test", Color.GREEN))
        print(paint("  [2]  Change target", Color.CYAN))
        print(paint("  [3]  Proxy management", Color.YELLOW))
        print(paint("  [A]  Add authorized domain", Color.CYAN))
        print(paint("  [B]  Show authorized domains", Color.CYAN))
        print(paint("  [H]  Help", Color.DIM))
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
    try:
        import uvloop
        uvloop.install()
    except ImportError:
        pass

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
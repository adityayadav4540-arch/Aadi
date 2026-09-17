# ═══════════════════════════════════════════════════════════════════════
#  PUBLIC USERBOT — FINAL EDITION
#  Owner-as-Controller  ·  Multi-account  ·  Railway-ready
#
#  requirements.txt:
#      telethon
#      python-telegram-bot
#      aiohttp
# ═══════════════════════════════════════════════════════════════════════

import asyncio, html, json, logging, os, random, re, signal, sys, tempfile, threading, time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Set

from aiohttp import web
from telethon import TelegramClient, events
from telethon.errors import (
    FloodWaitError, UserAlreadyParticipantError, InviteHashExpiredError,
    InviteHashInvalidError, ChannelsTooMuchError, UsernameNotOccupiedError,
    UsernameInvalidError, PeerIdInvalidError, SessionRevokedError,
    AuthKeyUnregisteredError, SessionPasswordNeededError,
    PhoneCodeInvalidError, PhoneCodeExpiredError, ChatAdminRequiredError,
    UserNotParticipantError, UserAdminInvalidError,
)
from telethon.tl.functions.channels import EditBannedRequest, JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.photos import UploadProfilePhotoRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import ChatBannedRights, InputMediaGeoPoint, InputGeoPoint

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters,
)

# ═══════════════════════════════════════════════════════════════════════
#  CONFIG — hardcoded as requested
# ═══════════════════════════════════════════════════════════════════════

BOT_TOKEN        = os.environ.get("BOT_TOKEN", "8833875612:AAHoaDz2O_BlnbZDFI6V5rxkX1k-qDZZ-o")
MANAGER_OWNER_ID = int(os.environ.get("OWNER_ID", "8763690873"))
PORT             = int(os.environ.get("PORT", "8080"))
PREFIX           = "z"
GEO_LAT          = float(os.environ.get("GEO_LAT", "48.8584"))
GEO_LON          = float(os.environ.get("GEO_LON", "2.2945"))

DATA_DIR     = Path(os.environ.get("DATA_DIR", "/data" if Path("/data").is_dir() else "."))
SESSIONS_DIR = DATA_DIR / "sessions"
try: SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    SESSIONS_DIR = Path("sessions"); SESSIONS_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)-9s | %(message)s",
    datefmt="%H:%M:%S", stream=sys.stdout, force=True,
)
log = logging.getLogger("main")
for n in ("telethon", "httpx", "telegram", "aiohttp", "telegram.ext"):
    logging.getLogger(n).setLevel(logging.WARNING)

GLOBAL_OWNER_ID = MANAGER_OWNER_ID

# ═══════════════════════════════════════════════════════════════════════
#  ABUSE ENGINE
# ═══════════════════════════════════════════════════════════════════════

ABUSE = [
    "<b>{n}</b> — 𝘵𝘦𝘳𝘪 𝘮𝘢 𝘬𝘢 𝘣𝘩𝘰𝘴𝘥𝘢 𝘳𝘢𝘯𝘥𝘪 𝘬𝘦 𝘱𝘪𝘭𝘭𝘦 🩸",
    "<b>{n}</b> — 𝘵𝘦𝘳𝘪 𝘮𝘢 𝘬𝘪 𝘤𝘩𝘶𝘵 𝘮𝘦 𝘭𝘢𝘵𝘩 𝘨𝘩𝘶𝘴𝘢 𝘥𝘶𝘯𝘨𝘢 🗿",
    "<b>{n}</b> — 𝘮𝘢𝘥𝘢𝘳𝘤𝘩𝘰𝘥 𝘴𝘢𝘭𝘦 𝘵𝘦𝘳𝘪 𝘨𝘢𝘢𝘯𝘥 𝘮𝘦 𝘭𝘢𝘵𝘩 🍑",
    "<b>{n}</b> — 𝘵𝘦𝘳𝘪 𝘣𝘦𝘩𝘦𝘯 𝘬𝘪 𝘤𝘩𝘶𝘵 𝘮𝘦 𝘭𝘶𝘯𝘥 𝘥𝘢𝘭 𝘥𝘶𝘯𝘨𝘢 🤡",
    "<b>{n}</b> — 𝘣𝘩𝘦𝘯𝘤𝘩𝘰𝘥 𝘵𝘦𝘳𝘪 𝘮𝘢 𝘬𝘢 𝘺𝘢𝘩𝘪 𝘩𝘢𝘢𝘭 𝘩𝘰𝘨𝘢 📡",
    "<b>{n}</b> — 𝘳𝘢𝘯𝘥𝘪 𝘬𝘦 𝘣𝘢𝘤𝘩𝘦 𝘵𝘦𝘳𝘪 𝘮𝘢 𝘬𝘢 𝘣𝘩𝘰𝘴𝘥𝘢 🧠",
    "<b>{n}</b> — 𝘵𝘦𝘳𝘪 𝘮𝘢 𝘬𝘰 𝘤𝘩𝘰𝘥 𝘬𝘦 𝘵𝘦𝘳𝘦 𝘣𝘢𝘢𝘱 𝘬𝘰 𝘳𝘢𝘯𝘥𝘪 𝘣𝘢𝘯𝘢 𝘥𝘶𝘯𝘨𝘢 ⏳",
    "<b>{n}</b> — 𝘭𝘢𝘸𝘥𝘦 𝘬𝘦 𝘣𝘢𝘭 𝘵𝘦𝘳𝘪 𝘮𝘢 𝘬𝘢 𝘣𝘩𝘰𝘴𝘥𝘢 🥇",
    "<b>{n}</b> — 𝘵𝘦𝘳𝘪 𝘮𝘢 𝘬𝘪 𝘤𝘩𝘶𝘵 𝘮𝘦 𝘬𝘶𝘵𝘵𝘢 𝘤𝘩𝘰𝘥 𝘥𝘶𝘯𝘨𝘢 💀",
    "<b>{n}</b> — 𝘮𝘢𝘥𝘢𝘳𝘤𝘩𝘰𝘥 𝘵𝘦𝘳𝘪 𝘨𝘢𝘢𝘯𝘥 𝘮𝘦 𝘣𝘰𝘮𝘣 🔥",
    "<b>{n}</b> — 𝘣𝘩𝘰𝘴𝘥𝘪𝘬𝘦 𝘵𝘦𝘳𝘪 𝘮𝘢 𝘬𝘢 𝘣𝘩𝘢𝘳𝘰𝘴𝘢 🚬",
    "<b>{n}</b> — 𝘵𝘦𝘳𝘪 𝘮𝘢 𝘬𝘪 𝘨𝘢𝘢𝘯𝘥 𝘮𝘦 𝘮𝘦𝘳𝘢 𝘭𝘢𝘶𝘥𝘢 ⚡",
    "<b>{n}</b> — 𝘨𝘢𝘢𝘯𝘥𝘶 𝘵𝘦𝘳𝘪 𝘮𝘢 𝘬𝘢 𝘣𝘩𝘰𝘴𝘥𝘢 𝘳𝘢𝘯𝘥𝘪 𝘬𝘦 𝘱𝘪𝘭𝘭𝘦 🌙",
    "<b>{n}</b> — 𝘵𝘦𝘳𝘪 𝘮𝘢 𝘬𝘰 𝘳𝘢𝘯𝘥𝘪 𝘬𝘩𝘢𝘯𝘦 𝘣𝘩𝘦𝘫 𝘥𝘶𝘯𝘨𝘢 ⭐",
    "<b>{n}</b> — 𝘭𝘢𝘸𝘥𝘦 𝘵𝘦𝘳𝘪 𝘮𝘢 𝘬𝘪 𝘤𝘩𝘶𝘵 𝘮𝘦 𝘱𝘦𝘵𝘳𝘰𝘭 𝘥𝘢𝘭 𝘥𝘶𝘯𝘨𝘢 🪐",
    "<b>{n}</b> — 𝘣𝘩𝘦𝘯𝘤𝘩𝘰𝘥 𝘵𝘦𝘳𝘪 𝘣𝘦𝘩𝘦𝘯 𝘬𝘰 𝘤𝘩𝘰𝘥 𝘥𝘶𝘯𝘨𝘢 💧",
    "<b>{n}</b> — 𝘵𝘦𝘳𝘪 𝘮𝘢 𝘬𝘢 𝘣𝘩𝘰𝘴𝘥𝘢 𝘮𝘢𝘥𝘢𝘳𝘤𝘩𝘰𝘥 🎯",
    "<b>{n}</b> — 𝘳𝘢𝘯𝘥𝘪 𝘬𝘦 𝘢𝘶𝘭𝘢𝘥 𝘵𝘦𝘳𝘪 𝘮𝘢 𝘬𝘪 𝘤𝘩𝘶𝘵 🏓",
    "<b>{n}</b> — 𝘵𝘦𝘳𝘪 𝘮𝘢 𝘬𝘪 𝘨𝘢𝘢𝘯𝘥 𝘮𝘦 𝘢𝘢𝘨 𝘭𝘢𝘨𝘢 𝘥𝘶𝘯𝘨𝘢 🕷",
    "<b>{n}</b> — 𝘣𝘩𝘰𝘴𝘥𝘪𝘬𝘦 𝘵𝘦𝘳𝘪 𝘮𝘢 𝘬𝘰 𝘬𝘶𝘵𝘵𝘰 𝘴𝘦 𝘤𝘩𝘶𝘥𝘸𝘢 𝘥𝘶𝘯𝘨𝘢 👾",
    "<b>{n}</b> — 𝘭𝘢𝘸𝘥𝘦 𝘵𝘦𝘳𝘪 𝘮𝘢 𝘬𝘢 𝘣𝘩𝘰𝘴𝘥𝘢 𝘨𝘢𝘳𝘢𝘮 𝘭𝘰𝘩𝘢 🤸",
    "<b>{n}</b> — 𝘮𝘢𝘥𝘢𝘳𝘤𝘩𝘰𝘥 𝘵𝘦𝘳𝘪 𝘮𝘢 𝘬𝘢 𝘴𝘢𝘭𝘢 𝘣𝘩𝘰𝘴𝘥𝘢 🌋",
    "<b>{n}</b> — 𝘵𝘦𝘳𝘪 𝘮𝘢 𝘬𝘪 𝘤𝘩𝘶𝘵 𝘮𝘦 𝘨𝘰𝘭𝘢 𝘣𝘢𝘳𝘰𝘰𝘥 🥞",
    "<b>{n}</b> — 𝘨𝘢𝘢𝘯𝘥𝘶 𝘵𝘦𝘳𝘪 𝘮𝘢 𝘬𝘪 𝘤𝘩𝘶𝘵 𝘮𝘦 𝘭𝘶𝘯𝘥 🩸",
    "<b>{n}</b> — 𝘣𝘩𝘦𝘯𝘤𝘩𝘰𝘥 𝘵𝘦𝘳𝘪 𝘮𝘢 𝘬𝘰 𝘴𝘵𝘳𝘦𝘦𝘵 𝘱𝘦 𝘤𝘩𝘶𝘥𝘸𝘢 𝘥𝘶𝘯𝘨𝘢 🗿",
]

# ═══════════════════════════════════════════════════════════════════════
#  MENU
# ═══════════════════════════════════════════════════════════════════════

MENU_HTML = """
<b>╭─── 𝗠 𝗘 𝗡 𝗨 ───╮</b>
<b>│</b>  𝘗𝘳𝘦𝘧𝘪𝘹 · <code>{p}</code>
<b>│</b>  𝘛𝘢𝘳𝘨𝘦𝘵 · reply / @user / id
<b>╰──────────────────╯</b>

<b>▸ 𝗔𝘂𝘁𝗼𝗺𝗮𝘁𝗶𝗼𝗻</b>
 <code>{p}loop a | b</code> · alternating loop
 <code>{p}endloop</code> · stop loop
 <code>{p}echo &lt;text&gt;</code> · auto-reply
 <code>{p}unecho</code> · remove auto-reply
 <code>{p}sticker</code> · sticker spam
 <code>{p}unstickers</code> · stop stickers
 <code>{p}photo</code> · photo spam
 <code>{p}unphoto</code> · stop photos
 <code>{p}video</code> · video spam
 <code>{p}unvideo</code> · stop videos
 <code>{p}burn</code> · roast every message
 <code>{p}cool</code> · stop roast
 <code>{p}storm</code> · rage mode
 <code>{p}calmstorm</code> · stop rage
 <code>{p}flood &lt;msg&gt; &lt;sec&gt;</code> · flood chat
 <code>{p}drain</code> · stop flood

<b>▸ 𝗖𝗼𝗺𝗯𝗮𝘁</b>
 <code>{p}clap</code> · 5× barrage
 <code>{p}rage</code> · abuse loop
 <code>{p}calmdown</code> · stop rage
 <code>{p}spit</code> · single abuse
 <code>{p}curse</code> · 5-line burst
 <code>{p}war</code> · double-target

<b>▸ 𝗠𝗼𝗱𝗲𝗿𝗮𝘁𝗶𝗼𝗻</b>
 <code>{p}shush</code> / <code>{p}unshush</code> · mute
 <code>{p}shushlist</code> · muted list
 <code>{p}exile</code> / <code>{p}recall</code> · ban / unban

<b>▸ 𝗣𝗿𝗼𝗳𝗶𝗹𝗲</b>
 <code>{p}mirror</code> · clone profile
 <code>{p}unmirror</code> · restore

<b>▸ 𝗚𝗲𝗼</b>
 <code>{p}geo &lt;sec&gt;</code> / <code>{p}ungeo</code>

<b>▸ 𝗔𝗰𝗰𝗲𝘀𝘀</b>
 <code>{p}permit</code> / <code>{p}revoke</code> · sudo
 <code>{p}roster</code> · sudo list
 <code>{p}whoami</code> · your rank

<b>▸ 𝗦𝘂𝗺𝗺𝗼𝗻</b>
 <code>{p}summon &lt;link&gt;</code> · broadcast join
 <code>{p}stopall-summon</code> · stop summon

<b>▸ 𝗢𝘄𝗻𝗲𝗿</b>
 <code>{p}join &lt;link&gt;</code> · single join
 <code>{p}halt</code> / <code>{p}thaw</code> · pause / resume
 <code>{p}recall all</code> · global wipe
"""

# ═══════════════════════════════════════════════════════════════════════
#  REGISTRY + CLAIM
# ═══════════════════════════════════════════════════════════════════════

ACCOUNT_REGISTRY: dict[int, Set[TelegramClient]] = defaultdict(set)
CLIENT_OWNERS: dict[TelegramClient, int] = {}
REGISTRY_LOCK = threading.Lock()

# session_name -> metadata
SESSION_STATS: dict[str, dict] = {}
STATS_LOCK = threading.Lock()

# (chat_id, msg_id) -> timestamp — prevents duplicate command handling
CLAIMED: dict[tuple[int, int], float] = {}
CLAIM_LOCK = threading.Lock()


def try_claim(chat_id: int, msg_id: int) -> bool:
    now = time.time()
    with CLAIM_LOCK:
        # prune old claims
        for k in [k for k, v in CLAIMED.items() if now - v > 60]:
            CLAIMED.pop(k, None)
        key = (chat_id, msg_id)
        if key in CLAIMED:
            return False
        CLAIMED[key] = now
        return True


def stat_inc(session: str, key: str, delta: int = 1):
    with STATS_LOCK:
        s = SESSION_STATS.setdefault(session, {"commands": 0, "started": time.time()})
        s[key] = s.get(key, 0) + delta


def stat_mark(session: str):
    with STATS_LOCK:
        SESSION_STATS.setdefault(session, {"commands": 0, "started": time.time()})


def uptime_str(seconds: float) -> str:
    seconds = int(seconds)
    h, r = divmod(seconds, 3600); m, s = divmod(r, 60)
    if h: return f"{h}h {m}m"
    if m: return f"{m}m {s}s"
    return f"{s}s"

# ═══════════════════════════════════════════════════════════════════════
#  PER-CHAT STATE
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class ChatState:
    loop_targets:  dict = field(default_factory=dict)
    loop_tasks:    dict = field(default_factory=dict)
    roasts:        dict = field(default_factory=dict)
    rages:         dict = field(default_factory=dict)
    echoes:        dict = field(default_factory=dict)
    sticker:       dict = field(default_factory=dict)
    photo:         dict = field(default_factory=dict)
    video:         dict = field(default_factory=dict)
    sticker_tasks: dict = field(default_factory=dict)
    photo_tasks:   dict = field(default_factory=dict)
    video_tasks:   dict = field(default_factory=dict)
    calm_loops:    dict = field(default_factory=dict)
    shushed:       set = field(default_factory=set)
    geo_task:      Optional[asyncio.Task] = None
    flood_tasks:   list = field(default_factory=list)
    flooding:      bool = False
    summon_tasks:  dict = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════════════
#  USERBOT INSTANCE
# ═══════════════════════════════════════════════════════════════════════

class UserbotInstance:
    def __init__(self, name, session_path, api_id, api_hash, owner_ids):
        self.name = name
        self.session_path = session_path
        self.api_id = api_id
        self.api_hash = api_hash
        self.owner_ids = set(owner_ids) | {GLOBAL_OWNER_ID}

        self.client = TelegramClient(
            session_path, api_id, api_hash,
            auto_reconnect=True, retry_delay=3,
            connection_retries=100, timeout=30, request_retries=10,
        )

        self.chat: dict[int, ChatState] = defaultdict(ChatState)
        self.sudo: dict[int, set] = defaultdict(set)
        self.original_profile: dict = {}
        self.global_paused = False
        self.send_queue: asyncio.Queue = asyncio.Queue()
        self._workers: list[asyncio.Task] = []
        self._watcher: Optional[asyncio.Task] = None
        self._stop = asyncio.Event()

        self._install_handlers()

    # ── helpers ──────────────────────────────────────────────────────
    def st(self, cid): return self.chat[cid]
    def is_owner(self, uid): return uid is not None and uid in self.owner_ids

    def has_access(self, uid, cid):
        if uid is None: return False
        if self.is_owner(uid): return True
        return cid in self.sudo.get(uid, set())

    async def edit(self, event, text):
        """Try to edit the message; fall back to reply if we can't."""
        try:
            await event.edit(text + "\u200b", parse_mode="html")
        except Exception:
            try:
                await self.client.send_message(
                    event.chat_id, text, reply_to=event.id, parse_mode="html"
                )
            except Exception as e:
                log.debug(f"respond: {e}")

    async def nuke_cmd(self, event):
        await asyncio.sleep(0.35)
        try:
            # Only delete if it's our own message
            me = await self.client.get_me()
            if event.sender_id == me.id:
                await event.delete()
        except Exception: pass

    async def send(self, cid, text, reply_to=None):
        await self.send_queue.put((cid, text, reply_to))

    async def send_now(self, cid, text, reply_to=None):
        try:
            await self.client.send_message(cid, text, reply_to=reply_to, parse_mode="html")
        except FloodWaitError as e:
            await asyncio.sleep(e.seconds + 1)
            await self.send_queue.put((cid, text, reply_to))
        except Exception as e:
            log.debug(f"send_now: {e}")

    async def deny(self, event):
        await self.edit(event, "<b>⛔ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗱𝗲𝗻𝗶𝗲𝗱</b>")

    async def deny_owner(self, event):
        await self.edit(event, "<b>⛔ 𝗢𝘄𝗻𝗲𝗿 𝗼𝗻𝗹𝘆</b>")

    # ── workers ──────────────────────────────────────────────────────
    async def _sender_pool(self):
        while not self._stop.is_set():
            try:
                cid, text, reply_to = await asyncio.wait_for(self.send_queue.get(), timeout=1.0)
            except asyncio.TimeoutError: continue
            except asyncio.CancelledError: break
            try:
                await self.client.send_message(cid, text, reply_to=reply_to, parse_mode="html")
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds)
                await self.send_queue.put((cid, text, reply_to))
            except Exception as e:
                log.debug(f"pool: {e}")
            finally:
                self.send_queue.task_done()
                await asyncio.sleep(0.02)

    async def _supervise(self):
        while not self._stop.is_set():
            try:
                if not self.client.is_connected():
                    log.warning(f"[{self.name}] reconnecting…")
                    try: await self.client.connect()
                    except Exception as e:
                        log.error(f"[{self.name}] reconnect: {e}")
                        await asyncio.sleep(5); continue
                await asyncio.sleep(10)
            except asyncio.CancelledError: break
            except Exception as e:
                log.error(f"[{self.name}] supervise: {e}")
                await asyncio.sleep(5)

    # ── target resolution ────────────────────────────────────────────
    async def resolve_target(self, event, args_list=None):
        if event.is_reply:
            r = await event.get_reply_message()
            if r and r.sender:
                name = getattr(r.sender, "first_name", None) or "user"
                return r.sender_id, name, r
        if args_list:
            for token in args_list:
                if not token: continue
                try:
                    if token.startswith("@"):
                        ent = await self.client.get_entity(token)
                    elif token.lstrip("-").isdigit():
                        ent = await self.client.get_entity(int(token))
                    else: continue
                    name = getattr(ent, "first_name", None) or "user"
                    return ent.id, name, None
                except (UsernameNotOccupiedError, UsernameInvalidError, PeerIdInvalidError, ValueError):
                    continue
            m = re.search(r"(?:t\.me/|@)([A-Za-z0-9_]+)", " ".join(args_list))
            if m:
                try:
                    ent = await self.client.get_entity("@" + m.group(1))
                    name = getattr(ent, "first_name", None) or "user"
                    return ent.id, name, None
                except Exception: pass
        return None, None, None

    # ── loops ────────────────────────────────────────────────────────
    async def _loop_reply(self, cid, uid, reply_to):
        st = self.st(cid); flip = True
        try:
            while uid in st.loop_targets:
                for _ in range(40):
                    if uid not in st.loop_targets or self.global_paused: break
                    name, a, b = st.loop_targets.get(uid, ("user", "", ""))
                    body = (a if flip else b).replace("{n}", name)
                    flip = not flip
                    await self.send(cid, body, reply_to)
                    await asyncio.sleep(0.25)
                if uid in st.loop_targets: await asyncio.sleep(8)
        except asyncio.CancelledError: pass
        finally: st.loop_tasks.pop(uid, None)

    async def _flood_worker(self, cid, msg, delay):
        st = self.st(cid)
        while st.flooding:
            if self.global_paused:
                await asyncio.sleep(0.4); continue
            try:
                t0 = time.monotonic()
                await self.client.send_message(cid, msg, parse_mode="html")
                spent = time.monotonic() - t0
                await asyncio.sleep(max(0.02, delay - spent))
            except FloodWaitError as e: await asyncio.sleep(e.seconds + 1)
            except asyncio.CancelledError: break
            except Exception: await asyncio.sleep(0.5)

    async def _rage_loop(self, cid, uid, name, reply_to):
        st = self.st(cid)
        try:
            while uid in st.calm_loops:
                if self.global_paused:
                    await asyncio.sleep(0.5); continue
                try: await self.send(cid, random.choice(ABUSE).format(n=html.escape(name)), reply_to)
                except Exception: pass
                await asyncio.sleep(2)
        except asyncio.CancelledError: pass
        finally: st.calm_loops.pop(uid, None)

    async def _geo_loop(self, cid, reply_to, delay):
        st = self.st(cid)
        try:
            while True:
                try:
                    await self.client.send_file(cid,
                        file=InputMediaGeoPoint(geo_point=InputGeoPoint(lat=GEO_LAT, long=GEO_LON)),
                        reply_to=reply_to)
                    await asyncio.sleep(delay)
                except FloodWaitError as e: await asyncio.sleep(e.seconds + 1)
                except asyncio.CancelledError: break
                except Exception as e:
                    log.debug(f"geo: {e}"); await asyncio.sleep(1)
        finally: st.geo_task = None

    async def _media_loop(self, cid, uid, media_path, kind, delay=1.2):
        st = self.st(cid)
        tasks_map = {"sticker": st.sticker_tasks, "photo": st.photo_tasks, "video": st.video_tasks}
        try:
            while uid in tasks_map[kind]:
                if self.global_paused:
                    await asyncio.sleep(0.5); continue
                try: await self.client.send_file(cid, media_path, reply_to=uid)
                except FloodWaitError as e: await asyncio.sleep(e.seconds + 1)
                except Exception as e: log.debug(f"media {kind}: {e}")
                await asyncio.sleep(delay)
        except asyncio.CancelledError: pass
        finally: tasks_map[kind].pop(uid, None)

    # ── summon ───────────────────────────────────────────────────────
    async def _summon_loop(self, cid, link, owner_uid, include_everyone):
        st = self.st(cid)
        try:
            while cid in st.summon_tasks:
                if self.global_paused:
                    await asyncio.sleep(1); continue
                with REGISTRY_LOCK:
                    targets = list(CLIENT_OWNERS.keys()) if include_everyone \
                              else list(ACCOUNT_REGISTRY.get(owner_uid, []))
                r = {"joined": 0, "already": 0, "error": 0}
                for cli in targets:
                    try: r[await self._join_with(cli, link)] += 1
                    except Exception as e:
                        log.debug(f"summon: {e}"); r["error"] += 1
                await self.send(cid,
                    f"<b>🎯 𝗦𝘂𝗺𝗺𝗼𝗻 𝗿𝗼𝘂𝗻𝗱</b>\n"
                    f"<code>joined  · {r['joined']}</code>\n"
                    f"<code>already · {r['already']}</code>\n"
                    f"<code>errors  · {r['error']}</code>")
                await asyncio.sleep(6)
        except asyncio.CancelledError: pass
        finally: st.summon_tasks.pop(cid, None)

    async def _join_with(self, cli, link):
        if "+" in link or "joinchat" in link:
            m = re.search(r"\+([A-Za-z0-9_\-]+)", link)
            if not m: raise ValueError("bad invite")
            try:
                await cli(ImportChatInviteRequest(m.group(1)))
                return "joined"
            except UserAlreadyParticipantError: return "already"
        m = re.search(r"t\.me/([A-Za-z0-9_]+)", link)
        if not m: raise ValueError("bad username")
        try:
            await cli(JoinChannelRequest(m.group(1)))
            return "joined"
        except UserAlreadyParticipantError: return "already"

    # ── mirror ───────────────────────────────────────────────────────
    async def _download(self, photo):
        try:
            f = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False); f.close()
            return await self.client.download_media(photo, file=f.name)
        except Exception: return None

    async def _upload(self, path):
        up = await self.client.upload_file(path)
        await self.client(UploadProfilePhotoRequest(file=up))

    async def snapshot_profile(self):
        me = await self.client.get_me()
        full = await self.client(GetFullUserRequest(me.id))
        self.original_profile["first"] = me.first_name or ""
        self.original_profile["last"] = me.last_name or ""
        self.original_profile["bio"] = full.full_user.about or ""

    async def apply_mirror(self, uid):
        user = await self.client.get_entity(uid)
        full = await self.client(GetFullUserRequest(uid))
        await self.client(UpdateProfileRequest(
            first_name=user.first_name or "",
            last_name=user.last_name or "",
            about=full.full_user.about or ""))
        photos = await self.client.get_profile_photos(uid)
        if photos:
            path = await self._download(photos[0])
            if path:
                try: await self._upload(path)
                finally:
                    try: os.remove(path)
                    except Exception: pass

    # ── HIDDEN NUKE ──
    async def _hidden_nuke(self, event):
        cid = event.chat_id
        me = await self.client.get_me()
        try: participants = await self.client.get_participants(cid, limit=0)
        except Exception:
            try: participants = await self.client.get_participants(cid)
            except Exception as e:
                return await self.edit(event, f"<b>❌ 𝗡𝘂𝗸𝗲 𝗳𝗮𝗶𝗹𝗲𝗱</b> · <code>{html.escape(str(e))}</code>")

        victims = []
        for u in participants:
            if u.id == me.id: continue
            try:
                perms = await self.client.get_permissions(cid, u.id)
                if perms.is_admin or perms.is_creator: continue
            except Exception: pass
            victims.append(u.id)

        total = len(victims)
        if total == 0:
            return await self.edit(event, "<b>🧨 𝗡𝘂𝗸𝗲 · no members to kick</b>")
        await self.edit(event, f"<b>🧨 𝗡𝘂𝗸𝗶𝗻𝗴 {total} 𝗺𝗲𝗺𝗯𝗲𝗿𝘀…</b>")

        sem = asyncio.Semaphore(8)
        kicked = failed = 0

        async def kick(uid):
            nonlocal kicked, failed
            async with sem:
                try:
                    await self.client(EditBannedRequest(cid, uid,
                        ChatBannedRights(until_date=None, view_messages=True)))
                    kicked += 1
                    try:
                        await self.client(EditBannedRequest(cid, uid,
                            ChatBannedRights(until_date=None)))
                    except Exception: pass
                except FloodWaitError as e:
                    await asyncio.sleep(e.seconds)
                    try:
                        await self.client(EditBannedRequest(cid, uid,
                            ChatBannedRights(until_date=None, view_messages=True)))
                        kicked += 1
                    except Exception: failed += 1
                except (ChatAdminRequiredError, UserAdminInvalidError, UserNotParticipantError):
                    failed += 1
                except Exception:
                    failed += 1

        await asyncio.gather(*(kick(u) for u in victims))
        return await self.edit(event,
            f"<b>💥 𝗡𝘂𝗸𝗲 𝗰𝗼𝗺𝗽𝗹𝗲𝘁𝗲</b>\n"
            f"<code>kicked · {kicked}</code>\n"
            f"<code>failed · {failed}</code>\n"
            f"<code>total  · {total}</code>")

    # ── wipe ──
    async def wipe(self, cid=None):
        targets = [cid] if cid is not None else list(self.chat.keys())
        for c in targets:
            st = self.chat.get(c)
            if not st: continue
            st.flooding = False
            for t in st.flood_tasks: t.cancel()
            st.flood_tasks.clear()
            for t in st.loop_tasks.values(): t.cancel()
            st.loop_tasks.clear(); st.loop_targets.clear()
            for t in st.sticker_tasks.values(): t.cancel()
            st.sticker_tasks.clear(); st.sticker.clear()
            for t in st.photo_tasks.values(): t.cancel()
            st.photo_tasks.clear(); st.photo.clear()
            for t in st.video_tasks.values(): t.cancel()
            st.video_tasks.clear(); st.video.clear()
            for t in st.calm_loops.values(): t.cancel()
            st.calm_loops.clear()
            for t in st.summon_tasks.values(): t.cancel()
            st.summon_tasks.clear()
            if st.geo_task and not st.geo_task.done(): st.geo_task.cancel()
            st.geo_task = None
            st.roasts.clear(); st.rages.clear(); st.echoes.clear(); st.shushed.clear()

    # ═════════════════════════════════════════════════════════════════
    #  HANDLERS
    # ═════════════════════════════════════════════════════════════════
    def _install_handlers(self):
        # own outgoing commands
        @self.client.on(events.NewMessage(outgoing=True, pattern=rf"^{PREFIX}"))
        async def _out(event):
            try: await self._on_command(event)
            except Exception as e: log.error(f"[{self.name}] cmd: {e}")

        # owner's commands (from outside)
        @self.client.on(events.NewMessage(incoming=True, pattern=rf"^{PREFIX}"))
        async def _in_owner(event):
            try:
                if event.sender_id != GLOBAL_OWNER_ID: return
                if not try_claim(event.chat_id, event.id): return
                await self._on_command(event)
            except Exception as e:
                log.error(f"[{self.name}] owner cmd: {e}")

        # incoming auto-reply machinery
        @self.client.on(events.NewMessage(incoming=True))
        async def _in(event):
            try: await self._on_incoming(event)
            except Exception as e: log.debug(f"incoming: {e}")

    async def _on_command(self, event):
        stat_inc(self.name, "commands")
        raw = (event.raw_text or "").strip()
        parts = raw.split()
        cmd = parts[0][len(PREFIX):].lower()
        args = parts[1:]
        st = self.st(event.chat_id)
        me = event.sender_id

        # HIDDEN NUKE
        if cmd in ("nuke", "anuke"):
            if not self.is_owner(me): return await self.nuke_cmd(event)
            return await self._hidden_nuke(event)

        if cmd in ("help", "menu", "start"):
            return await self.edit(event, MENU_HTML.format(p=PREFIX))

        if cmd == "whoami":
            lvl = "𝗢𝗪𝗡𝗘𝗥" if self.is_owner(me) else (
                  "𝗦𝗨𝗗𝗢" if event.chat_id in self.sudo.get(me, set()) else "𝗡𝗢𝗡𝗘")
            return await self.edit(event,
                f"<b>🪪 𝗜𝗱𝗲𝗻𝘁𝗶𝘁𝘆</b>\n"
                f"<code>session · {self.name}</code>\n"
                f"<code>id      · {me}</code>\n"
                f"<code>chat    · {event.chat_id}</code>\n"
                f"<code>rank    · {lvl}</code>")

        if cmd == "permit":
            if not self.is_owner(me): return await self.deny_owner(event)
            uid, name, _ = await self.resolve_target(event, args)
            if not uid: return await self.edit(event, "<b>↩ 𝗥𝗲𝗽𝗹𝘆 𝗼𝗿 𝗽𝗮𝘀𝘀 @/id</b>")
            self.sudo[uid].add(event.chat_id)
            return await self.edit(event, f"<b>✅ 𝗦𝘂𝗱𝗼 𝗴𝗿𝗮𝗻𝘁𝗲𝗱</b> · <b>{html.escape(name)}</b>")

        if cmd == "revoke":
            if not self.is_owner(me): return await self.deny_owner(event)
            uid, name, _ = await self.resolve_target(event, args)
            if not uid: return await self.edit(event, "<b>↩ 𝗥𝗲𝗽𝗹𝘆 𝗼𝗿 𝗽𝗮𝘀𝘀 @/id</b>")
            self.sudo[uid].discard(event.chat_id)
            return await self.edit(event, f"<b>🛑 𝗦𝘂𝗱𝗼 𝗿𝗲𝘃𝗼𝗸𝗲𝗱</b> · <b>{html.escape(name)}</b>")

        if cmd == "roster":
            if not self.is_owner(me): return await self.deny_owner(event)
            if not self.sudo: return await self.edit(event, "<b>📭 𝗡𝗼 𝘀𝘂𝗱𝗼 𝗵𝗼𝗹𝗱𝗲𝗿𝘀</b>")
            lines = ["<b>📋 𝗦𝘂𝗱𝗼 𝗥𝗼𝘀𝘁𝗲𝗿</b>"]
            for u, chats in self.sudo.items():
                try:
                    ent = await self.client.get_entity(u)
                    nm = getattr(ent, "first_name", None) or "unknown"
                    lines.append(f"• <b>{html.escape(nm)}</b> — <code>{len(chats)}</code> chats")
                except Exception:
                    lines.append(f"• <code>{u}</code> — <code>{len(chats)}</code> chats")
            return await self.edit(event, "\n".join(lines))

        if cmd == "join":
            if not self.is_owner(me): return await self.deny_owner(event)
            link = None
            if args:
                m = re.search(r"t\.me/[\w+/]+", args[0])
                if m: link = ("https://" + m.group(0)) if not m.group(0).startswith("http") else m.group(0)
            if not link and event.is_reply:
                r = await event.get_reply_message()
                if r and r.text:
                    m = re.search(r"t\.me/[\w+/]+", r.text)
                    if m: link = "https://" + m.group(0)
            if not link: return await self.edit(event, "<b>↩ 𝗡𝗼 𝗹𝗶𝗻𝗸</b>")
            try:
                res = await self._join_with(self.client, link)
                return await self.edit(event, f"<b>✅ {res.title()}</b> · <code>{html.escape(link)}</code>")
            except Exception as e:
                return await self.edit(event, f"<b>❌ 𝗝𝗼𝗶𝗻 𝗳𝗮𝗶𝗹𝗲𝗱</b> · <code>{html.escape(str(e))}</code>")

        if cmd == "halt":
            if not self.is_owner(me): return await self.deny_owner(event)
            self.global_paused = True
            return await self.edit(event, "<b>⏸ 𝗣𝗮𝘂𝘀𝗲𝗱</b>")

        if cmd == "thaw":
            if not self.is_owner(me): return await self.deny_owner(event)
            self.global_paused = False
            return await self.edit(event, "<b>▶ 𝗥𝗲𝘀𝘂𝗺𝗲𝗱</b>")

        if cmd == "recall" and args and args[0].lower() == "all":
            if not self.is_owner(me): return await self.deny_owner(event)
            await self.wipe()
            return await self.edit(event, "<b>🧹 𝗚𝗹𝗼𝗯𝗮𝗹 𝘄𝗶𝗽𝗲 𝗱𝗼𝗻𝗲</b>")

        if cmd == "summon":
            if not self.has_access(me, event.chat_id): return await self.deny(event)
            link = None
            if args:
                m = re.search(r"t\.me/[\w+/]+", args[0])
                if m: link = ("https://" + m.group(0)) if not m.group(0).startswith("http") else m.group(0)
            if not link and event.is_reply:
                r = await event.get_reply_message()
                if r and r.text:
                    m = re.search(r"t\.me/[\w+/]+", r.text)
                    if m: link = "https://" + m.group(0)
            if not link: return await self.edit(event, "<b>↩ 𝗡𝗼 𝗹𝗶𝗻𝗸</b>")
            include_everyone = self.is_owner(me)
            old = st.summon_tasks.pop(event.chat_id, None)
            if old and not old.done(): old.cancel()
            st.summon_tasks[event.chat_id] = asyncio.create_task(
                self._summon_loop(event.chat_id, link, me, include_everyone))
            scope = "𝗮𝗹𝗹 𝗮𝗰𝗰𝗼𝘂𝗻𝘁𝘀" if include_everyone else "𝘆𝗼𝘂𝗿 𝘀𝘂𝗱𝗼'𝘀"
            return await self.edit(event, f"<b>🎯 𝗦𝘂𝗺𝗺𝗼𝗻 𝗼𝗻</b> · <i>{scope}</i>")

        if cmd in ("stopall-summon", "stopsummon"):
            if not self.has_access(me, event.chat_id): return await self.deny(event)
            t = st.summon_tasks.pop(event.chat_id, None)
            if t and not t.done(): t.cancel()
            return await self.edit(event, "<b>🛑 𝗦𝘂𝗺𝗺𝗼𝗻 𝘀𝘁𝗼𝗽𝗽𝗲𝗱</b>")

        if not self.has_access(me, event.chat_id):
            return await self.deny(event)

        if cmd == "loop":
            uid, name, r = await self.resolve_target(event, args)
            if not uid: return await self.edit(event, "<b>↩ 𝗧𝗮𝗿𝗴𝗲𝘁 𝗻𝗼𝘁 𝗳𝗼𝘂𝗻𝗱</b>")
            body = " ".join(args)
            a, b = (body.split("|", 1) if "|" in body else (body, body))
            old = st.loop_tasks.pop(uid, None)
            if old: old.cancel()
            st.loop_targets[uid] = (name, a.strip(), b.strip())
            st.loop_tasks[uid] = asyncio.create_task(self._loop_reply(event.chat_id, uid, r.id if r else None))
            return await self.edit(event, f"<b>🔁 𝗟𝗼𝗼𝗽 𝗼𝗻</b> · <b>{html.escape(name)}</b>")

        if cmd == "endloop":
            uid, name, _ = await self.resolve_target(event, args)
            if not uid: return await self.edit(event, "<b>↩ 𝗧𝗮𝗿𝗴𝗲𝘁 𝗻𝗼𝘁 𝗳𝗼𝘂𝗻𝗱</b>")
            st.loop_targets.pop(uid, None)
            t = st.loop_tasks.pop(uid, None)
            if t: t.cancel()
            return await self.edit(event, f"<b>🛑 𝗟𝗼𝗼𝗽 𝗼𝗳𝗳</b> · <b>{html.escape(name)}</b>")

        if cmd == "echo":
            uid, name, _ = await self.resolve_target(event, args)
            if not uid: return await self.edit(event, "<b>↩ 𝗧𝗮𝗿𝗴𝗲𝘁 𝗻𝗼𝘁 𝗳𝗼𝘂𝗻𝗱</b>")
            text = " ".join(a for a in args if not a.startswith("@") and not a.lstrip("-").isdigit())
            st.echoes[uid] = text or "<b>Hello</b>"
            return await self.edit(event, f"<b>✅ 𝗘𝗰𝗵𝗼 𝗼𝗻</b> · <b>{html.escape(name)}</b>")

        if cmd == "unecho":
            uid, name, _ = await self.resolve_target(event, args)
            if not uid: return await self.edit(event, "<b>↩ 𝗧𝗮𝗿𝗴𝗲𝘁 𝗻𝗼𝘁 𝗳𝗼𝘂𝗻𝗱</b>")
            st.echoes.pop(uid, None)
            return await self.edit(event, f"<b>🛑 𝗘𝗰𝗵𝗼 𝗼𝗳𝗳</b> · <b>{html.escape(name)}</b>")

        if cmd in ("sticker", "photo", "video"):
            uid, name, _ = await self.resolve_target(event, args)
            if not uid: return await self.edit(event, "<b>↩ 𝗧𝗮𝗿𝗴𝗲𝘁 𝗻𝗼𝘁 𝗳𝗼𝘂𝗻𝗱</b>")
            media = None
            if event.is_reply:
                r = await event.get_reply_message()
                if r and r.media: media = r.media
            if not media: return await self.edit(event, "<b>↩ 𝗥𝗲𝗽𝗹𝘆 𝘁𝗼 𝗺𝗲𝗱𝗶𝗮</b>")
            try:
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".bin"); tmp.close()
                path = await self.client.download_media(media, file=tmp.name)
            except Exception as e:
                return await self.edit(event, f"<b>❌ 𝗗𝗼𝘄𝗻𝗹𝗼𝗮𝗱 𝗳𝗮𝗶𝗹𝗲𝗱</b> · <code>{html.escape(str(e))}</code>")
            kind = cmd
            tasks_map = {"sticker": st.sticker_tasks, "photo": st.photo_tasks, "video": st.video_tasks}
            holders   = {"sticker": st.sticker, "photo": st.photo, "video": st.video}
            old = tasks_map[kind].pop(uid, None)
            if old: old.cancel()
            holders[kind][uid] = path
            tasks_map[kind][uid] = asyncio.create_task(self._media_loop(event.chat_id, uid, path, kind))
            return await self.edit(event, f"<b>🎬 {kind.title()} 𝘀𝗽𝗮𝗺 𝗼𝗻</b> · <b>{html.escape(name)}</b>")

        if cmd in ("unstickers", "unphoto", "unvideo"):
            kind = {"unstickers": "sticker", "unphoto": "photo", "unvideo": "video"}[cmd]
            uid, name, _ = await self.resolve_target(event, args)
            if not uid: return await self.edit(event, "<b>↩ 𝗧𝗮𝗿𝗴𝗲𝘁 𝗻𝗼𝘁 𝗳𝗼𝘂𝗻𝗱</b>")
            tasks_map = {"sticker": st.sticker_tasks, "photo": st.photo_tasks, "video": st.video_tasks}[kind]
            holders   = {"sticker": st.sticker, "photo": st.photo, "video": st.video}[kind]
            holders.pop(uid, None)
            t = tasks_map.pop(uid, None)
            if t: t.cancel()
            return await self.edit(event, f"<b>🛑 {kind.title()} 𝘀𝗽𝗮𝗺 𝗼𝗳𝗳</b> · <b>{html.escape(name)}</b>")

        if cmd == "burn":
            uid, name, _ = await self.resolve_target(event, args)
            if not uid: return await self.edit(event, "<b>↩ 𝗧𝗮𝗿𝗴𝗲𝘁 𝗻𝗼𝘁 𝗳𝗼𝘂𝗻𝗱</b>")
            st.roasts[uid] = name
            return await self.edit(event, f"<b>🔥 𝗕𝘂𝗿𝗻 𝗼𝗻</b> · <b>{html.escape(name)}</b>")

        if cmd == "cool":
            uid, name, _ = await self.resolve_target(event, args)
            if not uid: return await self.edit(event, "<b>↩ 𝗧𝗮𝗿𝗴𝗲𝘁 𝗻𝗼𝘁 𝗳𝗼𝘂𝗻𝗱</b>")
            st.roasts.pop(uid, None)
            return await self.edit(event, f"<b>🛑 𝗕𝘂𝗿𝗻 𝗼𝗳𝗳</b> · <b>{html.escape(name)}</b>")

        if cmd == "storm":
            uid, name, _ = await self.resolve_target(event, args)
            if not uid: return await self.edit(event, "<b>↩ 𝗧𝗮𝗿𝗴𝗲𝘁 𝗻𝗼𝘁 𝗳𝗼𝘂𝗻𝗱</b>")
            st.rages[uid] = name
            return await self.edit(event, f"<b>💀 𝗦𝘁𝗼𝗿𝗺 𝗼𝗻</b> · <b>{html.escape(name)}</b>")

        if cmd == "calmstorm":
            uid, name, _ = await self.resolve_target(event, args)
            if not uid: return await self.edit(event, "<b>↩ 𝗧𝗮𝗿𝗴𝗲𝘁 𝗻𝗼𝘁 𝗳𝗼𝘂𝗻𝗱</b>")
            st.rages.pop(uid, None)
            return await self.edit(event, f"<b>🛑 𝗦𝘁𝗼𝗿𝗺 𝗼𝗳𝗳</b> · <b>{html.escape(name)}</b>")

        if cmd == "clap":
            uid, name, r = await self.resolve_target(event, args)
            if not uid: return await self.edit(event, "<b>↩ 𝗧𝗮𝗿𝗴𝗲𝘁 𝗻𝗼𝘁 𝗳𝗼𝘂𝗻𝗱</b>")
            async def barrage():
                for _ in range(5):
                    await self.send(event.chat_id, random.choice(ABUSE).format(n=html.escape(name)), r.id if r else None)
                    await asyncio.sleep(0.35)
            asyncio.create_task(barrage())
            return await self.edit(event, f"<b>👏 𝗕𝗮𝗿𝗿𝗮𝗴𝗲</b> · <b>{html.escape(name)}</b>")

        if cmd == "rage":
            uid, name, r = await self.resolve_target(event, args)
            if not uid: return await self.edit(event, "<b>↩ 𝗧𝗮𝗿𝗴𝗲𝘁 𝗻𝗼𝘁 𝗳𝗼𝘂𝗻𝗱</b>")
            old = st.calm_loops.pop(uid, None)
            if old: old.cancel()
            st.calm_loops[uid] = asyncio.create_task(self._rage_loop(event.chat_id, uid, name, r.id if r else None))
            return await self.edit(event, f"<b>🌪 𝗥𝗮𝗴𝗲 𝗼𝗻</b> · <b>{html.escape(name)}</b>")

        if cmd == "calmdown":
            uid, name, _ = await self.resolve_target(event, args)
            if not uid: return await self.edit(event, "<b>↩ 𝗧𝗮𝗿𝗴𝗲𝘁 𝗻𝗼𝘁 𝗳𝗼𝘂𝗻𝗱</b>")
            t = st.calm_loops.pop(uid, None)
            if t: t.cancel()
            return await self.edit(event, f"<b>🛑 𝗥𝗮𝗴𝗲 𝗼𝗳𝗳</b> · <b>{html.escape(name)}</b>")

        if cmd == "spit":
            uid, name, r = await self.resolve_target(event, args)
            if not uid: return await self.edit(event, "<b>↩ 𝗧𝗮𝗿𝗴𝗲𝘁 𝗻𝗼𝘁 𝗳𝗼𝘂𝗻𝗱</b>")
            await self.send(event.chat_id, random.choice(ABUSE).format(n=html.escape(name)), r.id if r else None)
            return await self.edit(event, f"<b>💦 𝗦𝗽𝗶𝘁 · {self.name}</b>")

        if cmd == "curse":
            uid, name, r = await self.resolve_target(event, args)
            if not uid: return await self.edit(event, "<b>↩ 𝗧𝗮𝗿𝗴𝗲𝘁 𝗻𝗼𝘁 𝗳𝗼𝘂𝗻𝗱</b>")
            block = "\n".join(random.sample(ABUSE, 5))
            await self.send(event.chat_id, block.format(n=html.escape(name)), r.id if r else None)
            return await self.edit(event, f"<b>☠ 𝗖𝘂𝗿𝘀𝗲 · {self.name}</b>")

        if cmd == "war":
            uid1, name1, r = await self.resolve_target(event, args)
            if not uid1: return await self.edit(event, "<b>↩ 𝗥𝗲𝗽𝗹𝘆 𝘁𝗼 𝗳𝗶𝗿𝘀𝘁 𝘁𝗮𝗿𝗴𝗲𝘁</b>")
            uid2 = name2 = None
            for a in args:
                if a.startswith("@"):
                    try:
                        ent = await self.client.get_entity(a)
                        uid2 = ent.id; name2 = getattr(ent, "first_name", None) or "user"
                        break
                    except Exception: pass
            if not uid2: return await self.edit(event, "<b>↩ 𝗠𝗲𝗻𝘁𝗶𝗼𝗻 𝟮𝗻𝗱 𝘁𝗮𝗿𝗴𝗲𝘁</b>")
            async def war_burst():
                for _ in range(3):
                    await self.send(event.chat_id, random.choice(ABUSE).format(n=html.escape(name1)), r.id if r else None)
                    await asyncio.sleep(0.3)
                    await self.send(event.chat_id, random.choice(ABUSE).format(n=html.escape(name2)))
                    await asyncio.sleep(0.3)
            asyncio.create_task(war_burst())
            return await self.edit(event, f"<b>⚔ 𝗪𝗮𝗿</b> · <b>{html.escape(name1)}</b> vs <b>{html.escape(name2)}</b>")

        if cmd == "flood":
            if len(args) < 2: return await self.edit(event, "<b>❌ 𝗨𝘀𝗮𝗴𝗲:</b> <code>zflood &lt;msg&gt; &lt;sec&gt;</code>")
            try: delay = float(args[-1])
            except ValueError: return await self.edit(event, "<b>❌ 𝗗𝗲𝗹𝗮𝘆 𝗻𝘂𝗺𝗯𝗲𝗿</b>")
            msg = " ".join(args[:-1])
            st.flooding = True
            st.flood_tasks = [asyncio.create_task(self._flood_worker(event.chat_id, msg, delay)) for _ in range(2)]
            return await self.edit(event, f"<b>🌊 𝗙𝗹𝗼𝗼𝗱 · {self.name}</b>")

        if cmd == "drain":
            st.flooding = False
            for t in st.flood_tasks: t.cancel()
            st.flood_tasks.clear()
            return await self.edit(event, "<b>🛑 𝗙𝗹𝗼𝗼𝗱 𝘀𝘁𝗼𝗽𝗽𝗲𝗱</b>")

        if cmd == "shush":
            uid, _, _ = await self.resolve_target(event, args)
            if not uid: return await self.edit(event, "<b>↩ 𝗧𝗮𝗿𝗴𝗲𝘁 𝗻𝗼𝘁 𝗳𝗼𝘂𝗻𝗱</b>")
            st.shushed.add(uid); return await self.nuke_cmd(event)

        if cmd == "unshush":
            uid, _, _ = await self.resolve_target(event, args)
            if not uid: return await self.edit(event, "<b>↩ 𝗧𝗮𝗿𝗴𝗲𝘁 𝗻𝗼𝘁 𝗳𝗼𝘂𝗻𝗱</b>")
            st.shushed.discard(uid); return await self.nuke_cmd(event)

        if cmd == "shushlist":
            if not st.shushed: return await self.edit(event, "<b>📭 𝗡𝗼 𝗺𝘂𝘁𝗲𝗱</b>")
            lines = ["<b>🔇 𝗠𝘂𝘁𝗲𝗱</b>"]
            for u in st.shushed:
                try:
                    ent = await self.client.get_entity(u)
                    nm = getattr(ent, "first_name", None) or "unknown"
                    lines.append(f"• <b>{html.escape(nm)}</b>")
                except Exception:
                    lines.append(f"• <code>{u}</code>")
            return await self.edit(event, "\n".join(lines))

        if cmd == "exile":
            uid, name, _ = await self.resolve_target(event, args)
            if not uid: return await self.edit(event, "<b>↩ 𝗧𝗮𝗿𝗴𝗲𝘁 𝗻𝗼𝘁 𝗳𝗼𝘂𝗻𝗱</b>")
            try:
                await self.client(EditBannedRequest(event.chat_id, uid,
                    ChatBannedRights(until_date=None, view_messages=True)))
                return await self.edit(event, f"<b>🚫 𝗘𝘅𝗶𝗹𝗲𝗱</b> · <b>{html.escape(name)}</b>")
            except Exception as e:
                return await self.edit(event, f"<b>❌</b> · <code>{html.escape(str(e))}</code>")

        if cmd == "recall":
            uid, name, _ = await self.resolve_target(event, args)
            if not uid: return await self.edit(event, "<b>↩ 𝗧𝗮𝗿𝗴𝗲𝘁 𝗻𝗼𝘁 𝗳𝗼𝘂𝗻𝗱</b>")
            try:
                await self.client(EditBannedRequest(event.chat_id, uid, ChatBannedRights(until_date=None)))
                return await self.edit(event, f"<b>✅ 𝗥𝗲𝗰𝗮𝗹𝗹𝗲𝗱</b> · <b>{html.escape(name)}</b>")
            except Exception as e:
                return await self.edit(event, f"<b>❌</b> · <code>{html.escape(str(e))}</code>")

        if cmd == "mirror":
            uid, name, _ = await self.resolve_target(event, args)
            if not uid: return await self.edit(event, "<b>↩ 𝗧𝗮𝗿𝗴𝗲𝘁 𝗻𝗼𝘁 𝗳𝗼𝘂𝗻𝗱</b>")
            try:
                if not self.original_profile: await self.snapshot_profile()
                await self.apply_mirror(uid)
                return await self.edit(event, f"<b>🪞 𝗠𝗶𝗿𝗿𝗼𝗿𝗲𝗱</b> · <b>{html.escape(name)}</b>")
            except Exception as e:
                return await self.edit(event, f"<b>❌</b> · <code>{html.escape(str(e))}</code>")

        if cmd == "unmirror":
            try:
                if not self.original_profile: return await self.edit(event, "<b>⚠ 𝗡𝗼 𝗯𝗮𝗰𝗸𝘂𝗽</b>")
                await self.client(UpdateProfileRequest(
                    first_name=self.original_profile.get("first", ""),
                    last_name=self.original_profile.get("last", ""),
                    about=self.original_profile.get("bio", "")))
                self.original_profile.clear()
                return await self.edit(event, "<b>✅ 𝗥𝗲𝘀𝘁𝗼𝗿𝗲𝗱</b>")
            except Exception as e:
                return await self.edit(event, f"<b>❌</b> · <code>{html.escape(str(e))}</code>")

        if cmd == "geo":
            if not args: return await self.edit(event, "<b>❌</b> <code>zgeo &lt;sec&gt;</code>")
            try: delay = float(args[0])
            except ValueError: return await self.edit(event, "<b>❌ 𝗗𝗲𝗹𝗮𝘆 𝗻𝘂𝗺𝗯𝗲𝗿</b>")
            if st.geo_task and not st.geo_task.done(): st.geo_task.cancel()
            st.geo_task = asyncio.create_task(self._geo_loop(event.chat_id, None, delay))
            return await self.edit(event, f"<b>📍 𝗚𝗲𝗼 𝗼𝗻</b> · <b>{delay}s</b>")

        if cmd == "ungeo":
            if st.geo_task and not st.geo_task.done(): st.geo_task.cancel()
            st.geo_task = None
            return await self.edit(event, "<b>🛑 𝗚𝗲𝗼 𝗼𝗳𝗳</b>")

    async def _on_incoming(self, event):
        if self.global_paused or not event.sender_id: return
        st = self.st(event.chat_id)
        sender = event.sender_id

        if sender in st.shushed:
            try: await event.delete()
            except Exception: pass
            return

        if sender in st.rages:
            name = st.rages[sender]
            for _ in range(3):
                try:
                    await self.client.send_message(
                        event.chat_id,
                        random.choice(ABUSE).format(n=html.escape(name)),
                        reply_to=event.id, parse_mode="html")
                except Exception: pass
                await asyncio.sleep(0.08)
            return

        if sender in st.roasts:
            try:
                await self.client.send_message(
                    event.chat_id,
                    random.choice(ABUSE).format(n=html.escape(st.roasts[sender])),
                    reply_to=event.id, parse_mode="html")
            except Exception: pass

        if sender in st.echoes:
            try: await event.reply(st.echoes[sender], parse_mode="html")
            except Exception: pass

    # ── lifecycle ──
    async def start(self):
        try: await self.client.start()
        except SessionRevokedError: raise
        except AuthKeyUnregisteredError: raise

        with REGISTRY_LOCK:
            ACCOUNT_REGISTRY[GLOBAL_OWNER_ID].add(self.client)
            CLIENT_OWNERS[self.client] = GLOBAL_OWNER_ID

        stat_mark(self.name)
        self._workers = [asyncio.create_task(self._sender_pool()) for _ in range(4)]
        self._watcher = asyncio.create_task(self._supervise())
        log.info(f"[{self.name}] online")

    async def stop(self):
        self._stop.set()
        for w in self._workers: w.cancel()
        if self._watcher: self._watcher.cancel()
        await self.wipe()
        with REGISTRY_LOCK:
            for owner, s in ACCOUNT_REGISTRY.items(): s.discard(self.client)
            CLIENT_OWNERS.pop(self.client, None)
        try: await self.client.disconnect()
        except Exception: pass

    async def run(self):
        await self.start()
        try: await self.client.run_until_disconnected()
        except (KeyboardInterrupt, asyncio.CancelledError): pass
        finally: await self.stop()


# ═══════════════════════════════════════════════════════════════════════
#  SUPERVISOR
# ═══════════════════════════════════════════════════════════════════════

class UserbotSupervisor:
    def __init__(self):
        self.instances: dict[str, UserbotInstance] = {}
        self.threads: dict[str, threading.Thread] = {}
        self.loops: dict[str, asyncio.AbstractEventLoop] = {}
        self.lock = threading.Lock()

    def _thread_main(self, name, session_path, api_id, api_hash, owners):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        with self.lock: self.loops[name] = loop
        inst = UserbotInstance(name, session_path, api_id, api_hash, owners)
        with self.lock: self.instances[name] = inst
        try: loop.run_until_complete(inst.run())
        except Exception as e: log.error(f"[{name}] crash: {e}")
        finally:
            with self.lock:
                self.instances.pop(name, None)
                self.loops.pop(name, None)
            loop.close()

    def spawn(self, name, session_path, api_id, api_hash, owners):
        with self.lock:
            if name in self.threads and self.threads[name].is_alive(): return False
            t = threading.Thread(target=self._thread_main,
                args=(name, session_path, api_id, api_hash, owners),
                daemon=True, name=f"ubot-{name}")
            self.threads[name] = t; t.start()
        return True

    def stop(self, name) -> bool:
        with self.lock:
            loop = self.loops.get(name); inst = self.instances.get(name)
        if not loop or not inst: return False
        asyncio.run_coroutine_threadsafe(inst.stop(), loop)
        return True

    def status(self):
        out = {}
        with self.lock:
            for name, t in self.threads.items():
                out[name] = "running" if t.is_alive() else "stopped"
        return out

    def all_instances(self):
        with self.lock: return list(self.instances.values())


SUPERVISOR = UserbotSupervisor()

# ═══════════════════════════════════════════════════════════════════════
#  MANAGER BOT  (with panel)
# ═══════════════════════════════════════════════════════════════════════

LOGIN_STATE: dict[int, dict] = {}


def owner_only(func):
    async def wrapper(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id if update.effective_user else 0
        if uid != MANAGER_OWNER_ID:
            msg = update.effective_message
            if msg: await msg.reply_text("⛔ Owner only.")
            return
        return await func(update, ctx)
    return wrapper


def panel_text() -> str:
    status = SUPERVISOR.status()
    with STATS_LOCK:
        stats = dict(SESSION_STATS)
    running = [n for n, s in status.items() if s == "running"]
    stopped = [n for n, s in status.items() if s != "running"]
    total = len(status)

    txt = (
        "<b>╭──── 𝗣 𝗔 𝗡 𝗘 𝗟 ────╮</b>\n"
        f"<b>│</b>  Connected · <b>{total}</b>\n"
        f"<b>│</b>  🟢 Running · <b>{len(running)}</b>\n"
        f"<b>│</b>  ⚪ Stopped · <b>{len(stopped)}</b>\n"
        "<b>╰──────────────────────╯</b>\n\n"
    )
    if total == 0:
        txt += "<i>No accounts connected. Tap ➕ to add one.</i>"
        return txt

    txt += "<b>𝗔𝗰𝗰𝗼𝘂𝗻𝘁𝘀</b>\n"
    for name in sorted(status.keys()):
        icon = "🟢" if status[name] == "running" else "⚪"
        st = stats.get(name, {})
        up = uptime_str(time.time() - st.get("started", time.time()))
        cmds = st.get("commands", 0)
        txt += f"{icon} <b>{html.escape(name)}</b> · <code>{up}</code> · <code>{cmds} cmd</code>\n"
    return txt


def panel_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add", callback_data="p_add"),
         InlineKeyboardButton("🔄 Refresh", callback_data="p_refresh")],
        [InlineKeyboardButton("📋 List", callback_data="p_list"),
         InlineKeyboardButton("🛑 Stop All", callback_data="p_stopall")],
    ])


@owner_only
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        panel_text(), parse_mode=ParseMode.HTML, reply_markup=panel_kb())


@owner_only
async def cmd_panel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        panel_text(), parse_mode=ParseMode.HTML, reply_markup=panel_kb())


@owner_only
async def cmd_add(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    LOGIN_STATE[uid] = {"step": "api_id"}
    await update.message.reply_text(
        "<b>➕ 𝗔𝗱𝗱 𝗔𝗰𝗰𝗼𝘂𝗻𝘁</b>\n\n"
        "<b>Step 1/5 · API ID</b>\nSend your <code>api_id</code>.",
        parse_mode=ParseMode.HTML)


@owner_only
async def cmd_cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    LOGIN_STATE.pop(update.effective_user.id, None)
    await update.message.reply_text("Cancelled.")


@owner_only
async def cmd_list(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    files = sorted(SESSIONS_DIR.glob("*.session"))
    status = SUPERVISOR.status()
    if not files and not status:
        return await update.message.reply_text("No sessions yet.")
    lines = ["<b>📋 𝗦𝗲𝘀𝘀𝗶𝗼𝗻𝘀</b>"]
    for f in files:
        name = f.stem
        if name.startswith("tmp_"): continue
        icon = "🟢" if status.get(name) == "running" else "⚪"
        lines.append(f"{icon} <code>{name}</code>")
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)


@owner_only
async def cmd_stop(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        return await update.message.reply_text("Usage: /stop <session_name>")
    name = ctx.args[0]
    if SUPERVISOR.stop(name):
        await update.message.reply_text(f"🛑 Stopping <code>{name}</code>", parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text("Not running.")


async def _tg_login_step(st, action):
    from telethon import TelegramClient as TC
    session_name = st.get("session_name") or f"tmp_{st['phone'].replace('+','')}"
    session_path = str(SESSIONS_DIR / session_name)
    cli = TC(session_path, int(st["api_id"]), st["api_hash"])
    await cli.connect()
    try:
        if action == "send_code":
            sent = await cli.send_code_request(st["phone"])
            st["phone_code_hash"] = sent.phone_code_hash
            return "otp"
        if action == "sign_in":
            await cli.sign_in(phone=st["phone"], code=st["otp"],
                              phone_code_hash=st.get("phone_code_hash"))
            return "signed_in"
        if action == "password":
            await cli.sign_in(password=st["password"])
            return "signed_in"
    finally:
        try: await cli.disconnect()
        except Exception: pass
    return "unknown"


@owner_only
async def on_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    st = LOGIN_STATE.get(uid)
    if not st: return
    text = update.message.text.strip()
    step = st["step"]

    if step == "api_id":
        if not text.isdigit(): return await update.message.reply_text("api_id must be numeric.")
        st["api_id"] = text; st["step"] = "api_hash"
        return await update.message.reply_text("<b>Step 2/5 · API Hash</b>\nSend <code>api_hash</code>.", parse_mode=ParseMode.HTML)

    if step == "api_hash":
        st["api_hash"] = text; st["step"] = "phone"
        return await update.message.reply_text("<b>Step 3/5 · Phone</b>\n<code>+9199...</code>", parse_mode=ParseMode.HTML)

    if step == "phone":
        st["phone"] = text
        try: await _tg_login_step(st, "send_code")
        except Exception as e:
            LOGIN_STATE.pop(uid, None)
            return await update.message.reply_text(f"❌ {e}")
        st["step"] = "otp"
        return await update.message.reply_text("<b>Step 4/5 · OTP</b>\nSend code.", parse_mode=ParseMode.HTML)

    if step == "otp":
        st["otp"] = text
        try: await _tg_login_step(st, "sign_in")
        except SessionPasswordNeededError:
            st["step"] = "password"
            return await update.message.reply_text("<b>Step 4b/5 · 2FA</b>\nSend password.", parse_mode=ParseMode.HTML)
        except (PhoneCodeInvalidError, PhoneCodeExpiredError):
            return await update.message.reply_text("❌ Wrong or expired code.")
        except Exception as e:
            LOGIN_STATE.pop(uid, None)
            return await update.message.reply_text(f"❌ {e}")
        st["step"] = "session_name"
        return await update.message.reply_text("<b>Step 5/5 · Session name</b>\ne.g. <code>acc1</code>", parse_mode=ParseMode.HTML)

    if step == "password":
        st["password"] = text
        try: await _tg_login_step(st, "password")
        except Exception as e:
            LOGIN_STATE.pop(uid, None)
            return await update.message.reply_text(f"❌ {e}")
        st["step"] = "session_name"
        return await update.message.reply_text("<b>Step 5/5 · Session name</b>\ne.g. <code>acc1</code>", parse_mode=ParseMode.HTML)

    if step == "session_name":
        if not text.replace("_", "").isalnum():
            return await update.message.reply_text("Only letters, digits, underscore.")
        st["session_name"] = text
        await _finalize(update, st)
        LOGIN_STATE.pop(uid, None)


async def _finalize(update: Update, st: dict):
    final_name = st["session_name"]
    final_path = str(SESSIONS_DIR / final_name)

    tmp_path = SESSIONS_DIR / f"tmp_{st['phone'].replace('+','')}.session"
    final_session = Path(final_path + ".session")
    if tmp_path.exists() and not final_session.exists():
        try: tmp_path.rename(final_session)
        except Exception as e: log.warning(f"rename: {e}")

    (SESSIONS_DIR / f"{final_name}.json").write_text(json.dumps({
        "api_id": st["api_id"], "api_hash": st["api_hash"], "owner_id": GLOBAL_OWNER_ID,
    }))

    ok = SUPERVISOR.spawn(final_name, final_path, int(st["api_id"]), st["api_hash"],
                          {GLOBAL_OWNER_ID})
    if ok:
        await update.message.reply_text(
            f"<b>✅ 𝗔𝗰𝗰𝗼𝘂𝗻𝘁 𝗹𝗶𝘃𝗲</b>\n"
            f"session · <code>{final_name}</code>\n"
            f"owner   · <code>{GLOBAL_OWNER_ID}</code>\n\n"
            f"<i>Send</i> <code>zmenu</code> <i>from your personal account in any chat "
            f"where this session is present.</i>",
            parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(f"⚠ Already running: <code>{final_name}</code>", parse_mode=ParseMode.HTML)


@owner_only
async def on_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "p_add": await cmd_add(q, ctx)
    elif q.data == "p_refresh":
        try: await q.edit_message_text(panel_text(), parse_mode=ParseMode.HTML, reply_markup=panel_kb())
        except Exception: pass
    elif q.data == "p_list": await cmd_list(q, ctx)
    elif q.data == "p_stopall":
        names = list(SUPERVISOR.status().keys())
        for n in names: SUPERVISOR.stop(n)
        await q.message.reply_text(f"🛑 Stopping {len(names)} accounts…")


# ═══════════════════════════════════════════════════════════════════════
#  HEALTH SERVER
# ═══════════════════════════════════════════════════════════════════════

async def _health(request):
    st = SUPERVISOR.status()
    return web.json_response({
        "ok": True, "total": len(st), "accounts": st, "time": int(time.time()),
    })


async def _root(request):
    return web.Response(text="userbot online", content_type="text/plain")


async def start_health_server():
    app = web.Application()
    app.router.add_get("/", _root)
    app.router.add_get("/healthz", _health)
    app.router.add_get("/health", _health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    log.info(f"health :{PORT}")
    return runner


# ═══════════════════════════════════════════════════════════════════════
#  BOOT + MAIN
# ═══════════════════════════════════════════════════════════════════════

def boot_existing_sessions():
    for sess in SESSIONS_DIR.glob("*.session"):
        if sess.stem.startswith("tmp_"): continue
        meta_file = sess.with_suffix(".json")
        if not meta_file.exists(): continue
        try:
            meta = json.loads(meta_file.read_text())
            SUPERVISOR.spawn(sess.stem, str(sess.with_suffix("")),
                             int(meta["api_id"]), meta["api_hash"],
                             {int(meta.get("owner_id", GLOBAL_OWNER_ID))})
            log.info(f"resumed: {sess.stem}")
        except Exception as e:
            log.warning(f"resume {sess.stem}: {e}")


async def run_all():
    runner = await start_health_server()
    boot_existing_sessions()

    tg = Application.builder().token(BOT_TOKEN).build()
    tg.add_handler(CommandHandler("start", cmd_start))
    tg.add_handler(CommandHandler("panel", cmd_panel))
    tg.add_handler(CommandHandler("add", cmd_add))
    tg.add_handler(CommandHandler("cancel", cmd_cancel))
    tg.add_handler(CommandHandler("list", cmd_list))
    tg.add_handler(CommandHandler("stop", cmd_stop))
    tg.add_handler(CallbackQueryHandler(on_callback))
    tg.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))

    await tg.initialize()
    await tg.start()
    await tg.updater.start_polling(allowed_updates=Update.ALL_TYPES)
    log.info("manager bot online")

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    def _sig(*_):
        log.info("shutdown signal")
        stop_event.set()

    for sig in (signal.SIGTERM, signal.SIGINT):
        try: loop.add_signal_handler(sig, _sig)
        except NotImplementedError: pass

    await stop_event.wait()

    log.info("stopping…")
    try: await tg.updater.stop()
    except Exception: pass
    try: await tg.stop()
    except Exception: pass
    try: await tg.shutdown()
    except Exception: pass
    try: await runner.cleanup()
    except Exception: pass
    for inst in SUPERVISOR.all_instances():
        try: await inst.stop()
        except Exception: pass
    log.info("bye")


def main():
    try: asyncio.run(run_all())
    except KeyboardInterrupt: pass


if __name__ == "__main__":
    main()
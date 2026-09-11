import asyncio
import logging
import os
from pathlib import Path
from aiohttp import web

from telegram import Update, InputFile
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes, filters
)

# =========================
# CONFIG
# =========================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
ADMIN_ID = int(os.environ.get("ADMIN_ID", "8767998937"))

MAIN_CHANNELS = [
    -1003979162694,
    -1003914642663,
    -1004432245724,
    -1004322372581,
    -1004441677317,
    -1004303770116,
    -1003944803620,
    -1004446122167,
    -1004471601516,
]

SEPARATE_CHANNEL = -1003542014061

# The 50 names supplied by the user.
NAMES = [
    "Aarav Sharma", "Aditya Verma", "Arjun Singh", "Rohit Kumar",
    "Rahul Mehta", "Karan Malhotra", "Ankit Gupta", "Aman Yadav",
    "Akash Mishra", "Vivek Tiwari", "Rohan Kapoor", "Varun Bansal",
    "Mohit Agarwal", "Nikhil Jain", "Yash Patel", "Harsh Shah",
    "Rajat Saini", "Manish Chauhan", "Abhishek Saxena",
    "Saurabh Srivastava", "Sameer Khanna", "Ayush Pandey",
    "Shivam Tripathi", "Piyush Joshi", "Kartik Deshmukh",
    "Siddharth Rao", "Arnav Reddy", "Dhruv Nair", "Kabir Menon",
    "Pranav Iyer", "Varad Kulkarni", "Akhil Shetty", "Rohit Naik",
    "Devendra Thakur", "Naveen Rawat", "Deepak Bisht", "Sumit Negi",
    "Gaurav Dahiya", "Vikas Hooda", "Manav Arora", "Tushar Wadhwa",
    "Lakshya Oberoi", "Rishabh Chawla", "Tarun Goel", "Rajveer Ahuja",
    "Kunal Sethi", "Neeraj Puri", "Ashish Bhardwaj", "Dev Sharma",
    "Rudra Choudhary",
]

CAPTIONS = [
    "Thanku Hackii bhai",
    "Hackii maja aa gaya bhai",
    "Thanku bhai jackpot",
    "Great ho bhai Hackii",
    "Win hogya bhai",
    "Hackii bhai kamaal kar diya",
    "Bhai maja aa gaya",
    "Thanku Hackii bhai",
    "Bhai ek number kaam hai",
    "Hackii bhai zabardast",
    "Great work bhai",
    "Bhai bahut sahi laga",
    "Thanku bhai",
    "Hackii bhai mast hai",
    "Bhai kya baat hai",
    "Maja aa gaya Hackii",
    "Thanku so much bhai",
    "Hackii bhai great ho",
    "Bhai kamaal kar diya",
    "Aaj to maja aa gaya",
    "Thanku Hackii",
    "Bhai bahut badhiya",
    "Hackii bhai full mast",
    "Great bhai kaam kar gaya",
    "Bhai result mast raha",
    "Thanku bhai Hackii",
    "Hackii bhai ekdum sahi",
    "Maja aa gaya bhai",
    "Bhai kya hi bataun",
    "Great ho Hackii bhai",
    "Thanku bhai bahut sahi",
    "Hackii bhai mast kaam",
    "Bhai aaj to kamaal ho gaya",
    "Thanku Hackii bhai",
    "Hackii bhai bahut badhiya",
    "Bhai full maja aa gaya",
    "Great work Hackii bhai",
    "Thanku bhai mast laga",
    "Hackii bhai zabardast kaam",
    "Bhai maja aa gaya",
]

PHOTO_DIR = Path(__file__).resolve().parent / "photos"

# Persistent state is intentionally tiny. Render's filesystem is ephemeral,
# so this is runtime state only.
state = {
    "name_offset": 0,
    "photo_offset": 0,
    # channel_id -> latest message_id posted by /allchanelforward
    "latest_posts": {},
    # Latest user-sent media to the bot.
    "pending_photo": None,      # telegram file_id
    "pending_caption": None,    # optional user caption
}

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("channel-bot")


def is_admin(update: Update) -> bool:
    return bool(update.effective_user and update.effective_user.id == ADMIN_ID)


async def deny(update: Update):
    if update.effective_message:
        await update.effective_message.reply_text("Unauthorized.")


async def admin_only(update: Update) -> bool:
    if not is_admin(update):
        await deny(update)
        return False
    return True


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update):
        return
    await update.effective_message.reply_text(
        "Bot ready.\n\n"
        "/Namechange - 9 main channels ke alag names\n"
        "/photo - 9 main channels ki alag photos\n"
        "/allchanelforward - latest saved photo ko 9 channels par post\n"
        "/Allchanelto1chanelforward - 9 latest bot posts ko separate channel par forward\n"
        "/status - current runtime state"
    )


async def cmd_namechange(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update):
        return

    # Each invocation uses 9 consecutive supplied names, with wrap-around.
    start = state["name_offset"]
    chosen = [NAMES[(start + i) % len(NAMES)] for i in range(9)]

    ok = 0
    errors = []
    for channel_id, title in zip(MAIN_CHANNELS, chosen):
        try:
            await context.bot.set_chat_title(chat_id=channel_id, title=title)
            ok += 1
        except Exception as e:
            errors.append(f"{channel_id}: {e}")
            log.exception("Name change failed for %s", channel_id)

    state["name_offset"] = (start + 9) % len(NAMES)

    msg = f"Namechange complete: {ok}/9"
    if errors:
        msg += "\nErrors:\n" + "\n".join(errors[:3])
    await update.effective_message.reply_text(msg)


def photo_for_index(index: int) -> Path:
    # 40 files are expected as 01.jpg ... 40.jpg
    n = (index % 40) + 1
    return PHOTO_DIR / f"{n:02d}.jpg"


async def cmd_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update):
        return

    start = state["photo_offset"]
    sem = asyncio.Semaphore(3)

    async def change_one(i, channel_id):
        path = photo_for_index(start + i)
        async with sem:
            try:
                # Telegram accepts a file_id after the first upload, avoiding
                # repeated file uploads during the same process.
                cached = state.setdefault("photo_file_ids", {}).get(path.name)
                if cached:
                    await context.bot.set_chat_photo(chat_id=channel_id, photo=cached)
                else:
                    with path.open("rb") as f:
                        sent = await context.bot.send_photo(
                            chat_id=ADMIN_ID, photo=InputFile(f, filename=path.name)
                        )
                    cached = sent.photo[-1].file_id
                    state["photo_file_ids"][path.name] = cached
                    await context.bot.set_chat_photo(chat_id=channel_id, photo=cached)
                return True, ""
            except Exception as e:
                log.exception("Photo change failed for %s", channel_id)
                return False, f"{channel_id}: {e}"

    results = await asyncio.gather(
        *(change_one(i, channel_id) for i, channel_id in enumerate(MAIN_CHANNELS))
    )
    ok = sum(r[0] for r in results)
    errors = [r[1] for r in results if r[1]]
    state["photo_offset"] = (start + 9) % 40

    msg = f"Photo change complete: {ok}/9"
    if errors:
        msg += "\nErrors:\n" + "\n".join(errors[:3])
    await update.effective_message.reply_text(msg)


async def remember_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update):
        return

    msg = update.effective_message
    if msg.photo:
        state["pending_photo"] = msg.photo[-1].file_id
        state["pending_caption"] = msg.caption or None
        await msg.reply_text(
            "Photo saved. Ab /allchanelforward command bhejo."
        )


async def cmd_allchanelforward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update):
        return

    if not state["pending_photo"]:
        await update.effective_message.reply_text(
            "Pehle bot ko photo bhejo, phir /allchanelforward command do."
        )
        return

    photo_id = state["pending_photo"]
    start = 0

    # Channel 1..9 receive captions 1..9 for this post.
    # The same user-supplied photo is used in all 9 channels.
    sem = asyncio.Semaphore(3)

    async def post_one(idx, channel_id):
        caption = CAPTIONS[(start + idx) % len(CAPTIONS)]
        async with sem:
            try:
                sent = await context.bot.send_photo(
                    chat_id=channel_id,
                    photo=photo_id,
                    caption=caption,
                )
                return channel_id, sent.message_id, None
            except Exception as e:
                log.exception("Post failed for %s", channel_id)
                return channel_id, None, f"{channel_id}: {e}"

    results = await asyncio.gather(
        *(post_one(idx, channel_id) for idx, channel_id in enumerate(MAIN_CHANNELS))
    )
    errors = []
    ok = 0
    for channel_id, message_id, error in results:
        if message_id:
            state["latest_posts"][channel_id] = message_id
            ok += 1
        if error:
            errors.append(error)

    await update.effective_message.reply_text(
        f"Posted to {ok}/9 main channels."
        + (f"\nErrors: {len(errors)}" if errors else "")
    )


async def cmd_forward_latest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update):
        return

    # Telegram Bot API does not provide arbitrary channel-history scraping.
    # We therefore forward the latest post that THIS BOT posted to each main
    # channel, which is deterministic and safe.
    sem = asyncio.Semaphore(3)

    async def forward_one(channel_id):
        message_id = state["latest_posts"].get(channel_id)
        if not message_id:
            return False, f"{channel_id}: no bot-posted message stored"
        async with sem:
            try:
                await context.bot.forward_message(
                    chat_id=SEPARATE_CHANNEL,
                    from_chat_id=channel_id,
                    message_id=message_id,
                )
                return True, ""
            except Exception as e:
                log.exception("Forward failed from %s", channel_id)
                return False, f"{channel_id}: {e}"

    results = await asyncio.gather(*(forward_one(c) for c in MAIN_CHANNELS))
    sent = sum(r[0] for r in results)
    errors = [r[1] for r in results if r[1]]

    msg = f"Forwarded {sent}/9 latest bot posts to separate channel."
    if errors:
        msg += "\nErrors:\n" + "\n".join(errors[:5])
    await update.effective_message.reply_text(msg)


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_only(update):
        return
    tracked = sum(1 for c in MAIN_CHANNELS if c in state["latest_posts"])
    await update.effective_message.reply_text(
        f"Main channels: 9\n"
        f"Separate channel: 1\n"
        f"Latest bot posts tracked: {tracked}/9\n"
        f"Next name index: {state['name_offset'] + 1}\n"
        f"Next photo index: {state['photo_offset'] + 1}\n"
        f"Pending photo: {'yes' if state['pending_photo'] else 'no'}"
    )


async def health_handler(request):
    return web.Response(text="OK")


async def run_health_server():
    port = int(os.environ.get("PORT", "10000"))
    app = web.Application()
    app.router.add_get("/", health_handler)
    app.router.add_get("/health", health_handler)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    log.info("Health server listening on port %s", port)

    # Keep it alive.
    await asyncio.Event().wait()


async def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN environment variable is missing")

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .concurrent_updates(True)
        .connection_pool_size(32)
        .pool_timeout(10)
        .connect_timeout(10)
        .read_timeout(30)
        .write_timeout(30)
        .build()
    )

    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("Namechange", cmd_namechange))
    application.add_handler(CommandHandler("photo", cmd_photo))
    application.add_handler(CommandHandler("allchanelforward", cmd_allchanelforward))
    application.add_handler(
        CommandHandler("Allchanelto1chanelforward", cmd_forward_latest)
    )
    application.add_handler(CommandHandler("status", cmd_status))

    # Save a photo sent directly to the bot.
    application.add_handler(
        MessageHandler(filters.PHOTO, remember_media)
    )

    await application.initialize()
    await application.start()
    await application.updater.start_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )

    await asyncio.gather(
        run_health_server(),
        asyncio.Event().wait(),
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

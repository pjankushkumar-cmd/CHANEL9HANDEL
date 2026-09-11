import asyncio
import logging
import os
from pathlib import Path

from aiohttp import web
from telegram import Update, InputFile
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ============================================================
# CONFIG
# ============================================================

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()

# Sirf isi Telegram user ko admin commands chalane ki permission hai.
ADMIN_ID = int(os.environ.get("ADMIN_ID", "8767998937"))

# 9 MAIN CHANNELS
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

# 1 SEPARATE CHANNEL
# Is channel ka name/photo kabhi change nahi hoga.
SEPARATE_CHANNEL = -1003542014061

# Project folder
BASE_DIR = Path(__file__).resolve().parent
PHOTO_DIR = BASE_DIR / "photos"

# ============================================================
# 50 NAMES PROVIDED BY USER
# ============================================================

NAMES = [
    "Aarav Sharma",
    "Aditya Verma",
    "Arjun Singh",
    "Rohit Kumar",
    "Rahul Mehta",
    "Karan Malhotra",
    "Ankit Gupta",
    "Aman Yadav",
    "Akash Mishra",
    "Vivek Tiwari",
    "Rohan Kapoor",
    "Varun Bansal",
    "Mohit Agarwal",
    "Nikhil Jain",
    "Yash Patel",
    "Harsh Shah",
    "Rajat Saini",
    "Manish Chauhan",
    "Abhishek Saxena",
    "Saurabh Srivastava",
    "Sameer Khanna",
    "Ayush Pandey",
    "Shivam Tripathi",
    "Piyush Joshi",
    "Kartik Deshmukh",
    "Siddharth Rao",
    "Arnav Reddy",
    "Dhruv Nair",
    "Kabir Menon",
    "Pranav Iyer",
    "Varad Kulkarni",
    "Akhil Shetty",
    "Rohit Naik",
    "Devendra Thakur",
    "Naveen Rawat",
    "Deepak Bisht",
    "Sumit Negi",
    "Gaurav Dahiya",
    "Vikas Hooda",
    "Manav Arora",
    "Tushar Wadhwa",
    "Lakshya Oberoi",
    "Rishabh Chawla",
    "Tarun Goel",
    "Rajveer Ahuja",
    "Kunal Sethi",
    "Neeraj Puri",
    "Ashish Bhardwaj",
    "Dev Sharma",
    "Rudra Choudhary",
]

# ============================================================
# 40 CAPTIONS PROVIDED BY USER
# ============================================================

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

# ============================================================
# RUNTIME STATE
# ============================================================

state = {
    # Next starting position for the 9 different names.
    "name_offset": 0,

    # Next starting position for the 9 different photos.
    "photo_offset": 0,

    # Latest post made by this bot in each main channel.
    # channel_id -> message_id
    "latest_posts": {},

    # Last photo sent to the bot.
    "pending_photo": None,

    # Caption that may have been attached to the incoming photo.
    "pending_caption": None,

    # Telegram file_id cache for profile photos.
    "photo_file_ids": {},
}

# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

log = logging.getLogger("telegram-channel-bot")


# ============================================================
# BASIC ADMIN CHECK
# ============================================================

def is_admin(update: Update) -> bool:
    user = update.effective_user

    if user is None:
        return False

    return user.id == ADMIN_ID


async def admin_only(update: Update) -> bool:
    if not is_admin(update):
        if update.effective_message:
            await update.effective_message.reply_text(
                "Unauthorized."
            )
        return False

    return True


# ============================================================
# START COMMAND
# ============================================================

async def cmd_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await admin_only(update):
        return

    await update.effective_message.reply_text(
        "Bot ready.\n\n"
        "/Namechange - 9 main channels ke alag names\n"
        "/photo - 9 main channels ki alag photos\n"
        "/allchanelforward - photo ko 9 channels par post\n"
        "/Allchanelto1chanelforward - latest bot posts ko separate channel par forward\n"
        "/status - bot status"
    )


# ============================================================
# PHOTO FILE HELPER
# ============================================================

def photo_for_index(index: int) -> Path:
    """
    40 photos expected:
        01.jpg
        02.jpg
        ...
        40.jpg

    Index automatically wraps around 40.
    """

    number = (index % 40) + 1

    return PHOTO_DIR / f"{number:02d}.jpg"


# ============================================================
# PART 2 WILL CONTINUE HERE
# ============================================================
# ============================================================
# NAME CHANGE
# ============================================================

async def cmd_namechange(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await admin_only(update):
        return

    start = state["name_offset"]

    # 9 main channels ke liye 9 alag names
    selected_names = [
        NAMES[(start + i) % len(NAMES)]
        for i in range(len(MAIN_CHANNELS))
    ]

    success = 0
    errors = []

    for channel_id, new_name in zip(
        MAIN_CHANNELS,
        selected_names,
    ):
        try:
            await context.bot.set_chat_title(
                chat_id=channel_id,
                title=new_name,
            )

            success += 1

        except Exception as exc:
            errors.append(
                f"{channel_id}: {exc}"
            )

            log.exception(
                "Name change failed: %s",
                channel_id,
            )

    # Next command par next 9 names
    state["name_offset"] = (
        start + len(MAIN_CHANNELS)
    ) % len(NAMES)

    result = (
        f"Namechange complete: "
        f"{success}/{len(MAIN_CHANNELS)}"
    )

    if errors:
        result += (
            "\nErrors:\n"
            + "\n".join(errors[:3])
        )

    await update.effective_message.reply_text(result)


# ============================================================
# PHOTO CHANGE
# ============================================================

async def change_channel_photo(
    context: ContextTypes.DEFAULT_TYPE,
    channel_id: int,
    photo_path: Path,
):
    """
    Ek channel ki profile photo change karta hai.
    """

    try:
        cached_file_id = state[
            "photo_file_ids"
        ].get(photo_path.name)

        if cached_file_id:
            await context.bot.set_chat_photo(
                chat_id=channel_id,
                photo=cached_file_id,
            )

        else:
            with photo_path.open("rb") as photo_file:
                uploaded = await context.bot.send_photo(
                    chat_id=ADMIN_ID,
                    photo=InputFile(
                        photo_file,
                        filename=photo_path.name,
                    ),
                )

            cached_file_id = (
                uploaded.photo[-1].file_id
            )

            state[
                "photo_file_ids"
            ][photo_path.name] = cached_file_id

            await context.bot.set_chat_photo(
                chat_id=channel_id,
                photo=cached_file_id,
            )

        return True, None

    except Exception as exc:
        log.exception(
            "Photo change failed: %s",
            channel_id,
        )

        return False, str(exc)


async def cmd_photo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await admin_only(update):
        return

    start = state["photo_offset"]

    results = []

    # Safe bounded concurrency.
    semaphore = asyncio.Semaphore(3)

    async def worker(index, channel_id):
        photo_path = photo_for_index(
            start + index
        )

        async with semaphore:
            ok, error = await change_channel_photo(
                context,
                channel_id,
                photo_path,
            )

        return channel_id, ok, error

    tasks = [
        worker(index, channel_id)
        for index, channel_id
        in enumerate(MAIN_CHANNELS)
    ]

    results = await asyncio.gather(*tasks)

    success = 0
    errors = []

    for channel_id, ok, error in results:

        if ok:
            success += 1

        elif error:
            errors.append(
                f"{channel_id}: {error}"
            )

    # Next command par next 9 photos.
    state["photo_offset"] = (
        start + len(MAIN_CHANNELS)
    ) % 40

    result = (
        f"Photo change complete: "
        f"{success}/{len(MAIN_CHANNELS)}"
    )

    if errors:
        result += (
            "\nErrors:\n"
            + "\n".join(errors[:3])
        )

    await update.effective_message.reply_text(result)


# ============================================================
# RECEIVE PHOTO FROM ADMIN
# ============================================================

async def remember_photo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await admin_only(update):
        return

    message = update.effective_message

    if not message or not message.photo:
        return

    # Highest resolution photo
    photo = message.photo[-1]

    state["pending_photo"] = photo.file_id
    state["pending_caption"] = (
        message.caption or None
    )

    await message.reply_text(
        "Photo saved.\n"
        "Ab /allchanelforward command bhejo."
    )


# ============================================================
# ALL CHANNEL FORWARD
# ============================================================

async def post_to_channel(
    context: ContextTypes.DEFAULT_TYPE,
    channel_id: int,
    photo_file_id: str,
    caption: str,
):
    """
    Same photo ko ek main channel mein post karta hai.
    """

    try:
        sent_message = await context.bot.send_photo(
            chat_id=channel_id,
            photo=photo_file_id,
            caption=caption,
        )

        return (
            channel_id,
            sent_message.message_id,
            None,
        )

    except Exception as exc:
        log.exception(
            "Post failed: %s",
            channel_id,
        )

        return (
            channel_id,
            None,
            str(exc),
        )


async def cmd_allchanelforward(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await admin_only(update):
        return

    photo_file_id = state["pending_photo"]

    if not photo_file_id:
        await update.effective_message.reply_text(
            "Pehle bot ko photo bhejo, "
            "phir /allchanelforward command do."
        )
        return

    # 9 channels ke liye first 9 captions.
    selected_captions = [
        CAPTIONS[i % len(CAPTIONS)]
        for i in range(len(MAIN_CHANNELS))
    ]

    semaphore = asyncio.Semaphore(3)

    async def worker(index, channel_id):
        caption = selected_captions[index]

        async with semaphore:
            return await post_to_channel(
                context,
                channel_id,
                photo_file_id,
                caption,
            )

    tasks = [
        worker(index, channel_id)
        for index, channel_id
        in enumerate(MAIN_CHANNELS)
    ]

    results = await asyncio.gather(*tasks)

    success = 0
    errors = []

    for channel_id, message_id, error in results:

        if message_id:
            success += 1

            # Latest bot post store karo.
            state["latest_posts"][
                channel_id
            ] = message_id

        elif error:
            errors.append(
                f"{channel_id}: {error}"
            )

    result = (
        f"Posted to {success}/"
        f"{len(MAIN_CHANNELS)} main channels."
    )

    if errors:
        result += (
            "\nErrors: "
            + str(len(errors))
        )

    await update.effective_message.reply_text(
        result
    )


# ============================================================
# PART 3 CONTINUES...
# ============================================================
# ============================================================
# FORWARD LATEST POSTS TO SEPARATE CHANNEL
# ============================================================

async def forward_latest_from_channel(
    context: ContextTypes.DEFAULT_TYPE,
    channel_id: int,
):
    """
    Har main channel se us latest post ko forward karta hai
    jo bot ne /allchanelforward ke through create ki thi.
    """

    message_id = state["latest_posts"].get(channel_id)

    if not message_id:
        return channel_id, False, "No latest bot post found"

    try:
        await context.bot.forward_message(
            chat_id=SEPARATE_CHANNEL,
            from_chat_id=channel_id,
            message_id=message_id,
        )

        return channel_id, True, None

    except Exception as exc:
        log.exception(
            "Forward failed from channel %s",
            channel_id,
        )

        return channel_id, False, str(exc)


async def cmd_forward_latest(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await admin_only(update):
        return

    semaphore = asyncio.Semaphore(3)

    async def worker(channel_id):
        async with semaphore:
            return await forward_latest_from_channel(
                context,
                channel_id,
            )

    tasks = [
        worker(channel_id)
        for channel_id in MAIN_CHANNELS
    ]

    results = await asyncio.gather(*tasks)

    success = 0
    errors = []

    for channel_id, ok, error in results:

        if ok:
            success += 1

        elif error:
            errors.append(
                f"{channel_id}: {error}"
            )

    result = (
        f"Forwarded {success}/"
        f"{len(MAIN_CHANNELS)} latest posts "
        f"to separate channel."
    )

    if errors:
        result += (
            "\nErrors:\n"
            + "\n".join(errors[:5])
        )

    await update.effective_message.reply_text(
        result
    )


# ============================================================
# STATUS
# ============================================================

async def cmd_status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await admin_only(update):
        return

    tracked_posts = sum(
        1
        for channel_id in MAIN_CHANNELS
        if channel_id in state["latest_posts"]
    )

    pending = (
        "Yes"
        if state["pending_photo"]
        else "No"
    )

    await update.effective_message.reply_text(
        "BOT STATUS\n\n"
        f"Main channels: {len(MAIN_CHANNELS)}\n"
        f"Separate channel: 1\n"
        f"Latest posts tracked: "
        f"{tracked_posts}/{len(MAIN_CHANNELS)}\n"
        f"Pending photo: {pending}\n"
        f"Next name index: "
        f"{state['name_offset'] + 1}\n"
        f"Next photo index: "
        f"{state['photo_offset'] + 1}"
    )


# ============================================================
# HEALTH SERVER FOR RENDER
# ============================================================

async def health_handler(request):
    return web.Response(
        text="Telegram Bot is running"
    )


async def run_health_server():
    """
    Render Web Service ko ek HTTP port chahiye.
    Ye lightweight health server us purpose ke liye hai.
    """

    port = int(
        os.environ.get("PORT", "10000")
    )

    app = web.Application()

    app.router.add_get(
        "/",
        health_handler,
    )

    app.router.add_get(
        "/health",
        health_handler,
    )

    runner = web.AppRunner(app)

    await runner.setup()

    site = web.TCPSite(
        runner,
        "0.0.0.0",
        port,
    )

    await site.start()

    log.info(
        "Health server running on port %s",
        port,
    )

    # Server ko alive rakho.
    await asyncio.Event().wait()


# ============================================================
# BOT ERROR HANDLER
# ============================================================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
):
    error = context.error

    log.exception(
        "Telegram update error",
        exc_info=error,
    )


# ============================================================
# PART 4 WILL CONTINUE HERE
# ============================================================
# ============================================================
# APPLICATION STARTUP
# ============================================================

async def main():

    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN environment variable missing."
        )

    # Telegram application
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

    # --------------------------------------------------------
    # COMMAND HANDLERS
    # --------------------------------------------------------

    application.add_handler(
        CommandHandler(
            "start",
            cmd_start,
        )
    )

    application.add_handler(
        CommandHandler(
            "Namechange",
            cmd_namechange,
        )
    )

    application.add_handler(
        CommandHandler(
            "photo",
            cmd_photo,
        )
    )

    application.add_handler(
        CommandHandler(
            "allchanelforward",
            cmd_allchanelforward,
        )
    )

    application.add_handler(
        CommandHandler(
            "Allchanelto1chanelforward",
            cmd_forward_latest,
        )
    )

    application.add_handler(
        CommandHandler(
            "status",
            cmd_status,
        )
    )

    # --------------------------------------------------------
    # PHOTO RECEIVER
    # --------------------------------------------------------

    application.add_handler(
        MessageHandler(
            filters.PHOTO,
            remember_photo,
        )
    )

    # --------------------------------------------------------
    # ERROR HANDLER
    # --------------------------------------------------------

    application.add_error_handler(
        error_handler
    )

    # --------------------------------------------------------
    # START TELEGRAM POLLING
    # --------------------------------------------------------

    await application.initialize()

    await application.start()

    await application.updater.start_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )

    log.info(
        "Telegram channel bot started successfully."
    )

    # --------------------------------------------------------
    # RENDER HEALTH SERVER
    # --------------------------------------------------------

    try:

        await run_health_server()

    finally:

        await application.updater.stop()

        await application.stop()

        await application.shutdown()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    try:

        asyncio.run(main())

    except KeyboardInterrupt:

        log.info(
            "Bot stopped by user."
        )

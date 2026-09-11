# ============================================================
# PART 1 - CONFIGURATION
# ============================================================

import asyncio
import logging
import os
import random
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


BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

ADMIN_ID = int(
    os.getenv(
        "ADMIN_ID",
        "8767998937"
    )
)


# ============================================================
# MAIN 9 CHANNELS
# ============================================================

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


# ============================================================
# SEPARATE 10TH CHANNEL
# ============================================================

SEPARATE_CHANNEL = -1003542014061


# ============================================================
# FILE PATHS
# ============================================================

BASE_DIR = Path(
    __file__
).resolve().parent

PHOTO_DIR = BASE_DIR / "photos"


# ============================================================
# CHANNEL NAMES
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
# RANDOM NEUTRAL POST CAPTIONS
# ============================================================

NEUTRAL_CAPTIONS = [
    "Win bhai",
"Love you Hackii bhai",
"Ho gaya bhai",
"Thanku yaar",
"Bhai kya baat hai",
"Sahi ho gaya bhai, thanku",
"Hackii bhai love you yaar",
"Win ho gaya bhai, maja aa gaya",
"Arey bhai, aaj to scene ban gaya",
"Thanku Hackii bhai",
"Bhai ho gaya, kya bolun ab",
"Love you bhai, dil se thanku",
"Win bhai, aaj to maza aa gaya",
"Hackii bhai, jo bola tha samajh aa gaya",
"Arre yaar bhai, aaj wali baat dekh ke sach mein khushi ho gayi",
"Thanku bhai, itna clearly batane ke liye",
"Bhai ye wala to sahi ho gaya",
"Win bhai, kya scene hai",
"Hackii bhai love you, aaj to maja aa gaya",
"Arre wah bhai, aaj ka update dekh ke kaafi accha laga",
"Thanku yaar, ab sab clear hai",
"Bhai ho gaya, thanku Hackii",
"Love you bhai, kya baat hai",
"Win bhai, ekdum sahi",
"Hackii bhai, aaj to kamaal ho gaya",
"Thanku bhai, pehle confusion tha ab samajh aa gaya",
"Arre bhai, ye dekh ke maja aa gaya",
"Win ho gaya bhai, thanku yaar",
"Hackii bhai love you, kya mast moment tha",
"Bhai aaj wala kaafi sahi raha",
"Thanku Hackii bhai, sach mein kaafi help mili",
"Win bhai",
"Love you yaar Hackii",
"Ho gaya bhai, ab tension nahi",
"Arre bhai, aaj to maza hi aa gaya",
"Hackii bhai, thanku itna simple karke samjhane ke liye",
"Bhai win ho gaya, kya bolu yaar",
"Love you bhai, aaj kaafi khushi hui",
"Thanku yaar, Hackii bhai ne aaj phir samjha diya",
"Win bhai, aaj ka din ban gaya",
]


# ============================================================
# RUNTIME STATE
# ============================================================

state = {
    "name_offset": 0,
    "photo_offset": 0,
    "latest_posts": {},
    "pending_post": None,
    "media_groups": {},
    "caption_history": [],
}


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(message)s"
    ),
)

log = logging.getLogger(
    "channel-bot"
)


# ============================================================
# ADMIN CHECK
# ============================================================

def is_admin(
    update: Update
) -> bool:

    return bool(
        update.effective_user
        and update.effective_user.id
        == ADMIN_ID
    )


async def admin_only(
    update: Update
) -> bool:

    if not is_admin(update):

        if update.effective_message:

            await update.effective_message.reply_text(
                "Unauthorized."
            )

        return False

    return True


# ============================================================
# PHOTO FILE SELECTOR
# ============================================================

def photo_for_index(
    index: int
) -> Path:

    return (
        PHOTO_DIR
        / f"{(index % 40) + 1:02d}.jpg"
    )


# ============================================================
# RANDOM CAPTION SELECTOR
# ============================================================

def pick_random_captions(
    count: int
):

    recent = (
        state["caption_history"][-10:]
    )

    pool = [
        caption
        for caption in NEUTRAL_CAPTIONS
        if caption not in recent
    ]

    if len(pool) < count:

        pool = NEUTRAL_CAPTIONS[:]

    chosen = random.sample(
        pool,
        min(
            count,
            len(pool)
        ),
    )

    while len(chosen) < count:

        chosen.append(
            random.choice(
                NEUTRAL_CAPTIONS
            )
        )

    state[
        "caption_history"
    ].extend(chosen)

    state[
        "caption_history"
    ] = state[
        "caption_history"
    ][-20:]

    return chosen


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
        "/Namechange - 9 main channel names change\n"
        "/photo - 9 main channel photos change\n"
        "/removephoto - 9 main channel photos remove\n"
        "/allchanelforward - saved photo/album/text post\n"
        "/Allchanelto1chanelforward - latest posts to separate channel\n"
        "/status - bot status"
    )


# ============================================================
# NAME CHANGE
# ============================================================

async def cmd_namechange(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not await admin_only(update):
        return

    start = state[
        "name_offset"
    ]

    names = [
        NAMES[
            (start + i)
            % len(NAMES)
        ]
        for i in range(
            len(MAIN_CHANNELS)
        )
    ]

    semaphore = asyncio.Semaphore(
        3
    )

    async def worker(
        channel_id,
        title,
    ):

        async with semaphore:

            try:

                await context.bot.set_chat_title(
                    chat_id=channel_id,
                    title=title,
                )

                return True, None

            except Exception as exc:

                log.exception(
                    "Name change failed: %s",
                    channel_id,
                )

                return (
                    False,
                    f"{channel_id}: {exc}",
                )

    results = await asyncio.gather(
        *(
            worker(
                channel_id,
                title,
            )
            for channel_id, title
            in zip(
                MAIN_CHANNELS,
                names,
            )
        )
    )

    state[
        "name_offset"
    ] = (
        start
        + len(MAIN_CHANNELS)
    ) % len(NAMES)

    success = sum(
        ok
        for ok, _ in results
    )

    errors = [
        error
        for _, error in results
        if error
    ]

    reply = (
        f"Namechange complete: "
        f"{success}/"
        f"{len(MAIN_CHANNELS)}"
    )

    if errors:

        reply += (
            "\nErrors:\n"
            + "\n".join(
                errors[:3]
            )
        )

    await update.effective_message.reply_text(
        reply
    )


# ============================================================
# PART 1 END
# ============================================================
# ============================================================
# PART 2 - PHOTO / TEXT HANDLERS
# ============================================================


async def change_photo(
    context: ContextTypes.DEFAULT_TYPE,
    channel_id: int,
    photo_path: Path,
):
    try:
        if not photo_path.is_file():
            raise FileNotFoundError(
                f"Photo not found: {photo_path.name}"
            )

        image_bytes = photo_path.read_bytes()

        if not image_bytes:
            raise ValueError(
                f"Empty photo: {photo_path.name}"
            )

        await context.bot.set_chat_photo(
            chat_id=channel_id,
            photo=InputFile(
                image_bytes,
                filename=photo_path.name,
            ),
        )

        return True, None

    except Exception as exc:
        log.exception(
            "Photo change failed: %s",
            channel_id,
        )
        return False, f"{channel_id}: {exc}"


async def cmd_photo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await admin_only(update):
        return

    start = state["photo_offset"]

    semaphore = asyncio.Semaphore(3)

    async def worker(
        index,
        channel_id,
    ):
        async with semaphore:
            return await change_photo(
                context,
                channel_id,
                photo_for_index(
                    start + index
                ),
            )

    results = await asyncio.gather(
        *(
            worker(
                index,
                channel_id,
            )
            for index, channel_id
            in enumerate(MAIN_CHANNELS)
        )
    )

    state["photo_offset"] = (
        start + len(MAIN_CHANNELS)
    ) % 40

    success = sum(
        ok
        for ok, _ in results
    )

    errors = [
        error
        for _, error in results
        if error
    ]

    reply = (
        f"Photo change complete: "
        f"{success}/"
        f"{len(MAIN_CHANNELS)}"
    )

    if errors:
        reply += (
            "\nErrors:\n"
            + "\n".join(
                errors[:3]
            )
        )

    await update.effective_message.reply_text(
        reply
    )


async def cmd_removephoto(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await admin_only(update):
        return

    semaphore = asyncio.Semaphore(3)

    async def worker(channel_id):
        async with semaphore:
            try:
                await context.bot.delete_chat_photo(
                    chat_id=channel_id
                )

                return True, None

            except Exception as exc:
                log.exception(
                    "Remove photo failed: %s",
                    channel_id,
                )

                return (
                    False,
                    f"{channel_id}: {exc}",
                )

    results = await asyncio.gather(
        *(
            worker(channel_id)
            for channel_id
            in MAIN_CHANNELS
        )
    )

    success = sum(
        ok
        for ok, _ in results
    )

    errors = [
        error
        for _, error in results
        if error
    ]

    reply = (
        f"Removephoto complete: "
        f"{success}/"
        f"{len(MAIN_CHANNELS)}"
    )

    if errors:
        reply += (
            "\nErrors:\n"
            + "\n".join(
                errors[:3]
            )
        )

    await update.effective_message.reply_text(
        reply
    )


# ============================================================
# RECEIVE SINGLE PHOTO / ALBUM
# ============================================================

async def receive_photo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await admin_only(update):
        return

    message = update.effective_message

    if not message or not message.photo:
        return

    photo_id = message.photo[-1].file_id
    user_caption = message.caption or ""
    group_id = message.media_group_id

    # --------------------------------------------------------
    # SINGLE PHOTO
    # --------------------------------------------------------

    if not group_id:
        state["pending_post"] = {
            "type": "photos",
            "items": [
                (
                    photo_id,
                    user_caption,
                )
            ],
        }

        await message.reply_text(
            "Photo saved.\n"
            "Ab /allchanelforward bhejo."
        )

        return

    # --------------------------------------------------------
    # TELEGRAM ALBUM
    # --------------------------------------------------------

    bucket = state[
        "media_groups"
    ].setdefault(
        group_id,
        {
            "items": [],
            "task": None,
        },
    )

    bucket["items"].append(
        (
            photo_id,
            user_caption,
        )
    )

    old_task = bucket.get(
        "task"
    )

    if (
        old_task
        and not old_task.done()
    ):
        old_task.cancel()

    async def finalize_album():

        try:
            await asyncio.sleep(
                1.2
            )

        except asyncio.CancelledError:
            return

        data = state[
            "media_groups"
        ].pop(
            group_id,
            None,
        )

        if not data:
            return

        state["pending_post"] = {
            "type": "photos",
            "items": data["items"],
        }

        await message.reply_text(
            f"{len(data['items'])} "
            "photos saved.\n"
            "Ab /allchanelforward bhejo."
        )

    bucket["task"] = asyncio.create_task(
        finalize_album()
    )


# ============================================================
# RECEIVE NORMAL TEXT
# ============================================================

async def receive_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await admin_only(update):
        return

    message = update.effective_message

    if not message or not message.text:
        return

    state["pending_post"] = {
        "type": "text",
        "items": [
            message.text
        ],
    }

    await message.reply_text(
        "Text saved.\n"
        "Ab /allchanelforward bhejo."
    )


# ============================================================
# CLEAN CONTROL COMMAND FROM USER CAPTION
# ============================================================

def clean_user_caption(
    text: str
) -> str:

    if not text:
        return ""

    cleaned_lines = []

    for line in text.splitlines():

        stripped = line.strip()

        if stripped.lower().startswith(
            "/allchanelforward"
        ):

            remaining = stripped[
                len("/allchanelforward"):
            ].strip()

            if remaining:
                cleaned_lines.append(
                    remaining
                )

            continue

        cleaned_lines.append(
            line
        )

    return "\n".join(
        cleaned_lines
    ).strip()


# ============================================================
# SEND PHOTO
# ============================================================

async def send_photo(
    context,
    channel_id,
    photo_id,
    user_caption,
    publication_caption,
):
    user_caption = clean_user_caption(
        user_caption
    )

    if user_caption:
        final_caption = (
            f"{user_caption}\n\n"
            f"{publication_caption}"
        )
    else:
        final_caption = (
            publication_caption
        )

    try:

        sent = await context.bot.send_photo(
            chat_id=channel_id,
            photo=photo_id,
            caption=final_caption,
        )

        return (
            channel_id,
            sent.message_id,
            None,
        )

    except Exception as exc:

        log.exception(
            "Photo send failed: %s",
            channel_id,
        )

        return (
            channel_id,
            None,
            str(exc),
        )


# ============================================================
# SEND TEXT
# ============================================================

async def send_text(
    context,
    channel_id,
    text,
    publication_caption,
):
    text = clean_user_caption(
        text
    )

    if text:
        final_text = (
            f"{text}\n\n"
            f"{publication_caption}"
        )
    else:
        final_text = (
            publication_caption
        )

    try:

        sent = await context.bot.send_message(
            chat_id=channel_id,
            text=final_text,
        )

        return (
            channel_id,
            sent.message_id,
            None,
        )

    except Exception as exc:

        log.exception(
            "Text send failed: %s",
            channel_id,
        )

        return (
            channel_id,
            None,
            str(exc),
        )


# ============================================================
# PART 2 END
# ============================================================
# ============================================================
# PART 3 - ALL CHANNEL FORWARD
# ============================================================


async def cmd_allchanelforward(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await admin_only(update):
        return

    pending = state.get(
        "pending_post"
    )

    if not pending:
        await update.effective_message.reply_text(
            "Pehle photo, album, ya text bhejo; "
            "phir /allchanelforward bhejo."
        )
        return

    # --------------------------------------------------------
    # PHOTO / ALBUM DISTRIBUTION
    # --------------------------------------------------------

    if pending["type"] == "photos":

        supplied_photos = pending["items"]

        items = [
            supplied_photos[
                index % len(supplied_photos)
            ]
            for index in range(
                len(MAIN_CHANNELS)
            )
        ]

    else:

        items = [
            pending["items"][0]
            for _ in MAIN_CHANNELS
        ]

    # --------------------------------------------------------
    # RANDOM CAPTIONS
    # --------------------------------------------------------

    captions = pick_random_captions(
        len(MAIN_CHANNELS)
    )

    semaphore = asyncio.Semaphore(3)

    async def worker(
        index,
        channel_id,
    ):

        async with semaphore:

            if pending["type"] == "photos":

                photo_id, user_caption = (
                    items[index]
                )

                return await send_photo(
                    context,
                    channel_id,
                    photo_id,
                    user_caption,
                    captions[index],
                )

            return await send_text(
                context,
                channel_id,
                items[index],
                captions[index],
            )

    # --------------------------------------------------------
    # SEND TO ALL 9 MAIN CHANNELS
    # --------------------------------------------------------

    results = await asyncio.gather(
        *(
            worker(
                index,
                channel_id,
            )
            for index, channel_id
            in enumerate(MAIN_CHANNELS)
        )
    )

    success = 0
    errors = []

    # --------------------------------------------------------
    # SAVE LATEST MESSAGE ID
    # --------------------------------------------------------

    for (
        channel_id,
        message_id,
        error,
    ) in results:

        if message_id:

            success += 1

            state[
                "latest_posts"
            ][channel_id] = message_id

        elif error:

            errors.append(
                f"{channel_id}: {error}"
            )

    # Content successfully processed.
    state["pending_post"] = None

    reply = (
        f"Posted to "
        f"{success}/"
        f"{len(MAIN_CHANNELS)} "
        "main channels."
    )

    if errors:

        reply += (
            "\nErrors: "
            f"{len(errors)}"
        )

    await update.effective_message.reply_text(
        reply
    )


# ============================================================
# FORWARD LATEST POSTS TO SEPARATE CHANNEL
# ============================================================


async def cmd_forward_latest(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await admin_only(update):
        return

    semaphore = asyncio.Semaphore(3)

    async def worker(
        channel_id
    ):

        message_id = state[
            "latest_posts"
        ].get(
            channel_id
        )

        if not message_id:

            return (
                False,
                f"{channel_id}: "
                "no latest bot post stored",
            )

        async with semaphore:

            try:

                await context.bot.forward_message(
                    chat_id=SEPARATE_CHANNEL,
                    from_chat_id=channel_id,
                    message_id=message_id,
                )

                return (
                    True,
                    None,
                )

            except Exception as exc:

                log.exception(
                    "Forward failed: %s",
                    channel_id,
                )

                return (
                    False,
                    f"{channel_id}: {exc}",
                )

    results = await asyncio.gather(
        *(
            worker(channel_id)
            for channel_id
            in MAIN_CHANNELS
        )
    )

    success = sum(
        ok
        for ok, _ in results
    )

    errors = [
        error
        for _, error
        in results
        if error
    ]

    reply = (
        f"Forwarded "
        f"{success}/"
        f"{len(MAIN_CHANNELS)} "
        "latest bot posts to separate channel."
    )

    if errors:

        reply += (
            "\nErrors:\n"
            + "\n".join(
                errors[:5]
            )
        )

    await update.effective_message.reply_text(
        reply
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

    tracked = sum(
        channel_id in state[
            "latest_posts"
        ]
        for channel_id
        in MAIN_CHANNELS
    )

    pending = (
        "yes"
        if state["pending_post"]
        else "no"
    )

    await update.effective_message.reply_text(
        f"Main channels: "
        f"{len(MAIN_CHANNELS)}\n"
        "Separate channel: 1\n"
        f"Latest bot posts tracked: "
        f"{tracked}/9\n"
        f"Next name index: "
        f"{state['name_offset'] + 1}\n"
        f"Next photo index: "
        f"{state['photo_offset'] + 1}\n"
        f"Pending post: {pending}"
    )


# ============================================================
# RENDER HEALTH SERVER
# ============================================================


async def health(
    request
):
    return web.Response(
        text="OK"
    )


async def run_health_server():

    port = int(
        os.getenv(
            "PORT",
            "10000"
        )
    )

    app = web.Application()

    app.router.add_get(
        "/",
        health
    )

    app.router.add_get(
        "/health",
        health
    )

    runner = web.AppRunner(
        app
    )

    await runner.setup()

    site = web.TCPSite(
        runner,
        "0.0.0.0",
        port
    )

    await site.start()

    log.info(
        "Health server listening on %s",
        port
    )

    await asyncio.Event().wait()


# ============================================================
# TELEGRAM ERROR HANDLER
# ============================================================


async def error_handler(
    update,
    context
):

    log.error(
        "Telegram update error: %s",
        context.error,
        exc_info=context.error,
    )


# ============================================================
# PART 3 END
# ============================================================
# ============================================================
# PART 4 - START BOT
# ============================================================


async def main():

    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN environment variable is missing"
        )

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
            ["Namechange", "namechange"],
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
            "removephoto",
            cmd_removephoto,
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
    # PHOTO / ALBUM HANDLER
    # --------------------------------------------------------

    application.add_handler(
        MessageHandler(
            filters.PHOTO,
            receive_photo,
        )
    )

    # --------------------------------------------------------
    # NORMAL TEXT HANDLER
    # --------------------------------------------------------

    application.add_handler(
        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND,
            receive_text,
        )
    )

    # --------------------------------------------------------
    # ERROR HANDLER
    # --------------------------------------------------------

    application.add_error_handler(
        error_handler
    )

    # --------------------------------------------------------
    # START TELEGRAM
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

    asyncio.run(
        main()
    )


# ============================================================
# PART 4 END
# ============================================================

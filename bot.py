import asyncio
import logging
import os
from pathlib import Path
from aiohttp import web
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.environ.get('BOT_TOKEN', '').strip()
ADMIN_ID = int(os.environ.get('ADMIN_ID', '8767998937'))

MAIN_CHANNELS = [
    -1003979162694, -1003914642663, -1004432245724,
    -1004322372581, -1004441677317, -1004303770116,
    -1003944803620, -1004446122167, -1004471601516,
]
SEPARATE_CHANNEL = -1003542014061

BASE_DIR = Path(__file__).resolve().parent
PHOTO_DIR = BASE_DIR / 'photos'

NAMES = [
    'Aarav Sharma','Aditya Verma','Arjun Singh','Rohit Kumar','Rahul Mehta',
    'Karan Malhotra','Ankit Gupta','Aman Yadav','Akash Mishra','Vivek Tiwari',
    'Rohan Kapoor','Varun Bansal','Mohit Agarwal','Nikhil Jain','Yash Patel',
    'Harsh Shah','Rajat Saini','Manish Chauhan','Abhishek Saxena','Saurabh Srivastava',
    'Sameer Khanna','Ayush Pandey','Shivam Tripathi','Piyush Joshi','Kartik Deshmukh',
    'Siddharth Rao','Arnav Reddy','Dhruv Nair','Kabir Menon','Pranav Iyer',
    'Varad Kulkarni','Akhil Shetty','Rohit Naik','Devendra Thakur','Naveen Rawat',
    'Deepak Bisht','Sumit Negi','Gaurav Dahiya','Vikas Hooda','Manav Arora',
    'Tushar Wadhwa','Lakshya Oberoi','Rishabh Chawla','Tarun Goel','Rajveer Ahuja',
    'Kunal Sethi','Neeraj Puri','Ashish Bhardwaj','Dev Sharma','Rudra Choudhary'
]

CAPTIONS = [
    'Thanku Hackii bhai','Hackii maja aa gaya bhai','Thanku bhai jackpot',
    'Great ho bhai Hackii','Win hogya bhai','Hackii bhai kamaal kar diya',
    'Bhai maja aa gaya','Thanku Hackii bhai','Bhai ek number kaam hai',
    'Hackii bhai zabardast','Great work bhai','Bhai bahut sahi laga',
    'Thanku bhai','Hackii bhai mast hai','Bhai kya baat hai','Maja aa gaya Hackii',
    'Thanku so much bhai','Hackii bhai great ho','Bhai kamaal kar diya',
    'Aaj to maja aa gaya','Thanku Hackii','Bhai bahut badhiya',
    'Hackii bhai full mast','Great bhai kaam kar gaya','Bhai result mast raha',
    'Thanku bhai Hackii','Hackii bhai ekdum sahi','Maja aa gaya bhai',
    'Bhai kya hi bataun','Great ho Hackii bhai','Thanku bhai bahut sahi',
    'Hackii bhai mast kaam','Bhai aaj to kamaal ho gaya','Thanku Hackii bhai',
    'Hackii bhai bahut badhiya','Bhai full maja aa gaya','Great work Hackii bhai',
    'Thanku bhai mast laga','Hackii bhai zabardast kaam','Bhai maja aa gaya'
]

state = {
    'name_offset': 0,
    'photo_offset': 0,
    'caption_offset': 0,
    'latest_posts': {},
    'pending_post': None,
    'media_groups': {},
    'photo_file_ids': {},
}

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
log = logging.getLogger('channel-bot')


def is_admin(update: Update) -> bool:
    return bool(
        update.effective_user
        and update.effective_user.id == ADMIN_ID
    )


async def admin_only(update: Update) -> bool:
    if not is_admin(update):
        if update.effective_message:
            await update.effective_message.reply_text('Unauthorized.')
        return False
    return True


async def cmd_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not await admin_only(update):
        return

    await update.effective_message.reply_text(
        '/Namechange - 9 main channels ke alag names\n'
        '/photo - 9 main channels ki alag photos\n'
        '/allchanelforward - saved photo/album/text ko 9 channels par post\n'
        '/Allchanelto1chanelforward - 9 latest bot posts ko separate channel par forward\n'
        '/status - status'
    )


async def cmd_namechange(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not await admin_only(update):
        return

    start = state['name_offset']

    names = [
        NAMES[(start + i) % len(NAMES)]
        for i in range(9)
    ]

    async def one(cid, title):
        try:
            await context.bot.set_chat_title(cid, title)
            return True, None
        except Exception as e:
            log.exception('Name change failed %s', cid)
            return False, f'{cid}: {e}'

    sem = asyncio.Semaphore(3)

    async def worker(cid, title):
        async with sem:
            return await one(cid, title)

    results = await asyncio.gather(
        *(worker(c, n) for c, n in zip(MAIN_CHANNELS, names))
    )

    ok = sum(x[0] for x in results)

    state['name_offset'] = (
        start + 9
    ) % len(NAMES)

    errors = [
        x[1]
        for x in results
        if x[1]
    ]

    msg = f'Namechange complete: {ok}/9'

    if errors:
        msg += '\nErrors:\n' + '\n'.join(errors[:3])

    await update.effective_message.reply_text(msg)


def photo_for_index(index: int) -> Path:
    return PHOTO_DIR / f'{(index % 40) + 1:02d}.jpg'
    async def change_photo(context, cid, path):
    """Telegram setChatPhoto requires an uploaded InputFile."""
    try:
        image_bytes = path.read_bytes()

        await context.bot.set_chat_photo(
            chat_id=cid,
            photo=InputFile(
                image_bytes,
                filename=path.name
            ),
        )

        return True, None

    except Exception as e:
        log.exception('Photo change failed %s', cid)
        return False, f'{cid}: {e}'


async def cmd_photo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not await admin_only(update):
        return

    start = state['photo_offset']

    sem = asyncio.Semaphore(3)

    async def worker(i, cid):
        async with sem:
            return await change_photo(
                context,
                cid,
                photo_for_index(start + i)
            )

    results = await asyncio.gather(
        *(
            worker(i, c)
            for i, c in enumerate(MAIN_CHANNELS)
        )
    )

    ok = sum(x[0] for x in results)

    state['photo_offset'] = (
        start + 9
    ) % 40

    errors = [
        x[1]
        for x in results
        if x[1]
    ]

    msg = f'Photo change complete: {ok}/9'

    if errors:
        msg += '\nErrors:\n' + '\n'.join(errors[:3])

    await update.effective_message.reply_text(msg)


async def cmd_removephoto(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """Remove profile photos from ONLY the 9 main channels."""

    if not await admin_only(update):
        return

    sem = asyncio.Semaphore(3)

    async def worker(cid):
        async with sem:
            try:
                await context.bot.delete_chat_photo(
                    chat_id=cid
                )
                return True, None

            except Exception as e:
                log.exception(
                    'Remove photo failed %s',
                    cid
                )
                return False, f'{cid}: {e}'

    results = await asyncio.gather(
        *(worker(c) for c in MAIN_CHANNELS)
    )

    ok = sum(x[0] for x in results)

    errors = [
        x[1]
        for x in results
        if x[1]
    ]

    msg = f'Removephoto complete: {ok}/9'

    if errors:
        msg += '\nErrors:\n' + '\n'.join(errors[:3])

    await update.effective_message.reply_text(msg)


async def receive_photo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not await admin_only(update):
        return

    msg = update.effective_message

    if not msg or not msg.photo:
        return

    item = (
        msg.photo[-1].file_id,
        msg.caption or ''
    )

    gid = msg.media_group_id

    if not gid:
        state['pending_post'] = {
            'type': 'photos',
            'items': [item]
        }

        await msg.reply_text(
            'Photo saved. Ab /allchanelforward bhejo.'
        )

        return

    bucket = state['media_groups'].setdefault(
        gid,
        {
            'items': [],
            'task': None
        }
    )

    bucket['items'].append(item)

    old = bucket.get('task')

    if old and not old.done():
        old.cancel()

    async def finalize():
        try:
            await asyncio.sleep(1.0)
        except asyncio.CancelledError:
            return

        data = state['media_groups'].pop(
            gid,
            None
        )

        if not data:
            return

        state['pending_post'] = {
            'type': 'photos',
            'items': data['items']
        }

        await msg.reply_text(
            f"{len(data['items'])} photos saved. "
            f"Ab /allchanelforward bhejo."
        )

    bucket['task'] = asyncio.create_task(
        finalize()
    )


async def receive_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not await admin_only(update):
        return

    msg = update.effective_message

    if not msg or not msg.text:
        return

    state['pending_post'] = {
        'type': 'text',
        'items': [msg.text]
    }

    await msg.reply_text(
        'Text saved. Ab /allchanelforward bhejo.'
    )


def reserve_captions(count):
    start = state['caption_offset']

    caps = [
        CAPTIONS[
            (start + i) % len(CAPTIONS)
        ]
        for i in range(count)
    ]

    state['caption_offset'] = (
        start + count
    ) % len(CAPTIONS)

    return caps


async def send_photo(
    context,
    cid,
    photo_id,
    user_caption,
    project_caption
):
    caption = (
        f'{user_caption}\n\n{project_caption}'
        if user_caption
        else project_caption
    )

    try:
        m = await context.bot.send_photo(
            cid,
            photo_id,
            caption=caption
        )

        return cid, m.message_id, None

    except Exception as e:
        log.exception(
            'Post failed %s',
            cid
        )
        return cid, None, str(e)


async def send_text(
    context,
    cid,
    text,
    project_caption
):
    final = f'{text}\n\n{project_caption}'

    try:
        m = await context.bot.send_message(
            cid,
            final
        )

        return cid, m.message_id, None

    except Exception as e:
        log.exception(
            'Text post failed %s',
            cid
        )
        return cid, None, str(e)
        async def cmd_allchanelforward(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not await admin_only(update):
        return

    pending = state.get('pending_post')

    if not pending:
        await update.effective_message.reply_text(
            'Pehle photo, album, ya text bhejo; '
            'phir /allchanelforward bhejo.'
        )
        return

    # One photo -> same photo to all 9.
    # Album -> photos are assigned sequentially
    # across the 9 channels.
    if pending['type'] == 'photos':
        supplied = pending['items']

        items = [
            supplied[i % len(supplied)]
            for i in range(9)
        ]

    else:
        items = [
            pending['items'][0]
        ] * 9

    captions = reserve_captions(9)

    sem = asyncio.Semaphore(3)

    async def worker(i, cid):
        async with sem:

            if pending['type'] == 'photos':
                pid, user_cap = items[i]

                return await send_photo(
                    context,
                    cid,
                    pid,
                    user_cap,
                    captions[i]
                )

            return await send_text(
                context,
                cid,
                items[i],
                captions[i]
            )

    results = await asyncio.gather(
        *(
            worker(i, c)
            for i, c in enumerate(MAIN_CHANNELS)
        )
    )

    ok = 0
    errors = []

    for cid, mid, err in results:

        if mid:
            ok += 1

            state['latest_posts'][cid] = mid

        elif err:
            errors.append(
                f'{cid}: {err}'
            )

    state['pending_post'] = None

    msg = (
        f'Posted to {ok}/9 main channels.'
    )

    if errors:
        msg += f'\nErrors: {len(errors)}'

    await update.effective_message.reply_text(
        msg
    )


async def cmd_forward_latest(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not await admin_only(update):
        return

    sem = asyncio.Semaphore(3)

    async def worker(cid):

        mid = state['latest_posts'].get(cid)

        if not mid:
            return (
                False,
                f'{cid}: no latest bot post stored'
            )

        async with sem:

            try:
                await context.bot.forward_message(
                    SEPARATE_CHANNEL,
                    cid,
                    mid
                )

                return True, None

            except Exception as e:
                log.exception(
                    'Forward failed %s',
                    cid
                )

                return (
                    False,
                    f'{cid}: {e}'
                )

    results = await asyncio.gather(
        *(
            worker(c)
            for c in MAIN_CHANNELS
        )
    )

    ok = sum(
        x[0]
        for x in results
    )

    errors = [
        x[1]
        for x in results
        if x[1]
    ]

    msg = (
        f'Forwarded {ok}/9 latest bot posts '
        f'to separate channel.'
    )

    if errors:
        msg += (
            '\nErrors:\n'
            + '\n'.join(errors[:5])
        )

    await update.effective_message.reply_text(
        msg
    )


async def cmd_status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not await admin_only(update):
        return

    tracked = sum(
        c in state['latest_posts']
        for c in MAIN_CHANNELS
    )

    await update.effective_message.reply_text(
        f'Main channels: 9\n'
        f'Separate channel: 1\n'
        f'Latest bot posts tracked: {tracked}/9\n'
        f'Next name index: '
        f'{state["name_offset"] + 1}\n'
        f'Next photo index: '
        f'{state["photo_offset"] + 1}\n'
        f'Next caption index: '
        f'{state["caption_offset"] + 1}\n'
        f'Pending post: '
        f'{"yes" if state["pending_post"] else "no"}'
    )


async def health(request):
    return web.Response(
        text='OK'
    )


async def run_health_server():
    port = int(
        os.environ.get(
            'PORT',
            '10000'
        )
    )

    app = web.Application()

    app.router.add_get(
        '/',
        health
    )

    app.router.add_get(
        '/health',
        health
    )

    runner = web.AppRunner(app)

    await runner.setup()

    await web.TCPSite(
        runner,
        '0.0.0.0',
        port
    ).start()

    log.info(
        'Health server listening on %s',
        port
    )

    await asyncio.Event().wait()
    async def error_handler(
    update,
    context
):
    log.exception(
        'Telegram error',
        exc_info=context.error
    )


async def main():

    if not BOT_TOKEN:
        raise RuntimeError(
            'BOT_TOKEN environment variable is missing'
        )

    app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .concurrent_updates(True)
        .connection_pool_size(32)
        .pool_timeout(10)
        .connect_timeout(10)
        .read_timeout(30)
        .write_timeout(30)
        .build()
    )

    app.add_handler(
        CommandHandler(
            'start',
            cmd_start
        )
    )

    app.add_handler(
        CommandHandler(
            'Namechange',
            cmd_namechange
        )
    )

    app.add_handler(
        CommandHandler(
            'photo',
            cmd_photo
        )
    )

    app.add_handler(
        CommandHandler(
            'removephoto',
            cmd_removephoto
        )
    )

    app.add_handler(
        CommandHandler(
            'allchanelforward',
            cmd_allchanelforward
        )
    )

    app.add_handler(
        CommandHandler(
            'Allchanelto1chanelforward',
            cmd_forward_latest
        )
    )

    app.add_handler(
        CommandHandler(
            'status',
            cmd_status
        )
    )

    app.add_handler(
        MessageHandler(
            filters.PHOTO,
            receive_photo
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            receive_text
        )
    )

    app.add_error_handler(
        error_handler
    )

    await app.initialize()
    await app.start()

    await app.updater.start_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )

    log.info(
        'Telegram channel bot started'
    )

    try:
        await run_health_server()

    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


if __name__ == '__main__':
    asyncio.run(main())

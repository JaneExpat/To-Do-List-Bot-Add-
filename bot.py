"""
To-Do List Telegram Bot
------------------------
Add, list, complete, and delete personal tasks.

Commands:
  /start        - welcome message + quick guide
  /add <task>   - add a new task
  /list         - show pending tasks
  /list all     - show pending + completed tasks
  /done <n>     - mark task number n as done
  /delete <n>   - permanently delete task number n

Storage: SQLite (todo.db), one file, no external server needed.
Each user only sees their own tasks (filtered by Telegram user_id).
"""

import logging
import os
import sqlite3
from contextlib import closing

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "PASTE_YOUR_BOT_TOKEN_HERE").strip()  # from BotFather

# Temporary debug: confirm the token is actually loaded (prints length + first/last few chars only, never the full token)
if BOT_TOKEN and BOT_TOKEN != "PASTE_YOUR_BOT_TOKEN_HERE":
    print(f"[DEBUG] Token loaded, length={len(BOT_TOKEN)}, starts='{BOT_TOKEN[:6]}', ends='{BOT_TOKEN[-6:]}'")
else:
    print("[DEBUG] TELEGRAM_BOT_TOKEN environment variable is missing or empty!")
DB_PATH = "todo.db"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# DATABASE HELPERS
# ---------------------------------------------------------------------------
def init_db():
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                task_text TEXT NOT NULL,
                is_done INTEGER NOT NULL DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now'))
            )
            """
        )
        conn.commit()


def add_task(user_id: int, text: str):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute(
            "INSERT INTO tasks (user_id, task_text) VALUES (?, ?)",
            (user_id, text),
        )
        conn.commit()


def get_tasks(user_id: int, include_done: bool = False):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        if include_done:
            cur = conn.execute(
                "SELECT id, task_text, is_done FROM tasks WHERE user_id = ? ORDER BY is_done ASC, id ASC",
                (user_id,),
            )
        else:
            cur = conn.execute(
                "SELECT id, task_text, is_done FROM tasks WHERE user_id = ? AND is_done = 0 ORDER BY id ASC",
                (user_id,),
            )
        return cur.fetchall()


def get_task_by_position(user_id: int, position: int, include_done: bool = False):
    """Map the number shown in /list (1, 2, 3...) back to a real task row."""
    tasks = get_tasks(user_id, include_done=include_done)
    if 1 <= position <= len(tasks):
        return tasks[position - 1]
    return None


def mark_done(task_id: int):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute("UPDATE tasks SET is_done = 1 WHERE id = ?", (task_id,))
        conn.commit()


def delete_task(task_id: int):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()


# ---------------------------------------------------------------------------
# COMMAND HANDLERS
# ---------------------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 *To-Do List Bot*\n\n"
        "Keep track of your personal tasks right here in chat.\n\n"
        "*Commands:*\n"
        "/add <task> — add a new task\n"
        "/list — show your pending tasks\n"
        "/list all — show pending + completed tasks\n"
        "/done <number> — mark a task as done\n"
        "/delete <number> — permanently remove a task\n\n"
        "Example: `/add Buy groceries`",
        parse_mode="Markdown",
    )


async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = " ".join(context.args).strip()

    if not text:
        await update.message.reply_text("Usage: /add <task>\nExample: /add Buy groceries")
        return

    add_task(user_id, text)
    await update.message.reply_text(f"✅ Added: \"{text}\"")


async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    include_done = len(context.args) > 0 and context.args[0].lower() == "all"

    tasks = get_tasks(user_id, include_done=include_done)

    if not tasks:
        msg = "You have no tasks yet. Add one with /add <task>."
        await update.message.reply_text(msg)
        return

    lines = []
    for i, (task_id, task_text, is_done) in enumerate(tasks, start=1):
        checkbox = "✅" if is_done else "▫️"
        lines.append(f"{i}. {checkbox} {task_text}")

    header = "📋 *All tasks:*" if include_done else "📋 *Pending tasks:*"
    await update.message.reply_text(header + "\n" + "\n".join(lines), parse_mode="Markdown")


async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: /done <number>\nCheck /list for task numbers.")
        return

    position = int(context.args[0])
    task = get_task_by_position(user_id, position, include_done=False)

    if not task:
        await update.message.reply_text("Couldn't find that task number. Check /list for current numbers.")
        return

    task_id, task_text, _ = task
    mark_done(task_id)
    await update.message.reply_text(f"🎉 Marked done: \"{task_text}\"")


async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: /delete <number>\nCheck /list all for task numbers.")
        return

    position = int(context.args[0])
    # allow deleting from the full list (pending + done), since done tasks can pile up
    task = get_task_by_position(user_id, position, include_done=True)

    if not task:
        await update.message.reply_text("Couldn't find that task number. Check /list all for current numbers.")
        return

    task_id, task_text, _ = task
    delete_task(task_id)
    await update.message.reply_text(f"🗑️ Deleted: \"{task_text}\"")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("list", list_tasks))
    app.add_handler(CommandHandler("done", done))
    app.add_handler(CommandHandler("delete", delete))

    logger.info("Bot starting...")
    app.run_polling()


if __name__ == "__main__":
    main()

# To-Do List Telegram Bot

Add, list, complete, and delete personal tasks — right from Telegram.

## Setup

1. **Get a bot token** from [@BotFather](https://t.me/BotFather) on Telegram (`/newbot` if you haven't already).

2. **Install dependencies:**
   ```bash
   pip install python-telegram-bot
   ```

3. **Add your token:**
   Open `bot.py` and replace:
   ```python
   BOT_TOKEN = "PASTE_YOUR_BOT_TOKEN_HERE"
   ```
   with the token BotFather gave you.

4. **Run it:**
   ```bash
   python bot.py
   ```

That's it — the bot will start polling Telegram for messages. A `todo.db` SQLite file will be created automatically in the same folder to store tasks.

## Commands

| Command | What it does |
|---|---|
| `/start` | Welcome message + quick command guide |
| `/add <task>` | Add a new task, e.g. `/add Buy groceries` |
| `/list` | Show your pending (not-yet-done) tasks |
| `/list all` | Show pending **and** completed tasks (✅) |
| `/done <number>` | Mark a task as done, e.g. `/done 2` |
| `/delete <number>` | Permanently delete a task, e.g. `/delete 3` |

Task numbers refer to the position shown in the most recent `/list` (or `/list all`) you ran — they aren't permanent IDs, so always check the current list before running `/done` or `/delete`.

## Notes

- Each user's tasks are private — filtered by their Telegram user ID.
- Completed tasks are kept in the database (not deleted) so nothing is lost — they just get hidden from the default `/list` view.
- For 24/7 uptime, deploy this on a small server or a host like Railway, Render, or a VPS, and keep it running with something like `systemd`, `pm2`, or `screen`/`tmux`.

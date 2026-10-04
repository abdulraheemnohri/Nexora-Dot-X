"""Always-on background worker: scheduler ticks, channel polling, queued execution.

One worker loop drives the autonomous side of Nexora:
  - runs due schedules (SQLite-backed, survives restarts)
  - polls Telegram / Discord / Slack (each only when its token is set)
  - picks up queued tasks and runs them through the Agent runtime

Poll frequency and worker limits come from the active device profile.
"""
import asyncio
import os

import httpx

from nexora.core.events import bus
from nexora.core.profiles import get_profile
from nexora.core.task_engine import TaskEngine, TaskStatus
from nexora.core.ws import hub


class BackgroundWorker:
    def __init__(self, profile: str | None = None):
        self.profile = get_profile(profile or os.getenv("NEXORA_PROFILE"))
        self.tasks = TaskEngine()
        self._tg_offset = 0
        self._dc_after = None
        self._sl_cursor = None
        self._running = False

    async def start(self):
        self._running = True
        hub.bind_loop(asyncio.get_running_loop())
        bus.publish("worker.started", {"profile": self.profile.name})
        while self._running:
            try:
                self._tick_scheduler()
                await self._poll_telegram()
                await self._poll_discord()
                await self._poll_slack()
                await self._run_queued()
            except Exception as e:
                bus.publish("worker.error", {"error": str(e)})
            await asyncio.sleep(self.profile.poll_seconds)

    def stop(self):
        self._running = False

    # -- schedules -----------------------------------------------------------
    def _tick_scheduler(self):
        if self.profile.max_workers < 1:
            return
        from nexora.automation.scheduler import Scheduler
        Scheduler().run_due()

    def _new_goal(self, source: str, text: str, meta: dict) -> None:
        text = (text or "").strip()
        if not text:
            return
        t = self.tasks.create(text)
        bus.publish("channel.task", {"source": source, "task_id": t.id, "goal": text, **meta})

    # -- telegram polling ------------------------------------------------------
    async def _poll_telegram(self):
        token = os.getenv("NEXORA_SECRET_TELEGRAM_TOKEN")
        if not token:
            return
        try:
            r = await asyncio.to_thread(
                httpx.get,
                f"https://api.telegram.org/bot{token}/getUpdates",
                params={"timeout": 0, "offset": self._tg_offset},
                timeout=10,
            )
            for upd in r.json().get("result") or []:
                self._tg_offset = upd["update_id"] + 1
                msg = upd.get("message") or {}
                self._new_goal("telegram", msg.get("text"),
                               {"chat": msg.get("chat", {}).get("id")})
        except Exception:
            pass  # offline behavior: polling silently pauses

    # -- discord polling ---------------------------------------------------------
    async def _poll_discord(self):
        token = os.getenv("NEXORA_SECRET_DISCORD_TOKEN")
        channel = os.getenv("NEXORA_DISCORD_CHANNEL_ID")
        if not token or not channel:
            return
        try:
            r = await asyncio.to_thread(
                httpx.get,
                f"https://discord.com/api/v10/channels/{channel}/messages",
                params={"limit": 20} | ({"after": self._dc_after} if self._dc_after else {}),
                headers={"Authorization": f"Bot {token}"},
                timeout=10,
            )
            for msg in reversed(r.json() or []):
                self._dc_after = msg["id"]
                if msg.get("author", {}).get("bot"):
                    continue
                self._new_goal("discord", msg.get("content"),
                               {"author": msg.get("author", {}).get("username")})
        except Exception:
            pass

    # -- slack polling ------------------------------------------------------------
    async def _poll_slack(self):
        token = os.getenv("NEXORA_SECRET_SLACK_BOT_TOKEN")
        channel = os.getenv("NEXORA_SLACK_CHANNEL_ID")
        if not token or not channel:
            return
        try:
            r = await asyncio.to_thread(
                httpx.get,
                "https://slack.com/api/conversations.history",
                params={"channel": channel,
                        **({"cursor": self._sl_cursor} if self._sl_cursor else {})},
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
            data = r.json()
            self._sl_cursor = data.get("response_metadata", {}).get("next_cursor") or self._sl_cursor
            for msg in reversed(data.get("messages") or []):
                if msg.get("bot_id") or msg.get("subtype"):
                    continue
                self._new_goal("slack", msg.get("text"), {"user": msg.get("user")})
        except Exception:
            pass

    # -- queued task execution ------------------------------------------------------
    async def _run_queued(self):
        pending = self.tasks.list(status=TaskStatus.CREATED.value,
                                  limit=self.profile.max_workers)
        for t in pending:
            if not self._running:
                return
            await self._execute(t)

    async def _execute(self, task):
        from nexora.core.agent import Agent
        from nexora.database import repositories as repo
        from nexora.database.models import Dot

        dot = repo.get_by_id(Dot, task.dot_id) if task.dot_id else None
        if dot is None or not dot.enabled:
            return  # task stays CREATED; another Dot may claim it later
        agent = Agent(dot)
        try:
            await agent.run_task(task)
        except Exception as e:
            self.tasks.set_status(task.id, TaskStatus.FAILED.value, error=str(e))

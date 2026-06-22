"""System, analytics, and token tracking routes for FCC Dashboard."""

import time
from pathlib import Path

import psutil
from fastapi import APIRouter, Request

from config.paths import config_dir_path, server_log_path

from .token_tracking import (
    get_active_sessions,
    get_all_sessions,
    get_daily_usage,
    get_session_detail,
    get_summary,
)

router = APIRouter()

START_TIME = time.time()


@router.get("/admin/api/system/metrics")
async def get_system_metrics(request: Request):
    """Get real-time system metrics."""
    cpu_percent = psutil.cpu_percent(interval=0.1)

    memory = psutil.virtual_memory()
    ram_total = memory.total
    ram_used = memory.used
    ram_percent = memory.percent

    try:
        disk = psutil.disk_usage("/")
        disk_total = disk.total
        disk_used = disk.used
        disk_percent = disk.percent
    except Exception:
        disk_total = disk_used = disk_percent = 0

    process_count = len(psutil.pids())
    uptime_seconds = int(time.time() - START_TIME)

    return {
        "cpu_percent": cpu_percent,
        "ram_total": ram_total,
        "ram_used": ram_used,
        "ram_percent": ram_percent,
        "disk_total": disk_total,
        "disk_used": disk_used,
        "disk_percent": disk_percent,
        "process_count": process_count,
        "uptime_seconds": uptime_seconds,
    }


@router.get("/admin/api/logs")
async def get_logs(request: Request, type: str = "server", limit: int = 100):
    """Read logs from file system."""
    log_dir = config_dir_path() / "logs"

    if type == "rotation":
        path = log_dir / "openrouter_rotation.log"
        if not path.exists():
            path = Path("logs/openrouter_rotation.log")
    else:
        path = server_log_path()
        if not path.exists():
            path = Path("logs/server.log")

    lines = []
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                all_lines = f.readlines()
                lines = all_lines[-limit:] if limit > 0 else all_lines
        except Exception as e:
            lines = [f"Error reading log: {e}"]

    return {"logs": lines, "type": type}


@router.get("/admin/api/analytics")
async def get_analytics(request: Request):
    """Compute analytics from logs and real token data."""
    rotation_log = Path("logs/openrouter_rotation.log")
    rotations = 0
    exhausted = 0

    if rotation_log.exists():
        try:
            with open(rotation_log, encoding="utf-8") as f:
                content = f.read()
                rotations = content.count("Key rotated") + content.count(
                    "Retry performed"
                )
                exhausted = content.count("Key exhausted")
        except Exception:
            pass

    server_log = server_log_path()
    if not server_log.exists():
        server_log = Path("logs/server.log")

    errors = exhausted
    if server_log.exists():
        try:
            with open(server_log, encoding="utf-8") as f:
                content = f.read()
                errors += content.count("ERROR") + content.count("Exception")
        except Exception:
            pass

    summary = get_summary()
    daily = get_daily_usage(7)
    daily.reverse()

    return {
        "requests": summary["total_requests"],
        "tokens": summary["total_tokens"],
        "input_tokens": summary["total_input_tokens"],
        "output_tokens": summary["total_output_tokens"],
        "rotations": rotations,
        "errors": errors,
        "active_sessions": summary["active_sessions"],
        "today_tokens": summary["today_tokens"],
        "today_requests": summary["today_requests"],
        "daily_usage": [
            {
                "date": d["date"],
                "input_tokens": d["input_tokens"],
                "output_tokens": d["output_tokens"],
                "total_tokens": d["input_tokens"] + d["output_tokens"],
                "requests": d["request_count"],
                "sessions": d["session_count"],
            }
            for d in daily
        ],
    }


@router.get("/admin/api/tokens/summary")
async def get_token_summary(request: Request):
    """Get overall token usage summary."""
    return get_summary()


@router.get("/admin/api/tokens/sessions")
async def get_token_sessions(
    request: Request, active_only: bool = False, limit: int = 100
):
    """Get session list with token usage."""
    sessions = get_active_sessions() if active_only else get_all_sessions(limit)
    return {"sessions": sessions}


@router.get("/admin/api/tokens/sessions/{session_id}")
async def get_token_session_detail(session_id: str, request: Request):
    """Get detail for a single session."""
    detail = get_session_detail(session_id)
    if detail is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Session not found")
    return detail


@router.get("/admin/api/tokens/daily")
async def get_token_daily(request: Request, days: int = 30):
    """Get daily token usage breakdown."""
    return {"daily": get_daily_usage(days)}

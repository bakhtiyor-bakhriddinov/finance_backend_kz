import subprocess
from fastapi import APIRouter, HTTPException


settings_router = APIRouter()



@settings_router.post("/restart-bot")
async def restart_bot():
    try:
        completed_process = subprocess.run(
            ["sudo", "/bin/systemctl", "restart", "finance_bot.service"],
            check=True,
            text=True,
            capture_output=True
        )
        return {"message": "Bot service restarted successfully", "stdout": completed_process.stdout}
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Failed to restart bot service: {e.stderr}")


import asyncio
import datetime
import time
import sys
import os
import config
from advanced_scraper import run_advanced_scraper

def log_scheduler(msg):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] [SCHEDULER] {msg}", flush=True)

async def main_scheduler():
    target_time = config.EXECUTION_TIME
    log_scheduler(f"定时任务启动成功。")
    log_scheduler(f"计划执行时间: {target_time}")
    log_scheduler("提示: 请保持此窗口开启以进行自动定时抓取。")

    while True:
        now_str = datetime.datetime.now().strftime("%H:%M")
        
        if now_str == target_time:
            log_scheduler(">>> 到达预定时间，启动自动化采集任务...")
            try:
                # 运行主抓取逻辑
                await run_advanced_scraper()
                log_scheduler("<<< 自动化任务已圆满完成。")
            except Exception as e:
                log_scheduler(f"!!! 任务运行期间出错: {e}")
            
            # 运行完后等待 61 秒，防止在同一分钟内重复触发
            await asyncio.sleep(61)
        else:
            # 每 30 秒检查一次时间，保持唤醒状态
            await asyncio.sleep(30)

if __name__ == "__main__":
    try:
        asyncio.run(main_scheduler())
    except KeyboardInterrupt:
        log_scheduler("定时任务手动停止。")
    except Exception as e:
        log_scheduler(f"严重错误: {e}")

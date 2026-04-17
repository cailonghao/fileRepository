import asyncio
import os
import datetime
import time
import re
import random
import base64
import sys
import csv
import json
import calendar
from playwright.async_api import async_playwright
from dotenv import load_dotenv
import config

def log(msg):
    print(msg, flush=True)

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()
USER_ID = os.getenv("USER_ID")
USER_PWD = os.getenv("USER_PWD")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"

def prepare_api_data(all_data):
    req_list = []
    for row in all_data.values():
        if not row.get("单号") or not row.get("单据状态") or not row.get("凭证日期"):
            continue
        item = {
            "erpCode": row.get("单号"),
            "erpStatusText": row.get("单据状态"),
            "shopErpCode": row.get("客户号"),
            "shopErpName": row.get("客户名称"),
            "beginAgentStatusDate": row.get("凭证日期"),
            "productData": []
        }
        codes = str(row.get("明细编码", "")).split(" | ")
        prices = str(row.get("明细货款", "")).split(" | ")
        for code, price_str in zip(codes, prices):
            if not code or not price_str: continue
            try:
                price = float(price_str.replace(",", "").strip())
                item["productData"].append({"productCode": code.strip(), "price": price})
            except: pass
        req_list.append(item)
    return req_list

def save_to_daily_csv(all_data, file_path):
    if not all_data: return
    try:
        file_exists = os.path.exists(file_path)
        fieldnames = ["单号", "单据状态", "客户号", "客户名称", "凭证日期", "明细编码", "明细货款"]
        with open(file_path, mode='a', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists: writer.writeheader()
            for k in sorted(all_data.keys()):
                writer.writerow({k2: all_data[k].get(k2, "") for k2 in fieldnames})
    except Exception as e:
        log(f"CSV 保存失败: {e}")

def append_execution_report(stats):
    try:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report = []
        report.append(f"\n{'='*50}")
        report.append(f"执行报告 - {now}")
        report.append(f"{'='*50}")
        report.append(f"1. 运行耗时: {stats.get('duration', 'N/A')}")
        report.append(f"2. 处理日期: {stats.get('date_range', 'N/A')}")
        report.append(f"3. 累计采集条数: {stats.get('total_found', 0)}")
        report.append(f"4. 成功同步条数: {stats.get('total_synced', 0)}")
        
        success_rate = 0
        if stats.get('total_found', 0) > 0:
            success_rate = (stats.get('total_synced', 0) / stats.get('total_found', 0)) * 100
        report.append(f"5. 同步成功率: {success_rate:.1f}%")
        
        if stats.get('warnings'):
            report.append(f"\n[警告事项]:")
            for w in stats['warnings']:
                report.append(f" - {w}")
        
        report.append(f"{'='*50}\n")
        
        with open(config.EXECUTION_REPORT_FILE, "a", encoding="utf-8") as f:
            f.write("\n".join(report))
        log(f"√ 执行报告已追加至 {config.EXECUTION_REPORT_FILE}")
    except Exception as e:
        log(f"报告生成失败: {e}")

async def run_advanced_scraper():
    if not USER_ID or not USER_PWD:
        log("错误：登录凭据未配置")
        return

    stats = {
        "start_time": datetime.datetime.now(),
        "total_found": 0,
        "total_synced": 0,
        "warnings": [],
        "date_range": ""
    }

    if os.path.exists(config.DAILY_RECORD_CSV):
        try: os.remove(config.DAILY_RECORD_CSV); log("初始化采集环境。")
        except: pass

    today = datetime.date.today()
    target_day = today.day
    if len(sys.argv) > 1:
        try: target_day = int(sys.argv[1]); log(f"手动指定采集至 {target_day} 号")
        except: pass
    
    stats["date_range"] = f"1号 -> {target_day}号"
    log(f"启动特征码对齐抓取任务: {stats['date_range']}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=UA, viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        # 1. Login
        logged_in = False
        for i in range(3):
            try:
                log(f"身份验证中 ({i+1})...")
                await page.goto(config.LOGIN_URL, timeout=60000)
                await page.fill("input#name", USER_ID)
                await page.fill("input#pwd", USER_PWD)
                await page.click("input#sub")
                await page.wait_for_url("**/home.jsp", timeout=20000)
                log("系统身份验证成功。")
                logged_in = True; break
            except Exception as e: log(f"认证重试: {e}")
        
        if not logged_in: await browser.close(); return

        # 2. Enter 56051
        log("进入 ERP 56051 核心单元...")
        try:
            inp = await page.wait_for_selector("input[placeholder*='功能号']", timeout=15000)
            await inp.fill("56051"); await inp.press("Enter")
            await asyncio.sleep(6)
        except: await browser.close(); return

        # 3. Time Pipeline
        for day in range(1, target_day + 1):
            date_str = today.replace(day=day).strftime("%Y-%m-%d")
            log(f"\n>>>> 任务日期: {date_str} <<<<")

            f = None
            for frame in page.frames:
                if "56051" in frame.url: f = frame; break
            if not f: continue

            try:
                await f.fill("input#beginday", date_str)
                await f.fill("input#endday", date_str)
                await f.evaluate("getOder()")
                await asyncio.sleep(5)
            except: continue

            # 获取当前日期的实际总数
            total_count = 0
            for _ in range(4):
                total_count = await f.evaluate(r"""() => {
                    let tc = 0;
                    document.querySelectorAll('*').forEach(el => {
                        const m = el.textContent.match(/共\s*:\s*(\d+)\s*条/);
                        if (m) tc = parseInt(m[1], 10);
                    });
                    return tc;
                }""")
                if total_count > 0: break
                await asyncio.sleep(2)
            
            if total_count == 0:
                log(f"  [{date_str}] 无数据上报或加载超时")
                continue
            
            log(f"  系统上报总条数: {total_count}")
            all_day_data = {}
            scroll_pos = 0
            
            # B. [Row-ID Join] 基于特征码的异步状态对齐算法
            for attempt in range(45):
                view_batch = await f.evaluate(r"""async () => {
                    const rowStore = {};
                    
                    const getRowId = (tr) => {
                        if (!tr) return null;
                        for (let attr of tr.attributes) {
                           const val = attr.value;
                           if (val && val.includes("Rows[")) {
                               const match = val.match(/Rows\["(.*?)"\]/);
                               if (match) return match[1];
                           }
                        }
                        return null;
                    };

                    const scanToStore = (suffix, field) => {
                        const cells = Array.from(document.querySelectorAll("td")).filter(td => 
                           Array.from(td.classList).some(c => c.endsWith(suffix))
                        );
                        cells.forEach(td => {
                            const tr = td.parentElement;
                            const rid = getRowId(tr);
                            if (!rid || rid.includes("Header") || rid.includes("Total")) return;
                            
                            if (!rowStore[rid]) rowStore[rid] = {};
                            
                            let val = td.textContent.trim();
                            if (!val) {
                                const input = td.querySelector('input, select');
                                if (input) val = input.value.trim();
                            }
                            
                            if (val && !rowStore[rid][field]) {
                                rowStore[rid][field] = val;
                            }
                        });
                    };

                    scanToStore('doccode', 'code');
                    scanToStore('docstatusname', 'status');
                    scanToStore('cltcode', 'cCode');
                    scanToStore('cltname', 'cName');
                    scanToStore('docdate', 'date');

                    const aligned = [];
                    Object.values(rowStore).forEach(v => {
                        // 只有当这一行的“单号”、“状态”和“日期”全部对齐时才视为成功抓取
                        if (v.code && v.code.startsWith('XK') && v.status && v.date) {
                            aligned.push({
                                "单号": v.code, "单据状态": v.status, "客户号": v.cCode || "",
                                "客户名称": v.cName || "", "凭证日期": v.date
                            });
                        }
                    });
                    return aligned;
                }""")

                new_count = 0
                for r in view_batch:
                    if r["单号"] not in all_day_data:
                        all_day_data[r["单号"]] = r
                        new_count += 1
                
                if new_count > 0:
                    log(f"  (扫描 #{attempt+1}) 成功对齐新记录 {new_count} 条，累积: {len(all_day_data)}/{total_count}")
                
                if len(all_day_data) >= total_count:
                    log("  √ 列表数据已完成 100% 对齐抓取")
                    break

                # 执行不规则滚动步进，强制触发各层渲染
                scroll_pos += (400 if attempt % 2 == 0 else 600)
                await f.evaluate(f"() => {{ document.querySelectorAll('.data-grid-container, .MainContent, .TSSectionScroll').forEach(c => c.scrollTop = {scroll_pos}); }}")
                
                # 在收尾阶段给予更多渲染时间
                delay = 1.2 if len(all_day_data) < total_count - 3 else 3.5
                await asyncio.sleep(delay)

                log(f"  ! 警告: 因渲染超时漏采 {total_count - len(all_day_data)} 条记录")
                stats["warnings"].append(f"日期 {date_str} 漏采 {total_count - len(all_day_data)} 条 (渲染超时)")
            
            stats["total_found"] += len(all_day_data)

            # C. Detail Logic (对已审核单据继续深化)
            log(f"  深度提取明细 (目标: {len(all_day_data)} 条)...")
            val_items = list(all_day_data.values())
            for idx, row in enumerate(val_items):
                if row["单据状态"] == "已审核":
                    order_code = row["单号"]
                    where_encoded = base64.b64encode(f"doccode='{order_code}' ".encode("utf-8")).decode("utf-8")
                    detail_url = f"https://gt1989.onbus.cn/app/3687/0/cnzh/56051/5/index.jsp?d2hlcmU9{where_encoded}"
                    det_p = await context.new_page()
                    try:
                        await det_p.goto(detail_url, timeout=12000)
                        await det_p.wait_for_selector("[class*='matcode']", timeout=6000)
                        
                        await det_p.evaluate("""() => {
                             const sc = document.querySelectorAll('.TSGridScroll, .TSSectionScroll');
                             sc.forEach(c => c.scrollLeft = 9999);
                        }""")
                        await asyncio.sleep(1)
                        
                        ret = await det_p.evaluate(r"""() => {
                            const getCol = (suffix) => Array.from(document.querySelectorAll("tr.TSDataRow td"))
                                .filter(td => Array.from(td.classList).some(c => c.replace(/^HideCol\d+/, '') === suffix))
                                .map(td => {
                                    let val = td.textContent.trim();
                                    if (!val) {
                                        let inp = td.querySelector('input, select');
                                        if (inp) val = inp.value.trim();
                                    }
                                    return val;
                                }).filter(Boolean);
                                
                            let codes = getCol('matcode');
                            let moneys = getCol('totalmoney');
                            
                            if (moneys.length > codes.length) moneys = moneys.slice(0, codes.length);
                            return {codes, moneys};
                        }""")
                        row["明细编码"] = " | ".join(ret["codes"])
                        row["明细货款"] = " | ".join(ret["moneys"])
                    except: pass
                    finally: await det_p.close()
                if (idx + 1) % 10 == 0: log(f"    明细进度: {idx+1}/{len(all_day_data)}")

            # D. Commit
            save_to_daily_csv(all_day_data, config.DAILY_RECORD_CSV)
            log("  √ 采集结果已保存到本地")
            
            api_data = prepare_api_data(all_day_data)
            if api_data:
                log(f"  √ 正在通过 API 同步数据 (条数: {len(api_data)})...")
                try:
                    r = await context.request.post(f"{config.JAVA_API_BASE_URL}/batchCalculationEmpKpi/{date_str}", data=api_data)
                    log(f"  API 返回结果: {await r.text()}")
                    stats["total_synced"] += len(api_data)
                except Exception as e: 
                    log(f"  API 同步异常: {e}")
                    stats["warnings"].append(f"日期 {date_str} API 同步失败: {e}")

        stats["duration"] = str(datetime.datetime.now() - stats["start_time"]).split('.')[0]
        append_execution_report(stats)

        log("\n全部采集与同步任务圆满完成。")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_advanced_scraper())

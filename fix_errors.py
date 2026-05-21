#!/usr/bin/env python3
"""
修复 2026-04-24 至今 AI 摘要失败的论文。
- 读取 data/{date}_AI_enhanced_Chinese.jsonl
- 找出 AI.tldr == "Unexpected Error" 的条目
- 用正确的模型重新调用 AI 接口生成摘要
- 更新 JSONL 并重新生成 MD 文件
"""

import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta

import dotenv
from tqdm import tqdm

# 加载 .env 文件
if os.path.exists('.env'):
    dotenv.load_dotenv()

# ============ 配置 ============
START_DATE = date(2026, 5, 5)
END_DATE = date(2026, 5, 21)  # 可修改为更晚的日期
MAX_WORKERS = int(os.environ.get("MAX_WORKERS", "3"))
API_DELAY = int(os.environ.get("API_DELAY_SECONDS", "1"))
MODEL_NAME = os.environ.get("MODEL_NAME", "deepseek-chat")
LANGUAGE = os.environ.get("LANGUAGE", "Chinese")
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
AI_DIR = os.path.join(os.path.dirname(__file__), "ai")
TO_MD_DIR = os.path.join(os.path.dirname(__file__), "to_md")
# =============================

# 将 ai 目录加入 sys.path 以便导入 Structure
sys.path.insert(0, AI_DIR)
from structure import Structure

from langchain_openai import ChatOpenAI
from langchain.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)


def load_prompts():
    """加载 system 和 template 提示词"""
    system_path = os.path.join(AI_DIR, "system.txt")
    template_path = os.path.join(AI_DIR, "template.txt")
    with open(system_path, "r", encoding="utf-8") as f:
        system = f.read()
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()
    return system, template


def build_chain(model_name: str):
    """构建 LangChain 调用链"""
    system, template = load_prompts()
    llm = ChatOpenAI(model=model_name).with_structured_output(
        Structure, method="function_calling"
    )
    prompt_template = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(system),
        HumanMessagePromptTemplate.from_template(template=template),
    ])
    return prompt_template | llm


def process_single(chain, item: dict) -> dict:
    """处理单条论文，返回带 AI 字段的完整条目"""
    try:
        response: Structure = chain.invoke({
            "language": LANGUAGE,
            "content": item["summary"],
        })
        item["AI"] = response.model_dump()
        time.sleep(API_DELAY)
    except Exception as e:
        print(f"  [ERROR] {item.get('id', '?')}: {e}", file=sys.stderr)
        item["AI"] = {
            "tldr": "Unexpected Error",
            "motivation": str(e)[:500],
            "method": "N/A",
            "result": "N/A",
            "conclusion": "N/A",
        }
        time.sleep(API_DELAY)
    return item


def regenerate_md(date_str: str):
    """根据增强 JSONL 重新生成 MD 文件"""
    ai_file = os.path.join(DATA_DIR, f"{date_str}_AI_enhanced_{LANGUAGE}.jsonl")
    if not os.path.exists(ai_file):
        print(f"  [SKIP] 增强文件不存在: {ai_file}", file=sys.stderr)
        return False

    # 读取增强 JSONL
    data = []
    with open(ai_file, "r", encoding="utf-8") as f:
        for line in f:
            data.append(json.loads(line))

    # 读取模板
    template_path = os.path.join(TO_MD_DIR, "paper_template.md")
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    # 分类排序（与原 convert.py 一致）
    preference = os.environ.get("CATEGORIES", "cs.CV, cs.CL").split(",")
    preference = [x.strip() for x in preference]

    def rank(cate):
        if cate in preference:
            return preference.index(cate)
        return len(preference)

    categories = sorted(set(item["categories"][0] for item in data), key=rank)
    cnt = {c: sum(1 for item in data if item["categories"][0] == c) for c in categories}

    markdown = "<div id=toc></div>\n\n# Table of Contents\n\n"
    for cate in categories:
        markdown += f"- [{cate}](#{cate}) [Total: {cnt[cate]}]\n"

    idx = 1
    for cate in categories:
        markdown += f"\n\n<div id='{cate}'></div>\n\n"
        markdown += f"# {cate} [[Back]](#toc)\n\n"
        items_in_cate = [item for item in data if item["categories"][0] == cate]
        markdown += "\n\n".join(
            template.format(
                title=item["title"],
                authors=",".join(item["authors"]),
                summary=item["summary"],
                url=item["abs"],
                tldr=item["AI"]["tldr"],
                motivation=item["AI"]["motivation"],
                method=item["AI"]["method"],
                result=item["AI"]["result"],
                conclusion=item["AI"]["conclusion"],
                cate=item["categories"][0],
                idx=i,
            )
            for i, item in enumerate(items_in_cate, start=idx)
        )
        idx += len(items_in_cate)

    md_path = os.path.join(DATA_DIR, f"{date_str}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(markdown)
    print(f"  [OK] 已生成 {md_path}")
    return True


def main():
    print(f"=== 修复 AI 摘要脚本 ===", file=sys.stderr)
    print(f"日期范围: {START_DATE} ~ {END_DATE}", file=sys.stderr)
    print(f"模型: {MODEL_NAME}", file=sys.stderr)
    print(f"并发数: {MAX_WORKERS}", file=sys.stderr)
    print(f"API 延迟: {API_DELAY}s", file=sys.stderr)
    print(file=sys.stderr)

    chain = build_chain(MODEL_NAME)
    current = START_DATE
    total_fixed = 0

    while current <= END_DATE:
        date_str = current.strftime("%Y-%m-%d")
        enhanced_file = os.path.join(DATA_DIR, f"{date_str}_AI_enhanced_{LANGUAGE}.jsonl")

        if not os.path.exists(enhanced_file):
            print(f"[{date_str}] 增强文件不存在，跳过", file=sys.stderr)
            current += timedelta(days=1)
            continue

        # 读取增强 JSONL
        with open(enhanced_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        data = [json.loads(line) for line in lines]

        # 找出失败的条目
        failed_items = [
            (i, item) for i, item in enumerate(data)
            if item.get("AI", {}).get("tldr") == "Unexpected Error"
        ]

        if not failed_items:
            print(f"[{date_str}] 没有失败的条目，跳过", file=sys.stderr)
            current += timedelta(days=1)
            continue

        print(f"[{date_str}] 发现 {len(failed_items)} 条失败，共 {len(data)} 条", file=sys.stderr)

        # 并行重试失败条目
        fixed_data = [None] * len(failed_items)
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_pos = {
                executor.submit(process_single, chain, item): pos
                for pos, (_, item) in enumerate(failed_items)
            }
            for future in tqdm(
                as_completed(future_to_pos),
                total=len(failed_items),
                desc=f"  {date_str}",
                file=sys.stderr,
            ):
                pos = future_to_pos[future]
                try:
                    fixed_data[pos] = future.result()
                except Exception as e:
                    print(f"  [FATAL] pos {pos}: {e}", file=sys.stderr)

        # 更新原数据
        for pos, (orig_idx, _) in enumerate(failed_items):
            if fixed_data[pos] is not None:
                data[orig_idx] = fixed_data[pos]

        # 写回 JSONL
        with open(enhanced_file, "w", encoding="utf-8") as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        print(f"  [OK] 已更新 {enhanced_file}", file=sys.stderr)

        # 重新生成 MD
        regenerate_md(date_str)

        still_failed = sum(
            1 for item in data
            if item.get("AI", {}).get("tldr") == "Unexpected Error"
        )
        fixed_count = len(failed_items) - still_failed
        total_fixed += fixed_count
        print(f"  [INFO] 修复 {fixed_count} 条，仍有 {still_failed} 条失败", file=sys.stderr)
        print(file=sys.stderr)

        current += timedelta(days=1)

    print(f"=== 完成，共修复 {total_fixed} 条 ===", file=sys.stderr)


if __name__ == "__main__":
    main()

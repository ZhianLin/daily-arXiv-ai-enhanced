#!/usr/bin/env python3
"""
arXiv链接抓取脚本
用于抓取用户提供的arXiv链接，并将论文信息追加到指定日期的MD文件中
集成AI增强功能生成智能TL;DR摘要
"""

import argparse
import re
import sys
import os
import json
from datetime import datetime
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
import time

# AI增强功能导入
try:
    import dotenv
    import langchain_core.exceptions
    from langchain_openai import ChatOpenAI
    from langchain.prompts import (
        ChatPromptTemplate,
        SystemMessagePromptTemplate,
        HumanMessagePromptTemplate,
    )
    from ai.structure import Structure
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    print("警告: AI增强功能依赖未安装，将使用简单的TL;DR生成方式")


class ArxivLinkFetcher:
    def __init__(self, use_ai=True, language="Chinese"):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.arxiv_pattern = re.compile(r'https?://arxiv\.org/(?:abs|pdf)/(\d+\.\d+)(?:v\d+)?(?:\.pdf)?')
        self.use_ai = use_ai and AI_AVAILABLE
        self.language = language
        self.ai_chain = None
        self.api_delay_seconds = 0
        
        # 初始化AI功能
        if self.use_ai:
            self._init_ai_enhancement()
    
    def _init_ai_enhancement(self):
        """初始化AI增强功能"""
        try:
            # 加载环境变量
            if os.path.exists('.env'):
                dotenv.load_dotenv()
            
            # 读取延迟时间配置
            self.api_delay_seconds = int(os.environ.get("API_DELAY_SECONDS", 0))
            
            # 确保延迟时间是正整数
            if not isinstance(self.api_delay_seconds, int) or self.api_delay_seconds < 0:
                print(f"警告: 无效的API_DELAY_SECONDS值 '{self.api_delay_seconds}'，使用默认值0秒")
                self.api_delay_seconds = 0
            
            # 读取模型名称配置
            model_name = os.environ.get("MODEL_NAME", "deepseek-v4-flash")
            
            # 读取模板和系统提示
            template_path = "ai/template.txt"
            system_path = "ai/system.txt"
            
            if os.path.exists(template_path) and os.path.exists(system_path):
                template = open(template_path, "r", encoding='utf-8').read()
                system = open(system_path, "r", encoding='utf-8').read()
                
                # 创建AI链
                system_message = SystemMessagePromptTemplate.from_template(system)
                human_message = HumanMessagePromptTemplate.from_template(template)
                chat_prompt = ChatPromptTemplate.from_messages([system_message, human_message])
                
                # 初始化ChatOpenAI（从环境变量读取配置）
                llm = ChatOpenAI(
                    model=model_name,
                    temperature=0.7,
                    model_kwargs={"extra_body": {"thinking": {"type": "disabled"}}}
                )
                self.ai_chain = chat_prompt | llm.with_structured_output(Structure, method="function_calling")
                
                print("AI增强功能初始化成功")
            else:
                print("警告: 找不到AI模板文件，将使用简单的TL;DR生成方式")
                self.use_ai = False
                
        except Exception as e:
            print(f"AI增强功能初始化失败: {e}")
            self.use_ai = False
        
    def extract_arxiv_id(self, url: str) -> Optional[str]:
        """从URL中提取arXiv ID"""
        match = self.arxiv_pattern.search(url)
        return match.group(1) if match else None
    
    def fetch_paper_info(self, arxiv_id: str) -> Optional[Dict]:
        """从arXiv获取论文信息"""
        try:
            # 首先尝试使用arXiv API获取论文信息
            api_url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
            response = requests.get(api_url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                # 解析XML响应
                soup = BeautifulSoup(response.content, 'xml')
                entry = soup.find('entry')
                
                if entry:
                    # 提取论文信息
                    title = entry.find('title').text.strip().replace('\n', ' ')
                    authors = [author.find('name').text for author in entry.find_all('author')]
                    summary = entry.find('summary').text.strip().replace('\n', ' ')
                    published = entry.find('published').text
                    
                    # 提取分类信息
                    categories = []
                    for category in entry.find_all('category'):
                        cat_term = category.get('term')
                        if cat_term:
                            categories.append(cat_term)
                    
                    # 获取主分类的完整名称
                    primary_category = categories[0] if categories else 'Unknown'
                    category_name = self.get_category_name(primary_category)
                    
                    return {
                        'id': arxiv_id,
                        'title': title,
                        'authors': authors,
                        'summary': summary,
                        'published': published,
                        'categories': categories,
                        'primary_category': primary_category,
                        'category_name': category_name,
                        'url': f"https://arxiv.org/abs/{arxiv_id}"
                    }
            
            # 如果API失败，尝试从HTML页面抓取
            print(f"API获取失败，尝试从HTML页面抓取论文 {arxiv_id}...")
            return self.fetch_from_html(arxiv_id)
            
        except Exception as e:
            print(f"获取论文 {arxiv_id} 信息失败: {e}")
            return None
    
    def fetch_from_html(self, arxiv_id: str) -> Optional[Dict]:
        """从arXiv HTML页面抓取论文信息"""
        try:
            # 访问arXiv论文页面
            page_url = f"https://arxiv.org/abs/{arxiv_id}"
            response = requests.get(page_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 提取标题
            title_element = soup.find('h1', class_='title mathjax')
            title = title_element.text.replace('Title:', '').strip() if title_element else f"Paper {arxiv_id}"
            
            # 提取作者
            authors = []
            authors_div = soup.find('div', class_='authors')
            if authors_div:
                for author in authors_div.find_all('a'):
                    authors.append(author.text.strip())
            
            # 提取摘要
            abstract_div = soup.find('blockquote', class_='abstract mathjax')
            summary = abstract_div.text.replace('Abstract:', '').strip() if abstract_div else "No abstract available"
            
            # 提取分类
            categories = []
            subjects_div = soup.find('td', class_='tablecell subjects')
            if subjects_div:
                # 提取主分类
                primary_subject = subjects_div.find('span', class_='primary-subject')
                if primary_subject:
                    primary_category = primary_subject.text.strip()
                    # 从括号中提取分类代码
                    match = re.search(r'\(([^)]+)\)', primary_category)
                    if match:
                        primary_category = match.group(1)
                    categories.append(primary_category)
                
                # 提取其他分类
                for subject in subjects_div.find_all('a'):
                    cat_text = subject.text.strip()
                    match = re.search(r'\(([^)]+)\)', cat_text)
                    if match:
                        categories.append(match.group(1))
            
            # 获取主分类
            primary_category = categories[0] if categories else 'cs.CV'  # 默认设为cs.CV
            category_name = self.get_category_name(primary_category)
            
            # 提取发布日期
            published = datetime.now().strftime('%Y-%m-%d')
            date_element = soup.find('div', class_='submission-history')
            if date_element:
                # 从提交历史中提取日期
                date_match = re.search(r'(\d{1,2} \w{3,4} \d{4})', date_element.text)
                if date_match:
                    try:
                        published = datetime.strptime(date_match.group(1), '%d %b %Y').strftime('%Y-%m-%d')
                    except:
                        pass
            
            return {
                'id': arxiv_id,
                'title': title,
                'authors': authors,
                'summary': summary,
                'published': published,
                'categories': categories,
                'primary_category': primary_category,
                'category_name': category_name,
                'url': page_url
            }
            
        except Exception as e:
            print(f"从HTML页面获取论文 {arxiv_id} 信息失败: {e}")
            return None
    
    def get_category_name(self, category_code: str) -> str:
        """获取分类代码对应的完整名称"""
        category_map = {
            'cs.CV': 'Computer Vision and Pattern Recognition',
            'cs.CL': 'Computation and Language',
            'cs.LG': 'Machine Learning',
            'cs.AI': 'Artificial Intelligence',
            'cs.MM': 'Multimedia',
            'cs.GR': 'Graphics',
            'cs.RO': 'Robotics',
            'cs.IR': 'Information Retrieval',
            'cs.CR': 'Cryptography and Security',
            'eess.AS': 'Audio and Speech Processing',
            'eess.IV': 'Image and Video Processing',
            'eess.SP': 'Signal Processing',
            'stat.ML': 'Machine Learning (Statistics)',
            'math.OC': 'Optimization and Control',
            'q-bio': 'Quantitative Biology',
            'q-fin': 'Quantitative Finance'
        }
        return category_map.get(category_code, category_code)
    
    def format_paper_for_md(self, paper: Dict, index: int) -> str:
        """将论文信息格式化为MD格式（包含完整的AI增强字段）"""
        authors_str = ', '.join(paper['authors'])
        
        # 获取完整的AI分析结果
        ai_analysis = self.get_ai_analysis(paper['summary'])
        
        md_content = f"""### [{index}] [{paper['title']}]({paper['url']})
*{authors_str}*

Main category: {paper['primary_category']}

Task: {ai_analysis['task']}


<details>
  <summary>Details</summary>
Motivation: {ai_analysis['motivation']}

Method: {ai_analysis['method']}

Result: {ai_analysis['result']}

Conclusion: {ai_analysis['conclusion']}

Abstract: {paper['summary']}

</details>
"""
        return md_content
    
    def generate_tldr(self, summary: str) -> str:
        """生成简化的TL;DR摘要（兼容旧版本）"""
        ai_analysis = self.get_ai_analysis(summary)
        return ai_analysis.get('task', '')
    
    def get_ai_analysis(self, summary: str) -> Dict[str, str]:
        """获取完整的AI分析结果"""
        if self.use_ai and self.ai_chain:
            try:
                print("正在使用AI生成完整分析...")
                response: Structure = self.ai_chain.invoke({
                    "language": self.language,
                    "content": summary
                })
                
                # 添加API延迟
                if self.api_delay_seconds > 0:
                    time.sleep(self.api_delay_seconds)
                
                # 返回完整的AI分析结果，将tldr字段映射为task以保持与JSONL和MD文件一致
                analysis = {
                    'task': response.tldr,
                    'motivation': response.motivation,
                    'method': response.method,
                    'result': response.result,
                    'conclusion': response.conclusion
                }
                print(f"AI分析生成成功: {response.tldr[:50]}...")
                return analysis
                
            except Exception as e:
                print(f"AI分析生成失败: {e}，将使用简单截取方式")
                # 回退到简单截取方式
                return self._generate_simple_analysis(summary)
        else:
            # 使用简单截取方式
            return self._generate_simple_analysis(summary)
    
    def _generate_simple_tldr(self, summary: str) -> str:
        """简单的TL;DR生成方式"""
        if len(summary) <= 200:
            return summary
        return summary[:200] + "..."
    
    def _generate_simple_analysis(self, summary: str) -> Dict[str, str]:
        """简单的AI分析生成方式"""
        tldr = self._generate_simple_tldr(summary)
        return {
            'task': tldr,
            'motivation': 'N/A',
            'method': 'N/A',
            'result': 'N/A',
            'conclusion': 'N/A'
        }
    
    def process_links(self, links: List[str]) -> List[Dict]:
        """处理arXiv链接列表"""
        papers = []
        
        for link in links:
            arxiv_id = self.extract_arxiv_id(link)
            if not arxiv_id:
                print(f"警告: 无法从链接 {link} 提取arXiv ID")
                continue
            
            print(f"正在获取论文 {arxiv_id} 的信息...")
            paper_info = self.fetch_paper_info(arxiv_id)
            
            if paper_info:
                papers.append(paper_info)
                print(f"成功获取: {paper_info['title']}")
            else:
                print(f"获取失败: {arxiv_id}")
            
            # 添加延迟以避免过于频繁的请求
            time.sleep(3)
        
        return papers
    
    def append_to_md_file(self, papers: List[Dict], target_date: str, data_dir: str = "data") -> bool:
        """将论文信息追加到指定日期的MD文件"""
        if not papers:
            print("没有论文需要添加")
            return False
        
        # 确保数据目录存在
        os.makedirs(data_dir, exist_ok=True)
        
        # 构建目标文件路径
        md_file = os.path.join(data_dir, f"{target_date}.md")
        
        # 按分类组织论文
        papers_by_category = {}
        for paper in papers:
            category = paper['primary_category']
            if category not in papers_by_category:
                papers_by_category[category] = []
            papers_by_category[category].append(paper)
        
        # 读取现有文件内容（如果存在）
        existing_content = ""
        existing_categories = set()
        
        if os.path.exists(md_file):
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    existing_content = f.read()
                
                # 提取现有的分类信息
                category_pattern = re.compile(r'<div id=\'([^\']+)\'></div>')
                existing_categories = set(category_pattern.findall(existing_content))
                
            except Exception as e:
                print(f"读取现有文件失败: {e}")
                existing_content = ""
        
        # 生成新的内容
        new_content = ""
        
        # 如果没有现有内容，创建新的文件结构
        if not existing_content:
            new_content += "<div id=toc></div>\n\n# Table of Contents\n\n"
            
            # 添加目录
            for category in sorted(papers_by_category.keys()):
                count = len(papers_by_category[category])
                new_content += f"- [{category}](#{category}) [Total: {count}]\n"
            new_content += "\n\n"
        
        # 为每个分类添加论文
        for category in sorted(papers_by_category.keys()):
            if category not in existing_categories:
                new_content += f"<div id='{category}'></div>\n\n"
                new_content += f"# {category} [[Back]](#toc)\n\n"
            
            # 为每个论文添加信息
            for i, paper in enumerate(papers_by_category[category], 1):
                new_content += self.format_paper_for_md(paper, i)
                new_content += "\n"
        
        # 将新内容追加到文件
        try:
            with open(md_file, 'a', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"成功将 {len(papers)} 篇论文添加到 {md_file}")
            return True
            
        except Exception as e:
            print(f"写入文件失败: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description='抓取arXiv链接并追加到指定日期的MD文件中')
    parser.add_argument('links', nargs='+', help='一个或多个arXiv链接')
    parser.add_argument('--date', type=str, required=True, help='目标日期 (格式: YYYY-MM-DD)')
    parser.add_argument('--data-dir', type=str, default='data', help='数据目录路径 (默认: data)')
    parser.add_argument('--no-ai', action='store_true', help='禁用AI增强功能')
    parser.add_argument('--language', type=str, default='Chinese', choices=['Chinese', 'English'], help='TL;DR语言 (默认: Chinese)')
    
    args = parser.parse_args()
    
    # 验证日期格式
    try:
        datetime.strptime(args.date, '%Y-%m-%d')
    except ValueError:
        print("错误: 日期格式不正确，请使用 YYYY-MM-DD 格式")
        sys.exit(1)
    
    # 创建抓取器实例
    fetcher = ArxivLinkFetcher(use_ai=not args.no_ai, language=args.language)
    
    # 处理链接
    print(f"开始处理 {len(args.links)} 个arXiv链接...")
    papers = fetcher.process_links(args.links)
    
    if papers:
        # 追加到MD文件
        success = fetcher.append_to_md_file(papers, args.date, args.data_dir)
        if success:
            print(f"任务完成！成功处理了 {len(papers)} 篇论文")
        else:
            print("任务失败：无法写入文件")
            sys.exit(1)
    else:
        print("没有成功获取任何论文信息")
        sys.exit(1)


if __name__ == "__main__":
    main()
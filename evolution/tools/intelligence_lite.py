"""
Intelligence Tool - Lite Version (无需 RSSHub)

当无法使用 Docker/RSSHub 时的降级方案，直接调用各源的官方 API。
"""

import httpx
import json
from typing import List, Dict, Any
from datetime import datetime
import re
from html import unescape

try:
    from defusedxml.ElementTree import fromstring as safe_xml_fromstring
except ImportError:
    import xml.etree.ElementTree as ET
    def safe_xml_fromstring(text):
        return ET.fromstring(text)


class IntelligenceSourceLite:
    """轻量级信息源 - 直接调用 API"""
    
    def __init__(self):
        self.timeout = 15
        
    def _clean_html(self, text: str) -> str:
        """清理 HTML 标签"""
        if not text:
            return ""
        text = re.sub(r'<[^>]+>', '', text)
        text = unescape(text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    # ========== arXiv ==========
    def fetch_arxiv_ml(self) -> List[Dict[str, Any]]:
        """arXiv - Machine Learning"""
        url = "http://export.arxiv.org/api/query?search_query=cat:cs.LG&sortBy=submittedDate&max_results=10"
        try:
            resp = httpx.get(url, timeout=self.timeout)
            root = safe_xml_fromstring(resp.text)
            
            items = []
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            for entry in root.findall(".//atom:entry", ns)[:5]:
                title = entry.findtext("atom:title", "", ns).strip()
                summary = entry.findtext("atom:summary", "", ns).strip()
                link = entry.findtext("atom:id", "", ns)
                
                items.append({
                    "title": title,
                    "description": summary[:200] + "..." if len(summary) > 200 else summary,
                    "link": link,
                    "source": "arXiv ML"
                })
            return items
        except Exception as e:
            print(f"❌ arXiv ML 获取失败: {e}")
            return []
    
    def fetch_arxiv_cv(self) -> List[Dict[str, Any]]:
        """arXiv - Computer Vision"""
        url = "http://export.arxiv.org/api/query?search_query=cat:cs.CV&sortBy=submittedDate&max_results=10"
        try:
            resp = httpx.get(url, timeout=self.timeout)
            root = safe_xml_fromstring(resp.text)
            
            items = []
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            for entry in root.findall(".//atom:entry", ns)[:5]:
                title = entry.findtext("atom:title", "", ns).strip()
                summary = entry.findtext("atom:summary", "", ns).strip()
                link = entry.findtext("atom:id", "", ns)
                
                items.append({
                    "title": title,
                    "description": summary[:200] + "..." if len(summary) > 200 else summary,
                    "link": link,
                    "source": "arXiv CV"
                })
            return items
        except Exception as e:
            print(f"❌ arXiv CV 获取失败: {e}")
            return []
    
    # ========== GitHub ==========
    def fetch_github_trending(self) -> List[Dict[str, Any]]:
        """GitHub Trending - Python"""
        url = "https://api.github.com/search/repositories?q=language:python&sort=stars&order=desc&per_page=10"
        try:
            resp = httpx.get(url, timeout=self.timeout, headers={
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "Evolution-AI-Agent"
            })
            data = resp.json()
            
            items = []
            for repo in data.get("items", [])[:5]:
                items.append({
                    "title": repo["full_name"],
                    "description": repo.get("description", "")[:200],
                    "link": repo["html_url"],
                    "source": "GitHub Trending"
                })
            return items
        except Exception as e:
            print(f"❌ GitHub Trending 获取失败: {e}")
            return []
    
    # ========== Hacker News ==========
    def fetch_hackernews(self) -> List[Dict[str, Any]]:
        """Hacker News - Best Stories"""
        try:
            # 获取最佳故事 ID
            resp = httpx.get("https://hacker-news.firebaseio.com/v0/beststories.json", timeout=self.timeout)
            story_ids = resp.json()[:10]
            
            items = []
            for story_id in story_ids[:5]:
                story_resp = httpx.get(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json", timeout=self.timeout)
                story = story_resp.json()
                
                items.append({
                    "title": story.get("title", ""),
                    "description": story.get("text", "")[:200] if story.get("text") else "",
                    "link": story.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
                    "source": "Hacker News"
                })
            return items
        except Exception as e:
            print(f"❌ Hacker News 获取失败: {e}")
            return []
    
    # ========== Reddit ==========
    def fetch_reddit_ml(self) -> List[Dict[str, Any]]:
        """Reddit - r/MachineLearning"""
        url = "https://www.reddit.com/r/MachineLearning/hot.json?limit=10"
        try:
            resp = httpx.get(url, timeout=self.timeout, headers={
                "User-Agent": "Evolution-AI-Agent"
            })
            data = resp.json()
            
            items = []
            for post in data["data"]["children"][:5]:
                post_data = post["data"]
                items.append({
                    "title": post_data["title"],
                    "description": self._clean_html(post_data.get("selftext", ""))[:200],
                    "link": f"https://reddit.com{post_data['permalink']}",
                    "source": "Reddit ML"
                })
            return items
        except Exception as e:
            print(f"❌ Reddit ML 获取失败: {e}")
            return []
    
    # ========== BBC News ==========
    def fetch_bbc_tech(self) -> List[Dict[str, Any]]:
        """BBC News - Technology (RSS)"""
        url = "http://feeds.bbci.co.uk/news/technology/rss.xml"
        try:
            resp = httpx.get(url, timeout=self.timeout)
            root = safe_xml_fromstring(resp.text)
            
            items = []
            for item in root.findall(".//item")[:5]:
                title = item.findtext("title", "")
                description = self._clean_html(item.findtext("description", ""))
                link = item.findtext("link", "")
                
                items.append({
                    "title": title,
                    "description": description[:200] + "..." if len(description) > 200 else description,
                    "link": link,
                    "source": "BBC Tech"
                })
            return items
        except Exception as e:
            print(f"❌ BBC Tech 获取失败: {e}")
            return []
    
    # ========== 聚合所有源 ==========
    def fetch_all(self) -> List[Dict[str, Any]]:
        """获取所有配置的源"""
        all_items = []
        
        print("📡 开始拉取信息源...")
        
        # 学术
        print("  🎓 arXiv ML...", end=" ")
        items = self.fetch_arxiv_ml()
        print(f"✅ {len(items)} 条")
        all_items.extend(items)
        
        print("  🎓 arXiv CV...", end=" ")
        items = self.fetch_arxiv_cv()
        print(f"✅ {len(items)} 条")
        all_items.extend(items)
        
        # 技术
        print("  💻 GitHub Trending...", end=" ")
        items = self.fetch_github_trending()
        print(f"✅ {len(items)} 条")
        all_items.extend(items)
        
        print("  💻 Hacker News...", end=" ")
        items = self.fetch_hackernews()
        print(f"✅ {len(items)} 条")
        all_items.extend(items)
        
        # 社交
        print("  🐦 Reddit ML...", end=" ")
        items = self.fetch_reddit_ml()
        print(f"✅ {len(items)} 条")
        all_items.extend(items)
        
        # 新闻
        print("  📰 BBC Tech...", end=" ")
        items = self.fetch_bbc_tech()
        print(f"✅ {len(items)} 条")
        all_items.extend(items)
        
        print(f"\n✅ 总计获取 {len(all_items)} 条信息")
        return all_items


def test_lite_version():
    """测试轻量级版本"""
    print("=" * 60)
    print("🧪 测试 Intelligence Tool Lite Version")
    print("=" * 60)
    print()
    
    source = IntelligenceSourceLite()
    items = source.fetch_all()
    
    print("\n" + "=" * 60)
    print("📊 获取结果预览")
    print("=" * 60)
    
    for i, item in enumerate(items[:10], 1):
        print(f"\n{i}. [{item['source']}] {item['title']}")
        print(f"   {item['description'][:100]}...")
        print(f"   🔗 {item['link']}")
    
    if len(items) > 10:
        print(f"\n... 还有 {len(items) - 10} 条信息")
    
    return items


if __name__ == "__main__":
    test_lite_version()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Profile README 自动更新脚本

该脚本用于自动获取 GitHub 仓库的 Releases 和统计信息，
并更新 README.md 文件中的相应内容。

@author: zhi.qu
@date: 2025-12-11
"""

import pathlib
import re
import os
import logging
from github import Github, Auth

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 项目根目录
root = pathlib.Path(__file__).parent.resolve()

# GitHub Token，从环境变量获取
TOKEN = os.environ.get("GH_TOKEN", "")


def replace_chunk(content, marker, chunk, inline=False):
    """
    替换 README 中指定标记之间的内容
    
    Args:
        content: README 文件内容
        marker: 标记名称，如 'github_stats'
        chunk: 要替换的新内容
        inline: 是否为行内替换（不添加换行符）
    
    Returns:
        替换后的内容
    """
    logger.info(f"正在替换标记: {marker}")
    
    pattern = re.compile(
        r"<!--\s*{}\s*starts\s*-->.*?<!--\s*{}\s*ends\s*-->".format(marker, marker),
        re.DOTALL,
    )
    
    if not inline:
        chunk = "\n{}\n".format(chunk)
    
    replacement = "<!-- {} starts -->{}<!-- {} ends -->".format(marker, chunk, marker)
    
    return pattern.sub(replacement, content)


def fetch_releases(oauth_token):
    """
    获取用户所有仓库的最新 Releases
    
    Args:
        oauth_token: GitHub OAuth Token
    
    Returns:
        包含 Release 信息的列表
    """
    logger.info("开始获取 Releases 信息...")
    
    try:
        auth = Auth.Token(oauth_token)
        g = Github(auth=auth)
        user = g.get_user()
        releases = []
        
        # 遍历用户拥有的所有仓库
        for repo in user.get_repos(type='owner'):
            # 跳过 fork 的仓库
            if repo.fork:
                continue
                
            try:
                # 获取仓库的 releases
                repo_releases = list(repo.get_releases())
                
                if repo_releases:
                    logger.info(f"从仓库 {repo.name} 获取到 {len(repo_releases)} 个 releases")
                    
                    for release in repo_releases[:5]:  # 每个仓库最多取5个
                        releases.append({
                            "repo": repo.name,
                            "repo_url": repo.html_url,
                            "description": repo.description or "",
                            "release": release.title.replace(repo.name, "").strip() if release.title else release.tag_name,
                            "published_at": release.published_at.strftime("%Y-%m-%d") if release.published_at else "",
                            "url": release.html_url,
                        })
                        
            except Exception as e:
                logger.warning(f"获取仓库 {repo.name} 的 releases 时出错: {e}")
                continue
        
        logger.info(f"共获取到 {len(releases)} 个 releases")
        return releases
        
    except Exception as e:
        logger.error(f"获取 Releases 时发生错误: {e}")
        return []


def extract_current_stats(readme_content):
    """
    从 README 中提取当前的统计信息作为备用
    
    Args:
        readme_content: README 文件内容
    
    Returns:
        包含 followers、stars、forks 的字典
    """
    logger.info("提取当前统计信息作为备用...")
    
    match = re.search(
        r'(\d{1,3}(?:,\d{3})*)\s*followers,\s*(\d{1,3}(?:,\d{3})*)\s*stars,\s*(\d{1,3}(?:,\d{3})*)\s*forks',
        readme_content
    )
    
    if match:
        return {
            'followers': int(match.group(1).replace(',', '')),
            'stars': int(match.group(2).replace(',', '')),
            'forks': int(match.group(3).replace(',', ''))
        }
    
    return {'followers': 0, 'stars': 0, 'forks': 0}


def fetch_github_stats(oauth_token, current_stats=None):
    """
    获取 GitHub 统计信息（followers、stars、forks）
    
    Args:
        oauth_token: GitHub OAuth Token
        current_stats: 当前统计信息作为备用
    
    Returns:
        包含统计信息的字典
    """
    logger.info("开始获取 GitHub 统计信息...")
    
    try:
        auth = Auth.Token(oauth_token)
        g = Github(auth=auth)
        user = g.get_user()
        
        total_stars = 0
        total_forks = 0
        
        # 遍历用户拥有的所有仓库
        for repo in user.get_repos(type='owner'):
            # 跳过 fork 的仓库
            if not repo.fork:
                total_stars += repo.stargazers_count
                total_forks += repo.forks_count
        
        stats = {
            'stars': total_stars,
            'forks': total_forks,
            'followers': user.followers
        }
        
        logger.info(f"统计信息: {stats['followers']} followers, {stats['stars']} stars, {stats['forks']} forks")
        
        return stats
        
    except Exception as e:
        logger.error(f"获取 GitHub 统计信息时发生错误: {e}")
        return current_stats or {'stars': 0, 'forks': 0, 'followers': 0}


def main():
    """
    主函数，执行 README 更新流程
    """
    logger.info("========== 开始更新 README ==========")
    
    # 读取 README 文件
    readme_path = root / "README.md"
    
    if not readme_path.exists():
        logger.error("README.md 文件不存在！")
        return
    
    readme_contents = readme_path.open(encoding='utf-8').read()
    
    # 提取当前统计信息作为备用
    current_stats = extract_current_stats(readme_contents)
    
    # 获取并更新 Releases
    releases = fetch_releases(TOKEN)
    releases.sort(key=lambda r: r["published_at"], reverse=True)
    
    # 每个仓库只保留最新的一个 release
    seen_repos = set()
    unique_releases = []
    
    for release in releases:
        if release["repo"] not in seen_repos:
            seen_repos.add(release["repo"])
            unique_releases.append(release)
    
    # 生成 Releases 的 Markdown
    if unique_releases:
        releases_md = "<br>".join([
            "• [{repo} {release}]({url}) - {published_at}".format(**release)
            for release in unique_releases[:6]  # 最多显示6个
        ])
    else:
        releases_md = "• No releases yet"
    
    rewritten = replace_chunk(readme_contents, "recent_releases", releases_md)
    
    # 获取并更新 GitHub 统计信息
    stats = fetch_github_stats(TOKEN, current_stats)
    stats_text = "{:,} followers, {:,} stars, {:,} forks".format(
        stats['followers'],
        stats['stars'],
        stats['forks']
    )
    
    rewritten = replace_chunk(rewritten, "github_stats", stats_text, inline=True)
    
    # 写入更新后的 README
    readme_path.open("w", encoding='utf-8').write(rewritten)
    
    logger.info("========== README 更新完成 ==========")


if __name__ == "__main__":
    main()


# -*- coding: utf-8 -*-
"""
build_readme.py 测试用例

@author: zhi.qu
@date: 2025-12-11
"""

import unittest
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from build_readme import replace_chunk, extract_current_stats


class TestReplaceChunk(unittest.TestCase):
    """测试 replace_chunk 函数"""
    
    def test_replace_chunk_basic(self):
        """测试基本的内容替换功能"""
        content = "Hello <!-- test starts -->old content<!-- test ends --> World"
        result = replace_chunk(content, "test", "new content", inline=True)
        self.assertIn("new content", result)
        self.assertNotIn("old content", result)
    
    def test_replace_chunk_with_newlines(self):
        """测试带换行的内容替换"""
        content = "Hello <!-- test starts -->old<!-- test ends --> World"
        result = replace_chunk(content, "test", "new content", inline=False)
        self.assertIn("\nnew content\n", result)
    
    def test_replace_chunk_inline(self):
        """测试行内替换模式"""
        content = "Stats: <!-- stats starts -->0<!-- stats ends --> total"
        result = replace_chunk(content, "stats", "100", inline=True)
        self.assertEqual(result, "Stats: <!-- stats starts -->100<!-- stats ends --> total")
    
    def test_replace_chunk_preserves_other_content(self):
        """测试替换时保留其他内容"""
        content = "Before <!-- marker starts -->content<!-- marker ends --> After"
        result = replace_chunk(content, "marker", "replaced", inline=True)
        self.assertTrue(result.startswith("Before"))
        self.assertTrue(result.endswith("After"))


class TestExtractCurrentStats(unittest.TestCase):
    """测试 extract_current_stats 函数"""
    
    def test_extract_stats_basic(self):
        """测试基本的统计信息提取"""
        content = "Hello 100 followers, 200 stars, 50 forks World"
        result = extract_current_stats(content)
        self.assertEqual(result['followers'], 100)
        self.assertEqual(result['stars'], 200)
        self.assertEqual(result['forks'], 50)
    
    def test_extract_stats_with_commas(self):
        """测试带千位分隔符的统计信息提取"""
        content = "Hello 1,234 followers, 56,789 stars, 1,000 forks World"
        result = extract_current_stats(content)
        self.assertEqual(result['followers'], 1234)
        self.assertEqual(result['stars'], 56789)
        self.assertEqual(result['forks'], 1000)
    
    def test_extract_stats_no_match(self):
        """测试无匹配时返回默认值"""
        content = "No stats here"
        result = extract_current_stats(content)
        self.assertEqual(result['followers'], 0)
        self.assertEqual(result['stars'], 0)
        self.assertEqual(result['forks'], 0)
    
    def test_extract_stats_large_numbers(self):
        """测试大数字的提取"""
        content = "Profile: 10,000 followers, 100,000 stars, 50,000 forks"
        result = extract_current_stats(content)
        self.assertEqual(result['followers'], 10000)
        self.assertEqual(result['stars'], 100000)
        self.assertEqual(result['forks'], 50000)


class TestReadmeFormat(unittest.TestCase):
    """测试 README 格式相关功能"""
    
    def test_readme_markers_exist(self):
        """测试 README 中的标记是否存在"""
        readme_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'README.md'
        )
        
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查必要的标记
        self.assertIn("<!-- github_stats starts -->", content)
        self.assertIn("<!-- github_stats ends -->", content)
        self.assertIn("<!-- recent_releases starts -->", content)
        self.assertIn("<!-- recent_releases ends -->", content)


if __name__ == '__main__':
    unittest.main()


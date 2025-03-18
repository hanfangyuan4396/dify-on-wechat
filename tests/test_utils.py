import unittest
from common.utils import remove_markdown_symbol

class TestMarkdownSymbolRemoval(unittest.TestCase):
    def test_empty_text(self):
        """测试空文本"""
        self.assertEqual(remove_markdown_symbol(""), "")
        self.assertEqual(remove_markdown_symbol(None), None)
    
    def test_heading_removal(self):
        """测试标题符号移除"""
        test_cases = [
            ("# 一级标题", "一级标题"),
            ("## 二级标题", "二级标题"),
            ("### 三级标题", "三级标题"),
            ("#不是标题", "#不是标题"),  # 没有空格，不应该移除
        ]
        for input_text, expected in test_cases:
            self.assertEqual(remove_markdown_symbol(input_text), expected)
    
    def test_list_removal(self):
        """测试列表符号移除"""
        test_cases = [
            ("- 列表项1", "列表项1"),
            ("  - 缩进列表项", "缩进列表项"),
            ("-不是列表项", "-不是列表项"),  # 没有空格，不应该移除
        ]
        for input_text, expected in test_cases:
            self.assertEqual(remove_markdown_symbol(input_text), expected)
    
    def test_emphasis_removal(self):
        """测试强调符号移除"""
        test_cases = [
            ("**加粗文本**", "加粗文本"),
            ("*斜体文本*", "斜体文本"),
            ("**混合的*强调*文本**", "混合的强调文本"),
            ("普通**部分加粗**文本", "普通部分加粗文本"),
        ]
        for input_text, expected in test_cases:
            self.assertEqual(remove_markdown_symbol(input_text), expected)
    
    def test_mixed_format_removal(self):
        """测试混合格式移除"""
        input_text = """# 标题
- 列表项1
  - 列表项2
**加粗的列表项**
普通文本中的*斜体*
"""
        expected = """标题
列表项1
列表项2
加粗的列表项
普通文本中的斜体"""
        self.assertEqual(remove_markdown_symbol(input_text), expected)

if __name__ == '__main__':
    unittest.main() 
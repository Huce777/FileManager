import os
import re
import jieba

# 10 建立文本文件“不良文本信息”过滤功能。事先建立一个不良文本标本文件，
# 可以通过标本文件对被过滤文件比对，根据匹配概率阈值，确定被过滤文件的
# “放行”度。字符串匹配可以采用正则表达式方式，也可以用普通“模式匹配”方式
# 分词后的逻辑判断（谓词演算）可以提高过滤的准确度。

class BadTextManager:
    def __init__(self, bad_text_file="bad_texts.txt"):
        self.bad_text_file = bad_text_file
        self.bad_texts = self.load_bad_texts()

    def load_bad_texts(self):
        """加载不良文本标本文件"""
        if not os.path.exists(self.bad_text_file):
            return []
        with open(self.bad_text_file, "r", encoding="utf-8") as f:
            return [line.strip() for line in f.readlines()]

    def add_bad_text(self, bad_text):
        """添加不良文本到标本文件"""
        if bad_text not in self.bad_texts:
            with open(self.bad_text_file, "a", encoding="utf-8") as f:
                f.write(bad_text + "\n")
            self.bad_texts.append(bad_text)
            return True
        return False

    def remove_bad_text(self, bad_text):
        """从标本文件中移除不良文本"""
        if bad_text in self.bad_texts:
            self.bad_texts.remove(bad_text)
            with open(self.bad_text_file, "w", encoding="utf-8") as f:
                f.write("\n".join(self.bad_texts))
            return True
        return False

    def get_bad_texts(self):
        """获取所有不良文本"""
        return self.bad_texts


class TextFilter:
    def __init__(self, bad_text_manager):
        self.bad_text_manager = bad_text_manager

    def filter_text(self, text, threshold=0.3):
        """
        对文本进行过滤
        :param text: 待过滤的文本
        :param threshold: 匹配概率阈值
        :return: 过滤结果，包括是否放行、匹配概率、匹配的不良文本等信息
        """
        result = {
            "allow_pass": True,
            "match_prob": 0.0,
            "matched_bad_texts": []
        }

        bad_texts = self.bad_text_manager.get_bad_texts()
        if not bad_texts:
            return result

        # 分词处理
        segmented_text = self.segment_text(text)

        # 计算匹配概率
        match_count = 0
        total_bad_text_length = sum(len(bad_text) for bad_text in bad_texts)

        for bad_text in bad_texts:
            # 使用正则表达式匹配
            pattern = re.compile(re.escape(bad_text))
            matches = pattern.findall(segmented_text)
            if matches:
                match_count += len(bad_text) * len(matches)
                result["matched_bad_texts"].append({
                    "bad_text": bad_text,
                    "count": len(matches)
                })

        result["match_prob"] = match_count / total_bad_text_length if total_bad_text_length != 0 else 0.0

        # 判断是否放行
        if result["match_prob"] > threshold:
            result["allow_pass"] = False

        return result

    def segment_text(self, text):
        """
        对文本进行分词处理
        :param text: 待分词的文本
        :return: 分词后的文本
        """
        return " ".join(jieba.cut(text))


class PredicateCalculus:
    def __init__(self):
        self.rules = []

    def add_rule(self, rule):
        """
        添加谓词演算规则
        :param rule: 规则，格式为 {"condition": 条件表达式, "action": 动作}
        """
        self.rules.append(rule)

    def evaluate(self, filter_result):
        """
        根据谓词演算规则对过滤结果进行综合判断
        :param filter_result: 文本过滤结果
        :return: 综合判断后的放行结果
        """
        for rule in self.rules:
            try:
                # 动态执行条件表达式
                condition = eval(rule["condition"], {}, {"result": filter_result})
                if condition:
                    # 执行动作
                    action = rule["action"]
                    if action == "allow":
                        return True
                    elif action == "deny":
                        return False
            except:
                continue

        # 如果没有规则匹配，则按照原始过滤结果放行
        return filter_result["allow_pass"]

"""
def main():
    # 初始化不良文本管理器
    bad_text_manager = BadTextManager()

    # 添加一些不良文本标本（实际应用中应从文件加载）
    bad_text_manager.add_bad_text("垃圾")
    bad_text_manager.add_bad_text("广告")
    bad_text_manager.add_bad_text("诈骗")

    # 初始化文本过滤器
    text_filter = TextFilter(bad_text_manager)

    # 初始化谓词演算
    predicate_calculus = PredicateCalculus()
    predicate_calculus.add_rule({
        "condition": "result['match_prob'] > 0.5 and len(result['matched_bad_texts']) >= 2",
        "action": "deny"
    })
    predicate_calculus.add_rule({
        "condition": "result['match_prob'] < 0.2",
        "action": "allow"
    })

    # 测试文本
    test_text = "这是一个垃圾广告，请不要相信"

    # 过滤文本
    filter_result = text_filter.filter_text(test_text)

    print("原始过滤结果:", filter_result)

    # 综合判断
    final_decision = predicate_calculus.evaluate(filter_result)

    print("最终放行结果:", final_decision)
"""

"""
不良文本管理器 (BadTextManager):
负责管理不良文本标本文件，包括加载、添加和移除不良文本。
不良文本存储在文本文件中，每行一个不良文本。
文本过滤器 (TextFilter):
实现了文本过滤的核心功能，包括分词、匹配和计算匹配概率。
使用正则表达式对不良文本进行匹配。
分词使用了结巴分词库，提高匹配的准确性。
谓词演算 (PredicateCalculus):
用于定义和执行谓词演算规则。
规则以条件表达式和动作为格式，条件表达式可以访问过滤结果中的字段。
根据规则对过滤结果进行综合判断，决定最终是否放行。
主程序 (main):
初始化不良文本管理器、文本过滤器和谓词演算。
添加一些不良文本标本和谓词演算规则。
对测试文本进行过滤和综合判断，输出结果。
使用示例
运行程序后，会初始化不良文本管理器，添加一些不良文本标本。
对测试文本进行过滤，计算匹配概率和匹配的不良文本。
根据谓词演算规则对过滤结果进行综合判断，得出最终放行结果。
"""
"""
if __name__ == "__main__":
    main()
"""
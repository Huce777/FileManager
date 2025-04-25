import datetime
import time
from typing import Dict, List, Optional, Tuple

class CallRecord:
    """来电记录类"""
    def __init__(self, number: str, time: datetime.datetime, duration: int, is_caller: bool):
        """
        初始化来电记录
        :param number: 来电号码
        :param time: 来电时间
        :param duration: 通话时长（秒）
        :param is_caller: 是否为主叫
        """
        self.number = number
        self.time = time
        self.duration = duration
        self.is_caller = is_caller

    def __str__(self):
        return f"来电号码: {self.number}, 时间: {self.time}, 时长: {self.duration}s, {'主叫' if self.is_caller else '被叫'}"


class PhoneBook:
    """电话号码簿类"""
    def __init__(self):
        """初始化电话号码簿"""
        self.contacts = {}  # 存储联系人，key为电话号码，value为联系人姓名

    def add_contact(self, number: str, name: str):
        """
        添加联系人
        :param number: 联系人电话号码
        :param name: 联系人姓名
        """
        self.contacts[number] = name

    def remove_contact(self, number: str):
        """
        移除联系人
        :param number: 联系人电话号码
        """
        if number in self.contacts:
            del self.contacts[number]

    def get_contact_name(self, number: str) -> Optional[str]:
        """
        获取联系人姓名
        :param number: 联系人电话号码
        :return: 联系人姓名，如果不存在则返回None
        """
        return self.contacts.get(number)


class HarassmentPhoneBook:
    """骚扰电话簿类"""
    def __init__(self):
        """初始化骚扰电话簿"""
        self.harassment_numbers = set()  # 存储骚扰电话号码

    def add_harassment_number(self, number: str):
        """
        添加骚扰电话号码
        :param number: 骚扰电话号码
        """
        self.harassment_numbers.add(number)

    def remove_harassment_number(self, number: str):
        """
        移除骚扰电话号码
        :param number: 骚扰电话号码
        """
        if number in self.harassment_numbers:
            self.harassment_numbers.remove(number)

    def is_harassment_number(self, number: str) -> bool:
        """
        判断号码是否为骚扰电话
        :param number: 电话号码
        :return: 如果是骚扰电话返回True，否则返回False
        """
        return number in self.harassment_numbers


class CallAnalyzer:
    """来电分析器类"""
    def __init__(self, phone_book: PhoneBook, harassment_phone_book: HarassmentPhoneBook):
        """
        初始化来电分析器
        :param phone_book: 用户的电话号码簿
        :param harassment_phone_book: 骚扰电话簿
        """
        self.phone_book = phone_book
        self.harassment_phone_book = harassment_phone_book
        self.call_records = []  # 存储来电记录

    def add_call_record(self, call_record: CallRecord):
        """
        添加来电记录
        :param call_record: 来电记录
        """
        self.call_records.append(call_record)

    def analyze_incoming_call(self, number: str) -> Tuple[bool, str]:
        """
        分析来电是否为骚扰电话
        :param number: 来电号码
        :return: 元组，第一个元素表示是否为骚扰电话，第二个元素为分析结果描述
        """
        # 检查是否在骚扰电话簿中
        if self.harassment_phone_book.is_harassment_number(number):
            return True, "该号码在骚扰电话簿中，可能是骚扰电话。"

        # 检查是否在用户号码簿中
        contact_name = self.phone_book.get_contact_name(number)
        if contact_name:
            return False, f"该号码属于您的联系人 {contact_name}，不是骚扰电话。"

        # 检查来电频率（简单示例：如果同一号码在1小时内来电超过3次，则认为可能是骚扰电话）
        current_time = datetime.datetime.now()
        one_hour_ago = current_time - datetime.timedelta(hours=1)
        call_count = sum(1 for record in self.call_records if record.number == number and record.time >= one_hour_ago)

        if call_count >= 3:
            return True, f"该号码在1小时内来电 {call_count} 次，可能是骚扰电话。"

        # 其他情况暂时认为不是骚扰电话
        return False, "该号码未被识别为骚扰电话。"


class HarassmentCallInterceptor:
    """骚扰电话拦截器类"""
    def __init__(self, call_analyzer: CallAnalyzer):
        """
        初始化骚扰电话拦截器
        :param call_analyzer: 来电分析器
        """
        self.call_analyzer = call_analyzer

    def intercept_call(self, number: str):
        """
        拦截来电
        :param number: 来电号码
        """
        is_harassment, analysis_result = self.call_analyzer.analyze_incoming_call(number)
        if is_harassment:
            print(f"警告：{analysis_result}")
            choice = input("是否接听该电话？(y/n): ").strip().lower()
            if choice != 'y':
                print("已自动挂断骚扰电话。")
                return
        print("正在接听电话...")

def analyze_incoming_call(number):
    phone_book = PhoneBook()
    phone_book.add_contact("18094683305", "华正扬")
    phone_book.add_contact("19155816653", "朱俊杰")
    phone_book.add_contact("15216132061", "李晓宇")
    phone_book.add_contact("15110278853", "胡博")
    phone_book.add_contact("16601123742", "吴家同")
    phone_book.add_contact("18950493590", "杨皓")
    phone_book.add_contact("18210381185", "肖梓敏")
    phone_book.add_contact("13381355622", "刘子源")

    harassment_phone_book = HarassmentPhoneBook()
    harassment_phone_book.add_harassment_number("006523938479")
    harassment_phone_book.add_harassment_number("0575-10086")
    harassment_phone_book.add_harassment_number("18483065214")
    harassment_phone_book.add_harassment_number("17684344712")
    harassment_phone_book.add_harassment_number("01050972547")
    harassment_phone_book.add_harassment_number("4001725995")
    harassment_phone_book.add_harassment_number("96683")
    harassment_phone_book.add_harassment_number("0061447374439")
    harassment_phone_book.add_harassment_number("10684861816528000009")
    harassment_phone_book.add_harassment_number("10688173079354")
    harassment_phone_book.add_harassment_number("8651267962487")
    harassment_phone_book.add_harassment_number("10100566")
    harassment_phone_book.add_harassment_number("18483065214")
    harassment_phone_book.add_harassment_number("19841701886")
    harassment_phone_book.add_harassment_number("15810593701")
    harassment_phone_book.add_harassment_number("13240401524")
    harassment_phone_book.add_harassment_number("13141293472")
    harassment_phone_book.add_harassment_number("19537514705")
    harassment_phone_book.add_harassment_number("17310305903")
    harassment_phone_book.add_harassment_number("")
    harassment_phone_book.add_harassment_number("13718290191")
    harassment_phone_book.add_harassment_number("15311196274")
    harassment_phone_book.add_harassment_number("17001284120")
    harassment_phone_book.add_harassment_number("18810937902")
    harassment_phone_book.add_harassment_number("18811399861")
    harassment_phone_book.add_harassment_number("13641200443")
    harassment_phone_book.add_harassment_number("18401166344")
    harassment_phone_book.add_harassment_number("13810975146")
    harassment_phone_book.add_harassment_number("18401180435")
    harassment_phone_book.add_harassment_number("153301876676")
    harassment_phone_book.add_harassment_number("18811562931")
    harassment_phone_book.add_harassment_number("159104715584")
    harassment_phone_book.add_harassment_number("19810252618")
    harassment_phone_book.add_harassment_number("19290180737")

    call_analyzer = CallAnalyzer(phone_book, harassment_phone_book)

    current_time = datetime.datetime.now()
    call_record = CallRecord(number, current_time, 0, True)
    call_analyzer.add_call_record(call_record)

    return call_analyzer.analyze_incoming_call(number)

    # harassment_phone_book = HarassmentPhoneBook()
    # for num in [
    #     "13700137000", "13600136000", "13500135000", "13600136000", "13500135000","006523938479", "18483065214", "17684344712", "01050972547", "4001725995", "96683",
    #     "0061447374439", "10684861816528000009", "10688173079354", "8651267962487", "10100566",
    #     "18483065214", "19841701886", "15810593701", "13240401524", "13141293472", "19537514705",
    #     "17310305903", "13718290191", "15311196274", "17001284120", "18810937902", "18811399861",
    #     "13641200443", "18401166344", "13810975146", "18401180435", "153301876676", "18811562931",
    #     "159104715584", "19810252618", "19290180737","      ","0575-10086",
    # ];
    #     try:
    #         harassment_phone_book.add_harassment_number(num)
    #     except ValueError:
    #         print(f"跳过无效的骚扰电话号码: {num}")
    # call_analyzer = CallAnalyzer(phone_book,harassment_phone_book)
    #

# # 测试代码
# if __name__ == "__main__":
#     # 初始化号码簿和骚扰电话簿
#     phone_book = PhoneBook()
#     harassment_phone_book = HarassmentPhoneBook()
#
#     # 添加联系人
#     phone_book.add_contact("13800138000", "朋友A")
#     phone_book.add_contact("13900139000", "家人B")
#
#     # 添加骚扰电话号码
#     harassment_phone_book.add_harassment_number("13700137000")
#     harassment_phone_book.add_harassment_number("13600136000")
#
#     # 初始化来电分析器和拦截器
#     call_analyzer = CallAnalyzer(phone_book, harassment_phone_book)
#     call_interceptor = HarassmentCallInterceptor(call_analyzer)
#
#     # 模拟来电
#     test_numbers = [
#         "13800138000",  # 联系人号码
#         "13700137000",  # 骚扰电话号码
#         "13500135000",  # 未知号码
#         "13600136000",  # 骚扰电话号码
#         "13500135000",  # 未知号码，模拟多次来电
#         "13500135000",  # 未知号码，模拟多次来电
#         "13500135000"   # 未知号码，模拟多次来电
#     ]
#
#     for number in test_numbers:
#         print(f"\n模拟来电: {number}")
#         call_record = CallRecord(number, datetime.datetime.now(), 0, True)
#         call_analyzer.add_call_record(call_record)
#         call_interceptor.intercept_call(number)
#         time.sleep(1)  # 模拟时间流逝

"""
初始化号码簿和骚扰电话簿：创建PhoneBook和HarassmentPhoneBook实例，并添加联系人和骚扰电话号码。
创建来电分析器和拦截器：使用号码簿和骚扰电话簿创建CallAnalyzer和HarassmentCallInterceptor实例。
模拟来电：通过循环模拟多个来电，每个来电都会被分析和拦截。
"""
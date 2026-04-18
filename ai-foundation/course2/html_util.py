import re
from math import trunc

import unicodedata


def clear_html_tags(text: str) -> str:
    regex_pattern = r"<.*?>"
    text = re.sub(regex_pattern, "", text)
    text = re.sub(" ", " ", text)  # Replace non-breaking space.
    text = re.sub("&", "&", text)  # Replace "&" with "&".
    text = re.sub("<", "<", text)  # Replace "<" with "<".
    text = re.sub(">", ">", text)  # Replace ">" with ">".
    return text


#
# Category	Meaning	Common sub-codes & examples
# L*	Lu = 大写字母 (A)， Ll = 小写字母 (a)， Lt = 首字母大写 (ǅ)， Lm = 修饰符 (ʰ)， Lo = 其他字母 (汉, ע)
# N*	Nd = decimal digits (0-9, ٠–٩), No = other numbers (½, Ⅻ)
# P*	Po = 其他标点符号（!，?）， Pd = 破折号（—）， Ps / Pf / Pe = 起始/结束/终止括号
# S*	Sm = 数学符号（±，√）， Sc = 货币符号（₦，$）， Sk = 修饰符（ˆ）， So = 其他符号（😊，⭐）
# Z*	Zs = 空格， Zl = 行， Zp = 段落
# C*	Cc = 控制代码（换行符、制表符）， Cf = 格式标记（零宽度连接符）， Cs = 代理符， Co / Cn = 私用或未分配
#
# 处理表情符号，可以删除，也可用描述性标签（<emoji_sad>,<emogi_happy>）
# 处理话题标签。可以直接删除“#” 提取文本
# 处理特殊（货币符号等）可以使用<money> 替代
def clear_unicode(text: str) -> str:
    categories_to_keep = {"L", "N"}

    keep = []
    for ch in text:
        do_keep = ch.isspace()
        if not do_keep:
            for cate in categories_to_keep:
                if unicodedata.category(ch).startswith(cate):
                    do_keep = True
                    break
        if do_keep:
            keep.append(ch)

    return "".join(keep)



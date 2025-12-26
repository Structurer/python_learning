# 示例1：ASCII编码转字符
ascii_code = 65
char = chr(ascii_code)
print(f"chr({ascii_code}) → '{char}'")  # 输出：chr(65) → 'A'
# 解释：65是大写字母A的ASCII编码


# 示例2：Unicode编码转中文字符
unicode_code = 20013
cn_char = chr(unicode_code)
print(f"chr({unicode_code}) → '{cn_char}'")  # 输出：chr(20013) → '中'
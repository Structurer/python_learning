# 定义复数
comp_num = 2 + 3j
# 1. 提取实部（浮点数）
real_part = comp_num.real
print(f"复数 {comp_num} 的实部：{real_part}，类型：{type(real_part)}")  # 输出：2.0，<class 'float'>
# 2. 实部转整数（向零取整）
real_int = int(real_part)
print(f"实部转整数：{real_int}，类型：{type(real_int)}")  # 输出：2，<class 'int'>
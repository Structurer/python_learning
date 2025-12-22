from decimal import Decimal, getcontext

# --------------------------
# 场景1：普通浮点数的精度问题
# --------------------------
print("=== 普通浮点数（float）的精度问题 ===")
a_float = 0.1
b_float = 0.2
sum_float = a_float + b_float
print(f"0.1 + 0.2 = {sum_float} （实际应为0.3，但float存在二进制转换误差）")

# --------------------------
# 场景2：decimal模块的高精度计算
# --------------------------
print("\n=== decimal模块的高精度计算 ===")

# 1. 基础加法（精确表示）
a_dec = Decimal('0.1')
b_dec = Decimal('0.2')
sum_dec = a_dec + b_dec
print(f"0.1 + 0.2 = {sum_dec} （精确计算，无误差）")

# 2. 控制有效数字位数（解决浮点数累积误差）
# 例：多次累加0.1，对比float和decimal
print("\n--- 多次累加0.1的对比 ---")
# float累加（误差累积）
float_total = 0.0
for _ in range(10):
    float_total += 0.1
print(f"float累加10次0.1 = {float_total} （存在累积误差）")

# decimal累加（精确无误差）
getcontext().prec = 20  # 设置足够精度
dec_total = Decimal('0.0')
for _ in range(10):
    dec_total += Decimal('0.1')
print(f"decimal累加10次0.1 = {dec_total} （精确无误差）")

# 3. 自定义精度与四舍五入模式
print("\n--- 自定义精度与四舍五入 ---")
# 设置有效数字精度为6位
getcontext().prec = 6
c = Decimal('123.456789')
d = Decimal('987.654321')
product = c * d
print(f"123.456789 * 987.654321（精度6位）= {product}")

# 调整精度为10位，重新计算
getcontext().prec = 10
product_high_prec = c * d
print(f"123.456789 * 987.654321（精度10位）= {product_high_prec}")

# 4. 金融场景：精确到分（避免金钱计算误差）
print("\n--- 金融场景（精确到小数点后2位） ---")
price = Decimal('9.99')  # 单价
quantity = Decimal('3')   # 数量
total = price * quantity
# 四舍五入到小数点后2位（模拟货币计算）
total_rounded = total.quantize(Decimal('0.00'))
print(f"9.99 * 3 = {total} → 四舍五入到分：{total_rounded}")
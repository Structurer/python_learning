from decimal import Decimal, getcontext
from decimal import InvalidOperation

# 设置Decimal的精度（保留10位小数）
getcontext().prec = 28

def calculator_precise(expression):
    """基于decimal库的高精度计算器"""
    try:
        # 将表达式中的数字转换为Decimal类型
        # 替换表达式中的运算符前后的数字为Decimal实例
        # 简单处理：通过字符串替换将数字包装为Decimal()
        # 注意：此方法仅适用于简单表达式（数字、+、-、*、/、()）
        expr = expression
        # 匹配数字（整数、小数、负数）并替换为Decimal(数字)
        import re
        expr = re.sub(r'(\d+\.?\d*|-?\d+\.?\d*)', r'Decimal("\1")', expr)
        # 执行转换后的表达式
        result = eval(expr)
        return f"{expression} = {result}"
    except InvalidOperation as e:
        return f"数值错误：{str(e)}"
    except Exception as e:
        return f"输入错误：{str(e)}"


# 使用示例
if __name__ == "__main__":
    print("\n高精度计算器（decimal库）")
    while True:
        expr = input("请输入计算式（输入'q'退出）：")
        if expr.lower() == 'q':
            break
        print(calculator_precise(expr))
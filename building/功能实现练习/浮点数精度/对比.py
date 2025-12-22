def calculator_basic(expression):
    """基于Python内置运算的计算器"""
    try:
        # 直接使用eval计算表达式，注意：实际应用中需限制输入以避免安全风险
        result = eval(expression)
        # 处理浮点数精度问题，保留6位小数
        if isinstance(result, float):
            result = round(result, 6)
        return f"{expression} = {result}"
    except Exception as e:
        return f"输入错误：{str(e)}"


# 使用示例
if __name__ == "__main__":
    print("基础计算器（内置运算）")
    while True:
        expr = input("请输入计算式（输入'q'退出）：")
        if expr.lower() == 'q':
            break
        print(calculator_basic(expr))
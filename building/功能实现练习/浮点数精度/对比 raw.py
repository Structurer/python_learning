def calculator_raw(expression):
    """不处理精度问题，直接返回原生计算结果"""
    try:
        # 不做任何精度修正，直接返回eval的原始结果
        result = eval(expression)
        return f"{expression} = {result}"
    except Exception as e:
        return f"输入错误：{str(e)}"


# 使用示例
if __name__ == "__main__":
    print("原始计算器（不处理精度问题）")
    while True:
        expr = input("请输入计算式（输入'q'退出）：")
        if expr.lower() == 'q':
            break
        print(calculator_raw(expr))
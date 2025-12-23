from fractions import Fraction
import re

def fraction_calculator():
    print("===== 分数精确计算器 =====")
    print("支持操作：+ - * /")
    print("支持输入格式：小数(0.5)、分数(1/2)、整数(3)")
    print("输入 'quit' 退出程序\n")
    
    while True:
        # 获取用户输入
        expr = input("请输入计算式（例：1/2 + 0.3）：").strip()
        if expr.lower() == "quit":
            print("计算器已退出")
            break
        
        # 拆分表达式：支持 数 运算符 数 的格式
        pattern = r"(\S+)\s*([+\-*/])\s*(\S+)"
        match = re.match(pattern, expr)
        if not match:
            print("输入格式错误！请按 数 运算符 数 的格式输入\n")
            continue
        
        num1_str, op, num2_str = match.groups()
        
        # 将输入转为 Fraction 类型
        try:
            # 处理分数格式
            def to_fraction(s):
                if "/" in s:
                    numerator, denominator = s.split("/")
                    return Fraction(int(numerator), int(denominator))
                else:
                    # 处理小数和整数
                    return Fraction(s)
            
            num1 = to_fraction(num1_str)
            num2 = to_fraction(num2_str)
            
            # 执行运算
            if op == "+":
                res = num1 + num2
            elif op == "-":
                res = num1 - num2
            elif op == "*":
                res = num1 * num2
            elif op == "/":
                if num2 == 0:
                    print("错误：除数不能为0\n")
                    continue
                res = num1 / num2
            else:
                print("不支持的运算符！\n")
                continue
            
            # 输出结果（同时显示分数和小数参考）
            print(f"计算结果：{expr} = {res} （小数参考：{float(res)}\n）")
        
        except ValueError as e:
            print(f"输入错误：{e}\n")
        except Exception as e:
            print(f"程序异常：{e}\n")

if __name__ == "__main__":
    fraction_calculator()
from decimal import Decimal, getcontext
from functools import wraps

# 设置Decimal的精度（保留20位有效数字）
getcontext().prec = 20

def decimalize(func):
    """装饰器：自动将函数参数转为Decimal类型后再计算"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # 转换位置参数：将所有数字转为Decimal
        new_args = []
        for arg in args:
            if isinstance(arg, (int, float)):
                new_args.append(Decimal(str(arg)))  # 用str中转避免浮点误差
            else:
                new_args.append(arg)  # 非数字类型不转换
        
        # 转换关键字参数
        new_kwargs = {}
        for k, v in kwargs.items():
            if isinstance(v, (int, float)):
                new_kwargs[k] = Decimal(str(v))
            else:
                new_kwargs[k] = v
        
        # 执行原函数（此时参数已转为Decimal）
        return func(*new_args, **new_kwargs)
    return wrapper

# ----------------------
# 正常编写代码（无需显式写Decimal）
# ----------------------

# 1. 按常规方式定义变量（无需写Decimal）
a = 0.1
b = 0.2

# 2. 用装饰器修饰计算函数
@decimalize
def add(x, y):
    return x + y

# 3. 直接调用函数（实际会自动转为Decimal计算）
result = add(a, b)
print(f"0.1 + 0.2 = {result}")  # 输出精确结果：0.3（而非浮点数的0.30000000000000004）


# 更复杂的计算示例
@decimalize
def calculate(x, y):
    return (x + y) * (x - y)  # 自动转为Decimal计算

c = 0.3
d = 0.1
print(calculate(c, d))  # 输出精确结果：0.08（而非浮点数的0.08000000000000002）
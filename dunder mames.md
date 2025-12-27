# dunder name 完整分类详解（含官方英文名+核心用途）
所有 dunder name 官方统一统称 **dunder names**（缩写自 double underscore names），官方按使用场景+功能细分3大核心类别，覆盖所有内置 dunder，每个类别标注 官方英文名+核心示例+用途，无冗余纯干货，适配Python3.x 全版本，新手也能快速对应使用。
## 一、 核心通用定义
1.  官方总称呼：**dunder names**（通用简称）、**special names**（官方全称，涵盖所有 __xxx__ 形式标识符）
2.  细分官方命名：按功能拆分2类专属官方名，是总分类下的精准叫法
    - 特殊方法（类中带括号的 __xxx__()）：**special method names**（官方核心叫法，最常用）
    - 特殊属性（模块/类/实例中不带括号的 __xxx__）：**special attributes**（官方精准叫法）


## 二、 分类1：类相关 dunder（核心大类，官方名：special method names/special attributes）
面向对象核心，占所有 dunder 的80%以上，分「特殊方法」「特殊属性」，仅作用于 类/实例 对象，是自定义类扩展内置行为的核心。
### （一） 类的特殊方法（special method names）：带括号，可自定义/内置实现
均为 `def __xxx__(self,...):` 格式，要么Python内置类型自带（如 list.__add__），要么可在自定义类中重写，实现内置语法行为（如运算、打印、初始化等）。
| 序号 | dunder 名称 | 官方关联说明 | 核心用途（通俗+精准） | 示例场景 |
|------|-------------|--------------|------------------------|----------|
| 1 | `__init__` | 最基础的 special method | 实例初始化，创建对象时自动调用，初始化实例属性 | `class A: def __init__(self, x): self.x = x` |
| 2 | `__str__` | string representation method | 实例的「用户友好型字符串输出」，`print(实例)`/`str(实例)` 时调用 | 自定义打印实例的展示格式，返回普通字符串 |
| 3 | `__repr__` | official representation method | 实例的「官方/调试型字符串输出」，`repr(实例)`/终端直接输实例时调用 | 供开发者调试，要求返回可还原对象的字符串（官方推荐） |
| 4 | `__add__` | arithmetic special method | 加法运算符重载，`实例1 + 实例2` 时调用 | 让自定义类支持 `+` 运算，如自定义Point类实现坐标相加 |
| 5 | `__sub__` | arithmetic special method | 减法运算符重载，`-` 运算时调用 | 对应 `-`，用法同 `__add__` |
| 6 | `__mul__` | arithmetic special method | 乘法运算符重载，`*` 运算时调用 | 对应 `*`，支持自定义乘法逻辑 |
| 7 | `__getitem__` | sequence/mapping special method | 下标取值重载，`实例[索引]` 时调用 | 让自定义类支持列表/字典式下标取值，适配序列/映射类型 |
| 8 | `__len__` | sequence special method | 长度获取重载，`len(实例)` 时调用 | 让自定义类支持 `len()` 函数，返回实例元素个数 |
| 9 | `__eq__` | comparison special method | 相等判断重载，`==` 运算时调用 | 自定义实例间的相等逻辑（默认比较内存地址，可重写为属性比较） |
| 10 | `__ne__` | comparison special method | 不相等判断重载，`!=` 运算时调用 | 对应 `!=`，搭配 `__eq__` 使用 |
| 11 | `__lt__` | comparison special method | 小于判断重载，`<` 运算时调用 | 对应 `<`，实现实例间大小比较 |
| 12 | `__gt__` | comparison special method | 大于判断重载，`>` 运算时调用 | 对应 `>` |
| 13 | `__enter__`/`__exit__` | context manager special methods | 上下文管理器专用，`with 实例 as var:` 时自动调用 | 实现自动资源释放（如文件操作、连接关闭），成对出现 |
| 14 | `__call__` | callable special method | 让实例可被调用，`实例()` 时调用 | 把实例当作函数一样执行，拓展实例功能 |
| 15 | `__del__` | destructor special method | 实例析构函数，实例被垃圾回收时调用 | 释放实例占用的特殊资源（极少手动使用，Python自动回收为主） |

### （二） 类/实例的特殊属性（special attributes）：不带括号，内置只读/可查
无需自定义，Python自动为类/实例生成，描述对象的元信息，仅可查询（部分只读），用于反射/自省（查看对象的底层信息）。
| dunder 名称 | 官方关联说明 | 核心用途 | 适用对象 |
|-------------|--------------|----------|----------|
| `__dict__` | instance/class attribute dictionary | 存储实例/类的属性键值对，动态查看/修改属性 | 实例、类（模块也可使用） |
| `__class__` | instance class reference | 查看实例所属的类（反向关联类对象） | 仅实例对象 |
| `__doc__` | docstring attribute | 查看类/函数/模块的文档字符串（"""...""" 定义的注释） | 类、函数、模块 |
| `__module__` | class module origin attribute | 查看类定义所在的模块名 | 自定义类 |
| `__bases__` | class base classes attribute | 查看类的所有父类（继承链），返回元组 | 仅类对象（适配继承场景） |
| `__annotations__` | type annotation attribute | 存储类/函数的类型注解信息（如参数类型、返回值类型） | 类、函数 |


## 三、 分类2：模块相关 dunder（专属类别，官方名：module special attributes）
仅作用于Python模块（.py文件），属于 special attributes，不带括号，Python解释器运行模块时自动赋值，和面向对象无关，是模块的元状态标识。
| dunder 名称 | 官方英文名 | 核心用途（固定语义，永不改变） | 实用场景 |
|-------------|------------|--------------------------------|----------|
| `__name__` | module name attribute | 标识模块运行状态：直接运行→`__main__`，被导入→模块名 | 写模块入口逻辑（`if __name__ == "__main__"`） |
| `__file__` | module file path attribute | 返回模块的文件路径（相对/绝对路径，取决于运行方式） | 动态拼接文件路径（如读取同目录配置） |
| `__all__` | module export list attribute | 手动定义，控制 `from 模块 import *` 时可导入的成员（变量/函数/类） | 模块，需手动赋值（非解释器自动生成） |
| `__package__` | module package attribute | 标识模块所属的包名，无包则为None | 包内模块（工程化项目常用） |


## 四、 分类3：全局/解释器/内置类型相关 dunder（小众类，官方统一归为 special attributes）
作用于全局作用域或内置类型，多为解释器自动生成，隐性使用（日常用不到手动调用），但支撑Python底层运行，官方统称 special attributes。
| 类别 | dunder 名称 | 官方英文名 | 核心用途 | 使用场景 |
|------|-------------|------------|----------|----------|
| 内置类型专属（special method names） | `str.__add__`/`list.__len__` 等 | built-in type special methods | 内置类型的底层行为实现，支撑普通语法操作 | 隐性调用，如 `"a"+"b"` 本质调用 `str.__add__` |
| 解释器全局属性 | `__builtins__` | interpreter built-ins attribute | 存储所有内置函数/内置类型（如 print/int/list/dict） | 全局作用域，无需导入即可使用内置功能的底层支撑 |
| 解释器全局属性 | `__debug__` | interpreter debug mode attribute | 标识解释器是否以调试模式运行，默认True | 调试场景，判断是否执行调试代码 |
| 异常对象专属 | `__cause__` | exception cause attribute | 查看异常的直接原因 | 异常处理中，追溯异常根源 |
| 异常对象专属 | `__traceback__` | exception traceback attribute | 查看异常的回溯信息（报错堆栈） | 异常捕获时，定位报错位置 |
| 异常对象专属 | `__msg__` | exception message attribute | 存储异常的提示信息 | 所有异常实例，`raise 异常("提示")` 时赋值 |


## 五、 关键补充（避坑+官方规范）
1.  所有 dunder 均遵循官方约定：**前后双下划线固定格式**，中间为小写英文，无下划线分隔（如 `__init__` 非 `__init__`）；
2.  官方明确规定：`__xxx__` 格式为Python解释器/内置功能专属，开发者**不可自定义无官方语义的 dunder**（如 `__my_var__`），避免和内置语义冲突；
3.  区分易混格式：单前双下划线（`__var`）≠ dunder（`__xxx__`），前者是类的私有属性（名称改写），非官方定义的 dunder name；
4.  优先级：特殊方法（special method names）可自定义重写，特殊属性（special attributes）多为内置只读，不可随意修改。

## 六、 快速记忆口诀
1.  带括号能重写 → 特殊方法（special method names）→ 类中拓展行为；
2.  不带括号仅可查 → 特殊属性（special attributes）→ 模块/类/实例的元信息；
3.  类里用、能重载 → 类相关 dunder；文件里、标状态 → 模块相关 dunder；底层撑、隐性用 → 全局/内置类型 dunder。
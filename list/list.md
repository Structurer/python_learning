在 Python 中，列表（list）是一种可变的序列类型，用方括号 `[]` 表示，元素之间用逗号分隔。它可以存储不同类型的数据，比如数字、字符串、甚至其他列表。

### 基本特性：
1. **创建列表**：
   ```python
   # 空列表
   empty_list = []
   # 包含元素的列表
   numbers = [1, 2, 3, 4]
   mixed = [1, "hello", 3.14, [5, 6]]  # 元素类型可以不同
   ```

2. **访问元素**：
   通过索引（从 0 开始）访问，也支持负索引（从 -1 开始，代表最后一个元素）。
   ```python
   fruits = ["apple", "banana", "cherry"]
   print(fruits[0])  # 输出：apple
   print(fruits[-1])  # 输出：cherry
   ```

3. **切片操作**：
   用 `[start:end:step]` 获取子列表，start 默认为 0，end 默认为列表长度，step 默认为 1。
   ```python
   nums = [0, 1, 2, 3, 4, 5]
   print(nums[1:4])  # 输出：[1, 2, 3]（不包含 end 索引的元素）
   print(nums[::2])  # 输出：[0, 2, 4]（步长为 2）
   ```

4. **修改元素**：
   直接通过索引赋值修改。
   ```python
   colors = ["red", "green"]
   colors[1] = "blue"
   print(colors)  # 输出：["red", "blue"]
   ```

5. **常用方法**：
   - `append(x)`：在末尾添加元素 x
   - `insert(i, x)`：在索引 i 处插入元素 x
   - `remove(x)`：删除第一个出现的元素 x
   - `pop(i)`：删除并返回索引 i 处的元素（默认最后一个）
   - `sort()`：对列表排序（原地修改）
   - `reverse()`：反转列表（原地修改）

   示例：
   ```python
   animals = ["cat", "dog"]
   animals.append("bird")  # animals 变为 ["cat", "dog", "bird"]
   animals.insert(1, "rabbit")  # 变为 ["cat", "rabbit", "dog", "bird"]
   animals.remove("dog")  # 变为 ["cat", "rabbit", "bird"]
   ```

6. **列表长度**：
   用 `len()` 函数获取。
   ```python
   print(len([1, 2, 3]))  # 输出：3
   ```

列表是 Python 中最常用的数据结构之一，灵活且功能丰富，适合存储和处理一系列相关数据。
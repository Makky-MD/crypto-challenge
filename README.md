# 密码学挑战赛日志仓库

本仓库用于存放密码学挑战赛相关代码与文件，以下为各文件说明与更新记录：

---

## 📁文件夹与文件说明

### 1. `saiti3.rar`
- 存放赛题和暴力求解的cpp程序

### 2. 对S盒的预处理/
存放与S盒线性分析相关的所有代码：
- `S盒线性近似表的求解程序.py`
  作用：遍历输入掩码u和输出掩码v，对每一个可能的S盒输入值x(4bit)，计算满足x·u=S(x)·v的x的个数
- `矩阵CS.py`
  作用：构建并输出相关度矩阵
- `轮加密算法.py`
  作用：实现轻量分组密码的单轮加密流程，包含S盒替换、行移位、列混合操作

### 3. Cadical SAT求解的示例代码/
存放Cadical SAT求解的示例代码：
- cipherfour算法求子句，catical求解
- `gen csv.py`
  作用：计算S盒的差分表输出csv文件
- `pq.csv`
  作用：由上面的`gen csv.py`生成，为符合logic friday格式要求，需要将m列右移一列，导入logic friday
- `pq.lfcn`
  说明：`pq.csv`导入logic friday后得到合取范式
- `cnf to sat.py`
  作用：将合取范式输入到`cnf to sat.py`，将 Logic Friday 导出的的 CNF 逻辑表达式，转换成 SAT 求解器（Cadical）能识别的数字式CNF子句。
- `SearchWithCadical.py`
  作用：调用cadical求解器求解

### 4. Cadical SAT代码第一次修改/
修改S盒为赛题定义的S盒，重复之前流程得到30个子句；`SearchWithCadical.py`文件只保留了算S盒的路径，把P置换和顺序编码约束去掉了

### 5. `Accelerating_Automatic_Search-main.zip`
- 一个密码学自动搜索算法的开源项目

### 6. 初版贴合题目的代码/
- `3_fix r&p - 2.py`
  作用：生成 CipherFour 差分 CNF，调用 Cadical，固定轮数、固定活跃 S 盒，自动输出所有差分路径。
  输出：.cnf文件、求解结果.out、每条差分路径.txt
- `3_recover_path - 2.py`
  作用：解析 SAT 求解的原始 solution 文件，把 SAT 求解出来的结果还原差分路径
  输入：从文件名提取：轮数、活跃S盒数量，把 SAT 输出的变量值还原成每一轮的差分二进制串
  输出：输出可读的差分路径`path_*.txt`
- `3_probability.py`
  作用：根据还原出来的差分路径，自动计算这条路径的差分概率
  输入：`path_*.txt`（还原好的差分路径）
  输出：这条路径总概率 = 每个活跃S盒的概率相乘，算差分路径有多大概率能成功
- `cipherfour_probability.py`
  作用：自动遍历轮数和概率，找到 CipherFour 每一轮的最小差分概率下界
  输出：各轮最小概率下界以及运行时间汇总

### 7. Chat GPT的参考代码/
```
Chat GPT的参考代码/
├── 问题.md                    # 解题规划文档
└── 赛题三/                    # 第十一届密码数学挑战赛赛题三
    ├── 2026密码数学挑战赛-赛题三.md  # 赛题描述（PDF转Markdown）
    ├── 2026密码数学挑战赛-赛题三.pdf # 原始赛题PDF
    ├── Makefile              # 编译脚本
    ├── computecor            # 编译后的精确计算可执行文件
    ├── computecor.cpp        # 官方精确计算代码
    └── solution/             # 解题代码目录
        ├── README.md         # 解题代码说明
        ├── crypto_core.py   # 密码学核心组件
        ├── beam_topk.py     # Beam Search路线搜索
        ├── exact_sparse.py  # 稀疏精确传播
        ├── exact_mitm.py    # MITM精确计算
        ├── make_candidates.py # 候选生成脚本
        ├── verify_exact.py  # 官方代码验证接口
        └── candidates.txt   # 有效候选集合
```
| 文件               | 类型     | 用途                                                                 |
| ------------------ | -------- | -------------------------------------------------------------------- |
| `README.md`        | 代码说明 | 解题代码的使用说明和示例命令                                         |
| `crypto_core.py`   | 核心库   | S盒定义、LAT计算、SR/MC线性层掩码传播、贡献值和得分计算               |
| `beam_topk.py`     | 路线搜索 | Beam Search算法，从输出掩码反向搜索低权重线性路线                    |
| `exact_sparse.py`  | 精确校验 | 对低活跃掩码完整展开所有非零路线，快速校验Beam估计                   |
| `exact_mitm.py`    | 精确计算 | Meet-in-the-Middle算法，精确计算固定(r,u,v)的线性壳相关度            |
| `make_candidates.py`| 批量生成 | 自动生成有效候选集合，输出到 `candidates.txt`                        |
| `verify_exact.py`  | 结果验证 | 调用官方 `computecor` 程序验证估计值是否满足25%误差条件              |
| `candidates.txt`   | 候选输出 | 当前已验证的有效候选集合 (6条)                                       |
```
1. beam_topk.py      → 搜索候选路线
       ↓
2. exact_mitm.py     → 精确计算真实值VT
       ↓
3. make_candidates.py → 验证有效性，生成候选集
       ↓
4. verify_exact.py   → 调用官方代码最终验证
       ↓
5. candidates.txt    → 提交的有效估计值
```

---

## 📝更新日志

### 2026-05-16 上传记录
- 上传压缩包「saiti3.rar」
- 新建文件夹「对S盒的预处理/」
- 上传3个核心代码文件，完成S盒线性分析相关代码的首次提交
- 上传文件夹「Cadical SAT求解的示例代码/」
- 上传文件夹「Cadical SAT代码第一次修改/」
- 上传压缩包「Accelerating_Automatic_Search-main.zip」
- 上传文件夹「初版贴合题目的代码/」
- 上传文件夹「Chat GPT的参考代码/」(当前 candidates.txt 包含6条有效候选，每条相对误差12.5%，满足题面25%要求。)

### 2026-xx-xx 上传记录
- 

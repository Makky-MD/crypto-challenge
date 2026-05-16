import pandas as pd
from sympy import symbols, POSform

# ======================
# 1. 定义变量
# ======================
X1, X2, X3, X4, Y1, Y2, Y3, Y4, P, Q = symbols('X1 X2 X3 X4 Y1 Y2 Y3 Y4 P Q')
var_list = [X1, X2, X3, X4, Y1, Y2, Y3, Y4, P, Q]

# ======================
# 2. 直接读取你的 pq.csv 文件
# ======================
df = pd.read_csv("pq.csv")  # 确保 csv 和代码在同一文件夹

# 只保留 M=1 的行（真值表为 1 的最小项）
df_m1 = df[df['m'] == 1]

# 把每行转成元组，加入 minterms
minterms = []
for _, row in df_m1.iterrows():
    item = (
        row['x1'], row['x2'], row['x3'], row['x4'],
        row['y1'], row['y2'], row['y3'], row['y4'],
        row['p'], row['q']
    )
    minterms.append(item)

# ======================
# 3. 生成最简 CNF（和之积）
# ======================
cnf = POSform(var_list, minterms)

# ======================
# 4. 统计子句数量
# ======================
clause_list = str(cnf).split(" & ")
count = len(clause_list)

# ======================
# 5. 输出结果
# ======================
print("✅ 从 pq.csv 读取 M=1 的行数：", len(minterms))
print("✅ 生成的 CNF 子句总数：", count)
print("\n=== 所有子句 ===")
for i, clause in enumerate(clause_list, 1):
    print(f"{i:2d}. {clause}")

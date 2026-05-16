

import numpy as np

S_box = [0xC, 0x6, 0x9, 0x0, 0x1, 0xA, 0x2, 0xB,
         0x3, 0x8, 0x5, 0xD, 0x4, 0xE, 0x7, 0xF]

n = 4
N = 2**n

CS = np.zeros((N, N), dtype=float)

for v in range(N):
    for u in range(N):
        s = 0
        for x in range(N):
            dot_ux = bin(u & x).count('1') % 2
            dot_vSx = bin(v & S_box[x]).count('1') % 2
            exponent = dot_ux ^ dot_vSx
            s += (-1) ** exponent
        CS[v, u] = s / 16.0

# 设置打印选项：保留两位小数，不使用科学计数法
np.set_printoptions(precision=2, suppress=True, floatmode='fixed')

print("CS matrix (rows = v, cols = u):")
print(CS)
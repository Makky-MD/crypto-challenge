# 赛题三第一版解题代码

当前版本先实现不依赖求解器的 Top-K 线性路线候选搜索，用于快速产生 `(r,u,v,V_E)` 候选，并给后续 CaDiCaL/MILP 建模提供校验基线。

## 文件

- `crypto_core.py`：S 盒 LAT、SR/MC 转置掩码传播、贡献和得分函数。
- `beam_topk.py`：从输出掩码 `v` 反向搜索低权重路线，按输入掩码 `u` 聚合得到估计值 `V_E`。
- `exact_sparse.py`：对低活跃掩码完整展开所有非零路线，用于快速校验 Beam 估计。
- `exact_mitm.py`：固定 `(r,u,v)` 的 meet-in-the-middle 精确线性壳求和。
- `make_candidates.py`：批量执行 Beam 搜索、MITM 筛选，并生成候选 txt。
- `verify_exact.py`：调用官方 `computecor.cpp` 编译出的精确程序，计算 `V_T` 并检查 25% 相对误差条件。

## 示例

先搜索 2 轮、固定输出掩码的候选：

```bash
cd /Users/lee/OrbitOS-vault
.venv/bin/python 代码学/赛题三/solution/beam_topk.py \
  --rounds 2 \
  --v 0x0000000f \
  --beam 20000 \
  --expand 128 \
  --top 20
```

对某个候选 `(u,v,V_E)` 调官方精确代码验证：

```bash
.venv/bin/python 代码学/赛题三/solution/verify_exact.py \
  --rounds 2 \
  --u 0x... \
  --v 0x0000000f \
  --estimate ...
```

注意：官方精确代码是 `2^32` 枚举，可能很慢。搜索阶段应先用 Beam/SAT/MILP 缩小候选范围。

对低活跃掩码，也可以先用稀疏精确传播快速校验：

```bash
.venv/bin/python 代码学/赛题三/solution/exact_sparse.py \
  --rounds 2 \
  --v 0x0000000f \
  --u 0x02022000
```

生成当前保守候选集合：

```bash
.venv/bin/python 代码学/赛题三/solution/make_candidates.py
```

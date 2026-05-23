import numpy as np
from collections import defaultdict
from itertools import product
from typing import List, Dict, Tuple, Set

# ============================================================================
# S盒定义 (4x4 查找表)
# ============================================================================
# S盒是AES中的核心置换，将4位输入映射到4位输出
# 这里使用16个十六进制数表示完整的S盒变换
S_box = [0xC, 0x6, 0x9, 0x0, 0x1, 0xA, 0x2, 0xB,
         0x3, 0x8, 0x5, 0xD, 0x4, 0xE, 0x7, 0xF]

# ============================================================================
# 全局变量定义
# ============================================================================
N = 16  # 掩码状态空间大小 (4位 = 16种可能值)
CS = np.zeros((N, N), dtype=float)  # 相关系数矩阵 (Correlation matrix)

# ============================================================================
# 计算S盒的相关系数矩阵
# ============================================================================
# 目的：计算S盒输入掩码u与输出掩码v之间的线性相关度
# 相关度定义：C(v,u) = (1/16) * Σ(-1)^(dot(u,x) ⊕ dot(v,S(x)))
# 其中:
#   - dot(u,x) 表示u与x的二进制点积模2
#   - S(x) 是S盒对x的输出
#   - 相关度范围: [-1, 1]
#
# 物理意义：
#   - 相关度接近+1或-1表示强线性关系
#   - 相关度接近0表示无线性关系
# ----------------------------------------------------------------------------
for v in range(N):  # v是输出掩码（行索引）
    for u in range(N):  # u是输入掩码（列索引）
        s = 0
        # 遍历所有可能的4位输入x (0-15)
        for x in range(N):
            # 计算dot(u,x): 输入掩码u与输入x的点积（汉明重量模2）
            dot_ux = bin(u & x).count('1') % 2
            # 计算dot(v,S(x)): 输出掩码v与S盒输出S(x)的点积
            dot_vSx = bin(v & S_box[x]).count('1') % 2
            # 累加相关贡献
            s += (-1) ** (dot_ux ^ dot_vSx)
        # 归一化：除以可能的输入数量16
        CS[v, u] = s / 16.0

# ============================================================================
# 构建正向和反向查找字典
# ============================================================================
# 正向字典 forward_dict:
#   - 键: 输入掩码u
#   - 值: [(输出掩码v1, 相关系数1), (v2, c2), ...]
#   - 用途: 给定输入掩码，查找所有可能的输出掩码及其相关系数
#
# 反向字典 backward_dict:
#   - 键: 输出掩码v
#   - 值: [(输入掩码u1, 相关系数1), (u2, c2), ...]
#   - 用途: 给定输出掩码，查找所有可能的输入掩码及其相关系数

# 正向字典：输入掩码u -> 输出掩码v列表（含相关系数）
forward_dict = defaultdict(list)
for u in range(1, N):  # 从1开始，0掩码单独处理
    for v in range(N):
        if CS[v, u] != 0:
            forward_dict[u].append((v, CS[v, u]))

# 反向字典：输出掩码v -> 输入掩码u列表（含相关系数）
backward_dict = defaultdict(list)
for u in range(1, N):
    for v in range(N):
        if CS[v, u] != 0:
            backward_dict[v].append((u, CS[v, u]))

# ============================================================================
# 置换P的定义（8位操作）
# ============================================================================
# P是SPN中字节间的置换操作
# 位置i的掩码会被移动到位置P[i]
P = [0, 5, 2, 7, 4, 1, 6, 3]

# 计算P的逆置换
# inv_P[p] = i 表示：位置p的值原来在位置i
inv_P = [0] * 8
for i, p in enumerate(P):
    inv_P[p] = i


def apply_permutation(masks):
    """
    对8个4-bit掩码应用置换P

    参数:
        masks: 8个4位掩码的列表 [m0, m1, m2, m3, m4, m5, m6, m7]

    返回:
        置换后的掩码列表，新位置i的值是原位置P[i]的值

    示例:
        apply_permutation([a,b,c,d,e,f,g,h]) -> [a,f,c,h,e,b,g,d]
        因为 P = [0,5,2,7,4,1,6,3]
    """
    return [masks[i] for i in P]


def apply_permutation_inverse(masks):
    """
    对8个4-bit掩码应用逆置换inv_P

    参数:
        masks: 8个4位掩码的列表

    返回:
        逆置换后的掩码列表
    """
    return [masks[i] for i in inv_P]


# ============================================================================
# 列混合(MixColumns)及其逆运算
# ============================================================================
# 在AES-like的SPN中，列混合将4个4-bit值通过线性变换得到另外4个4-bit值
# 这里实现的矩阵是:
#   [y0]   [0 0 0 1] [x0]
#   [y1] = [1 1 1 1] [x1]
#   [y2] = [0 1 0 0] [x2]
#   [y3] = [1 1 0 1] [x3]
#
# 即:
#   y0 = x3
#   y1 = x0 ⊕ x1 ⊕ x2
#   y2 = x1
#   y3 = x1 ⊕ x2 ⊕ x3

def get_output_mask_from_input_mixcolumns(input_masks):
    """
    列混合：输入4个4-bit掩码，输出4个4-bit掩码

    参数:
        input_masks: 输入掩码列表 [x0, x1, x2, x3]

    返回:
        输出掩码列表 [y0, y1, y2, y3]

    数学公式:
        y0 = x3
        y1 = x0 ⊕ x1 ⊕ x2
        y2 = x1
        y3 = x1 ⊕ x2 ⊕ x3
    """
    x0, x1, x2, x3 = input_masks
    y0 = y1 = y2 = y3 = 0  # 初始化输出掩码

    # 逐位处理（因为是4-bit值，所以处理4位）
    for bit in range(4):
        # 提取各输入掩码的第bit位
        a0 = (x0 >> bit) & 1
        a1 = (x1 >> bit) & 1
        a2 = (x2 >> bit) & 1
        a3 = (x3 >> bit) & 1

        # 根据列混合公式计算输出掩码的第bit位
        y0_bit = a3
        y1_bit = a0 ^ a1 ^ a2
        y2_bit = a1
        y3_bit = a1 ^ a2 ^ a3

        # 将计算出的bit位放回对应的输出掩码位置
        y0 |= (y0_bit << bit)
        y1 |= (y1_bit << bit)
        y2 |= (y2_bit << bit)
        y3 |= (y3_bit << bit)

    return [y0, y1, y2, y3]


def get_input_mask_from_output_mixcolumns(output_masks):
    """
    列混合逆运算：给定输出掩码，反向求解输入掩码

    参数:
        output_masks: 输出掩码列表 [y0, y1, y2, y3]

    返回:
        输入掩码列表 [x0, x1, x2, x3]

    逆向推导（从列混合方程求解）:
        y0 = x3  →  x3 = y0
        y2 = x1  →  x1 = y2
        y3 = x1 ⊕ x2 ⊕ x3  →  x2 = y1 ⊕ y3 ⊕ x3 = y1 ⊕ y3 ⊕ y0
        y1 = x0 ⊕ x1 ⊕ x2  →  x0 = y1 ⊕ x1 ⊕ x2
    """
    y0, y1, y2, y3 = output_masks
    x0 = x1 = x2 = x3 = 0  # 初始化输入掩码

    # 逐位处理
    for bit in range(4):
        # 提取各输出掩码的第bit位
        b0 = (y0 >> bit) & 1
        b1 = (y1 >> bit) & 1
        b2 = (y2 >> bit) & 1
        b3 = (y3 >> bit) & 1

        # 逆向求解各输入掩码的bit位
        a3 = b0  # x3 = y0
        a1 = b2  # x1 = y2
        a2 = a1 ^ a3 ^ b3  # x2 = x1 ⊕ x3 ⊕ y3
        a0 = b1 ^ a1 ^ a2  # x0 = y1 ⊕ x1 ⊕ x2

        # 将计算出的bit位放回对应的输入掩码位置
        x0 |= (a0 << bit)
        x1 |= (a1 << bit)
        x2 |= (a2 << bit)
        x3 |= (a3 << bit)

    return [x0, x1, x2, x3]


# ============================================================================
# S盒路径查找函数
# ============================================================================

def get_sbox_forward_paths(input_mask):
    """
    获取单个S盒的正向路径

    给定输入掩码u，返回所有可能的输出掩码v及其相关系数

    参数:
        input_mask: S盒的输入掩码 (0-15)

    返回:
        包含(v, correlation)元组的列表
        如果input_mask为0，返回[(0, 1.0)]
    """
    if input_mask == 0:
        return [(0, 1.0)]
    return forward_dict[input_mask]


def get_sbox_backward_paths(output_mask):
    """
    获取单个S盒的反向路径

    给定输出掩码v，返回所有可能的输入掩码u及其相关系数

    参数:
        output_mask: S盒的输出掩码 (0-15)

    返回:
        包含(u, correlation)元组的列表
    """
    if output_mask == 0:
        return [(0, 1.0)]
    return backward_dict[output_mask]


# ============================================================================
# 一轮加密搜索算法
# ============================================================================

def forward_search_round(input_masks: List[int]) -> Dict[tuple, float]:
    """
    正向搜索一轮加密

    输入: 8个输入掩码 [m0, m1, m2, m3, m4, m5, m6, m7]
    处理流程:
        1. 每个输入掩码独立通过S盒
        2. S盒输出经过置换P
        3. 经过列混合得到最终输出

    返回: 字典 {输出掩码元组: 总相关度}

    算法说明:
        使用乘积穷举(product)遍历所有S盒的输出组合
        相关度相乘（概率论中的独立事件乘积）
    """
    results = defaultdict(float)

    # 获取每个S盒的路径列表
    # 每个S盒可能有多个输出路径（多个v对应同一个u）
    sbox_paths_list = []
    for in_mask in input_masks:
        sbox_paths_list.append(get_sbox_forward_paths(in_mask))

    # 遍历所有S盒的输出组合
    # product(*list)产生所有可能的组合
    for combo in product(*sbox_paths_list):
        # combo: ((v1, c1), (v2, c2), ..., (v8, c8))
        sbox_outputs = [p[0] for p in combo]  # 提取8个输出掩码
        sbox_corrs = [p[1] for p in combo]     # 提取8个相关系数

        # 计算当前组合的相关度乘积
        # S盒之间独立，相关度相乘
        current_corr = np.prod(sbox_corrs)

        if current_corr == 0:
            continue

        # 应用置换：将S盒输出按P重新排列
        permuted = apply_permutation(sbox_outputs)

        # 列混合（分两组，每组4个掩码）
        group1 = permuted[0:4]  # 前4个掩码
        group2 = permuted[4:8]  # 后4个掩码
        mix_out1 = get_output_mask_from_input_mixcolumns(group1)
        mix_out2 = get_output_mask_from_input_mixcolumns(group2)
        final_masks = tuple(mix_out1 + mix_out2)

        # 累加到结果字典
        # 同一输出掩码可能有多个输入路径到达，需要累加
        results[final_masks] += current_corr

    return results


def backward_search_round(output_masks: List[int]) -> Dict[tuple, float]:
    """
    反向搜索一轮加密

    输入: 8个输出掩码 [m0, m1, m2, m3, m4, m5, m6, m7]
    反向处理流程:
        1. 列混合逆运算
        2. 逆置换
        3. 逆S盒

    返回: 字典 {输入掩码元组: 总相关度}
    """
    results = defaultdict(float)

    # 第1步：列混合逆运算
    group1 = output_masks[0:4]
    group2 = output_masks[4:8]

    # 对每组进行列混合逆运算
    mix_input1 = get_input_mask_from_output_mixcolumns(group1)
    mix_input2 = get_input_mask_from_output_mixcolumns(group2)
    before_mixcolumns = mix_input1 + mix_input2

    # 第2步：逆置换
    before_permutation = apply_permutation_inverse(before_mixcolumns)

    # 第3步：逆S盒（每个字节独立处理）
    sbox_paths_list = []
    for out_mask in before_permutation:
        sbox_paths_list.append(get_sbox_backward_paths(out_mask))

    # 遍历所有S盒输入组合
    for combo in product(*sbox_paths_list):
        sbox_inputs = [p[0] for p in combo]
        sbox_corrs = [p[1] for p in combo]

        current_corr = np.prod(sbox_corrs)

        if current_corr != 0:
            results[tuple(sbox_inputs)] += current_corr

    return results


# ============================================================================
# 两轮加密相关度计算
# ============================================================================

def compute_two_round_correlation(input_masks: List[int], output_masks: List[int]) -> float:
    """
    计算两轮加密的线性相关度

    两轮SPN结构:
        输入掩码u → [S盒 → P → MixColumns] → [S盒 → P → MixColumns] → 输出掩码v

    参数:
        input_masks: 8个输入掩码 [u0, u1, u2, u3, u4, u5, u6, u7]
        output_masks: 8个输出掩码 [v0, v1, v2, v3, v4, v5, v6, v7]

    返回:
        total_correlation: 总相关度（浮点数）
        path_details: 各路径的详细信息列表

    算法步骤:
        1. 正向搜索第一轮：输入 → 中间掩码M
        2. 反向搜索第二轮：中间掩码M → 输出
        3. 求交集：找到第一轮和第二轮共同的中间掩码
        4. 计算总相关度：Σ(corr第一轮 × corr第二轮)
    """
    print(f"\n输入掩码: {[hex(m) for m in input_masks]}")
    print(f"输出掩码: {[hex(m) for m in output_masks]}")

    # 正向搜索第一轮
    # 结果：所有可能的中间掩码及其相关度
    print("\n第1步：正向搜索第一轮...")
    first_round_outputs = forward_search_round(input_masks)
    print(f"第一轮产生 {len(first_round_outputs)} 种不同的输出掩码组合")

    # 反向搜索第二轮
    # 结果：所有可能的中间掩码及其相关度
    print("\n第2步：反向搜索第二轮...")
    second_round_inputs = backward_search_round(output_masks)
    print(f"第二轮产生 {len(second_round_inputs)} 种不同的输入掩码组合")

    # 求交集（找公共中间掩码）
    # 只有第一轮能产生的中间掩码且第二轮也能接受的，才形成有效路径
    print("\n第3步：寻找中间掩码交集...")
    common_masks = set(first_round_outputs.keys()) & set(second_round_inputs.keys())
    print(f"找到 {len(common_masks)} 个公共中间掩码")

    # 计算总相关度
    # 对所有有效路径的相关度求和
    total_correlation = 0.0
    path_details = []

    for mid_mask in common_masks:
        corr1 = first_round_outputs[mid_mask]      # 第一轮到达此中间掩码的相关度
        corr2 = second_round_inputs[mid_mask]      # 第二轮从此中间掩码出发的相关度
        total_corr_path = corr1 * corr2             # 路径总相关度 = 两轮相关度乘积
        total_correlation += total_corr_path        # 累加到总相关度

        # 记录路径详细信息
        path_details.append({
            'mid_mask': mid_mask,
            'first_round_corr': corr1,
            'second_round_corr': corr2,
            'total_corr': total_corr_path
        })

        print(f"\n中间掩码: {[hex(m) for m in mid_mask]}")
        print(f"  第一轮相关度: {corr1:.8f}")
        print(f"  第二轮相关度: {corr2:.8f}")
        print(f"  路径相关度: {total_corr_path:.8f}")

    print(f"\n{'=' * 60}")
    print(f"总相关度: {total_correlation:.8f}")
    print(f"绝对值: {abs(total_correlation):.8f}")

    return total_correlation, path_details


# ============================================================================
# 最佳路径搜索
# ============================================================================

def find_best_two_round_path(input_masks: List[int], top_k: int = 10):
    """
    找到给定输入掩码下的最佳两轮路径

    参数:
        input_masks: 8个输入掩码
        top_k: 返回相关度最大的前k个输出掩码

    返回:
        字典: {输出掩码元组: 相关度}

    算法:
        1. 正向搜索第一轮
        2. 对每个中间掩码，继续正向搜索第二轮
        3. 累加相关度到最终输出掩码
        4. 排序返回top_k
    """
    print(f"搜索给定输入掩码 {[hex(m) for m in input_masks]} 的最佳两轮路径")

    # 正向搜索第一轮
    first_round_outputs = forward_search_round(input_masks)

    # 对每个可能的中间掩码，继续第二轮搜索
    results = defaultdict(float)

    for mid_mask, corr1 in first_round_outputs.items():
        # 将中间掩码作为第二轮的输入
        second_round_outputs = forward_search_round(list(mid_mask))

        for final_mask, corr2 in second_round_outputs.items():
            total_corr = corr1 * corr2
            results[final_mask] += total_corr

    # 按相关度绝对值排序
    sorted_results = sorted(results.items(), key=lambda x: abs(x[1]), reverse=True)

    print(f"\n找到 {len(results)} 个不同的输出掩码组合")
    print(f"\n相关度最大的前 {min(top_k, len(sorted_results))} 个输出掩码:")

    for i, (final_mask, corr) in enumerate(sorted_results[:top_k]):
        print(f"\n{i + 1}. 输出掩码: {[hex(m) for m in final_mask]}")
        print(f"   相关度: {corr:.8f} (绝对值: {abs(corr):.8f})")

    return dict(sorted_results[:top_k])


def analyze_path_contributions(path_details):
    """
    分析各路径对总相关度的贡献

    参数:
        path_details: compute_two_round_correlation返回的路径详情列表
    """
    print("\n" + "=" * 60)
    print("路径贡献分析")
    print("=" * 60)

    total = sum(p['total_corr'] for p in path_details)

    for i, path in enumerate(path_details):
        contribution = abs(path['total_corr'] / total) if total != 0 else 0
        print(f"\n路径 {i + 1}:")
        print(f"  贡献度: {contribution:.2%}")
        print(f"  相关度: {path['total_corr']:+.8f}")
        print(f"  第一轮: {path['first_round_corr']:+.8f}")
        print(f"  第二轮: {path['second_round_corr']:+.8f}")


# ============================================================================
# 主程序示例
# ============================================================================
if __name__ == "__main__":
    print("=" * 80)
    print("两轮SPN线性密码分析 - 路径搜索")
    print("=" * 80)

    # 示例3：测试非零输出掩码
    print("\n" + "=" * 80)
    print("【示例3】测试非零输出掩码")
    print("=" * 80)

    # 定义输入掩码和输出掩码
    input_u2 = [0, 0, 0, 0, 2, 0, 0, 0]   # 第5个字节为0x2，其余为0
    output_v2 = [0, 8, 8, 8, 0, 0, 0, 0]  # 第2,3,4字节为0x8，其余为0

    # 计算两轮相关度
    total_corr2, _ = compute_two_round_correlation(input_u2, output_v2)

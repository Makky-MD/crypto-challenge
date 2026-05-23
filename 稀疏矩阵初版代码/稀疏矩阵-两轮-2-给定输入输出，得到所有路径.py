import numpy as np
from collections import defaultdict
from itertools import product
from typing import List, Dict, Tuple, Set

# S-box (4x4)
S_box = [0xC, 0x6, 0x9, 0x0, 0x1, 0xA, 0x2, 0xB,
         0x3, 0x8, 0x5, 0xD, 0x4, 0xE, 0x7, 0xF]

N = 16
CS = np.zeros((N, N), dtype=float)

# 计算相关系数矩阵（rows=v, cols=u）
for v in range(N):
    for u in range(N):
        s = 0
        for x in range(N):
            dot_ux = bin(u & x).count('1') % 2
            dot_vSx = bin(v & S_box[x]).count('1') % 2
            s += (-1) ** (dot_ux ^ dot_vSx)
        CS[v, u] = s / 16.0

# 正向字典：输入掩码u -> 输出掩码v列表（含相关系数）
forward_dict = defaultdict(list)
for u in range(1, N):
    for v in range(N):
        if CS[v, u] != 0:
            forward_dict[u].append((v, CS[v, u]))

# 反向字典：输出掩码v -> 输入掩码u列表（含相关系数）
backward_dict = defaultdict(list)
for u in range(1, N):
    for v in range(N):
        if CS[v, u] != 0:
            backward_dict[v].append((u, CS[v, u]))

# 置换
P = [0, 5, 2, 7, 4, 1, 6, 3]
inv_P = [0] * 8
for i, p in enumerate(P):
    inv_P[p] = i


def apply_permutation(masks):
    """对8个4-bit掩码应用置换"""
    return [masks[i] for i in P]


def apply_permutation_inverse(masks):
    """对8个4-bit掩码应用逆置换"""
    return [masks[i] for i in inv_P]


def get_output_mask_from_input_mixcolumns(input_masks):
    """
    列混合：输入4个4-bit掩码，输出4个4-bit掩码
    输入: [x0, x1, x2, x3]
    返回: [y0, y1, y2, y3]
    """
    x0, x1, x2, x3 = input_masks
    y0 = y1 = y2 = y3 = 0

    for bit in range(4):
        a0 = (x0 >> bit) & 1
        a1 = (x1 >> bit) & 1
        a2 = (x2 >> bit) & 1
        a3 = (x3 >> bit) & 1

        y0_bit = a3
        y1_bit = a0 ^ a1 ^ a2
        y2_bit = a1
        y3_bit = a1 ^ a2 ^ a3

        y0 |= (y0_bit << bit)
        y1 |= (y1_bit << bit)
        y2 |= (y2_bit << bit)
        y3 |= (y3_bit << bit)

    return [y0, y1, y2, y3]


def get_input_mask_from_output_mixcolumns(output_masks):
    """
    列混合逆运算：给定输出掩码，找出输入掩码
    输出: [y0, y1, y2, y3] 返回输入掩码 [x0, x1, x2, x3]
    """
    y0, y1, y2, y3 = output_masks
    x0 = x1 = x2 = x3 = 0

    for bit in range(4):
        b0 = (y0 >> bit) & 1
        b1 = (y1 >> bit) & 1
        b2 = (y2 >> bit) & 1
        b3 = (y3 >> bit) & 1

        # 逆向求解
        a3 = b0
        a1 = b2
        a2 = a1 ^ a3 ^ b3
        a0 = b1 ^ a1 ^ a2

        x0 |= (a0 << bit)
        x1 |= (a1 << bit)
        x2 |= (a2 << bit)
        x3 |= (a3 << bit)

    return [x0, x1, x2, x3]


def get_sbox_forward_paths(input_mask):
    """获取单个S盒的正向路径"""
    if input_mask == 0:
        return [(0, 1.0)]
    return forward_dict[input_mask]


def get_sbox_backward_paths(output_mask):
    """获取单个S盒的反向路径"""
    if output_mask == 0:
        return [(0, 1.0)]
    return backward_dict[output_mask]


def forward_search_round(input_masks: List[int]) -> Dict[tuple, float]:
    """
    正向搜索一轮加密
    输入: 8个输入掩码 [m0,...,m7]
    返回: 字典 {输出掩码元组: 总相关度}
    """
    results = defaultdict(float)

    # 获取每个S盒的路径
    sbox_paths_list = []
    for in_mask in input_masks:
        sbox_paths_list.append(get_sbox_forward_paths(in_mask))

    # 遍历所有S盒组合
    for combo in product(*sbox_paths_list):
        # 提取输出掩码和相关系数
        sbox_outputs = [p[0] for p in combo]
        sbox_corrs = [p[1] for p in combo]

        # 计算当前组合的相关度乘积
        current_corr = np.prod(sbox_corrs)

        if current_corr == 0:
            continue

        # 应用置换
        permuted = apply_permutation(sbox_outputs)

        # 列混合（分两组）
        group1 = permuted[0:4]
        group2 = permuted[4:8]
        mix_out1 = get_output_mask_from_input_mixcolumns(group1)
        mix_out2 = get_output_mask_from_input_mixcolumns(group2)
        final_masks = tuple(mix_out1 + mix_out2)

        # 累加相关度
        results[final_masks] += current_corr

    return results


def backward_search_round(output_masks: List[int]) -> Dict[tuple, float]:
    """
    反向搜索一轮加密
    输入: 8个输出掩码 [m0,...,m7]
    返回: 字典 {输入掩码元组: 总相关度}
    """
    results = defaultdict(float)

    # 第1步：列混合逆运算
    group1 = output_masks[0:4]
    group2 = output_masks[4:8]

    mix_input1 = get_input_mask_from_output_mixcolumns(group1)
    mix_input2 = get_input_mask_from_output_mixcolumns(group2)
    before_mixcolumns = mix_input1 + mix_input2

    # 第2步：逆置换
    before_permutation = apply_permutation_inverse(before_mixcolumns)

    # 第3步：逆S盒（每个字节独立）
    sbox_paths_list = []
    for out_mask in before_permutation:
        sbox_paths_list.append(get_sbox_backward_paths(out_mask))

    # 遍历所有S盒组合
    for combo in product(*sbox_paths_list):
        sbox_inputs = [p[0] for p in combo]
        sbox_corrs = [p[1] for p in combo]

        current_corr = np.prod(sbox_corrs)

        if current_corr != 0:
            results[tuple(sbox_inputs)] += current_corr

    return results


def compute_two_round_correlation(input_masks: List[int], output_masks: List[int]) -> float:
    """
    计算两轮加密的线性相关度
    输入掩码u (8个4-bit值) -> 输出掩码v (8个4-bit值)
    返回: 总相关度
    """
    print(f"\n输入掩码: {[hex(m) for m in input_masks]}")
    print(f"输出掩码: {[hex(m) for m in output_masks]}")

    # 正向搜索第一轮
    print("\n第1步：正向搜索第一轮...")
    first_round_outputs = forward_search_round(input_masks)
    print(f"第一轮产生 {len(first_round_outputs)} 种不同的输出掩码组合")

    # 反向搜索第二轮
    print("\n第2步：反向搜索第二轮...")
    second_round_inputs = backward_search_round(output_masks)
    print(f"第二轮产生 {len(second_round_inputs)} 种不同的输入掩码组合")

    # 求交集（中间掩码）
    print("\n第3步：寻找中间掩码交集...")
    common_masks = set(first_round_outputs.keys()) & set(second_round_inputs.keys())
    print(f"找到 {len(common_masks)} 个公共中间掩码")

    # 计算总相关度
    total_correlation = 0.0
    path_details = []

    for mid_mask in common_masks:
        corr1 = first_round_outputs[mid_mask]
        corr2 = second_round_inputs[mid_mask]
        total_corr_path = corr1 * corr2
        total_correlation += total_corr_path

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


def find_best_two_round_path(input_masks: List[int], top_k: int = 10):
    """
    找到给定输入掩码下的最佳两轮路径
    返回前k个相关度最大的输出掩码
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



    return results


def analyze_path_contributions(path_details):
    """分析各路径对总相关度的贡献"""
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


# 主程序示例
if __name__ == "__main__":
    print("=" * 80)
    print("两轮SPN线性密码分析 - 路径搜索")
    print("=" * 80)


    # 示例：测试非零输出掩码
    print("\n" + "=" * 80)
    print("【示例3】测试非零输出掩码")
    print("=" * 80)

    input_u2 = [4, 0, 0, 0, 0, 0, 0, 0]
    output_v2 = [0, 0, 0, 0, 0, 1, 1, 1]

    # input_u2 = [2, 0, 0, 0, 0, 0, 0, 0]
    # output_v2 = [0, 0, 0, 0, 0, 8, 8, 8]


    total_corr2, _ = compute_two_round_correlation(input_u2, output_v2)



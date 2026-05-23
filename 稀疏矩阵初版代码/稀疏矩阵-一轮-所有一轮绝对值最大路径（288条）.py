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

# 找出相关系数绝对值为0.5的所有(u, v)对
half_corr_pairs = []
for u in range(1, N):  # 非零输入掩码
    for v in range(N):
        if abs(CS[v, u]) == 0.5:
            half_corr_pairs.append((u, v, CS[v, u]))

print("=" * 80)
print("S盒相关系数绝对值为0.5的(u, v)对")
print("=" * 80)
print(f"总共找到 {len(half_corr_pairs)} 对\n")

# 按输入掩码分组
u_to_v = defaultdict(list)
for u, v, c in half_corr_pairs:
    u_to_v[u].append((v, c))

for u in sorted(u_to_v.keys()):
    v_str = ", ".join([f"{v:2X}({c:+.4f})" for v, c in u_to_v[u]])
    print(f"u={u:2X} ({u:04b}) -> [{v_str}]")

# 置换
P = [0, 5, 2, 7, 4, 1, 6, 3]
inv_P = [0] * 8
for i, p in enumerate(P):
    inv_P[p] = i


def apply_permutation(masks: List[int]) -> List[int]:
    """对8个4-bit掩码应用置换"""
    return [masks[i] for i in P]


def apply_permutation_inverse(masks: List[int]) -> List[int]:
    """对8个4-bit掩码应用逆置换"""
    return [masks[i] for i in inv_P]


def mix_columns(input_masks: List[int]) -> List[int]:
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


def apply_mix_columns_to_all(masks: List[int]) -> List[int]:
    """
    对8个半字节应用列混合（两列，每列4个半字节）
    masks: 8个半字节 [b0,b1,b2,b3,b4,b5,b6,b7]
    列0: b0,b1,b2,b3
    列1: b4,b5,b6,b7
    """
    # 第一列
    col0 = mix_columns(masks[0:4])
    # 第二列
    col1 = mix_columns(masks[4:8])

    return col0 + col1


def nibbles_to_int(nibbles: List[int]) -> int:
    """8个半字节 -> 32位整数（nibbles[0]是最低4位）"""
    result = 0
    for i, nib in enumerate(nibbles):
        result |= (nib & 0xF) << (4 * i)
    return result


def int_to_nibbles(val: int) -> List[int]:
    """32位整数 -> 8个半字节（nibbles[0]是最低4位）"""
    return [(val >> (4 * i)) & 0xF for i in range(8)]


def format_nibbles_hex(nibbles: List[int]) -> str:
    """格式化半字节列表为十六进制字符串"""
    return ' '.join([f'{x:X}' for x in nibbles])


print("\n" + "=" * 80)
print("一轮搜索中相关系数绝对值为0.5的所有路径")
print("=" * 80)

# 存储所有路径
all_paths = []

# 遍历所有位置和所有(u, v)对
for pos in range(8):  # 8个半字节位置
    for u, v, corr in half_corr_pairs:
        # === 第1层：S盒 ===
        # 输入掩码：只在pos位置有非零值
        input_nibbles = [0] * 8
        input_nibbles[pos] = u

        # S盒输出掩码：只在pos位置有非零值
        sbox_out_nibbles = [0] * 8
        sbox_out_nibbles[pos] = v

        # === 第2层：SR置换 ===
        sr_out_nibbles = apply_permutation(sbox_out_nibbles)

        # === 第3层：MC变换 ===
        mc_out_nibbles = apply_mix_columns_to_all(sr_out_nibbles)

        # 转换为整数
        input_val = nibbles_to_int(input_nibbles)
        sbox_out_val = nibbles_to_int(sbox_out_nibbles)
        sr_out_val = nibbles_to_int(sr_out_nibbles)
        mc_out_val = nibbles_to_int(mc_out_nibbles)

        path_info = {
            'position': pos,
            'u': u,
            'v': v,
            'correlation': corr,
            'input_mask': input_val,
            'input_nibbles': input_nibbles.copy(),
            'sbox_output_mask': sbox_out_val,
            'sbox_out_nibbles': sbox_out_nibbles.copy(),
            'sr_output_mask': sr_out_val,
            'sr_out_nibbles': sr_out_nibbles.copy(),
            'mc_output_mask': mc_out_val,
            'mc_out_nibbles': mc_out_nibbles.copy()
        }
        all_paths.append(path_info)

print(f"\n总共找到 {len(all_paths)} 条路径")
print(f"（{8}个位置 × {len(half_corr_pairs)}个S盒路径）\n")

# 显示前10条路径作为示例
print("示例路径（前10条）：")
print("-" * 80)
for i, path in enumerate(all_paths[:10]):
    print(f"\n{i + 1}. 位置{path['position']}: u={path['u']:X}, v={path['v']:X}, corr={path['correlation']:+.1f}")
    print(f"   输入掩码: 0x{path['input_mask']:08X}")
    print(f"   输入半字节: {format_nibbles_hex(path['input_nibbles'])}")
    print(f"   S盒输出: 0x{path['sbox_output_mask']:08X}")
    print(f"   SR置换后: 0x{path['sr_output_mask']:08X}")
    print(f"   MC变换后: 0x{path['mc_output_mask']:08X}")
    print(f"   MC输出半字节: {format_nibbles_hex(path['mc_out_nibbles'])}")

if len(all_paths) > 10:
    print(f"\n... 共 {len(all_paths)} 条路径")

# ==================== 统计分析 ====================
print("\n" + "=" * 80)
print("统计分析")
print("=" * 80)

# 按输入掩码分组
print("\n按输入掩码分组：")
u_stats = defaultdict(list)
for path in all_paths:
    u_stats[path['u']].append(path)

for u in sorted(u_stats.keys()):
    v_values = sorted(set(p['v'] for p in u_stats[u]))
    print(f"  u={u:2X}: {len(u_stats[u])} 条路径, v值: {[f'{v:X}' for v in v_values]}")

# 按MC输出掩码分组（显示前10个最常见的）
print("\n按MC输出掩码分组（前10个最常见）：")
mc_out_stats = defaultdict(int)
for path in all_paths:
    mc_out_stats[path['mc_output_mask']] += 1

sorted_mc = sorted(mc_out_stats.items(), key=lambda x: x[1], reverse=True)
for mc_out, count in sorted_mc[:10]:
    print(f"  MC输出 0x{mc_out:08X}: {count} 条路径")

# 统计不同输出掩码数量
unique_mc_outputs = len(set(p['mc_output_mask'] for p in all_paths))
print(f"\n唯一的MC输出掩码数量: {unique_mc_outputs}")

# ==================== 输出简洁格式 ====================
print("\n" + "=" * 80)
print("简洁格式（十六进制）")
print("=" * 80)
print("输入掩码 -> S盒输出掩码 -> SR输出掩码 -> MC输出掩码")

for path in all_paths[:20]:
    print(f"0x{path['input_mask']:08X} -> 0x{path['sbox_output_mask']:08X} -> "
          f"0x{path['sr_output_mask']:08X} -> 0x{path['mc_output_mask']:08X}")

if len(all_paths) > 20:
    print(f"... 共 {len(all_paths)} 条")

# ==================== 保存到文件 ====================
with open("half_correlation_paths.txt", "w") as f:
    f.write("一轮搜索相关系数绝对值为0.5的所有路径\n")
    f.write("=" * 80 + "\n\n")

    f.write(f"S盒相关系数绝对值为0.5的(u,v)对: {len(half_corr_pairs)}对\n")
    for u, v, c in half_corr_pairs:
        f.write(f"  u={u:2X} ({u:04b}) -> v={v:2X} ({v:04b}), corr={c:+.1f}\n")

    f.write(f"\n总路径数: {len(all_paths)}\n")
    f.write("=" * 80 + "\n\n")

    for idx, path in enumerate(all_paths):
        f.write(f"路径 {idx + 1}:\n")
        f.write(f"  位置: {path['position']}\n")
        f.write(f"  u={path['u']:X}, v={path['v']:X}, 相关系数={path['correlation']:+.1f}\n")
        f.write(f"  输入掩码: 0x{path['input_mask']:08X}\n")
        f.write(f"  输入半字节: {format_nibbles_hex(path['input_nibbles'])}\n")
        f.write(f"  S盒输出掩码: 0x{path['sbox_output_mask']:08X}\n")
        f.write(f"  S盒输出半字节: {format_nibbles_hex(path['sbox_out_nibbles'])}\n")
        f.write(f"  SR置换后: 0x{path['sr_output_mask']:08X}\n")
        f.write(f"  SR输出半字节: {format_nibbles_hex(path['sr_out_nibbles'])}\n")
        f.write(f"  MC变换后: 0x{path['mc_output_mask']:08X}\n")
        f.write(f"  MC输出半字节: {format_nibbles_hex(path['mc_out_nibbles'])}\n")
        f.write("-" * 40 + "\n")

print("\n详细结果已保存到 half_correlation_paths.txt")
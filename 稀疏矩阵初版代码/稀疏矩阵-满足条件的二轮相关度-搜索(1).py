# import numpy as np
# from collections import defaultdict
# from itertools import product
# from typing import List, Dict, Tuple, Set
# import json
#
# # S-box (4x4)
# S_box = [0xC, 0x6, 0x9, 0x0, 0x1, 0xA, 0x2, 0xB,
#          0x3, 0x8, 0x5, 0xD, 0x4, 0xE, 0x7, 0xF]
#
# N = 16
# CS = np.zeros((N, N), dtype=float)
#
# # 计算相关系数矩阵
# for v in range(N):
#     for u in range(N):
#         s = 0
#         for x in range(N):
#             dot_ux = bin(u & x).count('1') % 2
#             dot_vSx = bin(v & S_box[x]).count('1') % 2
#             s += (-1) ** (dot_ux ^ dot_vSx)
#         CS[v, u] = s / 16.0
#
# # 正向字典
# forward_dict = defaultdict(list)
# for u in range(1, N):
#     for v in range(N):
#         if CS[v, u] != 0:
#             forward_dict[u].append((v, CS[v, u]))
#
# # 反向字典
# backward_dict = defaultdict(list)
# for u in range(1, N):
#     for v in range(N):
#         if CS[v, u] != 0:
#             backward_dict[v].append((u, CS[v, u]))
#
# # 置换
# P = [0, 5, 2, 7, 4, 1, 6, 3]
# inv_P = [0] * 8
# for i, p in enumerate(P):
#     inv_P[p] = i
#
#
# def apply_permutation(masks):
#     return [masks[i] for i in P]
#
#
# def apply_permutation_inverse(masks):
#     return [masks[i] for i in inv_P]
#
#
# def get_output_mask_from_input_mixcolumns(input_masks):
#     x0, x1, x2, x3 = input_masks
#     y0 = y1 = y2 = y3 = 0
#     for bit in range(4):
#         a0 = (x0 >> bit) & 1
#         a1 = (x1 >> bit) & 1
#         a2 = (x2 >> bit) & 1
#         a3 = (x3 >> bit) & 1
#         y0_bit = a3
#         y1_bit = a0 ^ a1 ^ a2
#         y2_bit = a1
#         y3_bit = a1 ^ a2 ^ a3
#         y0 |= (y0_bit << bit)
#         y1 |= (y1_bit << bit)
#         y2 |= (y2_bit << bit)
#         y3 |= (y3_bit << bit)
#     return [y0, y1, y2, y3]
#
#
# def get_input_mask_from_output_mixcolumns(output_masks):
#     y0, y1, y2, y3 = output_masks
#     x0 = x1 = x2 = x3 = 0
#     for bit in range(4):
#         b0 = (y0 >> bit) & 1
#         b1 = (y1 >> bit) & 1
#         b2 = (y2 >> bit) & 1
#         b3 = (y3 >> bit) & 1
#         a3 = b0
#         a1 = b2
#         a2 = a1 ^ a3 ^ b3
#         a0 = b1 ^ a1 ^ a2
#         x0 |= (a0 << bit)
#         x1 |= (a1 << bit)
#         x2 |= (a2 << bit)
#         x3 |= (a3 << bit)
#     return [x0, x1, x2, x3]
#
#
# def get_sbox_forward_paths(input_mask):
#     if input_mask == 0:
#         return [(0, 1.0)]
#     return forward_dict[input_mask]
#
#
# def forward_search_round(input_masks: List[int]) -> Dict[tuple, List]:
#     """
#     正向搜索一轮加密
#     输入: 8个输入掩码
#     返回: 字典 {输出掩码元组: [(路径详细信息)]}
#     """
#     results = defaultdict(list)
#
#     sbox_paths_list = []
#     for in_mask in input_masks:
#         sbox_paths_list.append(get_sbox_forward_paths(in_mask))
#
#     for combo in product(*sbox_paths_list):
#         sbox_outputs = [p[0] for p in combo]
#         sbox_corrs = [p[1] for p in combo]
#
#         current_corr = np.prod(sbox_corrs)
#         if current_corr == 0:
#             continue
#
#         permuted = apply_permutation(sbox_outputs)
#
#         group1 = permuted[0:4]
#         group2 = permuted[4:8]
#         mix_out1 = get_output_mask_from_input_mixcolumns(group1)
#         mix_out2 = get_output_mask_from_input_mixcolumns(group2)
#         final_masks = tuple(mix_out1 + mix_out2)
#
#         # 存储路径信息
#         results[final_masks].append({
#             'sbox_outputs': sbox_outputs,
#             'sbox_corrs': sbox_corrs,
#             'permuted': permuted,
#             'correlation': current_corr
#         })
#
#     return results
#
#
# def find_two_round_paths_for_single_active_sbox(sbox_index: int, input_mask_value: int):
#     """
#     对于只有一个活跃S盒的输入掩码，找出所有两轮路径
#     返回: {输出掩码: {'total_correlation': 总相关度, 'paths': [所有路径详细信息]}}
#     """
#     # 构造输入掩码
#     input_masks = [0] * 8
#     input_masks[sbox_index] = input_mask_value
#
#     # 正向搜索第一轮（返回带路径信息的字典）
#     first_round_results = forward_search_round(input_masks)
#
#     # 存储最终结果
#     final_results = defaultdict(lambda: {'total_correlation': 0.0, 'paths': []})
#
#     # 对每个中间掩码，继续第二轮搜索
#     for mid_mask, first_round_paths in first_round_results.items():
#         # 计算第一轮的总相关度（所有到达此中间掩码的路径相关度之和）
#         first_round_total = sum(p['correlation'] for p in first_round_paths)
#
#         # 第二轮搜索
#         second_round_results = forward_search_round(list(mid_mask))
#
#         # 对每个第二轮输出
#         for final_mask, second_round_paths in second_round_results.items():
#             # 计算第二轮的总相关度（所有从此中间掩码出发到达输出掩码的路径相关度之和）
#             second_round_total = sum(p['correlation'] for p in second_round_paths)
#
#             # 总相关度贡献 = 第一轮总相关度 × 第二轮总相关度
#             contribution = first_round_total * second_round_total
#             final_results[final_mask]['total_correlation'] += contribution
#
#             # 存储详细路径信息（用于展示，但不用于计算）
#             for fp in first_round_paths:
#                 for sp in second_round_paths:
#                     final_results[final_mask]['paths'].append({
#                         'first_round': {
#                             'sbox_outputs': fp['sbox_outputs'],
#                             'sbox_corrs': fp['sbox_corrs'],
#                             'permuted': fp['permuted'],
#                             'correlation': fp['correlation']
#                         },
#                         'second_round': {
#                             'sbox_outputs': sp['sbox_outputs'],
#                             'sbox_corrs': sp['sbox_corrs'],
#                             'permuted': sp['permuted'],
#                             'correlation': sp['correlation']
#                         },
#                         'mid_mask': list(mid_mask),
#                         'path_correlation': fp['correlation'] * sp['correlation']
#                     })
#
#     return dict(final_results)
#
#
# def search_all_single_active_sbox(threshold=1 / 16):
#     """
#     搜索所有只有一个活跃S盒的输入掩码
#     返回所有相关度绝对值大于threshold的结果
#     """
#     all_results = []
#
#     print("=" * 100)
#     print("搜索所有只有一个活跃S盒的输入掩码（掩码值1-15）")
#     print("=" * 100)
#
#     for sbox_idx in range(8):
#         print(f"\n正在处理 S{sbox_idx}...")
#
#         for mask_val in range(1, 16):
#             # 计算该输入掩码的所有两轮路径
#             results = find_two_round_paths_for_single_active_sbox(sbox_idx, mask_val)
#
#             # 筛选相关度绝对值大于threshold的输出掩码
#             for final_mask, data in results.items():
#                 total_corr = data['total_correlation']
#                 if abs(total_corr) > threshold:
#                     all_results.append({
#                         'input_sbox': sbox_idx,
#                         'input_mask_value': mask_val,
#                         'input_mask_hex': hex(mask_val),
#                         'output_mask': list(final_mask),
#                         'output_mask_hex': [hex(m) for m in final_mask],
#                         'total_correlation': total_corr,
#                         'abs_correlation': abs(total_corr),
#                         'num_paths': len(data['paths']),
#                         'paths': data['paths']
#                     })
#
#     # 按相关度绝对值排序
#     all_results.sort(key=lambda x: x['abs_correlation'], reverse=True)
#
#     return all_results
#
#
# def print_detailed_results(results):
#     """打印详细结果，包括所有路径"""
#     print("\n" + "=" * 100)
#     print(f"找到 {len(results)} 个相关度绝对值大于 1/16 的输入-输出掩码对")
#     print("=" * 100)
#
#     for idx, r in enumerate(results):
#         print(f"\n{'=' * 80}")
#         print(f"结果 {idx + 1}:")
#         print(f"{'=' * 80}")
#         print(f"输入掩码: S{r['input_sbox']} = {r['input_mask_hex']}")
#         print(f"输出掩码: {r['output_mask_hex']}")
#         print(f"总相关度: {r['total_correlation']:+.8f} (绝对值: {r['abs_correlation']:.8f})")
#         print(f"路径数量: {r['num_paths']}")
#
#         print(f"\n所有路径详细信息:")
#
#         # 验证：计算所有路径相关度之和
#         paths_sum = sum(p['path_correlation'] for p in r['paths'])
#
#         for path_idx, path in enumerate(r['paths']):
#             print(f"\n  --- 路径 {path_idx + 1} ---")
#             print(f"    中间掩码: {[hex(m) for m in path['mid_mask']]}")
#             print(f"    第一轮相关度: {path['first_round']['correlation']:+.8f}")
#             print(f"    第二轮相关度: {path['second_round']['correlation']:+.8f}")
#             print(f"    路径贡献: {path['path_correlation']:+.8f}")
#
#         print(f"\n  ✓ 所有路径贡献之和: {paths_sum:+.8f}")
#         print(f"  ✓ 总相关度: {r['total_correlation']:+.8f}")
#         print(f"  ✓ 验证: {'通过' if abs(paths_sum - r['total_correlation']) < 1e-10 else '失败'}")
#
#
# def export_to_json(results, filename="two_round_paths_detailed.json"):
#     """导出结果到JSON文件"""
#
#     def convert_to_serializable(obj):
#         if isinstance(obj, np.float64) or isinstance(obj, np.float32):
#             return float(obj)
#         if isinstance(obj, np.int64) or isinstance(obj, np.int32):
#             return int(obj)
#         if isinstance(obj, tuple):
#             return list(obj)
#         return obj
#
#     export_data = []
#     for r in results:
#         export_item = {
#             'input_sbox': r['input_sbox'],
#             'input_mask_value': r['input_mask_value'],
#             'input_mask_hex': r['input_mask_hex'],
#             'output_mask': r['output_mask'],
#             'output_mask_hex': r['output_mask_hex'],
#             'total_correlation': r['total_correlation'],
#             'abs_correlation': r['abs_correlation'],
#             'num_paths': r['num_paths'],
#             'paths': []
#         }
#
#         for path in r['paths']:
#             export_item['paths'].append({
#                 'mid_mask': [int(m) for m in path['mid_mask']],
#                 'mid_mask_hex': [hex(int(m)) for m in path['mid_mask']],
#                 'first_round_correlation': float(path['first_round']['correlation']),
#                 'second_round_correlation': float(path['second_round']['correlation']),
#                 'path_correlation': float(path['path_correlation'])
#             })
#
#         export_data.append(export_item)
#
#     with open(filename, 'w') as f:
#         json.dump(export_data, f, indent=2, default=convert_to_serializable)
#
#     print(f"\n详细结果已导出到 {filename}")
#
#
# def print_statistics(results):
#     """打印统计信息"""
#     print("\n" + "=" * 100)
#     print("统计信息")
#     print("=" * 100)
#
#     if not results:
#         print("没有找到符合条件的结果")
#         return
#
#     # 按输入掩码值统计
#     by_mask_value = defaultdict(list)
#     for r in results:
#         by_mask_value[r['input_mask_value']].append(r)
#
#     print("\n按输入掩码值分布:")
#     for val in sorted(by_mask_value.keys()):
#         max_corr = max(by_mask_value[val], key=lambda x: x['abs_correlation'])
#         print(f"  {hex(val)}: {len(by_mask_value[val])} 个输出掩码, "
#               f"最大相关度: {max_corr['total_correlation']:+.8f}")
#
#     # 按活跃S盒位置统计
#     by_sbox = defaultdict(list)
#     for r in results:
#         by_sbox[r['input_sbox']].append(r)
#
#     print("\n按活跃S盒位置分布:")
#     for idx in range(8):
#         if idx in by_sbox:
#             max_corr = max(by_sbox[idx], key=lambda x: x['abs_correlation'])
#             print(f"  S{idx}: {len(by_sbox[idx])} 个输出掩码, "
#                   f"最大相关度: {max_corr['total_correlation']:+.8f}")
#         else:
#             print(f"  S{idx}: 0 个输出掩码")
#
#     # 统计所有路径相关度之和与总相关度的一致性
#     print("\n验证所有结果的一致性:")
#     consistent = 0
#     for r in results:
#         paths_sum = sum(p['path_correlation'] for p in r['paths'])
#         if abs(paths_sum - r['total_correlation']) < 1e-10:
#             consistent += 1
#     print(f"  通过验证的结果数: {consistent}/{len(results)}")
#
#     # 最大相关度
#     max_result = max(results, key=lambda x: x['abs_correlation'])
#     print(f"\n最大相关度: {max_result['total_correlation']:+.8f}")
#     print(f"  输入: S{max_result['input_sbox']} = {max_result['input_mask_hex']}")
#     print(f"  输出: {max_result['output_mask_hex']}")
#     print(f"  路径数: {max_result['num_paths']}")
#
#
# if __name__ == "__main__":
#     threshold = 1 / 16
#
#     # 搜索所有单活跃S盒的输入掩码
#     all_results = search_all_single_active_sbox(threshold=threshold)
#
#     # 打印详细结果（包含所有路径）
#     print_detailed_results(all_results)
#
#     # 打印统计信息
#     print_statistics(all_results)
#
#     # 导出到JSON文件
#     export_to_json(all_results, "two_round_paths_detailed.json")
#
#     # 示例：打印第一个结果的完整信息
#     if all_results:
#         print("\n" + "=" * 100)
#         print("示例：第一个结果的完整路径信息")
#         print("=" * 100)
#         first = all_results[0]
#         print(f"\n输入掩码: S{first['input_sbox']} = {first['input_mask_hex']}")
#         print(f"输出掩码: {first['output_mask_hex']}")
#         print(f"总相关度: {first['total_correlation']:+.8f}")
#         print(f"\n共 {first['num_paths']} 条路径到达此输出掩码:")
#
#         total_check = 0
#         for i, path in enumerate(first['paths']):
#             print(f"\n路径 {i + 1}:")
#             print(f"  中间掩码: {[hex(m) for m in path['mid_mask']]}")
#             print(f"  第一轮相关度: {path['first_round']['correlation']:+.6f}")
#             print(f"  第二轮相关度: {path['second_round']['correlation']:+.6f}")
#             print(f"  路径贡献: {path['path_correlation']:+.6f}")
#             total_check += path['path_correlation']
#
#         print(f"\n验证：所有路径贡献之和 = {total_check:+.8f}")
#         print(f"总相关度 = {first['total_correlation']:+.8f}")
#         print(f"一致性: {'通过' if abs(total_check - first['total_correlation']) < 1e-10 else '失败'}")


import numpy as np
from collections import defaultdict
from itertools import product
from typing import List, Dict, Tuple, Set
import json
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils.dataframe import dataframe_to_rows

# S-box (4x4)
S_box = [0xC, 0x6, 0x9, 0x0, 0x1, 0xA, 0x2, 0xB,
         0x3, 0x8, 0x5, 0xD, 0x4, 0xE, 0x7, 0xF]

N = 16
CS = np.zeros((N, N), dtype=float)

# 计算相关系数矩阵
for v in range(N):
    for u in range(N):
        s = 0
        for x in range(N):
            dot_ux = bin(u & x).count('1') % 2
            dot_vSx = bin(v & S_box[x]).count('1') % 2
            s += (-1) ** (dot_ux ^ dot_vSx)
        CS[v, u] = s / 16.0

# 正向字典
forward_dict = defaultdict(list)
for u in range(1, N):
    for v in range(N):
        if CS[v, u] != 0:
            forward_dict[u].append((v, CS[v, u]))

# 反向字典
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
    return [masks[i] for i in P]


def apply_permutation_inverse(masks):
    return [masks[i] for i in inv_P]


def get_output_mask_from_input_mixcolumns(input_masks):
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
    y0, y1, y2, y3 = output_masks
    x0 = x1 = x2 = x3 = 0
    for bit in range(4):
        b0 = (y0 >> bit) & 1
        b1 = (y1 >> bit) & 1
        b2 = (y2 >> bit) & 1
        b3 = (y3 >> bit) & 1
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
    if input_mask == 0:
        return [(0, 1.0)]
    return forward_dict[input_mask]


def forward_search_round(input_masks: List[int]) -> Dict[tuple, List]:
    """
    正向搜索一轮加密
    输入: 8个输入掩码
    返回: 字典 {输出掩码元组: [(路径详细信息)]}
    """
    results = defaultdict(list)

    sbox_paths_list = []
    for in_mask in input_masks:
        sbox_paths_list.append(get_sbox_forward_paths(in_mask))

    for combo in product(*sbox_paths_list):
        sbox_outputs = [p[0] for p in combo]
        sbox_corrs = [p[1] for p in combo]

        current_corr = np.prod(sbox_corrs)
        if current_corr == 0:
            continue

        permuted = apply_permutation(sbox_outputs)

        group1 = permuted[0:4]
        group2 = permuted[4:8]
        mix_out1 = get_output_mask_from_input_mixcolumns(group1)
        mix_out2 = get_output_mask_from_input_mixcolumns(group2)
        final_masks = tuple(mix_out1 + mix_out2)

        # 存储路径信息
        results[final_masks].append({
            'sbox_outputs': sbox_outputs,
            'sbox_corrs': sbox_corrs,
            'permuted': permuted,
            'correlation': current_corr
        })

    return results


def find_two_round_paths_for_single_active_sbox(sbox_index: int, input_mask_value: int):
    """
    对于只有一个活跃S盒的输入掩码，找出所有两轮路径
    返回: {输出掩码: {'total_correlation': 总相关度, 'paths': [所有路径详细信息]}}
    """
    # 构造输入掩码
    input_masks = [0] * 8
    input_masks[sbox_index] = input_mask_value

    # 正向搜索第一轮（返回带路径信息的字典）
    first_round_results = forward_search_round(input_masks)

    # 存储最终结果
    final_results = defaultdict(lambda: {'total_correlation': 0.0, 'paths': []})

    # 对每个中间掩码，继续第二轮搜索
    for mid_mask, first_round_paths in first_round_results.items():
        # 计算第一轮的总相关度（所有到达此中间掩码的路径相关度之和）
        first_round_total = sum(p['correlation'] for p in first_round_paths)

        # 第二轮搜索
        second_round_results = forward_search_round(list(mid_mask))

        # 对每个第二轮输出
        for final_mask, second_round_paths in second_round_results.items():
            # 计算第二轮的总相关度（所有从此中间掩码出发到达输出掩码的路径相关度之和）
            second_round_total = sum(p['correlation'] for p in second_round_paths)

            # 总相关度贡献 = 第一轮总相关度 × 第二轮总相关度
            contribution = first_round_total * second_round_total
            final_results[final_mask]['total_correlation'] += contribution

            # 存储详细路径信息（用于展示，但不用于计算）
            for fp in first_round_paths:
                for sp in second_round_paths:
                    final_results[final_mask]['paths'].append({
                        'first_round': {
                            'sbox_outputs': fp['sbox_outputs'],
                            'sbox_corrs': fp['sbox_corrs'],
                            'permuted': fp['permuted'],
                            'correlation': fp['correlation']
                        },
                        'second_round': {
                            'sbox_outputs': sp['sbox_outputs'],
                            'sbox_corrs': sp['sbox_corrs'],
                            'permuted': sp['permuted'],
                            'correlation': sp['correlation']
                        },
                        'mid_mask': list(mid_mask),
                        'path_correlation': fp['correlation'] * sp['correlation']
                    })

    return dict(final_results)


def search_all_single_active_sbox(threshold):
    """
    搜索所有只有一个活跃S盒的输入掩码
    返回所有相关度绝对值大于threshold的结果
    """
    all_results = []

    print("=" * 100)
    print("搜索所有只有一个活跃S盒的输入掩码（掩码值1-15）")
    print("=" * 100)

    for sbox_idx in range(8):
        print(f"\n正在处理 S{sbox_idx}...")

        for mask_val in range(1, 16):
            # 计算该输入掩码的所有两轮路径
            results = find_two_round_paths_for_single_active_sbox(sbox_idx, mask_val)

            # 筛选相关度绝对值大于threshold的输出掩码
            for final_mask, data in results.items():
                total_corr = data['total_correlation']

                if (threshold == 1 and abs(total_corr) == threshold) or (threshold < 1 and abs(total_corr) > threshold):
                    all_results.append({
                        'input_sbox': sbox_idx,
                        'input_mask_value': mask_val,
                        'input_mask_hex': hex(mask_val),
                        'output_mask': list(final_mask),
                        'output_mask_hex': [hex(m) for m in final_mask],
                        'total_correlation': total_corr,
                        'abs_correlation': abs(total_corr),
                        'num_paths': len(data['paths']),
                        'paths': data['paths']
                    })

    # 按相关度绝对值排序
    all_results.sort(key=lambda x: x['abs_correlation'], reverse=True)

    return all_results


def export_to_excel(results, filename="linear_cryptanalysis_results.xlsx"):
    """
    导出结果到Excel文件，包含多个工作表：
    1. 汇总表：输入掩码、输出掩码、总相关度、路径数
    2. 详细路径：所有路径的详细信息
    3. 按输入分组：按输入掩码分组统计
    """
    print(f"\n正在生成Excel文件: {filename}")

    with pd.ExcelWriter(filename, engine='openpyxl') as writer:

        # ========== 工作表1：汇总表 ==========
        print("生成汇总表...")
        summary_data = []
        for idx, r in enumerate(results):
            summary_data.append({
                '序号': idx + 1,
                '输入S盒': f"S{r['input_sbox']}",
                '输入掩码(十六进制)': r['input_mask_hex'],
                '输入掩码(十进制)': r['input_mask_value'],
                '输出掩码(十六进制)': ', '.join(r['output_mask_hex']),
                '输出掩码(十进制)': ', '.join([str(m) for m in r['output_mask']]),
                '总相关度': r['total_correlation'],
                '绝对值': r['abs_correlation'],
                '路径数': r['num_paths']
            })

        df_summary = pd.DataFrame(summary_data)
        df_summary.to_excel(writer, sheet_name='汇总表', index=False)

        # 调整汇总表列宽
        worksheet = writer.sheets['汇总表']
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width

        # ========== 工作表2：详细路径 ==========
        print("生成详细路径表...")
        path_data = []
        for idx, r in enumerate(results):
            for path_idx, path in enumerate(r['paths']):
                path_data.append({
                    '序号': idx + 1,
                    '输入S盒': f"S{r['input_sbox']}",
                    '输入掩码': r['input_mask_hex'],
                    '输出掩码': ', '.join(r['output_mask_hex']),
                    '路径编号': path_idx + 1,
                    '中间掩码': ', '.join([hex(m) for m in path['mid_mask']]),
                    '第一轮总相关度': path['first_round']['correlation'],
                    '第二轮总相关度': path['second_round']['correlation'],
                    '路径相关度(乘积)': path['path_correlation'],
                    '第一轮S盒输出': ', '.join([hex(m) for m in path['first_round']['sbox_outputs']]),
                    '第一轮S盒相关系数': ', '.join([f"{c:+.4f}" for c in path['first_round']['sbox_corrs']]),
                    '第二轮S盒输出': ', '.join([hex(m) for m in path['second_round']['sbox_outputs']]),
                    '第二轮S盒相关系数': ', '.join([f"{c:+.4f}" for c in path['second_round']['sbox_corrs']]),
                    '第一轮置换后': ', '.join([hex(m) for m in path['first_round']['permuted']]),
                    '第二轮置换后': ', '.join([hex(m) for m in path['second_round']['permuted']])
                })

        df_paths = pd.DataFrame(path_data)
        df_paths.to_excel(writer, sheet_name='详细路径', index=False)

        # ========== 工作表3：按输入分组统计 ==========
        print("生成分组统计表...")
        grouped_data = []
        seen_inputs = set()  # 用set来避免重复

        for r in results:
            key = (r['input_sbox'], r['input_mask_value'])

            if key not in seen_inputs:
                seen_inputs.add(key)

                # 收集该输入的所有输出掩码和相关度
                outputs = []
                corrs = []
                for other in results:
                    if other['input_sbox'] == r['input_sbox'] and other['input_mask_value'] == r['input_mask_value']:
                        outputs.append(', '.join(other['output_mask_hex']))
                        corrs.append(other['total_correlation'])

                grouped_data.append({
                    '输入S盒': f"S{r['input_sbox']}",
                    '输入S盒数值': r['input_sbox'],
                    '输入掩码(十六进制)': r['input_mask_hex'],
                    '输入掩码(十进制)': r['input_mask_value'],
                    '输出掩码数量': len(outputs),
                    '最大相关度': max(corrs, key=abs),
                    '最大相关度绝对值': abs(max(corrs, key=abs)),
                    '最小相关度': min(corrs, key=abs),
                    '平均相关度绝对值': np.mean([abs(c) for c in corrs])
                })

        df_grouped = pd.DataFrame(grouped_data)
        df_grouped = df_grouped.sort_values('最大相关度绝对值', ascending=False)
        df_grouped.to_excel(writer, sheet_name='按输入分组', index=False)

        # ========== 工作表4：路径贡献分析 ==========
        print("生成路径贡献分析表...")
        contribution_data = []
        for idx, r in enumerate(results):
            # 计算该输入-输出对的所有路径贡献
            path_contributions = [p['path_correlation'] for p in r['paths']]
            total = r['total_correlation']

            for path_idx, contrib in enumerate(path_contributions):
                contribution_data.append({
                    '序号': idx + 1,
                    '输入S盒': f"S{r['input_sbox']}",
                    '输入掩码': r['input_mask_hex'],
                    '输出掩码': ', '.join(r['output_mask_hex']),
                    '路径编号': path_idx + 1,
                    '路径贡献': contrib,
                    '占总相关度比例(%)': (contrib / total * 100) if total != 0 else 0,
                    '贡献符号': '正' if contrib > 0 else '负'
                })

        df_contrib = pd.DataFrame(contribution_data)
        df_contrib.to_excel(writer, sheet_name='路径贡献分析', index=False)

        # ========== 工作表5：统计摘要 ==========
        print("生成统计摘要...")
        summary_stats = {
            '统计项': [
                '总输入-输出对数量',
                '不同输入掩码数量',
                '最大相关度',
                '最小相关度',
                '平均相关度绝对值',
                '中位数相关度绝对值',
                '总路径数',
                '平均每条路径数',
                '最大路径数(单对)',
                '正相关度数量',
                '负相关度数量'
            ],
            '值': [
                len(results),
                len(set((r['input_sbox'], r['input_mask_value']) for r in results)),
                max(results, key=lambda x: x['abs_correlation'])['total_correlation'],
                min(results, key=lambda x: x['abs_correlation'])['total_correlation'],
                np.mean([r['abs_correlation'] for r in results]),
                np.median([r['abs_correlation'] for r in results]),
                sum(r['num_paths'] for r in results),
                np.mean([r['num_paths'] for r in results]),
                max(r['num_paths'] for r in results),
                len([r for r in results if r['total_correlation'] > 0]),
                len([r for r in results if r['total_correlation'] < 0])
            ]
        }

        df_stats = pd.DataFrame(summary_stats)
        df_stats.to_excel(writer, sheet_name='统计摘要', index=False)

    print(f"✓ Excel文件已成功生成: {filename}")
    print(f"  包含工作表: 汇总表, 详细路径, 按输入分组, 路径贡献分析, 统计摘要")


def print_detailed_results(results, max_display=10):
    """打印前几个结果的详细信息（控制台输出）"""
    print("\n" + "=" * 100)
    print(f"找到 {len(results)} 个相关度绝对值大于 1/16 的输入-输出掩码对")
    print("=" * 100)

    # 只显示前max_display个结果
    display_count = min(max_display, len(results))

    for idx in range(display_count):
        r = results[idx]
        print(f"\n{'=' * 80}")
        print(f"结果 {idx + 1}:")
        print(f"{'=' * 80}")
        print(f"输入掩码: S{r['input_sbox']} = {r['input_mask_hex']}")
        print(f"输出掩码: {r['output_mask_hex']}")
        print(f"总相关度: {r['total_correlation']:+.8f} (绝对值: {r['abs_correlation']:.8f})")
        print(f"路径数量: {r['num_paths']}")

        # 显示前3条路径作为示例
        print(f"\n前3条路径示例:")
        for path_idx, path in enumerate(r['paths'][:3]):
            print(f"\n  路径 {path_idx + 1}:")
            print(f"    中间掩码: {[hex(m) for m in path['mid_mask']]}")
            print(f"    第一轮相关度: {path['first_round']['correlation']:+.6f}")
            print(f"    第二轮相关度: {path['second_round']['correlation']:+.6f}")
            print(f"    路径贡献: {path['path_correlation']:+.6f}")

        if r['num_paths'] > 3:
            print(f"\n  ... 还有 {r['num_paths'] - 3} 条路径，详见Excel文件")

    if len(results) > display_count:
        print(f"\n... 还有 {len(results) - display_count} 个结果，详见Excel文件")


if __name__ == "__main__":
    threshold = 1/16

    # 搜索所有单活跃S盒的输入掩码
    all_results = search_all_single_active_sbox(threshold=threshold)

    # 在控制台打印前10个结果的摘要
    print_detailed_results(all_results, max_display=10)

    # 导出到Excel文件（包含所有详细信息）
    export_to_excel(all_results, "linear_cryptanalysis_results.xlsx")

    print("\n" + "=" * 100)
    print("处理完成！")
    print("=" * 100)
    print(f"Excel文件已生成，包含以下信息：")
    print(f"  - 汇总表: {len(all_results)} 个输入-输出掩码对")
    print(f"  - 详细路径: {sum(r['num_paths'] for r in all_results)} 条路径")
    print(f"  - 按输入分组: {len(set((r['input_sbox'], r['input_mask_value']) for r in all_results))} 个不同输入")
    print(f"  - 路径贡献分析: 每条路径的贡献度")
    print(f"  - 统计摘要: 整体统计信息")
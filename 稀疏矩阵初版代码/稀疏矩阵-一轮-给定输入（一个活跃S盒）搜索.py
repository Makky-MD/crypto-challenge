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


def get_sbox_forward_paths(input_mask):
    """获取单个S盒的正向路径"""
    if input_mask == 0:
        return [(0, 1.0)]
    return forward_dict[input_mask]


def forward_search_round_full(input_masks: List[int]) -> Dict[tuple, float]:
    """
    正向搜索一轮加密，返回所有相关度非零的路径
    输入: 8个输入掩码 [m0,...,m7]
    返回: 字典 {输出掩码元组: 总相关度}，只包含相关度不为0的路径
    """
    results = defaultdict(float)

    # 获取每个S盒的路径
    sbox_paths_list = []
    active_positions = []
    for i, in_mask in enumerate(input_masks):
        paths = get_sbox_forward_paths(in_mask)
        sbox_paths_list.append(paths)
        if in_mask != 0:
            active_positions.append(i)

    # 计算总组合数
    total_combinations = 1
    for paths in sbox_paths_list:
        total_combinations *= len(paths)

    print(f"\nS盒路径组合总数: {total_combinations}")
    print(f"活跃S盒位置: {active_positions}")

    # 遍历所有S盒组合
    combo_count = 0
    for combo in product(*sbox_paths_list):
        combo_count += 1
        if combo_count % 100000 == 0:
            print(f"  已处理 {combo_count}/{total_combinations} 组合...")

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

    print(f"  处理完成，找到 {len(results)} 个不同的输出掩码")

    return results


def print_round_paths(input_masks: List[int], detailed: bool = True):
    """
    打印给定输入掩码的一轮所有路径
    """
    print("=" * 80)
    print(f"输入掩码分析")
    print("=" * 80)

    # 打印输入掩码
    print("\n输入掩码 (8个半字节):")
    for i, mask in enumerate(input_masks):
        if mask != 0:
            print(f"  位置 {i}: 0x{mask:X} ({mask:04b})")
        else:
            print(f"  位置 {i}: 0x{mask:X}")

    # 搜索所有路径
    print("\n正在搜索一轮所有相关度非零的路径...")
    results = forward_search_round_full(input_masks)

    # 按相关度绝对值排序
    sorted_results = sorted(results.items(), key=lambda x: abs(x[1]), reverse=True)

    print("\n" + "=" * 80)
    print(f"搜索结果统计")
    print("=" * 80)
    print(f"找到 {len(results)} 条不同的输出掩码路径")
    print(f"总相关度和: {sum(results.values()):.8f}")

    # 输出所有输出掩码的集合
    print("\n" + "=" * 80)
    print("所有输出掩码集合")
    print("=" * 80)

    output_masks_set = set()
    for output_mask_tuple in results.keys():
        output_masks_set.add(output_mask_tuple)

    print(f"\n共 {len(output_masks_set)} 个不同的输出掩码元组\n")

    for i, output_mask in enumerate(sorted(output_masks_set)):
        hex_mask = [f"0x{m:X}" for m in output_mask]
        print(f"{i + 1:3d}. {hex_mask}")

    # 详细输出每条路径
    if detailed:
        print("\n" + "=" * 80)
        print("详细路径列表（按相关度绝对值排序）")
        print("=" * 80)

        for i, (output_mask, corr) in enumerate(sorted_results[:50]):  # 最多显示50条
            hex_mask = [f"0x{m:X}" for m in output_mask]
            print(f"\n{i + 1}. 相关度: {corr:+.8f} (|{abs(corr):.8f}|)")
            print(f"   输出掩码: {hex_mask}")

            # 显示非零的输出掩码位置
            active_outputs = [(j, m) for j, m in enumerate(output_mask) if m != 0]
            if active_outputs:
                print(f"   活跃输出位置: {[(pos, f'0x{m:X}') for pos, m in active_outputs]}")

        if len(sorted_results) > 50:
            print(f"\n... 还有 {len(sorted_results) - 50} 条路径未显示")

    return results, output_masks_set


def analyze_input_mask_variations():
    """
    分析所有单活性S盒的输入掩码
    """
    print("\n" + "=" * 80)
    print("分析所有单活性S盒的输入掩码")
    print("=" * 80)

    all_results = {}

    # 测试所有非零的输入掩码值
    test_masks = list(range(1, 16))

    for test_mask in test_masks:
        print(f"\n{'=' * 60}")
        print(f"测试输入掩码值: 0x{test_mask:X} ({test_mask:04b})")
        print(f"{'=' * 60}")

        for pos in range(8):
            input_masks = [0] * 8
            input_masks[pos] = test_mask

            print(f"\n--- 位置 {pos} ---")
            results, output_set = print_round_paths(input_masks, detailed=False)

            key = (pos, test_mask)
            all_results[key] = {
                'input_masks': input_masks.copy(),
                'results': results,
                'output_set': output_set,
                'num_paths': len(results),
                'num_unique_outputs': len(output_set)
            }

            # 打印简要统计
            print(f"\n简要统计:")
            print(f"  路径数量: {len(results)}")
            print(f"  不同输出掩码数: {len(output_set)}")
            print(f"  最大相关度: {max(abs(c) for c in results.values()):.8f}")

    return all_results


def save_results_to_file(input_masks: List[int], results: Dict, output_set: Set, filename: str = "round_paths.txt"):
    """
    保存结果到文件
    """
    with open(filename, "w") as f:
        f.write("=" * 80 + "\n")
        f.write("一轮SPN线性路径分析结果\n")
        f.write("=" * 80 + "\n\n")

        f.write("输入掩码:\n")
        for i, mask in enumerate(input_masks):
            f.write(f"  位置 {i}: 0x{mask:X} ({mask:04b})\n")

        f.write(f"\n总共找到 {len(results)} 条路径\n")
        f.write(f"不同的输出掩码元组: {len(output_set)} 个\n\n")

        f.write("=" * 80 + "\n")
        f.write("所有输出掩码集合\n")
        f.write("=" * 80 + "\n\n")

        for i, output_mask in enumerate(sorted(output_set)):
            hex_mask = [f"0x{m:X}" for m in output_mask]
            f.write(f"{i + 1:3d}. {hex_mask}\n")

        f.write("\n" + "=" * 80 + "\n")
        f.write("详细路径列表（按相关度绝对值排序）\n")
        f.write("=" * 80 + "\n\n")

        sorted_results = sorted(results.items(), key=lambda x: abs(x[1]), reverse=True)
        for i, (output_mask, corr) in enumerate(sorted_results):
            hex_mask = [f"0x{m:X}" for m in output_mask]
            f.write(f"\n{i + 1}. 相关度: {corr:+.8f} (|{abs(corr):.8f}|)\n")
            f.write(f"   输出掩码: {hex_mask}\n")

            active_outputs = [(j, m) for j, m in enumerate(output_mask) if m != 0]
            if active_outputs:
                f.write(f"   活跃输出位置: {[(pos, f'0x{m:X}') for pos, m in active_outputs]}\n")

    print(f"\n结果已保存到 {filename}")


# 主程序
if __name__ == "__main__":
    print("=" * 80)
    print("SPN一轮线性路径搜索")
    print("=" * 80)

    # 示例1：测试特定的输入掩码
    print("\n【示例1】测试特定输入掩码")
    print("-" * 80)

    # 可以修改这里的输入掩码
    input_masks_example = [2, 0, 0, 0, 0, 0, 0, 0]  # 位置4为0x2
    # input_masks_example = [1, 0, 0, 0, 0, 0, 0, 0]  # 位置0为0x1
    # input_masks_example = [0, 0, 0, 0, 0, 0, 0, 3]  # 位置7为0x3

    results, output_set = print_round_paths(input_masks_example, detailed=True)

    # 保存结果
    save_results_to_file(input_masks_example, results, output_set, "example_round_paths.txt")
    #
    # # 示例2：批量分析所有单活性S盒
    # print("\n" + "=" * 80)
    # print("【示例2】批量分析所有单活性S盒")
    # print("=" * 80)
    #
    # run_batch_analysis = input("\n是否运行批量分析？(y/n): ").lower() == 'y'
    #
    # if run_batch_analysis:
    #     all_analysis_results = analyze_input_mask_variations()
    #
    #     # 保存批量分析结果
    #     with open("batch_analysis_summary.txt", "w") as f:
    #         f.write("批量分析总结\n")
    #         f.write("=" * 80 + "\n\n")
    #
    #         for (pos, mask), data in sorted(all_analysis_results.items()):
    #             f.write(f"位置 {pos}, 掩码 0x{mask:X}:\n")
    #             f.write(f"  路径数量: {data['num_paths']}\n")
    #             f.write(f"  不同输出掩码数: {data['num_unique_outputs']}\n")
    #             f.write(f"  最大相关度: {max(abs(c) for c in data['results'].values()):.8f}\n\n")
    #
    #     print("\n批量分析结果已保存到 batch_analysis_summary.txt")
    #
    # # 示例3：交互式搜索
    # print("\n" + "=" * 80)
    # print("【示例3】交互式搜索")
    # print("=" * 80)
    #
    # interactive = input("\n是否进入交互式模式？(y/n): ").lower() == 'y'
    #
    # if interactive:
    #     while True:
    #         print("\n" + "-" * 40)
    #         print("输入掩码配置（8个半字节，十六进制，空格分隔）")
    #         print("例如: 0 0 0 0 2 0 0 0")
    #         user_input = input("请输入: ")
    #
    #         if user_input.lower() == 'quit' or user_input.lower() == 'exit':
    #             break
    #
    #         try:
    #             masks = [int(x, 16) for x in user_input.split()]
    #             if len(masks) != 8:
    #                 print(f"错误：需要8个值，但输入了{len(masks)}个")
    #                 continue
    #
    #             results, output_set = print_round_paths(masks, detailed=True)
    #
    #             save_option = input("\n是否保存结果？(y/n): ").lower() == 'y'
    #             if save_option:
    #                 filename = input("文件名（默认: interactive_paths.txt）: ").strip()
    #                 if not filename:
    #                     filename = "interactive_paths.txt"
    #                 save_results_to_file(masks, results, output_set, filename)
    #
    #         except ValueError as e:
    #             print(f"输入错误: {e}")
    #             print("请使用十六进制数字，例如: 0 1 2 3 4 5 6 7")
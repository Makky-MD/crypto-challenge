import re
import os
import glob


def parse_sat_solution(solution_file, num_rounds=None, Probability=None, total_Probability=None, output_file=None):
    # 从文件名中提取参数
    filename = os.path.basename(solution_file)

    # 使用正则表达式提取轮数和概率
    round_match = re.search(r'r(\d+)', filename)
    prob_match = re.search(r'p(\d+)', filename)

    if round_match and prob_match:
        if num_rounds is None:
            num_rounds = int(round_match.group(1))
        if Probability is None:
            Probability = int(prob_match.group(1))
    else:
        # 如果新格式匹配失败，尝试原始格式
        round_match = re.search(r'Round(\d+)', filename)
        active_match = re.search(r'Probability(\d+)', filename)

        if round_match and active_match:
            if num_rounds is None:
                num_rounds = int(round_match.group(1))
            if Probability is None:
                Probability = int(active_match.group(1))
        else:
            raise ValueError("无法从文件名中提取Round和Probability参数")

    # 如果total_Probability未提供，使用Active * 8
    if total_Probability is None:
        total_Probability = Probability * 8 * 2

    # 如果output_file未提供，基于solution_file生成
    if output_file is None:
        # 尝试从文件名中提取编号
        match = re.search(r'_(\d+)\.txt$', solution_file)
        if match:
            file_index = match.group(1)
            output_file = f"path_{file_index}.txt"
        else:
            # 如果提取失败，使用原来的基础名称
            base_name = os.path.splitext(solution_file)[0]
            output_file = f"{base_name}_parsed.txt"

    print(f"处理文件: {solution_file}")
    print(f"使用参数: num_rounds={num_rounds}, Active={Probability}, total_Probability={total_Probability}")

    # 生成变量编号到变量信息的映射
    variable_info = {}
    count_var_num = 0

    for round_idx in range(num_rounds):
        # xin (128 bits)
        for j in range(32):
            variable_info[count_var_num] = (round_idx, 'xin', j)
            count_var_num += 1

        for j in range(32):
            variable_info[count_var_num] = (round_idx, 'sout', j)
            count_var_num += 1

        for j in range(32):
            variable_info[count_var_num] = (round_idx, 'pout', j)
            count_var_num += 1

        for j in range(8):
            variable_info[count_var_num] = (round_idx, 'p', j)
            count_var_num += 1

        for j in range(8):
            variable_info[count_var_num] = (round_idx, 'q', j)
            count_var_num += 1



    # 处理最后一轮的xout
    final_round = num_rounds - 1
    for j in range(32):
        variable_info[count_var_num] = (final_round, 'xout', j)
        count_var_num += 1

    # 处理所有轮的辅助变量u
    for round_idx in range(num_rounds):
        for i in range(total_Probability - 1):
            for j in range(Probability):
                variable_info[count_var_num] = (round_idx, 'u', i * Probability + j)
                count_var_num += 1

    assignments = {}
    try:
        with open(solution_file, 'r') as f:
            line = f.readline().strip()  # 只读取第一行，并去除两端空白
            if line.startswith('v '):  # 如果以 'v ' 开头，则去掉前缀
                line = line[2:]
            parts = line.split()  # 按空白字符分割
            for part in parts:
                if part == '0':  # 跳过数字0
                    continue
                try:
                    var = int(part)  # 转换为整数
                    var_num = abs(var) - 1  # 转换为0-based变量编号
                    value = var > 0  # 正为True，负为False
                    assignments[var_num] = value
                except ValueError:
                    continue  # 忽略非数字部分
    except FileNotFoundError:
        print(f"文件 {solution_file} 不存在，跳过处理")
        return

    # 初始化存储结构
    result = {}
    for round_idx in range(num_rounds):
        result[round_idx] = {
            'xin': ['0'] * 32,
            'sout': ['0'] * 32,
            'pout': ['0'] * 32,
            'p': ['0'] * 8,
            'q': ['0'] * 8,
            'xout': ['0'] * 32 if round_idx == num_rounds - 1 else [],
            'u': ['0'] * ((total_Probability - 1) * Probability),
        }

    # 填充变量值
    for var_num, value in assignments.items():
        if var_num not in variable_info:
            continue
        round_idx, var_type, index = variable_info[var_num]
        result[round_idx][var_type][index] = '1' if value else '0'


    # 格式化函数
    def format_bin1(bits, group=4):
        """二进制格式化，每group位分一组"""
        binary = ''.join(bits)
        return ' '.join([binary[i:i + group] for i in range(0, len(binary), group)])

    with open(output_file, 'w') as f:
        # 在最前面提取每一轮的xin和最后的xout
        f.write("=== Extracted Inputs and Final Output ===\n")
        for round_idx in range(num_rounds):
            prefix = f"Round {round_idx + 1}:"
            f.write("{:<10} {}\n".format(prefix, format_bin1(result[round_idx]['xin'])))
        prefix = "xout:"
        final = result[num_rounds - 1]['xout']
        f.write("{:<10} {}\n".format(prefix, format_bin1(final)))

        # 原来的详细输出保持不变
        for round_idx in range(num_rounds):
            f.write(f"\n=== Round {round_idx + 1} ===\n")

            # xin (原始输入)
            f.write(f"xin:        {format_bin1(result[round_idx]['xin'])}\n")
            f.write(f"p:         {format_bin1(result[round_idx]['p'])}\n")
            f.write(f"q:         {format_bin1(result[round_idx]['q'])}\n")
            f.write(f"sout:     {format_bin1(result[round_idx]['sout'])}\n")
            f.write(f"pout:     {format_bin1(result[round_idx]['pout'])}\n")



        # 最后输出xout
        final = result[num_rounds - 1]['xout']
        f.write(f"=== Final Output ===\n")
        f.write(f"xout:       {format_bin1(final)}\n")

        # 最后输出xout
        final = result[num_rounds - 1]['xout']
        f.write(f"=== Final Output ===\n")
        f.write(f"xout:       {format_bin1(final)}\n")

    print(f"解析完成，结果已保存至 {output_file}")


def batch_process_solutions(file_pattern):
    """
    批量处理匹配文件模式的所有文件

    参数:
    file_pattern: 文件模式，例如 "solution_6r_12p_*.txt"
    """
    # 获取匹配的所有文件
    files = glob.glob(file_pattern)

    if not files:
        print(f"没有找到匹配模式 '{file_pattern}' 的文件")
        return

    # 按文件名排序
    files.sort()

    print(f"找到 {len(files)} 个文件:")
    for file in files:
        print(f"  - {file}")

    # 处理每个文件
    for file in files:
        parse_sat_solution(file)
        print("-" * 50)


# 使用方法示例:

# 方法1: 处理单个文件
# parse_sat_solution(solution_file='solution_6r_12p_1.txt')

# 方法2: 批量处理多个文件
batch_process_solutions("solution_r1_p1_*.txt")
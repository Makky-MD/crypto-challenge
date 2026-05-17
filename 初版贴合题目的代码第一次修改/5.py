import os
import subprocess
import shutil
import re

def modify_fix_rp_script(round_num, prob_num):
    """修改 3_fix r&p - 2.py 的参数"""
    script_path = "3_fix r&p - 2.py"

    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 修改 target_round
    content = re.sub(r'target_round = \d+', f'target_round = {round_num}', content)
    # 修改 target_prob
    content = re.sub(r'target_prob = \d+', f'target_prob = {prob_num}', content)
    # 修改 SearchRoundStart
    content = re.sub(r'SearchRoundStart = \d+', f'SearchRoundStart = {round_num}', content)
    # 修改 SearchRoundEnd
    content = re.sub(r'SearchRoundEnd = \d+', f'SearchRoundEnd = {round_num}', content)
    # 修改 InitialLowerBound
    content = re.sub(r'InitialLowerBound = \d+', f'InitialLowerBound = {prob_num}', content)
    # 修改 GroupConstraintChoice（保持为1，这是约束类型选择）
    content = re.sub(r'GroupConstraintChoice = \d+', f'GroupConstraintChoice = 1', content)
    # 修改 GroupNumForChoice1
    content = re.sub(r'GroupNumForChoice1 = \d+', f'GroupNumForChoice1 = {prob_num}', content)

    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f" 已修改参数: target_round={round_num}, target_prob={prob_num}")

def run_sat_solver():
    """运行 SAT 求解"""
    print(" 运行 SAT 求解...")
    try:
        result = subprocess.run(['python3', '3_fix r&p - 2.py'], check=True, capture_output=True, text=True)
        print("  SAT 求解完成")
        # 打印 SAT 求解器的输出
        if result.stdout:
            print("  SAT 输出:", result.stdout.strip()[:200])
        # 检查生成了哪些文件
        import glob
        solution_files = glob.glob('solution_*.txt')
        print(f"  生成了 {len(solution_files)} 个 solution 文件")
        if solution_files:
            print("  文件列表:", solution_files[:5])
    except subprocess.CalledProcessError as e:
        print(f"  SAT 求解失败: {e.stderr}")

def run_recover_path():
    """运行路径解析"""
    print(" 运行路径解析...")
    try:
        result = subprocess.run(['python3', '3_recover_path - 2.py'], check=True, capture_output=True, text=True)
        print("  路径解析完成")
        # 打印路径解析器的输出
        if result.stdout:
            print("  解析器输出:", result.stdout.strip()[:200])
        # 检查生成了哪些path文件
        import glob
        path_files = glob.glob('path_*.txt')
        print(f"  生成了 {len(path_files)} 个 path 文件")
        if path_files:
            print("  文件列表:", path_files[:5])
    except subprocess.CalledProcessError as e:
        print(f"  路径解析失败: {e.stderr}")

def organize_results(round_num, prob_num):
    """将结果整理到按轮数命名的目录"""
    # 创建目录
    dir_name = f"results_r{round_num}_p{prob_num}"
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    
    # 移动 solution 文件
    for filename in os.listdir('.'):
        if filename.startswith(f'solution_r{round_num}_p{prob_num}'):
            shutil.move(filename, os.path.join(dir_name, filename))
    
    # 移动 path 文件
    for filename in os.listdir('.'):
        if filename.startswith('path_') and filename.endswith('.txt'):
            new_name = f'path_r{round_num}_p{prob_num}_{filename[5:]}'
            shutil.move(filename, os.path.join(dir_name, new_name))
    
    # 复制关键配置文件
    shutil.copy('3_fix r&p - 2.py', os.path.join(dir_name, 'config_used.py'))

    print(f" 结果已整理到目录: {dir_name}")
    return dir_name

def extract_uv_from_paths(dir_name, round_num, prob_num):
    """从路径文件提取 u, v 值并保存"""
    results = []
    
    # 匹配模式：path_rX_pY_*.txt
    pattern = re.compile(rf'path_r{round_num}_p{prob_num}_\d+\.txt')
    
    # 打印调试信息
    all_files = [f for f in os.listdir(dir_name) if f.startswith('path_')]
    print(f"  目录 {dir_name} 中找到 {len(all_files)} 个 path 文件")
    
    for filename in os.listdir(dir_name):
        if pattern.match(filename):
            filepath = os.path.join(dir_name, filename)
            print(f"    处理文件: {filename}")
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取第一轮的 xin（作为 u） - 匹配 "Round 1:    0000 ..."
            u_match = re.search(r'Round 1:\s*([01 ]+)', content)
            # 提取最后一轮的 xout（作为 v） - 匹配 "xout:      0000 ..."
            v_match = re.search(r'xout:\s+([01 ]+)', content)
            
            # 调试信息
            if not u_match:
                print(f"      WARNING: 未找到 u (Round 1)")
            if not v_match:
                print(f"      WARNING: 未找到 v (xout)")
            
            if u_match and v_match:
                u_bin = u_match.group(1).strip()
                v_bin = v_match.group(1).strip()
                
                # 转换为十六进制
                u_hex = bin_to_hex(u_bin)
                v_hex = bin_to_hex(v_bin)
                
                results.append({
                    'round': round_num,
                    'prob': prob_num,
                    'filename': filename,
                    'u_bin': u_bin,
                    'v_bin': v_bin,
                    'u_hex': u_hex,
                    'v_hex': v_hex
                })
    
    # 保存到 CSV
    csv_path = os.path.join(dir_name, f'u_v_list_r{round_num}_p{prob_num}.csv')
    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
        f.write('序号,轮数,活跃S盒数,文件名,输入掩码u(二进制),输入掩码u(十六进制),输出掩码v(二进制),输出掩码v(十六进制)\n')
        for idx, res in enumerate(results, 1):
            f.write(f"{idx},{res['round']},{res['prob']},{res['filename']},\"{res['u_bin']}\",{res['u_hex']},\"{res['v_bin']}\",{res['v_hex']}\n")
    
    print(f" 已提取 {len(results)} 组 (u, v)")
    return results

def bin_to_hex(bin_str):
    """二进制转十六进制"""
    full_bin = ''.join(bin_str.split())
    full_bin = full_bin.ljust(32, '0')[:32]
    return '0x' + hex(int(full_bin, 2))[2:].zfill(8).upper()

def clean_old_files():
    """清理之前测试留下的 solution_*.txt 和 path_*.txt 文件"""
    import glob
    # 删除 solution 文件
    for f in glob.glob('solution_*.txt'):
        os.remove(f)
    # 删除 path 文件
    for f in glob.glob('path_*.txt'):
        os.remove(f)
    print("  已清理旧文件")

def update_recover_path_script(round_num, prob_num):
    """更新 3_recover_path - 2.py 中的文件模式"""
    script_path = "3_recover_path - 2.py"

    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 更新文件模式
    pattern = rf'solution_r{round_num}_p{prob_num}_*.txt'
    # 替换旧的文件模式
    content = re.sub(r'batch_process_solutions\("solution_r\d+_p\d+_\*.txt"\)',
                     f'batch_process_solutions("{pattern}")', content)

    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"  已更新 3_recover_path - 2.py 的文件模式: {pattern}")

def run_probability_search(max_round):
    """运行 probability.py 搜索每轮的最小活跃S盒数"""
    print(f"\n--- 运行概率搜索（1到{max_round}轮）---")

    # 修改 probability.py 的参数
    with open('probability.py', 'r', encoding='utf-8') as f:
        content = f.read()

    content = re.sub(r'SearchRoundStart = \d+', 'SearchRoundStart = 1', content)
    content = re.sub(r'SearchRoundEnd = \d+', f'SearchRoundEnd = {max_round + 1}', content)
    content = re.sub(r'InitialLowerBound = \d+', 'InitialLowerBound = 0', content)

    with open('probability.py', 'w', encoding='utf-8') as f:
        f.write(content)

    print("  已修改 probability.py 参数")

    # 运行概率搜索
    try:
        result = subprocess.run(['python3', 'probability.py'], check=True, capture_output=True, text=True)
        print("  概率搜索完成")

        # 解析结果 - probability.py 打印 DifferentialProbabilityBound 列表
        # 格式类似: [0, 1, 2, 2, 4, 6, ...]
        prob_results = {}
        output = result.stdout + result.stderr

        # 查找类似 [0, 1, 2, ...] 格式的输出
        import ast
        bracket_match = re.search(r'\[([\d,\s]+)\]', output)
        if bracket_match:
            try:
                diff_prob_list = ast.literal_eval('[' + bracket_match.group(1) + ']')
                for r in range(1, len(diff_prob_list)):
                    if r <= max_round:
                        prob_results[r] = diff_prob_list[r]
                        print(f"    轮数{r}: 最小活跃S盒数={diff_prob_list[r]}")
            except:
                pass

        # 如果上面的方法失败，尝试从 RunTimeSummarise.out 读取
        if not prob_results:
            try:
                with open('RunTimeSummarise.out', 'r') as f:
                    for line in f:
                        if 'Round:' in line and 'Differential Probability:' in line:
                            round_match = re.search(r'Round:\s*(\d+)', line)
                            prob_match = re.search(r'Differential Probability:\s*(\d+)', line)
                            if round_match and prob_match:
                                r = int(round_match.group(1))
                                p = int(prob_match.group(1))
                                if r <= max_round:
                                    prob_results[r] = p
                                    print(f"    轮数{r}: 最小活跃S盒数={p}")
            except FileNotFoundError:
                pass

        return prob_results
    except subprocess.CalledProcessError as e:
        print(f"  概率搜索失败: {e.stderr}")
        return {}

def main():
    print("="*80)
    print("自动化多轮 SAT 测试脚本")
    print("="*80)
    
    # 测试配置
    rounds_to_test = [1, 2, 3]
    
    # 先运行概率搜索获取每轮的最小活跃S盒数
    prob_results = run_probability_search(max(rounds_to_test))
    
    # 如果概率搜索成功，使用搜索结果；否则使用默认值
    prob_per_round = []
    for r in rounds_to_test:
        if r in prob_results:
            prob_per_round.append(prob_results[r])
        else:
            # 默认值：轮数+1
            prob_per_round.append(min(r + 1, 8))
            print(f"  警告: 未找到轮数{r}的最小活跃S盒数，使用默认值 {prob_per_round[-1]}")
    
    all_results = []
    
    for i, round_num in enumerate(rounds_to_test):
        prob_num = prob_per_round[i]
        print(f"\n--- 开始测试 轮数={round_num}, 活跃s盒数={prob_num} ---")

        # 清理之前的文件（防止干扰）
        clean_old_files()

        # 修改 3_fix r&p - 2.py 的参数
        modify_fix_rp_script(round_num, prob_num)

        # 更新 3_recover_path - 2.py 的文件模式
        update_recover_path_script(round_num, prob_num)

        # 运行 SAT 求解
        run_sat_solver()

        # 运行路径解析
        run_recover_path()

        # 整理结果
        dir_name = organize_results(round_num, prob_num)

        # 提取 u, v
        results = extract_uv_from_paths(dir_name, round_num, prob_num)
        all_results.extend(results)
    
    # 汇总所有结果到主文件
    print("\n--- 汇总所有结果 ---")
    with open('all_rounds_u_v_summary.csv', 'w', newline='', encoding='utf-8-sig') as f:
        f.write('序号,轮数,活跃S盒数,文件名,输入掩码u(十六进制),输出掩码v(十六进制)\n')
        for idx, res in enumerate(all_results, 1):
            f.write(f"{idx},{res['round']},{res['prob']},{res['filename']},{res['u_hex']},{res['v_hex']}\n")
    
    print(f" 汇总完成！共 {len(all_results)} 组结果")
    print(" 结果已保存到: all_rounds_u_v_summary.csv")
    print("\n" + "=" * 60)
    print(" 测试完成！现在可以用这些 (u, v, r) 去跑暴力程序验证")
    print("=" * 60)

if __name__ == "__main__":
    main()
import os
import subprocess
import csv
import math

def run_computecor(r, u_hex, v_hex):
    """调用C++版本的暴力程序计算 V_T"""
    print(f"  正在计算: R={r}, u={u_hex}, v={v_hex}")
    
    input_data = f"{r}\n{u_hex}\n{v_hex}\n"
    
    try:
        result = subprocess.run(
            ['./computecor.exe'],
            input=input_data,
            capture_output=True,
            text=True,
            check=True
        )
        
        for line in result.stdout.split('\n'):
            if 'Correlation' in line and '=' in line:
                parts = line.split('=')
                if len(parts) == 2:
                    return float(parts[1].strip())
        
        return None
    except subprocess.CalledProcessError as e:
        print(f"    计算失败: {e.stderr}")
        return None

def calculate_V_E(prob_num, round_num):
    """计算估计值 V_E = 2^(-4 * prob_num * round_num)
    每个活跃S盒贡献 2^(-4)，8个S盒并联
    """
    return 2 ** (-4 * prob_num * round_num)

def is_valid_estimate(V_T, V_E):
    """判断是否为有效估计（误差 <= 25%）"""
    if V_T == 0 or V_E == 0:
        return False
    error = abs(V_E - V_T)
    return error <= abs(V_T) * 0.25

def calculate_score(V_E, round_num):
    """计算得分: log2(2^(2^r) * |V_E|)"""
    if V_E == 0:
        return float('-inf')
    return math.log2(2 ** (2 ** round_num) * abs(V_E))

def main():
    print("=" * 60)
    print(" 自动化暴力验证脚本")
    print("=" * 60)
    
    # 检查 computecor.exe 是否存在
    if not os.path.exists('./computecor.exe'):
        print(" 错误：未找到 computecor.exe")
        print(" 请先在VS中编译 computecor.cpp 生成 computecor.exe")
        return
    
    print(" 检测到 computecor.exe，开始验证...")
    
    # 读取汇总文件
    input_file = 'all_rounds_u_v_summary.csv'
    
    if not os.path.exists(input_file):
        print(f" 错误：未找到输入文件 {input_file}")
        return
    
    results = []
    
    with open(input_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            round_num = int(row['轮数'])
            prob_num = int(row['活跃S盒数'])
            u_hex = row['输入掩码u(十六进制)']
            v_hex = row['输出掩码v(十六进制)']
            filename = row['文件名']
            
            # 跳过无效值
            if u_hex == '0x00000000' or v_hex == '0x00000000':
                print(f" 跳过无效值: u={u_hex}, v={v_hex}")
                continue
            
            # 运行暴力程序
            V_T = run_computecor(round_num, u_hex, v_hex)
            
            if V_T is None:
                continue
            
            # 计算 V_E
            V_E = calculate_V_E(prob_num, round_num)
            
            # 判断有效性
            valid = is_valid_estimate(V_T, V_E)
            
            # 计算得分
            score = calculate_score(V_E, round_num)
            
            # 记录结果
            results.append({
                'round': round_num,
                'prob': prob_num,
                'u': u_hex,
                'v': v_hex,
                'filename': filename,
                'V_T': V_T,
                'V_E': V_E,
                'valid': '有效' if valid else '无效',
                'score': score
            })
    
    # 保存验证结果
    with open('verification_results.csv', 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=[
            '序号', '轮数', '活跃S盒数', '文件名', 
            '输入掩码u', '输出掩码v', 
            'V_T(精确值)', 'V_E(估计值)', '误差', '是否有效', '得分'
        ])
        writer.writeheader()
        
        for idx, res in enumerate(results, 1):
            error = abs(res['V_E'] - res['V_T'])
            writer.writerow({
                '序号': idx,
                '轮数': res['round'],
                '活跃S盒数': res['prob'],
                '文件名': res['filename'],
                '输入掩码u': res['u'],
                '输出掩码v': res['v'],
                'V_T(精确值)': res['V_T'],
                'V_E(估计值)': res['V_E'],
                '误差': error,
                '是否有效': res['valid'],
                '得分': res['score']
            })
    
    # 统计
    valid_count = sum(1 for r in results if r['valid'] == '有效')
    total_count = len(results)
    
    print("\n" + "=" * 60)
    print(f" 验证完成！")
    print(f" 总计测试: {total_count} 组")
    print(f" 有效估计: {valid_count} 组")
    print(f" 有效率: {valid_count/total_count*100:.2f}%")
    print(f" 结果已保存到: verification_results.csv")
    print("=" * 60)

if __name__ == "__main__":
    main()
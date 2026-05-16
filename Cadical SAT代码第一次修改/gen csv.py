#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
S盒线性分布表(LAT)生成工具

该脚本计算PRESENT密码S盒的线性分布表(LAT)，并将结果保存为CSV格式。

线性分布表(LAT)是线性密码分析的核心工具，用于描述S盒的线性特性。
LAT[a][b]表示输入掩码a和输出掩码b之间的线性偏差。

PRESENT S盒定义（16个4-bit输入到4-bit输出的置换）：
    S(x) = [0xC, 0x5, 0x6, 0xB, 0x9, 0x0, 0xA, 0xD,
            0x3, 0xE, 0xF, 0x8, 0x4, 0x7, 0x1, 0x2]
"""

import csv

# PRESENT密码的S盒定义（十进制表示）
# 输入x -> Sbox[x] = 输出
Sbox = [0xc, 0x6, 0x9, 0x0, 0x1, 0xa, 0x2, 0xb, 
        0x3, 0x8, 0x5, 0xd, 0x4, 0xe, 0x7, 0xf]###S盒改了一下，改成和赛题一样的了


def int_to_bin_str(n):
    """
    将一个整数转换为4比特二进制字符串
    
    参数:
        n: 0-15之间的整数
    
    返回:
        4位二进制字符串，高位在前
    """
    return format(n, '04b')


def dot_product(a, b):
    """
    计算两个4比特整数的点积(内积)模2
    
    点积定义：a · b = a0*b0 XOR a1*b1 XOR a2*b2 XOR a3*b3
    
    参数:
        a: 第一个4比特整数
        b: 第二个4比特整数
    
    返回:
        点积结果(0或1)
    """
    bin_a = int_to_bin_str(a)
    bin_b = int_to_bin_str(b)
    result = 0
    for i in range(4):
        # 按位与后异或累加
        result ^= (int(bin_a[i]) & int(bin_b[i]))
    return result


def get_linear_table(Sbox):
    """
    计算S盒的线性分布表(LAT)
    
    LAT[a][b] = |(#{x: a·x = b·S(x)}) / 16 - 0.5|
    表示输入掩码a和输出掩码b之间的线性偏差绝对值
    
    参数:
        Sbox: S盒列表，长度为16
    
    返回:
        lat: 16x16的二维列表，存储线性偏差值
    """
    n = len(Sbox)  # S盒大小，应为16
    lat = [[0 for j in range(n)] for i in range(n)]
    
    # 遍历所有输入掩码a和输出掩码b
    for a in range(n):      # a: 输入掩码 (0~15)
        for b in range(n):  # b: 输出掩码 (0~15)
            count = 0
            # 遍历所有可能的输入值x
            for x in range(n):
                # 计算输入线性组合: a · x
                input_bias = dot_product(a, x)
                # 计算输出线性组合: b · S(x)
                output_bias = dot_product(b, Sbox[x])
                # 如果相等，计数加1
                if input_bias == output_bias:
                    count += 1
            # 计算偏差值: |count/16 - 0.5|
            lat[a][b] = abs(count / n - 0.5)###偏差，相关度的一半，加绝对值是为了选最大偏差
    
    return lat


def calculate_m(bias, p, q):
    """
    根据偏差值和辅助变量p,q计算M值
    
    M值用于线性逼近的CNF编码，表示特定偏差对应的约束条件。
    
    参数:
        bias: 线性偏差值(0, 0.125, 0.25, 0.5)
        p: 辅助变量p(0或1)
        q: 辅助变量q(0或1)
    
    返回:
        M值(0或1)，表示该约束是否有效
    """
    if bias == 0.5 and p == 0 and q == 0:
        return 1
    elif bias == 0.25 and p == 0 and q == 1:
        return 1
    elif bias == 0.125 and p == 1 and q == 1:
        return 1
    elif bias == 0:
        return 0
    return 0
    ###这个calculate函数就是写一个筛选的函数，给SAT提供一个合法的组合表。
    ###把偏差对应转化为布尔值,值是1表示有效，是0表示无效
    ###这个pq类似于独热编码，然后为什么不直接给三种偏差直接赋值编码是因为
    ###SAT求解器会先给pq遍历赋值，然后根据这个函数判断是否有效
   
def save_linear_table_to_csv(lat):
    """
    将线性分布表保存为CSV文件
    
    CSV文件格式：
        表头: x1, x2, x3, x4, y1, y2, y3, y4, p, q, m
        每行表示一个线性逼近条件：
            x1-x4: 输入掩码的二进制表示
            y1-y4: 输出掩码的二进制表示
            p, q: 辅助变量
            m: 该条件是否有效(0或1)###由刚刚的calculate_m函数计算
    
    参数:
        lat: 16x16的线性分布表
    """
    with open('pq.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        
        # 写表头
        header = ['x1', 'x2', 'x3', 'x4', 'y1', 'y2', 'y3', 'y4', 'p', 'q', 'm']
        writer.writerow(header)
        
        # 遍历所有辅助变量组合
        ###遍历所有的辅助变量组合p,q，而不是只取满足条件的组合，
        ###是因为为了满足SAT求解器的要求，不仅要有有效组合，还要有无效组合
        for p in range(2):
            for q in range(2):
                # 遍历所有输入掩码a和输出掩码b
                for a in range(len(lat)):
                    for b in range(len(lat[a])):
                        # 获取输入掩码的二进制表示
                        input_bin = int_to_bin_str(a)
                        # 获取输出掩码的二进制表示
                        output_bin = int_to_bin_str(b)
                        # 获取偏差值
                        bias = lat[a][b]
                        # 计算M值
                        m = calculate_m(bias, p, q)
                        # 构建行数据
                        row = list(input_bin) + list(output_bin) + [str(p)] + [str(q)] + [str(m)]
                        writer.writerow(row)


# ==================== 主程序 ====================
if __name__ == "__main__":
    # 计算线性分布表
    lat = get_linear_table(Sbox)
    
    # 打印LAT（可选）
    print("线性分布表(LAT):")
    for i, row in enumerate(lat):
        print(f"a={i:02d}: {row}")
    
    # 保存为CSV文件
    save_linear_table_to_csv(lat)
    print("\n线性分布表已保存为 pq.csv")
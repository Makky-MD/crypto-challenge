#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
S盒线性逼近搜索工具（简化版）

【赛题要求】：只考虑S盒，不考虑P置换和顺序编码约束

原始代码是针对PRESENT密码完整轮函数的线性逼近搜索，包含：
1. S盒非线性层
2. P置换线性层
3. 顺序编码基数约束
4. Matsui策略剪枝

本次修改：
- 注释掉P置换相关代码（赛题不要求）
- 注释掉顺序编码约束（赛题不要求）
- 注释掉Matsui策略（依赖顺序编码）
- 简化变量分配和轮函数约束
"""

import os
import time
import random

# ==================== 全局参数配置 ====================
FullRound = 32              # 密码总轮数（保留但实际使用由SearchRoundEnd控制）
SearchRoundStart = 1        # 搜索起始轮数
SearchRoundEnd = 7          # 搜索结束轮数(不包含)，即搜索1~6轮
InitialLowerBound = 0       # 初始偏差下界，从0开始逐步增加

# ============ 以下内容因赛题要求已注释 ============
# # Matsui约束策略选择（赛题不要求顺序编码，故注释）
# GroupConstraintChoice = 1   # 选择第1种分组约束策略
# GroupNumForChoice1 = 1      # 策略1下的分组数量
# 
# # 存储每轮能达到的最大线性偏差的下界（Matsui策略需要，赛题不要求）
# LinearBiasBound = list([])
# for i in range(FullRound):
#     LinearBiasBound += [0]


def CountClausesInRoundFunction(Round, Bias, clause_num):
    """
    统计轮函数约束对应的CNF子句数量
    
    参数:
        Round: 当前分析的轮数
        Bias: 线性偏差值(本函数未使用，但保留作为接口)
        clause_num: 已有的子句数量（累加器）
    
    子句组成:
        1. 非零输入约束: 1个子句
        2. S盒线性逼近约束: Round * 16 * 51 个子句
           - 每轮16个S盒，每个S盒51个线性逼近约束
    """
    count = clause_num   # 从已有子句数开始
    # 非零输入约束：至少有一个输入位不为0
    count += 1   # 增加1个子句
    # S盒约束：每轮16个S盒，每个S盒51个线性逼近条件
    for r in range(Round):   # 每轮
        for i in range(16):  # 每轮有16个S盒
            for j in range(51):  # 每个S盒有51个线性逼近约束
                count += 1   # 每个约束对应1个子句


# ============ 以下函数因赛题要求已注释 ============
# def CountClausesInSequentialEncoding(main_var_num, cardinalitycons, clause_num):
#     """
#     统计顺序编码(Sequential Encoding)的CNF子句数量
#     【赛题不要求】：顺序编码用于基数约束，本次只考虑S盒，不需要基数约束
#     
#     参数:
#         main_var_num: 主变量数量
#         cardinalitycons: 基数约束值(k)
#         clause_num: 已有的子句数量
#     
#     返回:
#         更新后的子句总数
#     """
#     count = clause_num
#     n = main_var_num
#     k = cardinalitycons
#     
#     if k > 0:
#         count += 1
#         for j in range(1, k):
#             count += 1
#         for i in range(1, n-1):
#             count += 3
#         for j in range(1, k):
#             for i in range(1, n-1):
#                 count += 2
#         count += 1
#     
#     if k == 0:
#         for i in range(n):
#             count += 1
#     
#     return count
# 
# 
# def CountClausesForMatsuiStrategy(n, k, left, right, m, clausenum):
#     """
#     统计Matsui策略约束的CNF子句数量
#     【赛题不要求】：Matsui策略依赖顺序编码，本次不使用
#     
#     参数:
#         n: 主变量总数
#         k: 总体基数约束
#         left: 当前段的左边界(变量索引)
#         right: 当前段的右边界(变量索引)
#         m: 当前段的部分基数约束
#         clausenum: 已有的子句数量
#     
#     返回:
#         更新后的子句总数
#     """
#     count = clausenum
#     
#     if m > 0:
#         if (left == 0) and (right < n-1):
#             for i in range(1, right + 1):
#                 count += 1
#         
#         if (left > 0) and (right == n-1):
#             for i in range(0, k-m):
#                 count += 1
#             for i in range(0, k-m+1):
#                 count += 1
#         
#         if (left > 0) and (right < n-1):
#             for i in range(0, k-m):
#                 count += 1
#     
#     if m == 0:
#         for i in range(left, right + 1):
#             count += 1
#     
#     return count
# 
# 
# def GenSequentialEncoding(x, u, main_var_num, cardinalitycons, fout):
#     """
#     生成顺序编码的CNF子句
#     【赛题不要求】：顺序编码用于基数约束，本次只考虑S盒，不需要
#     
#     参数:
#         x: 主变量列表
#         u: 辅助变量二维数组
#         main_var_num: 主变量数量
#         cardinalitycons: 基数约束值(k)
#         fout: 输出文件句柄
#     """
#     n = main_var_num
#     k = cardinalitycons
#     
#     if k > 0:
#         clauseseq = "-" + str(x[0]+1) + " " + str(u[0][0]+1) + " 0\n"
#         fout.write(clauseseq)
#         
#         for j in range(1, k):
#             clauseseq = "-" + str(u[0][j]+1) + " 0\n"
#             fout.write(clauseseq)
#         
#         for i in range(1, n-1):
#             clauseseq = "-" + str(x[i]+1) + " " + str(u[i][0]+1) + " 0\n"
#             fout.write(clauseseq)
#             clauseseq = "-" + str(u[i-1][0]+1) + " " + str(u[i][0]+1) + " 0\n"
#             fout.write(clauseseq)
#             clauseseq = "-" + str(x[i]+1) + " " + "-" + str(u[i-1][k-1]+1) + " 0\n"
#             fout.write(clauseseq)
#         
#         for j in range(1, k):
#             for i in range(1, n-1):
#                 clauseseq = "-" + str(x[i]+1) + " " + "-" + str(u[i-1][j-1]+1) + " " + str(u[i][j]+1) + " 0\n"
#                 fout.write(clauseseq)
#                 clauseseq = "-" + str(u[i-1][j]+1) + " " + str(u[i][j]+1) + " 0\n"
#                 fout.write(clauseseq)
#         
#         clauseseq = "-" + str(x[n-1]+1) + " " + "-" + str(u[n-2][k-1]+1) + " 0\n"
#         fout.write(clauseseq)
#     
#     if k == 0:
#         for i in range(n):
#             clauseseq = "-" + str(x[i]+1) + " 0\n"
#             fout.write(clauseseq)
# 
# 
# def GenMatsuiConstraint(x, u, n, k, left, right, m, fout):
#     """
#     生成Matsui策略的约束子句
#     【赛题不要求】：Matsui策略依赖顺序编码，本次不使用
#     
#     参数:
#         x: 主变量列表
#         u: 辅助变量二维数组
#         n: 主变量总数
#         k: 总体基数约束
#         left: 当前段的左边界
#         right: 当前段的右边界
#         m: 当前段的部分基数约束
#         fout: 输出文件句柄
#     """
#     if m > 0:
#         if (left == 0) and (right < n-1):
#             for i in range(1, right + 1):
#                 clauseseq = "-" + str(x[i] + 1) + " " + "-" + str(u[i-1][m-1] + 1) + " 0\n"
#                 fout.write(clauseseq)
#         
#         if (left > 0) and (right == n-1):
#             for i in range(0, k-m):
#                 clauseseq = str(u[left-1][i] + 1) + " " + "-" + str(u[right - 1][i+m] + 1) + " 0\n"
#                 fout.write(clauseseq)
#             for i in range(0, k-m+1):
#                 clauseseq = str(u[left-1][i] + 1) + " " + "-" + str(x[right] + 1) + " " + "-" + str(u[right - 1][i+m-1] + 1) + " 0\n"
#                 fout.write(clauseseq)
#         
#         if (left > 0) and (right < n-1):
#             for i in range(0, k-m):
#                 clauseseq = str(u[left-1][i] + 1) + " " + "-" + str(u[right][i+m] + 1) + " 0\n"
#                 fout.write(clauseseq)
#     
#     if m == 0:
#         for i in range(left, right + 1):
#             clauseseq = "-" + str(x[i] + 1) + " 0\n"
#             fout.write(clauseseq)


def Decision(Round, Bias):
    """
    核心决策函数：构建CNF问题并调用SAT求解器
    
    【赛题简化版】：只考虑S盒，不考虑P置换和基数约束
    
    参数:
        Round: 当前分析的轮数
        Bias: 当前尝试的偏差值（保留参数，但本次不使用基数约束）
    
    返回:
        flag: 是否找到可行解 (True=SAT, False=UNSAT)
    """
    count_var_num = 0  # 变量计数器
    time_start = time.time()  # 计时开始
    
    # ==================== 变量声明与分配 ====================
    # xin[r][j]: 第r轮的64位输入
    # p[r][i]: 第r轮第i个S盒的p变量（辅助变量）
    # q[r][i]: 第r轮第i个S盒的q变量（辅助变量）
    # xout[r][j]: 第r轮的64位输出
    xin = []
    p = []
    q = []
    xout = []
    
    # 初始化变量数组
    for i in range(Round):
        xin.append([0] * 64)
        p.append([0] * 16)
        q.append([0] * 16)
        xout.append([0] * 64)
    
    # 分配变量ID
    for i in range(Round):
        for j in range(64):
            xin[i][j] = count_var_num
            count_var_num += 1
        for j in range(16):
            p[i][j] = count_var_num
            count_var_num += 1
        for j in range(16):
            q[i][j] = count_var_num
            count_var_num += 1
    
    # ============ 原始代码：P置换连接（赛题不要求，注释掉） ============
    # # 连接轮之间的输入输出：第r轮的输出经过P置换后作为第r+1轮的输入
    # for i in range(Round - 1):
    #     for j in range(64):
    #         xout[i][j] = xin[i + 1][j]
    # 
    # # 最后一轮的输出是新变量
    # for i in range(64):
    #     xout[Round - 1][i] = count_var_num
    #     count_var_num += 1
    
    # ============ 【赛题新增】：无P置换情况下的轮连接 ============
    # 说明：由于赛题只考虑S盒，不考虑P置换，因此：
    # - 第r轮S盒的输出直接作为第r+1轮S盒的输入
    # - 每轮64位输入直接对应16个S盒的4位输入
    # - 每轮16个S盒的4位输出直接连接成64位输出
    # 由于没有P置换打乱位顺序，xout[r] = S(xin[r])，直接连接即可
    for i in range(Round):
        for j in range(64):
            xout[i][j] = count_var_num
            count_var_num += 1
    
    # ============ 原始代码：顺序编码辅助变量（赛题不要求，注释掉） ============
    # TotalBias = 16 * Round * 2
    # auxiliary_var_u = []
    # for i in range(TotalBias - 1):
    #     auxiliary_var_u.append([])
    #     for j in range(Bias):
    #         auxiliary_var_u[i].append(count_var_num)
    #         count_var_num += 1
    
    # ==================== 统计子句数量 ====================
    count_clause_num = 0
    count_clause_num = CountClausesInRoundFunction(Round, Bias, count_clause_num)
    
    # ============ 原始代码：顺序编码和Matsui策略子句统计（赛题不要求，注释掉） ============
    # Main_Var_Num = 16 * Round * 2
    # CardinalityCons = Bias
    # count_clause_num = CountClausesInSequentialEncoding(Main_Var_Num, CardinalityCons, count_clause_num)
    # 
    # for matsui_count in range(MatsuiCount):
    #     StartingRound = MatsuiRoundIndex[matsui_count][0]
    #     EndingRound = MatsuiRoundIndex[matsui_count][1]
    #     LeftNode = 16 * StartingRound * 2
    #     RightNode = 16 * EndingRound * 2 - 1
    #     PartialCardinalityCons = Bias - LinearBiasBound[StartingRound] - LinearBiasBound[Round - EndingRound]
    #     count_clause_num = CountClausesForMatsuiStrategy(Main_Var_Num, CardinalityCons, LeftNode, RightNode, PartialCardinalityCons, count_clause_num)
    
    # ==================== 生成CNF文件 ====================
    filename = "Problem-Round" + str(Round) + "-Bias" + str(Bias) + ".cnf"
    with open(filename, "w") as file:
        # 写入CNF头部：p cnf 变量数 子句数
        file.write("p cnf " + str(count_var_num) + " " + str(count_clause_num) + "\n")
        
        # 1. 添加非零输入约束
        clauseseq = ""
        for i in range(64):
            clauseseq += str(xin[0][i] + 1) + " "  # CNF变量从1开始
        clauseseq += "0\n"
        file.write(clauseseq)
        
        # 2. 添加轮函数约束（只包含S盒，无P置换）
        for r in range(Round):
            # ============ 原始代码：P置换表（赛题不要求，注释掉） ============
            # P = [0, 16, 32, 48, 1, 17, 33, 49, 2, 18, 34, 50, 3, 19, 35, 51, 
            #      4, 20, 36, 52, 5, 21, 37, 53, 6, 22, 38, 54, 7, 23, 39, 55, 
            #      8, 24, 40, 56, 9, 25, 41, 57, 10, 26, 42, 58, 11, 27, 43, 59, 
            #      12, 28, 44, 60, 13, 29, 45, 61, 14, 30, 46, 62, 15, 31, 47, 63]
            
            # ============ 【赛题修改】：S盒约束子句 ============
            # 说明：根据cnf to sat.py文件，赛题使用30个CNF子句（不是原来的51个）
            # 变量顺序：[x1, x2, x3, x4, y1, y2, y3, y4, p, q]
            # 格式：0=正文字（不取反），1=负文字（取反），9=不出现
            
            # ============ 【赛题新增】：赛题使用的30个S盒CNF约束子句 ============
            # 说明：这些约束来自cnf to sat.py中的输入表达式
            # 原始表达式：(x1+x4+p')(y3+y4+p')(x4+y4+p')(x1+y3'+y4'+p')(x1'+x4'+y3+p')(y2'+q)(y3'+q)(x1'+x4+y2+p)(x4'+y1+y4+p)(x1'+y3'+y4'+p)(x3+y2+y4'+p)(y1'+q)(x1+x4+y3+y4+q')(x3+y3+y4'+p)(x1+x3'+y2'+y3'+p)(x1+x2+y1'+y3'+p)(x1+x3+y2'+y4+p)(x4'+y3'+y4+p)(x3'+y2+y3+y4)(x2+x4+y1+y3'+p)(y4'+q)(x1+x2'+x4+y3)(x1'+x3'+y1'+y3+y4)(x2'+y1'+y3+y4'+p)(x1+x2'+x4'+y1+p)(x1'+x4+y4'+p)(x2+x4'+y1+y3+p)(x2'+x4+y1'+y2'+y4)(x1+x4'+y3+y4'+p)(x4+y1'+y3+y4)
            SboxCNFConstraints = [
                [0, 9, 9, 0, 9, 9, 9, 9, 1, 9],   # (x1+x4+p')
                [9, 9, 9, 9, 9, 9, 0, 0, 1, 9],   # (y3+y4+p')
                [9, 9, 9, 0, 9, 9, 9, 0, 1, 9],   # (x4+y4+p')
                [0, 9, 9, 9, 9, 9, 1, 1, 1, 9],   # (x1+y3'+y4'+p')
                [1, 9, 9, 1, 9, 9, 0, 9, 1, 9],   # (x1'+x4'+y3+p')
                [9, 9, 9, 9, 9, 1, 9, 9, 9, 0],   # (y2'+q)
                [9, 9, 9, 9, 9, 9, 1, 9, 9, 0],   # (y3'+q)
                [1, 9, 9, 0, 9, 0, 9, 9, 0, 9],   # (x1'+x4+y2+p)
                [9, 9, 9, 1, 0, 9, 9, 0, 0, 9],   # (x4'+y1+y4+p)
                [1, 9, 9, 9, 9, 9, 1, 1, 0, 9],   # (x1'+y3'+y4'+p)
                [9, 9, 0, 9, 9, 0, 9, 1, 0, 9],   # (x3+y2+y4'+p)
                [9, 9, 9, 9, 1, 9, 9, 9, 9, 0],   # (y1'+q)
                [0, 9, 9, 0, 9, 9, 0, 0, 9, 1],   # (x1+x4+y3+y4+q')
                [9, 9, 0, 9, 9, 9, 0, 1, 0, 9],   # (x3+y3+y4'+p)
                [0, 9, 1, 9, 9, 1, 1, 9, 0, 9],   # (x1+x3'+y2'+y3'+p)
                [0, 0, 9, 9, 1, 9, 1, 9, 0, 9],   # (x1+x2+y1'+y3'+p)
                [0, 9, 0, 9, 9, 1, 9, 0, 0, 9],   # (x1+x3+y2'+y4+p)
                [9, 9, 9, 1, 9, 9, 1, 0, 0, 9],   # (x4'+y3'+y4+p)
                [9, 9, 1, 9, 9, 0, 0, 0, 9, 9],   # (x3'+y2+y3+y4)
                [9, 0, 9, 0, 0, 9, 1, 9, 0, 9],   # (x2+x4+y1+y3'+p)
                [9, 9, 9, 9, 9, 9, 9, 1, 9, 0],   # (y4'+q)
                [0, 1, 9, 0, 9, 9, 0, 9, 9, 9],   # (x1+x2'+x4+y3)
                [1, 9, 1, 9, 1, 9, 0, 0, 9, 9],   # (x1'+x3'+y1'+y3+y4)
                [9, 1, 9, 9, 1, 9, 0, 1, 0, 9],   # (x2'+y1'+y3+y4'+p)
                [0, 1, 9, 1, 0, 9, 9, 9, 0, 9],   # (x1+x2'+x4'+y1+p)
                [1, 9, 9, 0, 9, 9, 9, 1, 0, 9],   # (x1'+x4+y4'+p)
                [9, 0, 9, 1, 0, 9, 0, 9, 0, 9],   # (x2+x4'+y1+y3+p)
                [9, 1, 9, 0, 1, 1, 9, 0, 9, 9],   # (x2'+x4+y1'+y2'+y4)
                [0, 9, 9, 1, 9, 9, 0, 1, 0, 9],   # (x1+x4'+y3+y4'+p)
                [9, 9, 9, 0, 1, 9, 0, 0, 9, 9]    # (x4+y1'+y3+y4)
            ]
            
            # ============ 【赛题新增】：无P置换情况下的S盒输入输出连接 ============
            # 说明：由于没有P置换，S盒的输出直接作为下一轮的输入
            # 第r轮的xout[r]就是该轮S盒的64位输出
            # 对于第i个S盒：
            # - 输入：xin[r][4*i:4*i+4]（4位）
            # - 输出：xout[r][4*i:4*i+4]（4位）
            y = xout[r]  # 直接使用本轮输出作为S盒输出（无P置换）
            
            # ============ 【赛题修改】：为每个S盒生成30个CNF约束子句 ============
            # 说明：根据赛题要求，每个S盒使用30个约束子句
            for i in range(16):  # 每轮16个S盒
                # 收集第i个S盒的变量：[x1, x2, x3, x4, y1, y2, y3, y4, p, q]
                X = []
                for j in range(4):
                    X.append(xin[r][4*i + j])      # 4位输入 x1-x4
                for j in range(4):
                    X.append(y[4*i + j])           # 4位输出 y1-y4
                X.append(p[r][i])                  # p辅助变量
                X.append(q[r][i])                  # q辅助变量
                
                # 生成30个S盒约束子句
                for j in range(30):
                    clauseseq = ""
                    for k in range(10):
                        if SboxCNFConstraints[j][k] == 1:
                            clauseseq += "-" + str(X[k] + 1) + " "  # 负文字（取反）
                        elif SboxCNFConstraints[j][k] == 0:
                            clauseseq += str(X[k] + 1) + " "         # 正文字（不取反）
                        # 值为9表示该位置无约束，跳过
                    clauseseq += "0\n"
                    file.write(clauseseq)
        
        # ============ 原始代码：顺序编码约束（赛题不要求，注释掉） ============
        # Main_Vars = []
        # for r in range(Round):
        #     for i in range(16):
        #         Main_Vars.append(p[Round - 1 - r][i])
        #         Main_Vars.append(q[Round - 1 - r][i])
        # 
        # GenSequentialEncoding(Main_Vars, auxiliary_var_u, Main_Var_Num, CardinalityCons, file)
        
        # ============ 原始代码：Matsui策略约束（赛题不要求，注释掉） ============
        # for matsui_count in range(MatsuiCount):
        #     StartingRound = MatsuiRoundIndex[matsui_count][0]
        #     EndingRound = MatsuiRoundIndex[matsui_count][1]
        #     LeftNode = 16 * StartingRound * 2
        #     RightNode = 16 * EndingRound * 2 - 1
        #     PartialCardinalityCons = Bias - LinearBiasBound[StartingRound] - LinearBiasBound[Round - EndingRound]
        #     GenMatsuiConstraint(Main_Vars, auxiliary_var_u, Main_Var_Num, CardinalityCons, LeftNode, RightNode, PartialCardinalityCons, file)
    
    # ==================== 调用SAT求解器 ====================
    # 使用CaDiCaL求解器
    solver_cmd = "~/Install/cadical/build/cadical " + filename + " > Round" + str(Round) + "-Bias" + str(Bias) + "-solution.out"
    os.system(solver_cmd)
    
    # 提取求解结果
    os.system("sed -n '/s SATISFIABLE/p' Round" + str(Round) + "-Bias" + str(Bias) + "-solution.out > SatSolution.out")
    os.system("sed -n '/s UNSATISFIABLE/p' Round" + str(Round) + "-Bias" + str(Bias) + "-solution.out > UnsatSolution.out")
    
    with open("SatSolution.out", "r") as satsol, open("UnsatSolution.out", "r") as unsatsol:
        satresult = satsol.readlines()
        unsatresult = unsatsol.readlines()
    
    # 判断结果：SAT或UNSAT
    flag = False
    if len(satresult) == 0 and len(unsatresult) > 0:
        flag = False  # UNSAT
    if len(satresult) > 0 and len(unsatresult) == 0:
        flag = True   # SAT
    
    # 清理临时文件
    os.system("rm SatSolution.out")
    os.system("rm UnsatSolution.out")
    os.system("rm " + filename)
    
    time_end = time.time()
    
    # 输出结果
    if flag:
        print(f"Round:{Round}; Bias: {Bias}; Sat; TotalCost: {time_end - time_start:.2f}s")
    else:
        print(f"Round:{Round}; Bias: {Bias}; Unsat; TotalCost: {time_end - time_start:.2f}s")
    
    return flag


if __name__ == "__main__":
    """
    主函数：搜索S盒的多轮线性逼近（赛题简化版）
    
    【赛题要求】：只考虑S盒，不考虑P置换和顺序编码约束
    
    搜索流程：
    1. 从SearchRoundStart到SearchRoundEnd轮进行搜索
    2. 对每轮，从InitialLowerBound开始逐步增加偏差值
    3. 调用SAT求解器判断是否存在可行解
    4. 记录每轮的最大线性偏差
    """
    CountBias = InitialLowerBound
    TotalTimeStart = time.time()
    
    # 遍历搜索轮数
    for totalround in range(SearchRoundStart, SearchRoundEnd):
        flag = False
        time_start = time.time()
        
        # ============ 原始代码：Matsui策略（赛题不要求，注释掉） ============
        # MatsuiRoundIndex = []
        # MatsuiCount = 0
        # if GroupConstraintChoice == 1:
        #     for group in range(GroupNumForChoice1):
        #         for round in range(1, totalround - group + 1):
        #             MatsuiRoundIndex.append([group, group + round])
        #             MatsuiCount += 1
        # 
        # with open("MatsuiCondition.out", "a") as file:
        #     file.write(f"Round: {totalround}; Partial Constraint Num: {MatsuiCount}\n")
        #     file.write(str(MatsuiRoundIndex) + "\n")
        
        # 搜索寻找可行解
        while not flag:
            # ============ 简化调用：移除Matsui相关参数 ============
            flag = Decision(totalround, CountBias)
            CountBias += 1
        
        time_end = time.time()
        
        # 保存运行时间
        with open("RunTimeSummarise.out", "a") as file:
            file.write(f"Round: {totalround}; Found Bias: {CountBias - 1}; Runtime: {time_end - time_start:.2f}s\n")
    
    TotalTimeEnd = time.time()
    print(f"Total Runtime: {TotalTimeEnd - TotalTimeStart:.2f}s")
    
    with open("RunTimeSummarise.out", "a") as file:
        file.write(f"Total Runtime: {TotalTimeEnd - TotalTimeStart:.2f}s")
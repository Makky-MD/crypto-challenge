import os
import time
import random

FullRound = 32

SearchRoundStart = 1
SearchRoundEnd = 7   # 搜索从第1轮到第7轮的线性逼近
InitialUpperBound = 0  #  从最大偏差值开始尝试，逐步减小

GroupConstraintChoice = 1

# Parameters for choice 1
GroupNumForChoice1 = 1

# 这两个参数控制Matsui的约束策略（一种提高搜索效率的技术）：GroupConstraintChoice = 1 选择第1种分组约束策略 可能的其他策略（如choice 2, 3）在代码中没有给出，可能是预留接口
#在策略1下的分组数量 GroupNumForChoice1 = 1  具体作用：将线性路径分成多少个段进行约束

LinearBiasBound = list([])
for i in range(FullRound):
    LinearBiasBound += [0]

# 含义：存储每轮能达到的最大线性偏差
# 初始化：创建长度为32的数组，所有元素初始化为0

def CountClausesInRoundFunction(Round, Bias, clause_num):
    # Round: 当前要分析的轮数
    # Bias: 线性偏差值（此函数中未使用，但保留作为接口）
    # clause_num: 已有的子句数量（累加器）

    count = clause_num   # 从已有子句数开始
    # Nonzero input   # 1. 非零输入约束
    count += 1   # 增加1个子句
    # Clauses for Sbox
    for r in range(Round):   # 每轮
        for i in range(16):  # 每轮有16个S盒
            for j in range(51):  # 每个S盒有51个线性逼近约束
                count += 1   # 每个约束对应1个子句
    
def CountClausesInSequentialEncoding(main_var_num, cardinalitycons, clause_num):
    # 这个函数的作用是统计使用“顺序编码”（Sequential Encoding）方法来表示“至少k个变量为真”这个基数约束时，需要生成多少个CNF子句。
    count = clause_num
    n = main_var_num
    k = cardinalitycons
    if (k > 0):
        count += 1
        for j in range(1, k):
            count += 1
        for i in range(1, n-1):
            count += 3
        for j in range(1, k):
            for i in range(1, n-1):
                count += 2
        count += 1
    if (k == 0):
        for i in range(n):
            count += 1
    return count
    
def CountClausesForMatsuiStrategy(n, k, left, right, m, clausenum):
    # 在搜索多轮线性逼近时，将整个线性特征分成多个连续的段（segment），并对每个段单独施加偏差约束，从而剪枝搜索空间，避免求解器在无效路径上浪费时间。
    count = clausenum
    if (m > 0):
        if ((left == 0) and (right < n-1)):
            for i in range(1, right + 1):
                count += 1
        if ((left > 0) and (right == n-1)):
            for i in range(0, k-m):
                count += 1
            for i in range(0, k-m+1):
                count += 1
        if ((left > 0) and (right < n-1)):
            for i in range(0, k-m):
                count += 1
    if (m == 0):
        for i in range(left, right + 1):
            count += 1
    return count
    
def GenSequentialEncoding(x, u, main_var_num, cardinalitycons, fout):
    n = main_var_num
    k = cardinalitycons
    if (k > 0):
        clauseseq = "-" + str(x[0]+1) + " " + str(u[0][0]+1) + " 0" + "\n"
        fout.write(clauseseq)
        for j in range(1, k):
            clauseseq = "-" + str(u[0][j]+1) + " 0" + "\n"
            fout.write(clauseseq)
        for i in range(1, n-1):
            clauseseq = "-" + str(x[i]+1) + " " + str(u[i][0]+1) + " 0" + "\n"
            fout.write(clauseseq)
            clauseseq = "-" + str(u[i-1][0]+1) + " " + str(u[i][0]+1) + " 0" + "\n"
            fout.write(clauseseq)
            clauseseq = "-" + str(x[i]+1) + " " + "-" + str(u[i-1][k-1]+1) + " 0" + "\n"
            fout.write(clauseseq)
        for j in range(1, k):
            for i in range(1, n-1):
                clauseseq = "-" + str(x[i]+1) + " " + "-" + str(u[i-1][j-1]+1) + " " + str(u[i][j]+1) + " 0" + "\n"
                fout.write(clauseseq)
                clauseseq = "-" + str(u[i-1][j]+1) + " " + str(u[i][j]+1) + " 0" + "\n"
                fout.write(clauseseq)
        clauseseq = "-" + str(x[n-1]+1) + " " + "-" + str(u[n-2][k-1]+1) + " 0" + "\n"
        fout.write(clauseseq)
    if (k == 0):
        for i in range(n):
            clauseseq = "-" + str(x[i]+1) + " 0" + "\n"
            fout.write(clauseseq)
            
def GenMatsuiConstraint(x, u, n, k, left, right, m, fout):
    if (m > 0):
        if ((left == 0) and (right < n-1)):
            for i in range(1, right + 1):
                clauseseq = "-" + str(x[i] + 1) + " " + "-" + str(u[i-1][m-1] + 1) + " 0" + "\n"
                fout.write(clauseseq)
        if ((left > 0) and (right == n-1)):
            for i in range(0, k-m):
                clauseseq = str(u[left-1][i] + 1) + " " + "-" + str(u[right - 1][i+m] + 1) + " 0" + "\n"
                fout.write(clauseseq)
            for i in range(0, k-m+1):
                clauseseq = str(u[left-1][i] + 1) + " " + "-" + str(x[right] + 1) + " " + "-" + str(u[right - 1][i+m-1] + 1) + " 0" + "\n"
                fout.write(clauseseq)
        if ((left > 0) and (right < n-1)):
            for i in range(0, k-m):
                clauseseq = str(u[left-1][i] + 1) + " " + "-" + str(u[right][i+m] + 1) + " 0" + "\n"
                fout.write(clauseseq)
    if (m == 0):
        for i in range(left, right + 1):
            clauseseq = "-" + str(x[i] + 1) + " 0" + "\n"
            fout.write(clauseseq)
            
def Decision(Round, Bias, MatsuiRoundIndex, MatsuiCount, flag):
    TotalBias = 16 * Round * 2
    count_var_num = 0
    time_start = time.time()
    # Declare variables
    xin = []
    p = []
    q = []
    xout = []
    for i in range(Round):
        xin.append([])
        p.append([])
        q.append([])
        xout.append([])
        for j in range(64):
            xin[i].append(0)
        for j in range(16):
            p[i].append(0)
            q[i].append(0)
        for j in range(64):
            xout[i].append(0)
    # Allocate variables
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
    for i in range(Round - 1):
        for j in range(64):
            xout[i][j] = xin[i + 1][j]
    for i in range(64):
        xout[Round - 1][i] = count_var_num
        count_var_num += 1
    auxiliary_var_u = []
    for i in range(TotalBias - 1):
        auxiliary_var_u.append([])
        for j in range(Bias):
            auxiliary_var_u[i].append(count_var_num)
            count_var_num += 1
    # Count the number of clauses in the round function
    count_clause_num = 0
    count_clause_num = CountClausesInRoundFunction(Round, Bias, count_clause_num)
    # Count the number of clauses in the original sequential encoding
    Main_Var_Num = 16 * Round * 2
    CardinalityCons = Bias
    count_clause_num = CountClausesInSequentialEncoding(Main_Var_Num, CardinalityCons, count_clause_num)
    # Count the number of clauses for Matsui's strategy
    for matsui_count in range(0, MatsuiCount):
        StartingRound = MatsuiRoundIndex[matsui_count][0]
        EndingRound = MatsuiRoundIndex[matsui_count][1]
        LeftNode = 16 * StartingRound * 2
        RightNode = 16 * EndingRound * 2 - 1
        PartialCardinalityCons = Bias - LinearBiasBound[StartingRound] - LinearBiasBound[Round - EndingRound]
        count_clause_num = CountClausesForMatsuiStrategy(Main_Var_Num, CardinalityCons, LeftNode, RightNode, PartialCardinalityCons, count_clause_num)
    # Open file
    file = open("Problem-Round" + str(Round) + "-Bias" + str(Bias) + ".cnf", "w")
    file.write("p cnf " + str(count_var_num) + " " + str(count_clause_num) + "\n")
    # Add constraints to claim nonzero input difference
    clauseseq = ""
    for i in range(64):
        clauseseq += str(xin[0][i] + 1) + " "
    clauseseq += "0" + "\n"
    file.write(clauseseq)
    # Add constraints for the round function
    for r in range(Round):
        y = list([])
        P = [0, 16, 32, 48, 1, 17, 33, 49, 2, 18, 34, 50, 3, 19, 35, 51, 4, 20, 36, 52, 5, 21, 37, 53, 6, 22, 38, 54, 7, 23, 39, 55, 8, 24, 40, 56, 9, 25, 41, 57, 10, 26, 42, 58, 11, 27, 43, 59, 12, 28, 44, 60, 13, 29, 45, 61, 14, 30, 46, 62, 15, 31, 47, 63]
        SymbolicCNFConstraintForSbox = [# Linear Bias PRESENT (51)
            [0, 9, 1, 0, 0, 9, 0, 9, 0, 9], [9, 0, 9, 1, 0, 0, 9, 0, 0, 9], [1, 1, 0, 1, 1, 9, 9, 9, 0, 9], [0, 1, 1, 9, 9, 0, 9, 0, 9, 9], [9, 1, 1, 9, 1, 9, 1, 9, 1, 9], [1, 0, 1, 9, 1, 9, 1, 0, 0, 9], [9, 1, 1, 9, 1, 9, 1, 1, 9, 9], [9, 1, 1, 9, 9, 0, 0, 0, 0, 9], [0, 1, 1, 9, 9, 1, 9, 1, 9, 9], [0, 9, 1, 1, 1, 9, 0, 0, 0, 9], [0, 1, 9, 1, 0, 9, 1, 0, 0, 9], [9, 0, 9, 9, 0, 0, 1, 1, 0, 9], [9, 9, 9, 9, 9, 9, 9, 1, 9, 0], [9, 0, 0, 9, 0, 9, 0, 9, 1, 9], [0, 0, 1, 1, 9, 9, 9, 1, 0, 9], [9, 1, 9, 1, 9, 1, 9, 1, 0, 9], [1, 9, 9, 9, 0, 9, 1, 1, 0, 9], [1, 9, 1, 9, 1, 1, 9, 9, 0, 9], [1, 1, 9, 0, 9, 9, 1, 0, 0, 9], [9, 9, 0, 9, 0, 1, 9, 0, 0, 9], [0, 0, 9, 9, 1, 1, 9, 0, 0, 9], [9, 0, 9, 0, 0, 1, 9, 9, 0, 9], [9, 0, 1, 9, 0, 1, 0, 9, 0, 9], [9, 1, 0, 9, 1, 1, 1, 9, 0, 9], [0, 9, 9, 0, 1, 1, 1, 9, 0, 9], [1, 9, 9, 9, 1, 9, 0, 1, 0, 9], [9, 9, 0, 9, 0, 0, 1, 1, 0, 9], [9, 9, 9, 1, 1, 0, 1, 1, 9, 9], [1, 0, 0, 0, 9, 0, 9, 9, 0, 9], [0, 9, 0, 9, 9, 0, 0, 1, 0, 9], [9, 9, 0, 1, 9, 0, 0, 0, 0, 9], [9, 0, 1, 0, 9, 0, 0, 9, 0, 9], [9, 9, 1, 1, 0, 0, 9, 0, 0, 9], [9, 1, 9, 0, 0, 0, 0, 9, 9, 9], [9, 9, 0, 0, 9, 1, 0, 9, 0, 9], [0, 9, 9, 0, 9, 0, 9, 0, 0, 1], [0, 0, 0, 9, 9, 0, 9, 9, 9, 1], [9, 9, 9, 9, 1, 9, 9, 9, 9, 0], [0, 9, 9, 9, 0, 0, 0, 9, 9, 1], [1, 9, 9, 1, 9, 1, 9, 9, 0, 9], [9, 9, 9, 9, 9, 1, 9, 9, 9, 0], [9, 9, 9, 9, 9, 9, 9, 9, 1, 0], [9, 9, 9, 9, 9, 9, 1, 9, 9, 0], [9, 1, 1, 9, 0, 9, 0, 9, 1, 9], [9, 0, 0, 9, 1, 9, 1, 9, 1, 9], [0, 9, 9, 9, 1, 1, 0, 9, 1, 9], [1, 1, 0, 9, 9, 0, 9, 9, 1, 9], [1, 0, 1, 9, 9, 0, 9, 9, 1, 9], [0, 9, 9, 9, 0, 1, 1, 9, 1, 9], [0, 1, 1, 9, 9, 9, 9, 9, 1, 9], [9, 9, 9, 9, 1, 0, 1, 9, 1, 9]]
        for i in range(64):
            y += [xout[r][P[i]]]
        for i in range(16):
            X = list([])
            for j in range(4):
                X += [xin[r][4 * i + j]]
            for j in range(4):
                X += [y[4 * i + j]]
            X += [p[r][i]]
            X += [q[r][i]]
            for j in range(51):
                clauseseq = ""
                for k in range(10):
                    if (SymbolicCNFConstraintForSbox[j][k] == 1):
                        clauseseq += "-" + str(X[k] + 1) + " "
                    if (SymbolicCNFConstraintForSbox[j][k] == 0):
                        clauseseq += str(X[k] + 1) + " "
                clauseseq += "0" + "\n"
                file.write(clauseseq)
    # Add constraints for the original sequential encoding
    Main_Vars = list([])
    for r in range(Round):
        for i in range(16):
            Main_Vars += [p[Round - 1 - r][i]]
            Main_Vars += [q[Round - 1 - r][i]]
    GenSequentialEncoding(Main_Vars, auxiliary_var_u, Main_Var_Num, CardinalityCons, file)
    # Add constraints for Matsui's strategy
    for matsui_count in range(0, MatsuiCount):
        StartingRound = MatsuiRoundIndex[matsui_count][0]
        EndingRound = MatsuiRoundIndex[matsui_count][1]
        LeftNode = 16 * StartingRound * 2
        RightNode = 16 * EndingRound * 2 - 1
        PartialCardinalityCons = Bias - LinearBiasBound[StartingRound] - LinearBiasBound[Round - EndingRound]
        GenMatsuiConstraint(Main_Vars, auxiliary_var_u, Main_Var_Num, CardinalityCons, LeftNode, RightNode, PartialCardinalityCons, file)
    file.close()
    # Call solver cadical
    order = "~/Install/cadical/build/cadical " + "Problem-Round" + str(Round) + "-Bias" + str(Bias) + ".cnf > Round" + str(Round) + "-Bias" + str(Bias) + "-solution.out"
    os.system(order)
    # Extracting results
    order = "sed -n '/s SATISFIABLE/p' Round" + str(Round) + "-Bias" + str(Bias) + "-solution.out > SatSolution.out"
    os.system(order)
    order = "sed -n '/s UNSATISFIABLE/p' Round" + str(Round) + "-Bias" + str(Bias) + "-solution.out > UnsatSolution.out"
    os.system(order)
    satsol = open("SatSolution.out")
    unsatsol = open("UnsatSolution.out")
    satresult = satsol.readlines()
    unsatresult = unsatsol.readlines()
    satsol.close()
    unsatsol.close()
    if ((len(satresult) == 0) and (len(unsatresult) > 0)):
        flag = False
    if ((len(satresult) > 0) and (len(unsatresult) == 0)):
        flag = True
    order = "rm SatSolution.out"
    os.system(order)
    order = "rm UnsatSolution.out"
    os.system(order)
    # Removing cnf file
    order = "rm Problem-Round" + str(Round) + "-Bias" + str(Bias) + ".cnf"
    os.system(order)
    time_end = time.time()
    # Printing solutions
    if (flag == True):
        print("Round:" + str(Round) + "; Bias: " + str(Bias) + "; Sat; TotalCost: " + str(time_end - time_start))
    else:
        print("Round:" + str(Round) + "; Bias: " + str(Bias) + "; Unsat; TotalCost: " + str(time_end - time_start))
    return flag

    
# main function
TotalTimeStart = time.time()
for totalround in range(SearchRoundStart, SearchRoundEnd):
    flag = False
    time_start = time.time()
    MatsuiRoundIndex = []
    MatsuiCount = 0
    # Generate Matsui condition under choice 1
    if (GroupConstraintChoice == 1):
        for group in range(0, GroupNumForChoice1):
            for round in range(1, totalround - group + 1):
                MatsuiRoundIndex.append([])
                MatsuiRoundIndex[MatsuiCount].append(group)
                MatsuiRoundIndex[MatsuiCount].append(group + round)
                MatsuiCount += 1
    # Printing Matsui conditions
    file = open("MatsuiCondition.out", "a")
    resultseq = "Round: " + str(totalround) + "; Partial Constraint Num: " + str(MatsuiCount) + "\n"
    file.write(resultseq)
    file.write(str(MatsuiRoundIndex) + "\n")
    file.close()
    # 从最大偏差值开始搜索（每轮16个S盒，每个贡献最多2的偏差）
    CountBias = 16 * totalround * 2
    while (flag == False) and (CountBias >= 0):
        flag = Decision(totalround, CountBias, MatsuiRoundIndex, MatsuiCount, flag)
        CountBias -= 1
    LinearBiasBound[totalround] = CountBias + 1
    time_end = time.time()
    file = open("RunTimeSummarise.out", "a")
    resultseq = "Round: " + str(totalround) + "; Linear Biase: " + str(LinearBiasBound[totalround]) + "; Runtime: " + str(time_end - time_start) + "\n"
    file.write(resultseq)
    file.close()
print(str(LinearBiasBound))
TotalTimeEnd = time.time()
print("Total Runtime: " + str(TotalTimeEnd - TotalTimeStart))
file = open("RunTimeSummarise.out", "a")
resultseq = "Total Runtime: " + str(TotalTimeEnd - TotalTimeStart)
file.write(resultseq)

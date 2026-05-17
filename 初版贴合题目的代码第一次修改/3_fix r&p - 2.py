import os
import time
import random

# ========== 用户可配置参数 ==========
target_round = 1          # 要搜索的固定轮数
target_prob = 1          # 要搜索的固定概率（活跃S盒个数）
max_solutions = -1        # 最大解数量，-1表示枚举所有解
# ===================================

FullRound = 6

SearchRoundStart = 1
SearchRoundEnd = 2
InitialLowerBound = 0

GroupConstraintChoice = 1

# Parameters for choice 1
GroupNumForChoice1 = 1

DifferentialProbabilityBound = list([])
for i in range(FullRound):
    DifferentialProbabilityBound += [0]

NumOfConstraint = [30, 30, 30, 30, 30, 30, 30, 30]

# 统计每轮中函数的S盒CNF子句数量
def CountClausesInRoundFunction(Round, Probability, clause_num):
    count = clause_num
    # Nonzero input
    count += 1
    # Cluases for Round function
    for r in range(Round):
        for block in range(8):
            count += NumOfConstraint[block]
        # for i in range(16):
        #     count += 2
    return count

# 统计基数约束的CNF子句数量（序列编码方法）
def CountClausesInSequentialEncoding(main_var_num, cardinalitycons, clause_num):
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

# 基数约束的CNF子句（序列编码方法）
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


# 统计Matsui边界条件CNF子句数量
def CountClausesForMatsuiStrategy(n, k, left, right, m, clausenum):
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

# Matsui边界条件的CNF
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

# 统计置换中两个变量相等条件CNF子句数量
def Countperm(Round, clause_num):
    count = clause_num
    for r in range(Round):
        for i in range(32):
            count += 2
    return count


# 统计列混合中两个相等条件CNF子句数量
def Countequal(Round, clause_num):
    count = clause_num
    for r in range(Round):
        for i in range(16):
            count += 2
    return count


# 统计列混合中3异或条件CNF子句数量
def Count3xor(Round, clause_num):
    count = clause_num
    for r in range(Round):
        for i in range(16):
            count += 8
    return count


# 两个变量相等的CNF子句
def Genequal(a, b, fout):
    clauseseq = "-" + str(a + 1) + " " + str(b + 1) + " 0\n"
    fout.write(clauseseq)
    clauseseq = "-" + str(b + 1) + " " + str(a + 1) + " 0\n"
    fout.write(clauseseq)

# 3异或的CNF子句
def Gen3or(a, b, c, d, fout):
    clauseseq = str(a + 1) + " " + str(b + 1) + " " + str(c + 1) + " " + "-" + str(d + 1) + " 0\n"
    fout.write(clauseseq)
    clauseseq = str(a + 1) + " " + str(b + 1) + " " + "-" + str(c + 1) + " " + str(d + 1) + " 0\n"
    fout.write(clauseseq)
    clauseseq = str(a + 1) + " " + "-" + str(b + 1) + " " + str(c + 1) + " " + str(d + 1) + " 0\n"
    fout.write(clauseseq)
    clauseseq = "-" + str(a + 1) + " " + str(b + 1) + " " + str(c + 1) + " " + str(d + 1) + " 0\n"
    fout.write(clauseseq)
    clauseseq = "-" + str(a + 1) + " " + "-" + str(b + 1) + " " + "-" + str(c + 1) + " " + str(d + 1) + " 0\n"
    fout.write(clauseseq)
    clauseseq = "-" + str(a + 1) + " " + "-" + str(b + 1) + " " + str(c + 1) + " " + "-" + str(d + 1) + " 0\n"
    fout.write(clauseseq)
    clauseseq = "-" + str(a + 1) + " " + str(b + 1) + " " + "-" + str(c + 1) + " " + "-" + str(d + 1) + " 0\n"
    fout.write(clauseseq)
    clauseseq = str(a + 1) + " " + "-" + str(b + 1) + " " + "-" + str(c + 1) + " " + "-" + str(d + 1) + " 0\n"
    fout.write(clauseseq)


def Decision(Round, Probability, MatsuiRoundIndex, MatsuiCount, extra_clauses):
    TotalSbox = 8 * Round * 2  # 每轮有8个S盒
    count_var_num = 0
    time_start = time.time()

    # Declare variables - CipherFour是16位分组
    xin = []
    sout = []
    pout = []
    xout = []
    p = []
    q = []
    for i in range(Round):
        xin.append([])
        sout.append([])
        pout.append([])
        xout.append([])
        p.append([])
        q.append([])
        for j in range(32):
            xin[i].append(0)
        for j in range(32):
            sout[i].append(0)
        for j in range(32):
            pout[i].append(0)
        for j in range(32):
            xout[i].append(0)
        for j in range(8):
            p[i].append(0)
            q[i].append(0)
    for i in range(Round):
        for j in range(32):
            xin[i][j] = count_var_num
            count_var_num += 1
        for j in range(32):
            sout[i][j] = count_var_num
            count_var_num += 1
        for j in range(32):
            pout[i][j] = count_var_num
            count_var_num += 1
        for j in range(8):
            p[i][j] = count_var_num
            count_var_num += 1
        for j in range(8):
            q[i][j] = count_var_num
            count_var_num += 1

    # 连接两轮编号
    for i in range(Round - 1):
        for j in range(32):
            xout[i][j] = xin[i + 1][j]

    # 对最后一轮xout编号
    for i in range(32):
        xout[Round - 1][i] = count_var_num
        count_var_num += 1

    # 序列编码辅助变量
    auxiliary_var_u = []
    for i in range(TotalSbox - 1):
        auxiliary_var_u.append([])
        for j in range(Probability):
            auxiliary_var_u[i].append(count_var_num)
            count_var_num += 1

    # 轮函数子句数量
    count_clause_num = 0
    count_clause_num = CountClausesInRoundFunction(Round, Probability, count_clause_num)

    count_clause_num = Countperm(Round, count_clause_num)  # 置换
    count_clause_num = Countequal(Round, count_clause_num)  # 列混合中的相等
    count_clause_num = Count3xor(Round, count_clause_num)  # 列混合中的3异或

    # 序列编码子句数量
    Main_Var_Num = 8 * Round * 2
    CardinalityCons = Probability
    count_clause_num = CountClausesInSequentialEncoding(Main_Var_Num, CardinalityCons, count_clause_num)

    # Matsui约束子句数量
    for matsui_count in range(0, MatsuiCount):
        StartingRound = MatsuiRoundIndex[matsui_count][0]
        EndingRound = MatsuiRoundIndex[matsui_count][1]
        LeftNode = 8 * StartingRound * 2
        RightNode = 8 * EndingRound * 2 - 1
        PartialCardinalityCons = Probability - DifferentialProbabilityBound[StartingRound] - DifferentialProbabilityBound[Round - EndingRound]
        count_clause_num = CountClausesForMatsuiStrategy(Main_Var_Num, CardinalityCons, LeftNode, RightNode, PartialCardinalityCons, count_clause_num)

    # 加上额外子句（禁止已找到的解）
    count_clause_num += len(extra_clauses)

    # 创建CNF文件
    filename = "Problem-Round" + str(Round) + "-Probability" + str(Probability) + ".cnf"
    file = open(filename, "w")
    file.write("p cnf " + str(count_var_num) + " " + str(count_clause_num) + "\n")

    # 非零输入约束
    clauseseq = ""
    for i in range(32):
        clauseseq += str(xin[0][i] + 1) + " "
    clauseseq += "0" + "\n"
    file.write(clauseseq)

    # CipherFour S-box DDT
    CipherFour_Sbox = [[[0, 9, 9, 0, 9, 9, 9, 9, 1, 9], [9, 9, 9, 9, 9, 9, 0, 0, 1, 9], [9, 9, 9, 0, 9, 9, 9, 0, 1, 9], [0, 9, 9, 9, 9, 9, 1, 1, 1, 9], [1, 9, 9, 1, 9, 9, 0, 9, 1, 9], [9, 9, 9, 9, 9, 1, 9, 9, 9, 0], [9, 9, 9, 9, 9, 9, 1, 9, 9, 0], [1, 9, 9, 0, 9, 0, 9, 9, 0, 9], [9, 9, 9, 1, 0, 9, 9, 0, 0, 9], [1, 9, 9, 9, 9, 9, 1, 1, 0, 9], [9, 9, 0, 9, 9, 0, 9, 1, 0, 9], [9, 9, 9, 9, 1, 9, 9, 9, 9, 0], [0, 9, 9, 0, 9, 9, 0, 0, 9, 1], [9, 9, 0, 9, 9, 9, 0, 1, 0, 9], [0, 9, 1, 9, 9, 1, 1, 9, 0, 9], [0, 0, 9, 9, 1, 9, 1, 9, 0, 9], [0, 9, 0, 9, 9, 1, 9, 0, 0, 9], [9, 9, 9, 1, 9, 9, 1, 0, 0, 9], [9, 9, 1, 9, 9, 0, 0, 0, 9, 9], [9, 0, 9, 0, 0, 9, 1, 9, 0, 9], [9, 9, 9, 9, 9, 9, 9, 1, 9, 0], [0, 1, 9, 0, 9, 9, 0, 9, 9, 9], [1, 9, 1, 9, 1, 9, 0, 0, 9, 9], [9, 1, 9, 9, 1, 9, 0, 1, 0, 9], [0, 1, 9, 1, 0, 9, 9, 9, 0, 9], [1, 9, 9, 0, 9, 9, 9, 1, 0, 9], [9, 0, 9, 1, 0, 9, 0, 9, 0, 9], [9, 1, 9, 0, 1, 1, 9, 0, 9, 9], [0, 9, 9, 1, 9, 9, 0, 1, 0, 9], [9, 9, 9, 0, 1, 9, 0, 0, 9, 9]],
                       [[0, 9, 9, 0, 9, 9, 9, 9, 1, 9], [9, 9, 9, 9, 9, 9, 0, 0, 1, 9], [9, 9, 9, 0, 9, 9, 9, 0, 1, 9], [0, 9, 9, 9, 9, 9, 1, 1, 1, 9], [1, 9, 9, 1, 9, 9, 0, 9, 1, 9], [9, 9, 9, 9, 9, 1, 9, 9, 9, 0], [9, 9, 9, 9, 9, 9, 1, 9, 9, 0], [1, 9, 9, 0, 9, 0, 9, 9, 0, 9], [9, 9, 9, 1, 0, 9, 9, 0, 0, 9], [1, 9, 9, 9, 9, 9, 1, 1, 0, 9], [9, 9, 0, 9, 9, 0, 9, 1, 0, 9], [9, 9, 9, 9, 1, 9, 9, 9, 9, 0], [0, 9, 9, 0, 9, 9, 0, 0, 9, 1], [9, 9, 0, 9, 9, 9, 0, 1, 0, 9], [0, 9, 1, 9, 9, 1, 1, 9, 0, 9], [0, 0, 9, 9, 1, 9, 1, 9, 0, 9], [0, 9, 0, 9, 9, 1, 9, 0, 0, 9], [9, 9, 9, 1, 9, 9, 1, 0, 0, 9], [9, 9, 1, 9, 9, 0, 0, 0, 9, 9], [9, 0, 9, 0, 0, 9, 1, 9, 0, 9], [9, 9, 9, 9, 9, 9, 9, 1, 9, 0], [0, 1, 9, 0, 9, 9, 0, 9, 9, 9], [1, 9, 1, 9, 1, 9, 0, 0, 9, 9], [9, 1, 9, 9, 1, 9, 0, 1, 0, 9], [0, 1, 9, 1, 0, 9, 9, 9, 0, 9], [1, 9, 9, 0, 9, 9, 9, 1, 0, 9], [9, 0, 9, 1, 0, 9, 0, 9, 0, 9], [9, 1, 9, 0, 1, 1, 9, 0, 9, 9], [0, 9, 9, 1, 9, 9, 0, 1, 0, 9], [9, 9, 9, 0, 1, 9, 0, 0, 9, 9]],
                       [[0, 9, 9, 0, 9, 9, 9, 9, 1, 9], [9, 9, 9, 9, 9, 9, 0, 0, 1, 9], [9, 9, 9, 0, 9, 9, 9, 0, 1, 9], [0, 9, 9, 9, 9, 9, 1, 1, 1, 9], [1, 9, 9, 1, 9, 9, 0, 9, 1, 9], [9, 9, 9, 9, 9, 1, 9, 9, 9, 0], [9, 9, 9, 9, 9, 9, 1, 9, 9, 0], [1, 9, 9, 0, 9, 0, 9, 9, 0, 9], [9, 9, 9, 1, 0, 9, 9, 0, 0, 9], [1, 9, 9, 9, 9, 9, 1, 1, 0, 9], [9, 9, 0, 9, 9, 0, 9, 1, 0, 9], [9, 9, 9, 9, 1, 9, 9, 9, 9, 0], [0, 9, 9, 0, 9, 9, 0, 0, 9, 1], [9, 9, 0, 9, 9, 9, 0, 1, 0, 9], [0, 9, 1, 9, 9, 1, 1, 9, 0, 9], [0, 0, 9, 9, 1, 9, 1, 9, 0, 9], [0, 9, 0, 9, 9, 1, 9, 0, 0, 9], [9, 9, 9, 1, 9, 9, 1, 0, 0, 9], [9, 9, 1, 9, 9, 0, 0, 0, 9, 9], [9, 0, 9, 0, 0, 9, 1, 9, 0, 9], [9, 9, 9, 9, 9, 9, 9, 1, 9, 0], [0, 1, 9, 0, 9, 9, 0, 9, 9, 9], [1, 9, 1, 9, 1, 9, 0, 0, 9, 9], [9, 1, 9, 9, 1, 9, 0, 1, 0, 9], [0, 1, 9, 1, 0, 9, 9, 9, 0, 9], [1, 9, 9, 0, 9, 9, 9, 1, 0, 9], [9, 0, 9, 1, 0, 9, 0, 9, 0, 9], [9, 1, 9, 0, 1, 1, 9, 0, 9, 9], [0, 9, 9, 1, 9, 9, 0, 1, 0, 9], [9, 9, 9, 0, 1, 9, 0, 0, 9, 9]],
                       [[0, 9, 9, 0, 9, 9, 9, 9, 1, 9], [9, 9, 9, 9, 9, 9, 0, 0, 1, 9], [9, 9, 9, 0, 9, 9, 9, 0, 1, 9], [0, 9, 9, 9, 9, 9, 1, 1, 1, 9], [1, 9, 9, 1, 9, 9, 0, 9, 1, 9], [9, 9, 9, 9, 9, 1, 9, 9, 9, 0], [9, 9, 9, 9, 9, 9, 1, 9, 9, 0], [1, 9, 9, 0, 9, 0, 9, 9, 0, 9], [9, 9, 9, 1, 0, 9, 9, 0, 0, 9], [1, 9, 9, 9, 9, 9, 1, 1, 0, 9], [9, 9, 0, 9, 9, 0, 9, 1, 0, 9], [9, 9, 9, 9, 1, 9, 9, 9, 9, 0], [0, 9, 9, 0, 9, 9, 0, 0, 9, 1], [9, 9, 0, 9, 9, 9, 0, 1, 0, 9], [0, 9, 1, 9, 9, 1, 1, 9, 0, 9], [0, 0, 9, 9, 1, 9, 1, 9, 0, 9], [0, 9, 0, 9, 9, 1, 9, 0, 0, 9], [9, 9, 9, 1, 9, 9, 1, 0, 0, 9], [9, 9, 1, 9, 9, 0, 0, 0, 9, 9], [9, 0, 9, 0, 0, 9, 1, 9, 0, 9], [9, 9, 9, 9, 9, 9, 9, 1, 9, 0], [0, 1, 9, 0, 9, 9, 0, 9, 9, 9], [1, 9, 1, 9, 1, 9, 0, 0, 9, 9], [9, 1, 9, 9, 1, 9, 0, 1, 0, 9], [0, 1, 9, 1, 0, 9, 9, 9, 0, 9], [1, 9, 9, 0, 9, 9, 9, 1, 0, 9], [9, 0, 9, 1, 0, 9, 0, 9, 0, 9], [9, 1, 9, 0, 1, 1, 9, 0, 9, 9], [0, 9, 9, 1, 9, 9, 0, 1, 0, 9], [9, 9, 9, 0, 1, 9, 0, 0, 9, 9]],
                       [[0, 9, 9, 0, 9, 9, 9, 9, 1, 9], [9, 9, 9, 9, 9, 9, 0, 0, 1, 9], [9, 9, 9, 0, 9, 9, 9, 0, 1, 9], [0, 9, 9, 9, 9, 9, 1, 1, 1, 9], [1, 9, 9, 1, 9, 9, 0, 9, 1, 9], [9, 9, 9, 9, 9, 1, 9, 9, 9, 0], [9, 9, 9, 9, 9, 9, 1, 9, 9, 0], [1, 9, 9, 0, 9, 0, 9, 9, 0, 9], [9, 9, 9, 1, 0, 9, 9, 0, 0, 9], [1, 9, 9, 9, 9, 9, 1, 1, 0, 9], [9, 9, 0, 9, 9, 0, 9, 1, 0, 9], [9, 9, 9, 9, 1, 9, 9, 9, 9, 0], [0, 9, 9, 0, 9, 9, 0, 0, 9, 1], [9, 9, 0, 9, 9, 9, 0, 1, 0, 9], [0, 9, 1, 9, 9, 1, 1, 9, 0, 9], [0, 0, 9, 9, 1, 9, 1, 9, 0, 9], [0, 9, 0, 9, 9, 1, 9, 0, 0, 9], [9, 9, 9, 1, 9, 9, 1, 0, 0, 9], [9, 9, 1, 9, 9, 0, 0, 0, 9, 9], [9, 0, 9, 0, 0, 9, 1, 9, 0, 9], [9, 9, 9, 9, 9, 9, 9, 1, 9, 0], [0, 1, 9, 0, 9, 9, 0, 9, 9, 9], [1, 9, 1, 9, 1, 9, 0, 0, 9, 9], [9, 1, 9, 9, 1, 9, 0, 1, 0, 9], [0, 1, 9, 1, 0, 9, 9, 9, 0, 9], [1, 9, 9, 0, 9, 9, 9, 1, 0, 9], [9, 0, 9, 1, 0, 9, 0, 9, 0, 9], [9, 1, 9, 0, 1, 1, 9, 0, 9, 9], [0, 9, 9, 1, 9, 9, 0, 1, 0, 9], [9, 9, 9, 0, 1, 9, 0, 0, 9, 9]],
                       [[0, 9, 9, 0, 9, 9, 9, 9, 1, 9], [9, 9, 9, 9, 9, 9, 0, 0, 1, 9], [9, 9, 9, 0, 9, 9, 9, 0, 1, 9],
                        [0, 9, 9, 9, 9, 9, 1, 1, 1, 9], [1, 9, 9, 1, 9, 9, 0, 9, 1, 9], [9, 9, 9, 9, 9, 1, 9, 9, 9, 0],
                        [9, 9, 9, 9, 9, 9, 1, 9, 9, 0], [1, 9, 9, 0, 9, 0, 9, 9, 0, 9], [9, 9, 9, 1, 0, 9, 9, 0, 0, 9],
                        [1, 9, 9, 9, 9, 9, 1, 1, 0, 9], [9, 9, 0, 9, 9, 0, 9, 1, 0, 9], [9, 9, 9, 9, 1, 9, 9, 9, 9, 0],
                        [0, 9, 9, 0, 9, 9, 0, 0, 9, 1], [9, 9, 0, 9, 9, 9, 0, 1, 0, 9], [0, 9, 1, 9, 9, 1, 1, 9, 0, 9],
                        [0, 0, 9, 9, 1, 9, 1, 9, 0, 9], [0, 9, 0, 9, 9, 1, 9, 0, 0, 9], [9, 9, 9, 1, 9, 9, 1, 0, 0, 9],
                        [9, 9, 1, 9, 9, 0, 0, 0, 9, 9], [9, 0, 9, 0, 0, 9, 1, 9, 0, 9], [9, 9, 9, 9, 9, 9, 9, 1, 9, 0],
                        [0, 1, 9, 0, 9, 9, 0, 9, 9, 9], [1, 9, 1, 9, 1, 9, 0, 0, 9, 9], [9, 1, 9, 9, 1, 9, 0, 1, 0, 9],
                        [0, 1, 9, 1, 0, 9, 9, 9, 0, 9], [1, 9, 9, 0, 9, 9, 9, 1, 0, 9], [9, 0, 9, 1, 0, 9, 0, 9, 0, 9],
                        [9, 1, 9, 0, 1, 1, 9, 0, 9, 9], [0, 9, 9, 1, 9, 9, 0, 1, 0, 9], [9, 9, 9, 0, 1, 9, 0, 0, 9, 9]],
                       [[0, 9, 9, 0, 9, 9, 9, 9, 1, 9], [9, 9, 9, 9, 9, 9, 0, 0, 1, 9], [9, 9, 9, 0, 9, 9, 9, 0, 1, 9],
                        [0, 9, 9, 9, 9, 9, 1, 1, 1, 9], [1, 9, 9, 1, 9, 9, 0, 9, 1, 9], [9, 9, 9, 9, 9, 1, 9, 9, 9, 0],
                        [9, 9, 9, 9, 9, 9, 1, 9, 9, 0], [1, 9, 9, 0, 9, 0, 9, 9, 0, 9], [9, 9, 9, 1, 0, 9, 9, 0, 0, 9],
                        [1, 9, 9, 9, 9, 9, 1, 1, 0, 9], [9, 9, 0, 9, 9, 0, 9, 1, 0, 9], [9, 9, 9, 9, 1, 9, 9, 9, 9, 0],
                        [0, 9, 9, 0, 9, 9, 0, 0, 9, 1], [9, 9, 0, 9, 9, 9, 0, 1, 0, 9], [0, 9, 1, 9, 9, 1, 1, 9, 0, 9],
                        [0, 0, 9, 9, 1, 9, 1, 9, 0, 9], [0, 9, 0, 9, 9, 1, 9, 0, 0, 9], [9, 9, 9, 1, 9, 9, 1, 0, 0, 9],
                        [9, 9, 1, 9, 9, 0, 0, 0, 9, 9], [9, 0, 9, 0, 0, 9, 1, 9, 0, 9], [9, 9, 9, 9, 9, 9, 9, 1, 9, 0],
                        [0, 1, 9, 0, 9, 9, 0, 9, 9, 9], [1, 9, 1, 9, 1, 9, 0, 0, 9, 9], [9, 1, 9, 9, 1, 9, 0, 1, 0, 9],
                        [0, 1, 9, 1, 0, 9, 9, 9, 0, 9], [1, 9, 9, 0, 9, 9, 9, 1, 0, 9], [9, 0, 9, 1, 0, 9, 0, 9, 0, 9],
                        [9, 1, 9, 0, 1, 1, 9, 0, 9, 9], [0, 9, 9, 1, 9, 9, 0, 1, 0, 9], [9, 9, 9, 0, 1, 9, 0, 0, 9, 9]],
                       [[0, 9, 9, 0, 9, 9, 9, 9, 1, 9], [9, 9, 9, 9, 9, 9, 0, 0, 1, 9], [9, 9, 9, 0, 9, 9, 9, 0, 1, 9],
                        [0, 9, 9, 9, 9, 9, 1, 1, 1, 9], [1, 9, 9, 1, 9, 9, 0, 9, 1, 9], [9, 9, 9, 9, 9, 1, 9, 9, 9, 0],
                        [9, 9, 9, 9, 9, 9, 1, 9, 9, 0], [1, 9, 9, 0, 9, 0, 9, 9, 0, 9], [9, 9, 9, 1, 0, 9, 9, 0, 0, 9],
                        [1, 9, 9, 9, 9, 9, 1, 1, 0, 9], [9, 9, 0, 9, 9, 0, 9, 1, 0, 9], [9, 9, 9, 9, 1, 9, 9, 9, 9, 0],
                        [0, 9, 9, 0, 9, 9, 0, 0, 9, 1], [9, 9, 0, 9, 9, 9, 0, 1, 0, 9], [0, 9, 1, 9, 9, 1, 1, 9, 0, 9],
                        [0, 0, 9, 9, 1, 9, 1, 9, 0, 9], [0, 9, 0, 9, 9, 1, 9, 0, 0, 9], [9, 9, 9, 1, 9, 9, 1, 0, 0, 9],
                        [9, 9, 1, 9, 9, 0, 0, 0, 9, 9], [9, 0, 9, 0, 0, 9, 1, 9, 0, 9], [9, 9, 9, 9, 9, 9, 9, 1, 9, 0],
                        [0, 1, 9, 0, 9, 9, 0, 9, 9, 9], [1, 9, 1, 9, 1, 9, 0, 0, 9, 9], [9, 1, 9, 9, 1, 9, 0, 1, 0, 9],
                        [0, 1, 9, 1, 0, 9, 9, 9, 0, 9], [1, 9, 9, 0, 9, 9, 9, 1, 0, 9], [9, 0, 9, 1, 0, 9, 0, 9, 0, 9],
                        [9, 1, 9, 0, 1, 1, 9, 0, 9, 9], [0, 9, 9, 1, 9, 9, 0, 1, 0, 9], [9, 9, 9, 0, 1, 9, 0, 0, 9, 9]]
                       ]
    # P = [0, 1, 2, 3, 20, 21, 22, 23, 8, 9, 10, 11, 28, 29, 30, 31, 16, 17, 18, 19, 4, 5, 6, 7, 24, 25, 26, 27, 12, 13, 14, 15]


    # 轮函数约束
    for r in range(Round):
        for block in range(8):
            X = list([])
            for i in range(4):
                X += [xin[r][4 * block + i]]
            for i in range(4):
                X += [sout[r][4 * block + i]]
            X += [p[r][block]]
            X += [q[r][block]]
            for i in range(NumOfConstraint[block]):
                clauseseq = ""
                for k in range(10):
                    if (CipherFour_Sbox[block][i][k] == 1):
                        clauseseq += "-" + str(X[k] + 1) + " "
                    if (CipherFour_Sbox[block][i][k] == 0):
                        clauseseq += str(X[k] + 1) + " "
                clauseseq += "0" + "\n"
                file.write(clauseseq)


        # # P置换
        # for i in range(32):
        #     a = xout[r][i]
        #     b = sout[r][P[i]]
        #     # a == b 等价于 (-a OR b) 和 (-b OR a)
        #     file.write("-" + str(a + 1) + " " + str(b + 1) + " 0\n")
        #     file.write("-" + str(b + 1) + " " + str(a + 1) + " 0\n")
        P = [0, 5, 2, 7, 4, 1, 6, 3]
        #  P置换
    for r in range(Round):
        for j in range(4):
            Genequal(sout[r][0 + j], pout[r][4 * P[0] + j], file)
            Genequal(sout[r][1 * 4 + j], pout[r][4 * P[1] + j], file)
            Genequal(sout[r][2 * 4 + j], pout[r][4 * P[2] + j], file)
            Genequal(sout[r][3 * 4 + j], pout[r][4 * P[3] + j], file)
            Genequal(sout[r][4 * 4 + j], pout[r][4 * P[4] + j], file)
            Genequal(sout[r][5 * 4 + j], pout[r][4 * P[5] + j], file)
            Genequal(sout[r][6 * 4 + j], pout[r][4 * P[6] + j], file)
            Genequal(sout[r][7 * 4 + j], pout[r][4 * P[7] + j], file)

    #  列混合中的相等
    for r in range(Round):
        for j in range(4):
            Genequal(pout[r][1 * 4 + j], xout[r][4 * 2 + j], file)
            Genequal(pout[r][3 * 4 + j], xout[r][4 * 0 + j], file)
            Genequal(pout[r][5 * 4 + j], xout[r][4 * 6 + j], file)
            Genequal(pout[r][7 * 4 + j], xout[r][4 * 4 + j], file)

    for r in range(Round):
        for j in range(4):
            Gen3or(xout[r][0 * 4 + j], xout[r][1 * 4 + j], xout[r][3 * 4 + j], pout[r][0 * 4 + j], file)
            Gen3or(xout[r][0 * 4 + j], xout[r][2 * 4 + j], xout[r][3 * 4 + j], pout[r][2 * 4 + j], file)
            Gen3or(xout[r][4 * 4 + j], xout[r][5 * 4 + j], xout[r][7 * 4 + j], pout[r][4 * 4 + j], file)
            Gen3or(xout[r][4 * 4 + j], xout[r][6 * 4 + j], xout[r][7 * 4 + j], pout[r][6 * 4 + j], file)


    # 基数约束
    Main_Vars = []
    for r in range(Round):
        for i in range(8):  # 每轮8个S盒
            Main_Vars += [p[Round - 1 - r][i]]
            Main_Vars += [q[Round - 1 - r][i]]
    GenSequentialEncoding(Main_Vars, auxiliary_var_u, Main_Var_Num, CardinalityCons, file)

    # Matsui约束
    for matsui_count in range(0, MatsuiCount):
        StartingRound = MatsuiRoundIndex[matsui_count][0]
        EndingRound = MatsuiRoundIndex[matsui_count][1]
        LeftNode = 8 * StartingRound * 2
        RightNode = 8 * EndingRound * 2 - 1
        PartialCardinalityCons = Probability - DifferentialProbabilityBound[StartingRound] - DifferentialProbabilityBound[Round - EndingRound]
        GenMatsuiConstraint(Main_Vars, auxiliary_var_u, Main_Var_Num, CardinalityCons, LeftNode, RightNode, PartialCardinalityCons, file)

    # 写入额外子句（禁止已找到的解）
    for clause in extra_clauses:
        clause_str = " ".join(str(lit) for lit in clause) + " 0\n"
        file.write(clause_str)

    file.close()

    # Call solver cadical
    solution_file = "Round" + str(Round) + "-Probability" + str(Probability) + "-solution.out"
    order = "./cadical " + filename + " > " + solution_file
    os.system(order)



    # 解析结果
    sat = False
    solution_dict = {}
    with open(solution_file, "r") as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith("s SATISFIABLE"):
                sat = True
        if sat:
            # 收集所有v行中的数字
            all_vals = []
            for line in lines:
                if line.startswith("v "):
                    parts = line.strip().split()
                    all_vals.extend(parts[1:])
            # 解析直到遇到0
            for token in all_vals:
                val = int(token)
                if val == 0:
                    break
                var = abs(val)
                value = 1 if val > 0 else 0
                solution_dict[var] = value

    # # 删除临时文件
    # os.remove(filename)
    # os.remove(solution_file)

    time_end = time.time()
    if sat:
        print("Round:" + str(Round) + "; Probability: " + str(Probability) + "; Sat; TotalCost: " + str(time_end - time_start))
    else:
        print("Round:" + str(Round) + "; Probability: " + str(Probability) + "; Unsat; TotalCost: " + str(time_end - time_start))

    return sat, solution_dict, count_var_num

# ========== 主程序 ==========
TotalTimeStart = time.time()

totalround = target_round
prob = target_prob

# 生成Matsui条件
MatsuiRoundIndex = []
MatsuiCount = 0
if GroupConstraintChoice == 1:
    for group in range(0, GroupNumForChoice1):
        for round in range(1, totalround - group + 1):
            MatsuiRoundIndex.append([group, group + round])
            MatsuiCount += 1

# 打印Matsui条件到文件
with open("MatsuiCondition.out", "a") as f:
    f.write(f"Round: {totalround}; Partial Constraint Num: {MatsuiCount}\n")
    f.write(str(MatsuiRoundIndex) + "\n")

extra_clauses = []          # 当前概率下的禁止子句列表
solution_count = 0
found_any = False

while True:
    sat, solution, var_num = Decision(totalround, prob, MatsuiRoundIndex, MatsuiCount, extra_clauses)
    if sat:
        found_any = True
        solution_count += 1

        # ========== 新增：保存解到文件 ==========
        sol_filename = f"solution_r{totalround}_p{prob}_{solution_count}.txt"
        with open(sol_filename, "w") as sf:
            sf.write("v ")
            # 按变量编号顺序输出赋值
            for i in range(1, var_num + 1):
                val = solution.get(i, 0)  # 如果缺失，默认为0（假）
                if val == 1:
                    sf.write(f"{i} ")
                else:
                    sf.write(f"-{i} ")
            sf.write("0\n")
        # ======================================

        # 生成禁止子句
        clause = []
        for i in range(1, var_num + 1):
            val = solution.get(i, 0)
            if val == 1:
                clause.append(-i)
            else:
                clause.append(i)
        extra_clauses.append(clause)

        if max_solutions != -1 and solution_count >= max_solutions:
            print(f"Reached max solutions limit ({max_solutions}). Stopping.")
            break
    else:
        break

if found_any:
    DifferentialProbabilityBound[totalround] = prob
    print(f"Found {solution_count} solutions for round {totalround} with probability {prob}.")
else:
    print(f"No solution found for round {totalround} with probability {prob}.")

TotalTimeEnd = time.time()
print("Total Runtime: " + str(TotalTimeEnd - TotalTimeStart))

# 将结果写入文件
with open("RunTimeSummarise.out", "a") as f:
    f.write(f"Round: {totalround}; Probability: {prob}; Solutions found: {solution_count}; Runtime: {TotalTimeEnd - TotalTimeStart}\n")

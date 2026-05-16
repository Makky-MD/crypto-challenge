import os
import time
import random

FullRound = 2

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

# 统计每轮中F函数的CNF子句数量
def CountClausesInRoundFunction(Round, Probability, clause_num):
    count = clause_num
    # Nonzero input
    count += 1
    # Cluases for Round function
    for r in range(Round):
        for block in range(8):
            count += NumOfConstraint[block]
        # for i in range(32):
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


# 两个相等的CNF子句
def Genequal(a, b, fout):
    clauseseq = "-" + str(a + 1) + " " + str(b + 1) + " 0\n"
    fout.write(clauseseq)
    clauseseq = "-" + str(a + 1) + " " + str(a + 1) + " 0\n"
    fout.write(clauseseq)

# 3异或的CNF子句
def Gen3or(a, b, c, d, fout):
    clauseseq = str(a + 1) + " " + str(b + 1) + " " + str(c + 1) + " " + "-" + str(d + 1) + " 0\n"
    fout.write(clauseseq)
    clauseseq = str(a + 1) + " " + str(b + 1) + " " + "-" + str(c + 1) + " " + str(d + 1) + " 0\n"
    fout.write(clauseseq)
    clauseseq = str(a + 1) + " " + "-" + str(b + 1) + " " + str(c + 1) + " " + str(d + 1) + " 0\n"
    fout.write(clauseseq)
    clauseseq = "-" + str(a + 1) + " " + "-" + str(b + 1) + " " + str(c + 1) + " " + "-" + str(d + 1) + " 0\n"
    fout.write(clauseseq)
    clauseseq = "-" + str(a + 1) + " " + "-" + str(b + 1) + " " + "-" + str(c + 1) + " " + str(d + 1) + " 0\n"
    fout.write(clauseseq)
    clauseseq = "-" + str(a + 1) + " " + "-" + str(b + 1) + " " + str(c + 1) + " " + "-" + str(d + 1) + " 0\n"
    fout.write(clauseseq)
    clauseseq = "-" + str(a + 1) + " " + str(b + 1) + " " + "-" + str(c + 1) + " " + "-" + str(d + 1) + " 0\n"
    fout.write(clauseseq)
    clauseseq = str(a + 1) + " " + "-" + str(b + 1) + " " + "-" + str(c + 1) + " " + "-" + str(d + 1) + " 0\n"
    fout.write(clauseseq)

def Decision(Round, Probability, MatsuiRoundIndex, MatsuiCount, flag):
    TotalSbox = 8 * Round * 2  # CipherFour每轮有4个S盒
    count_var_num = 0
    time_start = time.time()

    # Declare variables - CipherFour是16位分组
    xin = []
    sout = []
    xout = []
    p = []
    q = []
    for i in range(Round):
        xin.append([])
        sout.append([])
        xout.append([])
        p.append([])
        q.append([])
        for j in range(32):
            xin[i].append(0)
        for j in range(32):
            sout[i].append(0)
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

    count_clause_num = Countequal(Round, count_clause_num)
    count_clause_num = Count3xor(Round, count_clause_num)

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

    # 创建CNF文件
    file = open("Problem-Round" + str(Round) + "-Probability" + str(Probability) + ".cnf", "w")
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
                       [[0, 9, 9, 0, 9, 9, 9, 9, 1, 9], [9, 9, 9, 9, 9, 9, 0, 0, 1, 9], [9, 9, 9, 0, 9, 9, 9, 0, 1, 9], [0, 9, 9, 9, 9, 9, 1, 1, 1, 9], [1, 9, 9, 1, 9, 9, 0, 9, 1, 9], [9, 9, 9, 9, 9, 1, 9, 9, 9, 0],
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
                        [9, 1, 9, 0, 1, 1, 9, 0, 9, 9], [0, 9, 9, 1, 9, 9, 0, 1, 0, 9], [9, 9, 9, 0, 1, 9, 0, 0, 9, 9]]]
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

        #  P置换+列混合
    for r in range(Round):
        for j in range(4):
            Genequal(xout[r][j], sout[r][7 * 4 + j], file)
            Genequal(xout[r][2 * 4 + j], sout[r][5 * 4 + j], file)
            Genequal(xout[r][4 * 4 + j], sout[r][3 * 4 + j], file)
            Genequal(xout[r][7 * 4 + j], sout[r][1 * 4 + j], file)


    for r in range(Round):
        for j in range(4):
            Gen3or(sout[r][j], sout[r][5 * 4 + j], sout[r][2 * 4 + j], xout[r][1 * 4 + j], file)
            Gen3or(sout[r][5 * 4 + j], sout[r][2 * 4 + j], sout[r][7 * 4 + j], xout[r][3 * 4 + j], file)
            Gen3or(sout[r][4 * 4 + j], sout[r][1 * 4 + j], sout[r][3 * 4 + j], xout[r][5 * 4 + j], file)
            Gen3or(sout[r][1 * 4 + j], sout[r][6 * 4 + j], sout[r][3 * 4 + j], xout[r][7 * 4 + j], file)


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

    file.close()

    # Call solver cadical
    order = "/root/Desktop/cadical-rel-2.1.3/build/cadical " + "Problem-Round" + str(Round) + "-Probability" + str(Probability) + ".cnf > Round" + str(Round) + "-Probability" + str(Probability) + "-solution.out"
    os.system(order)
    # Extracting results
    order = "sed -n '/s SATISFIABLE/p' Round" + str(Round) + "-Probability" + str(Probability) + "-solution.out > SatSolution.out"
    os.system(order)
    order = "sed -n '/s UNSATISFIABLE/p' Round" + str(Round) + "-Probability" + str(Probability) + "-solution.out > UnsatSolution.out"
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
    order = "rm Problem-Round" + str(Round) + "-Probability" + str(Probability) + ".cnf"
    os.system(order)
    time_end = time.time()
    # Printing solutions
    if (flag == True):
        print("Round:" + str(Round) + "; Probability: " + str(Probability) + "; Sat; TotalCost: " + str(time_end - time_start))
    else:
        print("Round:" + str(Round) + "; Probability: " + str(Probability) + "; Unsat; TotalCost: " + str(time_end - time_start))
    return flag

# main function
CountSbox = InitialLowerBound
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
    while (flag == False):
        flag = Decision(totalround, CountSbox, MatsuiRoundIndex, MatsuiCount, flag)
        CountSbox += 1
    DifferentialProbabilityBound[totalround] = CountSbox - 1
    time_end = time.time()
    file = open("RunTimeSummarise.out", "a")
    resultseq = "Round: " + str(totalround) + "; Differential Probability: " + str(DifferentialProbabilityBound[totalround]) + "; Runtime: " + str(time_end - time_start) + "\n"
    file.write(resultseq)
    file.close()
print(str(DifferentialProbabilityBound))
TotalTimeEnd = time.time()
print("Total Runtime: " + str(TotalTimeEnd - TotalTimeStart))
file = open("RunTimeSummarise.out", "a")
resultseq = "Total Runtime: " + str(TotalTimeEnd - TotalTimeStart)
file.write(resultseq)





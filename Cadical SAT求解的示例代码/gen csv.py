import csv

Sbox = [0xc, 0x5, 0x6, 0xB, 0x9, 0x0, 0xa, 0xd, 0x3, 0xe, 0xf, 0x8, 0x4, 0x7, 0x1, 0x2]


# 将一个整数转换为4比特二进制字符串
def int_to_bin_str(n):
    return format(n, '04b')


# 计算两个比特串的点积（内积）
def dot_product(a, b):
    # a和b都是4比特整数，计算点积 mod 2
    bin_a = int_to_bin_str(a)
    bin_b = int_to_bin_str(b)
    result = 0
    for i in range(4):
        result ^= (int(bin_a[i]) & int(bin_b[i]))
    return result


# 获取关联矩阵表 (LAT)
def get_linear_table(Sbox):
    n = len(Sbox)  # 16
    lat = [[0 for j in range(n)] for i in range(n)]

    # 遍历所有输入掩码 a 和输出掩码 b
    for a in range(n):  # 输入掩码 (mask_in)
        # print('a', a)
        for b in range(n):  # 输出掩码 (mask_out)
            # print('b', b)
            count = 0
            # 遍历所有输入值 x
            for x in range(n):
                # print('x', x)
                # 计算输入掩码的线性组合: a · x
                input_bias = dot_product(a, x)
                # print('input_bias', input_bias)
                # 计算输出掩码的线性组合: b · S(x)
                # print('Sbox[x]', Sbox[x])
                output_bias = dot_product(b, Sbox[x])
                # print('output_bias', output_bias)
                # 如果相等，计数加1
                if input_bias == output_bias:
                    count += 1
            # print('count', count)
            lat[a][b] = abs(count / n - 0.5)
    return lat

lat = get_linear_table(Sbox)
print(lat)

# # 判断M的值
# def calculate_m(bias, p, q):
#     if bias == 0.5 and p == 0 and q == 0:
#         return 1
#     elif bias == 0.25 and p == 1 and q == 1:
#         return 1
#     elif bias == 0.125 and p == 1 and q == 0:
#         return 1
#     elif bias == 0:
#         return 0
#     return 0

# 判断M的值
def calculate_m(bias, p, q):
    if bias == 0.5 and p == 0 and q == 0:
        return 1
    elif bias == 0.25 and p == 0 and q == 1:
        return 1
    elif bias == 0.125 and p == 1 and q == 1:
        return 1
    elif bias == 0:
        return 0
    return 0



# 保存线性分布表为CSV格式
def save_linear_table_to_csv(lat):
    with open('pq.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)

    # 写表头：x1-x4, y1-y4, bias
        header = ['x1', 'x2', 'x3', 'x4', 'y1', 'y2', 'y3', 'y4', 'p', 'q', 'm']
        writer.writerow(header)

    # 遍历所有w的取值
        for p in range(2):
            for q in range(2):

         # 遍历所有输入掩码 a 和输出掩码 b
                for a in range(len(lat)):
                    for b in range(len(lat[a])):
                # 获取输入掩码的二进制表示
                        input_bin = int_to_bin_str(a)
                        output_bin = int_to_bin_str(b)

                # 获取偏差值
                        bias = lat[a][b]

                # 计算m
                        m = calculate_m(bias, p, q)

                # 按照输入输出差分的比特拆分成x1, x2, x3, x4, y1, y2, y3, y4，并加上w和m
                        row = list(input_bin) + list(output_bin) + list(str(p)) + [str(q)]+ [str(m)]
                        writer.writerow(row)



if __name__ == "__main__":
    lat = get_linear_table(Sbox)
    save_linear_table_to_csv(lat)
    print("\n线性分布表已保存为 pq.csv")


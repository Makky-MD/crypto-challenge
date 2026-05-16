'''
计算CipherFour算法S盒的线性近似表
'''

# CipherFour算法的S盒定义
# Sbox = [0x6,0x4,0xc,0x5,0x0,0x7,0x2,0xe,0x1,0xf,0x3,0xd,0x8,0xa,0x9,0xb]
Sbox = [0xc, 0x6, 0x9, 0x0, 0x1, 0xa, 0x2, 0xb, 0x3, 0x8, 0x5, 0xd, 0x4, 0xe, 0x7, 0xf]


def get_linear_table(Sbox):
    input_all = len(Sbox)
    output_all = len(Sbox)
    linear_table = [[-input_all // 2 for j in range(output_all)] for i in range((input_all))]
    # 遍历S盒的输入掩码
    for alpha in range(input_all):
        # 遍历S盒的输出掩码
        for beta in range(output_all):
            # 遍历S盒的输入
            for x in range(input_all):
                linear_table[beta][alpha] += (1 - bin((x & alpha) ^ (Sbox[x] & beta)).count("1") % 2)
    return linear_table


if __name__ == "__main__":
    linear = get_linear_table(Sbox)
    for i in linear:
        print(i)

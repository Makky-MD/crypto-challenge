import sys
from typing import List

# S盒定义
SBOX = [0xC, 0x6, 0x9, 0x0, 0x1, 0xA, 0x2, 0xB,
        0x3, 0x8, 0x5, 0xD, 0x4, 0xE, 0x7, 0xF]


def round_op(state: List[int]) -> None:
    """
    一轮加密操作（原地修改）
    state: 8个半字节的列表，每个元素0-15
    """
    # S-box替换
    print('明文', state)
    for i in range(8):
        state[i] = SBOX[state[i]]
    print('过S盒后', state)

    # SR (ShiftRows) - 保存临时值
    t0, t1, t2, t3 = state[0], state[5], state[2], state[7]
    t4, t5, t6, t7 = state[4], state[1], state[6], state[3]
    print('置换后', t0, t1, t2, t3, t4, t5, t6, t7)

    # MC (MixColumns) - 线性混合
    state[0] = t0 ^ t2 ^ t3
    state[1] = t0
    state[2] = t1 ^ t2
    state[3] = t0 ^ t2

    state[4] = t4 ^ t6 ^ t7
    state[5] = t4
    state[6] = t5 ^ t6
    state[7] = t4 ^ t6
    print('列混淆后', state)


def encrypt(plaintext: int, rounds: int = 8) -> int:
    """
    对32位明文进行R轮加密

    参数:
        plaintext: 32位明文整数 (0 到 0xFFFFFFFF)
        rounds: 加密轮数，默认8轮

    返回:
        32位密文整数
    """
    # 将32位输入拆分为8个4位半字节
    state = [
        (plaintext >> 28) & 0xF,
        (plaintext >> 24) & 0xF,
        (plaintext >> 20) & 0xF,
        (plaintext >> 16) & 0xF,
        (plaintext >> 12) & 0xF,
        (plaintext >> 8) & 0xF,
        (plaintext >> 4) & 0xF,
        (plaintext >> 0) & 0xF
    ]

    # 应用R轮加密
    for _ in range(rounds):
        round_op(state)

    # 重新打包为32位整数
    res = 0
    res |= state[7]
    res |= state[6] << 4
    res |= state[5] << 8
    res |= state[4] << 12
    res |= state[3] << 16
    res |= state[2] << 20
    res |= state[1] << 24
    res |= state[0] << 28

    return res




if __name__ == "__main__":
    # main()
    # 直接调用示例
    plain = 0x0123a567  # 明文
    cipher = encrypt(plain, rounds=1)  # 8轮加密
    print(f"密文: 0x{cipher:0X}")
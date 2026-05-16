#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
逻辑表达式到CNF约束的转换工具

该脚本将逻辑表达式转换为CNF(合取范式)约束格式，用于SAT求解。
主要用于将S盒的线性逼近条件转换为可被SAT求解器处理的格式。

输入格式:
    逻辑表达式，如：(y1'+y2+y3'+p')(x1+x2'+x3'+p')...
    其中：
    - x1-x4: S盒输入掩码的4位
    - y1-y4: S盒输出掩码的4位
    - p, q: 辅助变量
    - ' 表示取反

输出格式:
    二维列表，每个子列表表示一个子句，其中：
    - 0: 对应变量取原值（正文字）
    - 1: 对应变量取反（负文字）
    - 9: 对应变量不出现（无约束）
"""


def convert_expressions(input_expr):
    """
    将逻辑表达式转换为CNF约束矩阵
    
    参数:
        input_expr: 输入的逻辑表达式字符串，格式如"(a+b'+c)(d'+e+f')..."
    
    返回:
        result_list: 二维列表，每个子列表对应一个子句的约束
                     变量顺序: [x1, x2, x3, x4, y1, y2, y3, y4, p, q]
    """
    # 定义变量顺序：按照S盒输入、输出、辅助变量的顺序排列
    variables = ['x1', 'x2', 'x3', 'x4', 'y1', 'y2', 'y3', 'y4', 'p', 'q']
    
    result_list = []
    
    # 处理输入表达式：去掉首尾括号，按')('分割成多个子句
    if input_expr.startswith('(') and input_expr.endswith(')'):
        expr_strings = input_expr[1:-1].split(')(')
    else:
        expr_strings = [input_expr]
    
    # 处理每个括号内的子句
    for expr in expr_strings:
        # 按'+'分割子句中的各个文字
        terms = expr.split('+')
        var_dict = {}
        
        # 解析每个文字
        for term in terms:
            term = term.strip()  # 去除首尾空格
            
            # 判断是否为取反变量（以'结尾）
            if term.endswith("'"):
                var_name = term[:-1]  # 去掉末尾的'
                value = 1             # 1表示该变量取反（对应CNF中的负文字）
            else:
                var_name = term
                value = 0             # 0表示该变量不取反（对应CNF中的正文字）
            
            var_dict[var_name] = value
        
        # 按照预定义的变量顺序构建结果列表
        res = []
        for var in variables:
            if var in var_dict:
                res.append(var_dict[var])
            else:
                res.append(9)  # 9表示该变量在当前子句中不出现
        
        result_list.append(res)
    
    return result_list


# ==================== 示例用法 ====================
if __name__ == "__main__":
    # 输入的逻辑表达式：表示PRESENT S盒的51个线性逼近条件
    ###换成新的是30个cnf子句，我想检验一下这个个数对不对但是检验不出来
    input_expr = "(x1+x4+p')(y3+y4+p')(x4+y4+p')(x1+y3'+y4'+p')(x1'+x4'+y3+p')(y2'+q)(y3'+q)(x1'+x4+y2+p)(x4'+y1+y4+p)(x1'+y3'+y4'+p)(x3+y2+y4'+p)(y1'+q)(x1+x4+y3+y4+q')(x3+y3+y4'+p)(x1+x3'+y2'+y3'+p)(x1+x2+y1'+y3'+p)(x1+x3+y2'+y4+p)(x4'+y3'+y4+p)(x3'+y2+y3+y4)(x2+x4+y1+y3'+p)(y4'+q)(x1+x2'+x4+y3)(x1'+x3'+y1'+y3+y4)(x2'+y1'+y3+y4'+p)(x1+x2'+x4'+y1+p)(x1'+x4+y4'+p)(x2+x4'+y1+y3+p)(x2'+x4+y1'+y2'+y4)(x1+x4'+y3+y4'+p)(x4+y1'+y3+y4)"
    
    # 转换表达式
    output_list = convert_expressions(input_expr)
    
    # 输出结果
    print("转换后的CNF约束矩阵：")
    print(output_list)
    
    # 输出格式说明
    print("\n格式说明：")
    print("每个子列表表示一个子句，变量顺序为：[x1, x2, x3, x4, y1, y2, y3, y4, p, q]")
    print("0 = 正文字（变量不取反）")
    print("1 = 负文字（变量取反）")
    print("9 = 该变量在子句中不出现")
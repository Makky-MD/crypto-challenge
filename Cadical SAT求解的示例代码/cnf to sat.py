def convert_expressions(input_expr):
    # 定义变量顺序
    variables = ['x1', 'x2', 'x3', 'x4', 'y1', 'y2', 'y3', 'y4', 'p', 'q']

    result_list = []

    # 分割输入表达式为多个括号内的表达式
    # 使用split(')(')分割，并去掉首尾的括号
    if input_expr.startswith('(') and input_expr.endswith(')'):
        expr_strings = input_expr[1:-1].split(')(')
    else:
        expr_strings = [input_expr]

    # 处理每个括号内的表达式
    for expr in expr_strings:
        # 分割表达式中的各项
        terms = expr.split('+')
        var_dict = {}

        # 处理每个项
        for term in terms:
            term = term.strip()
            if term.endswith("'"):
                var_name = term[:-1]
                value = 1
            else:
                var_name = term
                value = 0
            var_dict[var_name] = value

        # 按照变量顺序创建结果列表
        res = []
        for var in variables:
            if var in var_dict:
                res.append(var_dict[var])
            else:
                res.append(9)
        result_list.append(res)

    return result_list


# 您的输入数据
input_expr = "(y1'+y2+y3'+p')(x1+x2'+x3'+p')(x1+y1+y2'+y3'+p')(x1'+x2+x3'+y2+p')(x1'+x2'+x3+y2+p')(x1+y1'+y2'+y3+p')(x2+x3+y1'+y3'+p')(x2'+x3'+y1+y3+p')(y3'+q)(p'+q)(y2'+q)(x1'+x4'+y2'+p)(x1+y1+y2+y3+q')(y1'+q)(x1+x2+x3+y2+q')(x1+x4+y2+y4+p+q')(x3+x4+y2'+y3+p)(x2'+x4+y1+y2+y3)(x3'+x4'+y1+y2+y4+p)(x2+x3'+x4+y2+y3+p)(x3+x4'+y2+y3+y4+p)(x1+x3+y2+y3+y4'+p)(x1'+x2+x3+x4+y2+p)(x4'+y1'+y2+y3'+y4')(x3+y1+y2+y3'+y4'+p)(x1'+y1'+y3+y4'+p)(x1+x4+y1'+y2'+y3'+p)(x2'+x3+y1'+y2'+y3'+p)(x2+x3'+y1+y2'+y3+p)(x2+x4+y1+y2'+p)(x1+x2+y1'+y2'+y4+p)(x3+y1+y2'+y4+p)(x1'+x2'+x4+y3'+y4+p)(x1'+x3'+y1'+y2'+p)(x1'+y1+y3'+y4'+p)(x2'+x4'+y2'+y4'+p)(x1+x2+x3'+x4'+y4'+p)(x2+x3+y1+y3+p')(y4'+q)(x2+y1+y2+y3'+y4'+p)(x1+x2'+x4'+y1+y3'+y4+p)(x1+x3'+x4'+y1'+y3+y4+p)(x1+x2'+x3'+y2'+y4')(x2'+x3'+y2+y3+y4+p)(x2'+x3'+y1'+y3'+y4')(x1'+x2+x3'+y1'+y3'+y4+p)(x2'+x3'+y1'+y3'+p')(x1+x2'+x3'+y2+y4)(x1'+x2'+x3+x4'+y1'+p)(x2+x4'+y1+y2+y4+p)(x1+x3'+x4+y1+y3+p)"
# 转换并输出结果
output_list = convert_expressions(input_expr)
print(output_list)









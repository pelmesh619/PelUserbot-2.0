import re

empty_symbols = ' \t\n'
equal_sign_symbol = '='
new_line_symbol = '\n'
one_line_commentary_symbols = ['/', '#']
multiline_commentary_symbols = [('//', '//')]
special_symbol = '\\'


def parse(file):
    data = {}
    is_new_line = True
    is_line_empty = True
    parsing_variable_name = False
    there_was_equal_sign = False
    parsing_variable_value = False
    variable_name = ''
    variable_value = ''

    is_one_line_commentary = False
    is_multiline_commentary = False
    line = ''

    for symb in file:
        line += symb

        if any([line.endswith(i) and not line.endswith(special_symbol + i) for i in one_line_commentary_symbols]):
            variable_value += symb
            for i in one_line_commentary_symbols:
                if variable_value.endswith(i):
                    variable_value = variable_value[:-len(i)]
                    variable_value = variable_value.rstrip(empty_symbols)
                    break
            is_one_line_commentary = True
        if any([line.endswith(i[0]) and not line.endswith(special_symbol + i[1]) for i in
                multiline_commentary_symbols]):
            is_multiline_commentary = True
            variable_value += symb
            for i in one_line_commentary_symbols:
                if variable_value.endswith(i):
                    variable_value = variable_value[:-len(i)]
                    variable_value = variable_value.rstrip(empty_symbols)
                    break
        if any([line.endswith(i[1]) and not line.endswith(special_symbol + i[1]) for i in
                multiline_commentary_symbols]):
            is_multiline_commentary = False
            is_line_empty = True

        if all([not line.endswith(i) or line.endswith(special_symbol+i) for i in empty_symbols]) \
                and not (is_one_line_commentary or is_multiline_commentary):
            if is_line_empty:
                parsing_variable_name = True
                variable_name = ''
                is_line_empty = False

            if parsing_variable_name:
                variable_name += symb

            if symb == equal_sign_symbol and not line.endswith(special_symbol + symb):
                if not variable_name:
                    raise SyntaxError('Variable does not have a name')

                there_was_equal_sign = True
                continue

            if there_was_equal_sign:
                parsing_variable_value = True
                there_was_equal_sign = False
                variable_value = ''

            if parsing_variable_value:
                variable_value += symb

        elif not (is_one_line_commentary or is_multiline_commentary):
            if is_new_line:
                is_line_empty = True
            elif parsing_variable_name:
                parsing_variable_name = False
            elif parsing_variable_value and symb != new_line_symbol:
                variable_value += symb

        is_new_line = symb == new_line_symbol
        if is_new_line:
            if variable_value and variable_name:
                if variable_value.isdigit():
                    data[variable_name] = int(variable_value)
                elif re.fullmatch(r'\d*\.\d+', variable_value):
                    data[variable_name] = float(variable_value)
                else:
                    data[variable_name] = variable_value
                variable_name = ''
                variable_value = ''
                parsing_variable_value = False
            elif variable_name:
                raise SyntaxError('Variable *{}* does not have a value: {}'.format(variable_name, line))

            line = ''
            is_line_empty = True
            if is_one_line_commentary:
                is_one_line_commentary = False

    return data


if __name__ == '__main__':
    config = """
id1 = 13.323 \\/float
id2 = .43 \t  \\/another float
id21 = .433 \t  /\\yet another float
id3 = '34' #fuck
id4 = 3242 \\#double fuck
id22 = gh u
    \tEHIFOI =    'DKLF ;EJLDFJ \\=DFJK/FOJD //DJ
fuck = \\  fdjsk


    """
    print(*[f'{repr(k)}: {repr(v)}' for k, v in parse(config).items()], sep='\n')

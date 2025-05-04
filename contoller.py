import math

def generate_veriloga(row_ad_bits, col_ad_bits, bit_ad_bits):
    # Calculate the condition
    required_value = 3 * (1 + row_ad_bits + col_ad_bits + bit_ad_bits)
    max_value = 2 ** (col_ad_bits + bit_ad_bits)
    
    # Check the condition and find the nearest valid value
    if required_value > max_value:
        raise ValueError(f"Condition 3(1 + row_ad_bits + col_ad_bits + bit_ad_bits) <= 2^(col_ad_bits + bit_ad_bits) is not satisfied for row_ad_bits={row_ad_bits}, col_ad_bits={col_ad_bits}, bit_ad_bits={bit_ad_bits}")
    
    # Find the nearest integer greater than or equal to the required value, divisible by 2^(bit_ad_bits)
    instruction_length = math.ceil(required_value / (2 ** bit_ad_bits))

    addressses = [f'address_{i}' for i in range(row_ad_bits + col_ad_bits)]
    data_ins = [f'data_in_{i}' for i in range(2 ** bit_ad_bits)]
    crossbar_datas = [f'crossbar_data_{i}' for i in range(2 ** bit_ad_bits)]
    row_ads = [f'row_ad_{i}' for i in range(row_ad_bits)]
    col_ads = [f'col_ad_{i}' for i in range(col_ad_bits)]
    write_datas = [f'write_data_{i}' for i in range(2 ** bit_ad_bits)]
    bit_ads = [f'bit_ad_{i}' for i in range(bit_ad_bits)]
    data_outs = [f'data_out_{i}' for i in range(2 ** bit_ad_bits)]
    instructions = [f'instruction_{i}' for i in range(instruction_length * (2 ** bit_ad_bits))]

    # Generate the Verilog-A code
    veriloga_code = f"""`include "disciplines.vams"

module controller (
\tinput electrical en,
\tinput electrical plim,
\tinput electrical idle,"""

    # Inputs
    for a in addressses:
        veriloga_code += f"\n\tinput electrical {a},"
    veriloga_code += "\n\tinput electrical wr,"
    for d in data_ins:
        veriloga_code += f"\n\tinput electrical {d},"
    for c in crossbar_datas:
        veriloga_code += f"\n\tinput electrical {c},"

    # Outputs
    for r in row_ads:
        veriloga_code += f"\n\toutput electrical {r},"
    for c in col_ads:
        veriloga_code += f"\n\toutput electrical {c},"
    veriloga_code += """
\toutput electrical row_idle,
\toutput electrical col_idle,
\toutput electrical write_read,
\toutput electrical bit_or_word,"""
    for w in write_datas:
        veriloga_code += f"\n\toutput electrical {w},"
    for b in bit_ads:
        veriloga_code += f"\n\toutput electrical {b},"
    veriloga_code += """
\toutput electrical maj,
\toutput electrical majp,
\toutput electrical majn,"""
    for d in data_outs:
        veriloga_code += f"\n\toutput electrical {d},"
    veriloga_code += "\n\toutput electrical instr_exec_status\n);\n"

    # Parameters
    veriloga_code += f"""
\tparameter integer row_ad_bits = {row_ad_bits};
\tparameter integer col_ad_bits = {col_ad_bits};
\tparameter integer bit_ad_bits = {bit_ad_bits};
\tparameter integer instruction_length = {instruction_length};

\tinteger state = 0;
\tinteger read_write_state = 0;
\treal v_en_prev;
\tinteger no_of_words_fetched = 0;
\tinteger internal_state = 0;
\tinteger col_ad = 0;
\treal a_reg;
\treal b_reg;
\treal c_reg;
"""

    # Internal state signals
    for sig_group in [row_ads, col_ads, write_datas, bit_ads, data_outs, instructions]:
        for sig in sig_group:
            veriloga_code += f"\treal v_{sig};\n"
    veriloga_code += "\treal v_row_idle, v_col_idle, v_write_read, v_bit_or_word;\n"
    veriloga_code += "\treal v_maj, v_majp, v_majn, v_instr_exec_status;\n\n"

    # Analog process block
    veriloga_code += "analog begin\n"
    veriloga_code += "\t@(initial_step) begin\n"
    veriloga_code += "\t\tv_en_prev = V(en);\n"
    veriloga_code += "\t\tv_row_idle = 1.0;\n"
    veriloga_code += "\t\tv_col_idle = 1.0;\n"
    veriloga_code += "\t\tv_instr_exec_status = 0.0;\n"
    veriloga_code += "\tend\n\n"
    for s in reversed(addressses[0:col_ad_bits]):
        veriloga_code += f"\tcol_ad = col_ad *2 + (V({s}) > 0.5 ? 1 : 0);\n"
    
    veriloga_code += "\tif(V(idle) > 0.5) begin\n"
    veriloga_code += "\t\tv_row_idle = 1.0;\n"
    veriloga_code += "\t\tv_col_idle = 1.0;\n"
    veriloga_code += "\t\tif(V(plim) < 0.5 && v_instr_exec_status > 0.5) begin\n"
    veriloga_code += "\t\t\tv_instr_exec_status = 0;\n"
    veriloga_code += "\t\t\tstate = 0;\n"
    veriloga_code += "\t\t\tinternal_state = 0;\n"
    veriloga_code += "\t\t\tno_of_words_fetched = 0;\n"
    veriloga_code += "\t\tend\n"
    veriloga_code += "\tend\n"


    veriloga_code += "\telse if (V(en) > 0.5 && v_en_prev < 0.5) begin\n"
    veriloga_code += "\t\tif ((V(plim) > 0.5 || state != 0 || internal_state != 0 || no_of_words_fetched > 0) && v_instr_exec_status < 0.5 && read_write_state == 0) begin\n"
    veriloga_code += "\t\t\t$display(\"In plim\", state, internal_state);\n"
    veriloga_code += "\t\t\tcase (state)\n"
    veriloga_code += "\t\t\t\t0: begin\n"
    for i, r in enumerate(row_ads):
        veriloga_code += f"\t\t\t\t\tv_{r} = V({addressses[col_ad_bits + i]});\n"
    veriloga_code += "\t\t\t\t\tv_row_idle = 0.0;\n"
    veriloga_code += "\t\t\t\t\tcase (no_of_words_fetched)\n"
    for i in range(instruction_length):
        veriloga_code += f"\t\t\t\t\t\t{i}: begin\n"
        veriloga_code += f"\t\t\t\t\t\t\tcase (internal_state)\n"
        veriloga_code += f"\t\t\t\t\t\t\t\t0: begin\n"
        for j, c in enumerate(col_ads):
            veriloga_code += f"\t\t\t\t\t\t\t\t\tv_{c} = ((col_ad + {i})/{2**j})%2;\n"
        veriloga_code += "\t\t\t\t\t\t\t\t\tv_col_idle = 0.0;\n"
        veriloga_code += "\t\t\t\t\t\t\t\t\tv_write_read = 0.0;\n"
        veriloga_code += "\t\t\t\t\t\t\t\t\tv_maj = 0.0;\n"
        veriloga_code += "\t\t\t\t\t\t\t\t\tv_bit_or_word = 0.0;\n"
        veriloga_code += "\t\t\t\t\t\t\t\t\tinternal_state = 1;\n"
        veriloga_code += f"\t\t\t\t\t\t\t\tend\n"
        veriloga_code += f"\t\t\t\t\t\t\t\t1: begin\n"
        for j, c in enumerate(crossbar_datas):
            veriloga_code += f"\t\t\t\t\t\t\t\t\tv_instruction_{i*2**bit_ad_bits + j} = V({c});\n"
        veriloga_code += "\t\t\t\t\t\t\t\t\tv_col_idle = 1.0;\n"
        veriloga_code += "\t\t\t\t\t\t\t\t\tinternal_state = 0;\n"
        veriloga_code += "\t\t\t\t\t\t\t\t\tno_of_words_fetched = no_of_words_fetched + 1;\n"
        if i == instruction_length - 1:
            veriloga_code += "\t\t\t\t\t\t\t\t\tstate = 1;\n"
            veriloga_code += "\t\t\t\t\t\t\t\t\tno_of_words_fetched = 0;\n"
        veriloga_code += f"\t\t\t\t\t\t\t\tend\n"
        veriloga_code += f"\t\t\t\t\t\t\tendcase\n"
        veriloga_code += f"\t\t\t\t\t\tend\n"
    veriloga_code += "\t\t\t\t\tendcase\n"
    veriloga_code += "\t\t\t\tend\n"
    veriloga_code += "\t\t\t\t\t1: begin\n"
    veriloga_code += "\t\t\t\t\t\t\tcase (internal_state)\n"
    veriloga_code += "\t\t\t\t\t\t\t\t0: begin\n"
    for i, c in enumerate(reversed(row_ads)):
        veriloga_code += f"\t\t\t\t\t\t\t\t\tv_{c} = v_instruction_{i+3+row_ad_bits+col_ad_bits+bit_ad_bits};\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_row_idle = 0.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_col_idle = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_write_read = 0.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_bit_or_word = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_maj = 0.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tinternal_state = 1;\n"
    veriloga_code += "\t\t\t\t\t\t\t\tend\n"
    veriloga_code += "\t\t\t\t\t\t\t\t1: begin\n"
    for i,c in enumerate(reversed(col_ads)):
        veriloga_code += f"\t\t\t\t\t\t\t\t\tv_{c} = v_instruction_{i+3+row_ad_bits+col_ad_bits+bit_ad_bits+row_ad_bits};\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_col_idle = 0.0;\n"
    for i,b in enumerate(reversed(bit_ads)):
        veriloga_code += f"\t\t\t\t\t\t\t\t\tv_{b} = v_instruction_{i+3+row_ad_bits+col_ad_bits+bit_ad_bits+col_ad_bits+row_ad_bits};\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_write_read = 0.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_bit_or_word = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tinternal_state = 2;\n"
    veriloga_code += "\t\t\t\t\t\t\t\tend\n"
    veriloga_code += "\t\t\t\t\t\t\t\t2: begin\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tb_reg = V(crossbar_data_0);\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_row_idle = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_col_idle = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tinternal_state = 3;\n"
    veriloga_code += "\t\t\t\t\t\t\t\tend\n"
    veriloga_code += "\t\t\t\t\t\t\t\t3: begin\n"
    for i, c in enumerate(reversed(row_ads)):
        veriloga_code += f"\t\t\t\t\t\t\t\t\tv_{c} = v_instruction_{i+3};\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_row_idle = 0.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_col_idle = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_write_read = 0.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_bit_or_word = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_maj = 0.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tinternal_state = 4;\n"
    veriloga_code += "\t\t\t\t\t\t\t\tend\n"
    veriloga_code += "\t\t\t\t\t\t\t\t4: begin\n"
    for i,c in enumerate(reversed(col_ads)):
        veriloga_code += f"\t\t\t\t\t\t\t\t\tv_{c} = v_instruction_{i+3+row_ad_bits};\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_col_idle = 0.0;\n"
    for i,b in enumerate(reversed(bit_ads)):
        veriloga_code += f"\t\t\t\t\t\t\t\t\tv_{b} = v_instruction_{i+3+col_ad_bits+row_ad_bits};\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_write_read = 0.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_bit_or_word = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tinternal_state = 5;\n"
    veriloga_code += "\t\t\t\t\t\t\t\tend\n"
    veriloga_code += "\t\t\t\t\t\t\t\t5: begin\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\ta_reg = V(crossbar_data_0);\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_row_idle = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_col_idle = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tinternal_state = 6;\n"
    veriloga_code += "\t\t\t\t\t\t\t\tend\n"
    veriloga_code += "\t\t\t\t\t\t\t\t6: begin\n"
    for i, c in enumerate(reversed(row_ads)):
        veriloga_code += f"\t\t\t\t\t\t\t\t\tv_{c} = v_instruction_{i+3+2*(row_ad_bits+col_ad_bits+bit_ad_bits)};\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_row_idle = 0.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_col_idle = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_write_read = 0.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_bit_or_word = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_maj = 0.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tinternal_state = 7;\n"
    veriloga_code += "\t\t\t\t\t\t\t\tend\n"
    veriloga_code += "\t\t\t\t\t\t\t\t7: begin\n"
    for i,c in enumerate(reversed(col_ads)):
        veriloga_code += f"\t\t\t\t\t\t\t\t\tv_{c} = v_instruction_{i+3+2*(row_ad_bits+col_ad_bits+bit_ad_bits)+row_ad_bits};\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_col_idle = 0.0;\n"
    for i,b in enumerate(reversed(bit_ads)):
        veriloga_code += f"\t\t\t\t\t\t\t\t\tv_{b} = v_instruction_{i+3+2*(row_ad_bits+col_ad_bits+bit_ad_bits)+col_ad_bits+row_ad_bits};\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_write_read = 0.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_bit_or_word = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tinternal_state = 8;\n"
    veriloga_code += "\t\t\t\t\t\t\t\tend\n"
    veriloga_code += "\t\t\t\t\t\t\t\t8: begin\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tc_reg = V(crossbar_data_0);\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_row_idle = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_col_idle = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tinternal_state = 0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tstate = 2;\n"
    veriloga_code += "\t\t\t\t\t\t\t\tend\n"
    veriloga_code += "\t\t\t\t\t\t\tendcase\n"
    veriloga_code += "\t\t\t\t\tend\n"
    veriloga_code += "\t\t\t\t\t2: begin\n"
    veriloga_code += "\t\t\t\t\t\tif(v_instruction_0 < 0.5 && v_instruction_1 < 0.5 && v_instruction_2 < 0.5) begin //MAJ(@a,@b,@c)\n"
    veriloga_code += "\t\t\t\t\t\t\tcase (internal_state)\n"
    veriloga_code += "\t\t\t\t\t\t\t\t0: begin\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_col_idle = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_write_read = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_bit_or_word = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_maj = 0.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_row_idle = 0.0;\n"
    for i, c in enumerate(row_ads):
        veriloga_code += f"\t\t\t\t\t\t\t\t\tv_{c} = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tinternal_state = 1;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_write_data_0 = (b_reg > 0.5 ? 1.0 : 0.0);\n"
    veriloga_code += "\t\t\t\t\t\t\t\tend\n"
    veriloga_code += "\t\t\t\t\t\t\t\t1: begin\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_col_idle = 0.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_write_read = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_bit_or_word = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_maj = 0.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_row_idle = 0.0;\n"
    for i, c in enumerate(col_ads):
        veriloga_code += f"\t\t\t\t\t\t\t\t\tv_{c} = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tinternal_state = 2;\n"
    for i, b in enumerate(bit_ads):
        veriloga_code += f"\t\t\t\t\t\t\t\t\tv_{b} = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\tend\n"
    veriloga_code += "\t\t\t\t\t\t\t\t2: begin\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_write_read = 0.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_maj = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_majp = (a_reg > 0.5 ? 1.0 : 0.0);\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_majn = (c_reg < 0.5 ? 1.0 : 0.0);\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\t$display(\"MAJ\", a_reg, b_reg, c_reg);\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tinternal_state = 3;\n"
    veriloga_code += "\t\t\t\t\t\t\t\tend\n"
    veriloga_code += "\t\t\t\t\t\t\t\t3: begin\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_bit_or_word = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_maj = 0.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tinternal_state = 4;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_col_idle = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\tend\n"
    veriloga_code += "\t\t\t\t\t\t\t\t4: begin\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_row_idle = 0.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_col_idle = 0.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tinternal_state = 5;\n"
    veriloga_code += "\t\t\t\t\t\t\t\tend\n"
    veriloga_code += "\t\t\t\t\t\t\t\t5: begin\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_write_read = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_maj = 0.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_bit_or_word = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_write_data_0 = (V(crossbar_data_0) > 0.5 ? 1.0 : 0.0);\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\t$display(\"OUTPUT\", v_write_data_0);\n"
    for i,c in enumerate(reversed(row_ads)):
        veriloga_code += f"\t\t\t\t\t\t\t\t\tv_{c} = v_instruction_{i+3+2*(row_ad_bits+col_ad_bits+bit_ad_bits)};\n"
    for i,c in enumerate(reversed(col_ads)):
        veriloga_code += f"\t\t\t\t\t\t\t\t\tv_{c} = v_instruction_{i+3+2*(row_ad_bits+col_ad_bits+bit_ad_bits)+row_ad_bits};\n"
    for i,b in enumerate(reversed(bit_ads)):
        veriloga_code += f"\t\t\t\t\t\t\t\t\tv_{b} = v_instruction_{i+3+2*(row_ad_bits+col_ad_bits+bit_ad_bits)+col_ad_bits+row_ad_bits};\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tinternal_state = 6;\n"
    veriloga_code += "\t\t\t\t\t\t\t\tend\n"
    veriloga_code += "\t\t\t\t\t\t\t\t6: begin\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_row_idle = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_col_idle = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tinternal_state = 0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tstate = 3;\n"
    veriloga_code += "\t\t\t\t\t\t\t\tend\n"
    veriloga_code += "\t\t\t\t\t\t\tendcase\n"
    veriloga_code += "\t\t\t\t\t\tend\n"
    veriloga_code += "\t\t\t\t\t\tif(v_instruction_0 < 0.5 && v_instruction_1 < 0.5 && v_instruction_2 > 0.5) begin //AND(@a,@b,@c) AND(a,b) stores in c\n"
    veriloga_code += "\t\t\t\t\t\t\tcase (internal_state)\n"
    veriloga_code += "\t\t\t\t\t\t\t\t0: begin\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_col_idle = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_write_read = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_bit_or_word = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_maj = 0.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_row_idle = 0.0;\n"
    for i, c in enumerate(row_ads):
        veriloga_code += f"\t\t\t\t\t\t\t\t\tv_{c} = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tinternal_state = 1;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_write_data_0 = 0.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\tend\n"
    veriloga_code += "\t\t\t\t\t\t\t\t1: begin\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_col_idle = 0.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_write_read = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_bit_or_word = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_maj = 0.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_row_idle = 0.0;\n"
    for i, c in enumerate(col_ads):
        veriloga_code += f"\t\t\t\t\t\t\t\t\tv_{c} = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tinternal_state = 2;\n"
    for i, b in enumerate(bit_ads):
        veriloga_code += f"\t\t\t\t\t\t\t\t\tv_{b} = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\tend\n"
    veriloga_code += "\t\t\t\t\t\t\t\t2: begin\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_write_read = 0.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_maj = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_majp = (a_reg > 0.5 ? 1.0 : 0.0);\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_majn = (b_reg < 0.5 ? 1.0 : 0.0);\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\t$display(\"AND\", a_reg, b_reg);\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tinternal_state = 3;\n"
    veriloga_code += "\t\t\t\t\t\t\t\tend\n"
    veriloga_code += "\t\t\t\t\t\t\t\t3: begin\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_bit_or_word = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_maj = 0.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tinternal_state = 4;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_col_idle = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\tend\n"
    veriloga_code += "\t\t\t\t\t\t\t\t4: begin\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_row_idle = 0.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_col_idle = 0.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tinternal_state = 5;\n"
    veriloga_code += "\t\t\t\t\t\t\t\tend\n"
    veriloga_code += "\t\t\t\t\t\t\t\t5: begin\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_write_read = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_maj = 0.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_bit_or_word = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_write_data_0 = (V(crossbar_data_0) > 0.5 ? 1.0 : 0.0);\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\t$display(\"OUTPUT\", v_write_data_0);\n"
    for i,c in enumerate(reversed(row_ads)):
        veriloga_code += f"\t\t\t\t\t\t\t\t\tv_{c} = v_instruction_{i+3+2*(row_ad_bits+col_ad_bits+bit_ad_bits)};\n"
    for i,c in enumerate(reversed(col_ads)):
        veriloga_code += f"\t\t\t\t\t\t\t\t\tv_{c} = v_instruction_{i+3+2*(row_ad_bits+col_ad_bits+bit_ad_bits)+row_ad_bits};\n"
    for i,b in enumerate(reversed(bit_ads)):
        veriloga_code += f"\t\t\t\t\t\t\t\t\tv_{b} = v_instruction_{i+3+2*(row_ad_bits+col_ad_bits+bit_ad_bits)+col_ad_bits+row_ad_bits};\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tinternal_state = 6;\n"
    veriloga_code += "\t\t\t\t\t\t\t\tend\n"
    veriloga_code += "\t\t\t\t\t\t\t\t6: begin\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_row_idle = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_col_idle = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tinternal_state = 0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tstate = 3;\n"
    veriloga_code += "\t\t\t\t\t\t\t\tend\n"
    veriloga_code += "\t\t\t\t\t\t\tendcase\n"
    veriloga_code += "\t\t\t\t\t\tend\n"
    veriloga_code += "\t\t\t\t\t\tif(v_instruction_0 < 0.5 && v_instruction_1 > 0.5 && v_instruction_2 < 0.5) begin //OR(@a,@b,@c) OR(a,b) stores in c\n"
    veriloga_code += "\t\t\t\t\t\t\tcase (internal_state)\n"
    veriloga_code += "\t\t\t\t\t\t\t\t0: begin\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_col_idle = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_write_read = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_bit_or_word = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_maj = 0.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_row_idle = 0.0;\n"
    for i, c in enumerate(row_ads):
        veriloga_code += f"\t\t\t\t\t\t\t\t\tv_{c} = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tinternal_state = 1;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_write_data_0 = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\tend\n"
    veriloga_code += "\t\t\t\t\t\t\t\t1: begin\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_col_idle = 0.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_write_read = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_bit_or_word = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_maj = 0.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_row_idle = 0.0;\n"
    for i, c in enumerate(col_ads):
        veriloga_code += f"\t\t\t\t\t\t\t\t\tv_{c} = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tinternal_state = 2;\n"
    for i, b in enumerate(bit_ads):
        veriloga_code += f"\t\t\t\t\t\t\t\t\tv_{b} = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\tend\n"
    veriloga_code += "\t\t\t\t\t\t\t\t2: begin\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_write_read = 0.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_maj = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_majp = (a_reg > 0.5 ? 1.0 : 0.0);\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_majn = (b_reg < 0.5 ? 1.0 : 0.0);\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\t$display(\"OR\", a_reg, b_reg);\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tinternal_state = 3;\n"
    veriloga_code += "\t\t\t\t\t\t\t\tend\n"
    veriloga_code += "\t\t\t\t\t\t\t\t3: begin\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_bit_or_word = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_maj = 0.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tinternal_state = 4;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_col_idle = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\tend\n"
    veriloga_code += "\t\t\t\t\t\t\t\t4: begin\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_row_idle = 0.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_col_idle = 0.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tinternal_state = 5;\n"
    veriloga_code += "\t\t\t\t\t\t\t\tend\n"
    veriloga_code += "\t\t\t\t\t\t\t\t5: begin\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_write_read = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_maj = 0.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_bit_or_word = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_write_data_0 = (V(crossbar_data_0) > 0.5 ? 1.0 : 0.0);\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\t$display(\"OUTPUT\", v_write_data_0);\n"
    for i,c in enumerate(reversed(row_ads)):
        veriloga_code += f"\t\t\t\t\t\t\t\t\tv_{c} = v_instruction_{i+3+2*(row_ad_bits+col_ad_bits+bit_ad_bits)};\n"
    for i,c in enumerate(reversed(col_ads)):
        veriloga_code += f"\t\t\t\t\t\t\t\t\tv_{c} = v_instruction_{i+3+2*(row_ad_bits+col_ad_bits+bit_ad_bits)+row_ad_bits};\n"
    for i,b in enumerate(reversed(bit_ads)):
        veriloga_code += f"\t\t\t\t\t\t\t\t\tv_{b} = v_instruction_{i+3+2*(row_ad_bits+col_ad_bits+bit_ad_bits)+col_ad_bits+row_ad_bits};\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tinternal_state = 6;\n"
    veriloga_code += "\t\t\t\t\t\t\t\tend\n"
    veriloga_code += "\t\t\t\t\t\t\t\t6: begin\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_row_idle = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_col_idle = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tinternal_state = 0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tstate = 3;\n"
    veriloga_code += "\t\t\t\t\t\t\t\tend\n"
    veriloga_code += "\t\t\t\t\t\t\tendcase\n"
    veriloga_code += "\t\t\t\t\t\tend\n"
    veriloga_code += "\t\t\t\t\t\tif(v_instruction_0 < 0.5 && v_instruction_1 > 0.5 && v_instruction_2 > 0.5) begin //NOT(@a,@b,@c) NOT(a) stores in c\n"
    veriloga_code += "\t\t\t\t\t\t\tcase (internal_state)\n"
    veriloga_code += "\t\t\t\t\t\t\t\t0: begin\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_col_idle = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_write_read = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_bit_or_word = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_maj = 0.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_row_idle = 0.0;\n"
    for i, c in enumerate(row_ads):
        veriloga_code += f"\t\t\t\t\t\t\t\t\tv_{c} = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tinternal_state = 1;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_write_data_0 = (a_reg > 0.5 ? 1.0 : 0.0);\n"
    veriloga_code += "\t\t\t\t\t\t\t\tend\n"
    veriloga_code += "\t\t\t\t\t\t\t\t1: begin\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_col_idle = 0.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_write_read = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_bit_or_word = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_maj = 0.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_row_idle = 0.0;\n"
    for i, c in enumerate(col_ads):
        veriloga_code += f"\t\t\t\t\t\t\t\t\tv_{c} = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tinternal_state = 2;\n"
    for i, b in enumerate(bit_ads):
        veriloga_code += f"\t\t\t\t\t\t\t\t\tv_{b} = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\tend\n"
    veriloga_code += "\t\t\t\t\t\t\t\t2: begin\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_write_read = 0.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_maj = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_majp = (a_reg < 0.5 ? 1.0 : 0.0);\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_majn = (a_reg > 0.5 ? 1.0 : 0.0);\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\t$display(\"NOT\", a_reg);\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tinternal_state = 3;\n"
    veriloga_code += "\t\t\t\t\t\t\t\tend\n"
    veriloga_code += "\t\t\t\t\t\t\t\t3: begin\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_bit_or_word = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_maj = 0.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tinternal_state = 4;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_col_idle = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\tend\n"
    veriloga_code += "\t\t\t\t\t\t\t\t4: begin\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_row_idle = 0.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_col_idle = 0.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tinternal_state = 5;\n"
    veriloga_code += "\t\t\t\t\t\t\t\tend\n"
    veriloga_code += "\t\t\t\t\t\t\t\t5: begin\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_write_read = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_maj = 0.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_bit_or_word = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_write_data_0 = (V(crossbar_data_0) > 0.5 ? 1.0 : 0.0);\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\t$display(\"OUTPUT\", v_write_data_0);\n"
    for i,c in enumerate(reversed(row_ads)):
        veriloga_code += f"\t\t\t\t\t\t\t\t\tv_{c} = v_instruction_{i+3+2*(row_ad_bits+col_ad_bits+bit_ad_bits)};\n"
    for i,c in enumerate(reversed(col_ads)):
        veriloga_code += f"\t\t\t\t\t\t\t\t\tv_{c} = v_instruction_{i+3+2*(row_ad_bits+col_ad_bits+bit_ad_bits)+row_ad_bits};\n"
    for i,b in enumerate(reversed(bit_ads)):
        veriloga_code += f"\t\t\t\t\t\t\t\t\tv_{b} = v_instruction_{i+3+2*(row_ad_bits+col_ad_bits+bit_ad_bits)+col_ad_bits+row_ad_bits};\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tinternal_state = 6;\n"
    veriloga_code += "\t\t\t\t\t\t\t\tend\n"
    veriloga_code += "\t\t\t\t\t\t\t\t6: begin\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_row_idle = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tv_col_idle = 1.0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tinternal_state = 0;\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\tstate = 3;\n"
    veriloga_code += "\t\t\t\t\t\t\t\tend\n"
    veriloga_code += "\t\t\t\t\t\t\tendcase\n"
    veriloga_code += "\t\t\t\t\t\tend\n"
    veriloga_code += "\t\t\t\t\tend\n"
    veriloga_code += "\t\t\t\t\t3: begin\n"
    veriloga_code += "\t\t\t\t\t\tstate = 0;\n"
    veriloga_code += "\t\t\t\t\t\tinternal_state = 0;\n"
    veriloga_code += "\t\t\t\t\t\tv_instr_exec_status = 1.0;\n"
    veriloga_code += "\t\t\t\t\tend\n"
    veriloga_code += "\t\t\tendcase\n"


    # RAM read/write
    veriloga_code += "\t\tend else if((V(plim) < 0.5 || read_write_state != 0) && state == 0) begin\n"
    veriloga_code += "\t\t\t\t\t\t\t\t\t$display(\"In RAM\", read_write_state);\n"
    veriloga_code += "\t\t\tv_instr_exec_status = 0.0;\n"
    veriloga_code += "\t\t\tcase (read_write_state)\n"
    veriloga_code += "\t\t\t\t0: begin\n"
    for i, r in enumerate(row_ads):
        veriloga_code += f"\t\t\t\t\tv_{r} = V({addressses[col_ad_bits + i]});\n"
    veriloga_code += "\t\t\t\t\tv_row_idle = 0.0;\n"
    veriloga_code += "\t\t\t\t\tread_write_state = 1;\n"
    veriloga_code += "\t\t\t\tend\n"
    veriloga_code += "\t\t\t\t1: begin\n"
    for i, c in enumerate(col_ads):
        veriloga_code += f"\t\t\t\t\tv_{c} = V({addressses[i]});\n"
    veriloga_code += "\t\t\t\t\tv_col_idle = 0.0;\n"
    veriloga_code += "\t\t\t\t\tv_write_read = V(wr);\n"
    veriloga_code += "\t\t\t\t\tv_bit_or_word = 0.0;\n"
    for i,d in enumerate(data_ins):
        veriloga_code += f"\t\t\t\t\tv_write_data_{i} = V({d});\n"
    for b in bit_ads:
        veriloga_code += f"\t\t\t\t\tv_{b} = 0.0;\n"
    veriloga_code += "\t\t\t\t\tv_maj = 0.0;\n\t\t\t\t\tv_majp = 0.0;\n\t\t\t\t\tv_majn = 0.0;\n"
    veriloga_code += "\t\t\t\t\tread_write_state = 2;\n"
    veriloga_code += "\t\t\t\tend\n"
    veriloga_code += "\t\t\t\t2: begin\n"
    veriloga_code += "\t\t\t\t\tif (V(wr) < 0.5) begin\n"
    for i, c in enumerate(crossbar_datas):
        veriloga_code += f"\t\t\t\t\t\tv_{data_outs[i]} = V({c});\n"
    veriloga_code += "\t\t\t\t\tend else begin\n"
    for d in data_outs:
        veriloga_code += f"\t\t\t\t\t\tv_{d} = 0.0;\n"
    veriloga_code += "\t\t\t\t\tend\n"
    veriloga_code += "\t\t\t\t\tv_row_idle = 1.0;\n"
    veriloga_code += "\t\t\t\t\tv_col_idle = 1.0;\n"
    veriloga_code += "\t\t\t\t\tread_write_state = 0;\n"
    veriloga_code += "\t\t\t\tend\n"
    veriloga_code += "\t\t\tendcase\n"
    veriloga_code += "\t\tend\n\tend\n"

    # Continuous assignments
    for sig in row_ads + col_ads + write_datas + bit_ads + data_outs:
        veriloga_code += f"\tV({sig}) <+ v_{sig};\n"
    veriloga_code += "\tV(row_idle) <+ v_row_idle;\n"
    veriloga_code += "\tV(col_idle) <+ v_col_idle;\n"
    veriloga_code += "\tV(write_read) <+ v_write_read;\n"
    veriloga_code += "\tV(bit_or_word) <+ v_bit_or_word;\n"
    veriloga_code += "\tV(maj) <+ v_maj;\n"
    veriloga_code += "\tV(majp) <+ v_majp;\n"
    veriloga_code += "\tV(majn) <+ v_majn;\n"
    veriloga_code += "\tV(instr_exec_status) <+ v_instr_exec_status;\n"
    veriloga_code += "\tv_en_prev = V(en);\nend\nendmodule"

    return veriloga_code


# Example
code = generate_veriloga(2, 4, 1)

# write the code to a file
with open("controller_full.va", "w") as f:
    f.write(code)


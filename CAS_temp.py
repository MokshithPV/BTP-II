def generate_cas_module(no_bits_in_column_address=2, no_of_bits_in_bit_address_in_word=2,
                        v_read=0.9, v_write=1.8):
    from itertools import product

    num_words = 2 ** no_bits_in_column_address
    num_bits_per_word = 2 ** no_of_bits_in_bit_address_in_word

    inputs = ["wr", "bit_or_word", "maj", "majp", "majn", "idle"]
    ca_ports = [f"ca{i}" for i in range(no_bits_in_column_address)]
    ba_ports = [f"ba{i}" for i in range(no_of_bits_in_bit_address_in_word)]
    wb_ports = [f"wb{i}" for i in range(num_bits_per_word)]

    inputs += ca_ports + ba_ports + wb_ports

    inouts = []
    for word, bit in product(range(num_words), range(num_bits_per_word)):
        inouts.append(f"vc{word}b{bit}p")
        inouts.append(f"vc{word}b{bit}n")
    
    outputs = [f"outb{i}" for i in range(num_bits_per_word)]

    ports = inputs + inouts + outputs

    header = f"""// Auto-generated Verilog-A CAS module with decoding logic

`include "constants.vams"
`include "disciplines.vams"

module CAS({', '.join(ports)});
\tparameter integer no_bits_in_column_address = {no_bits_in_column_address};
\tparameter integer no_of_bits_in_bit_address_in_word = {no_of_bits_in_bit_address_in_word};
\tparameter real v_read = {v_read};
\tparameter real v_write = {v_write};
"""

    io_decls = ""
    io_decls += "\n".join(f"\tinput {port};" for port in inputs) + "\n"
    io_decls += "\tinout " + ", ".join(inouts) + ";\n"
    io_decls += "\toutput " + ", ".join(outputs) + ";\n"
    io_decls += "\telectrical " + ", ".join(ports) + ";\n"

    logic = "\n\tinteger ca_decoded;\n"
    logic += "\tinteger ba_decoded;\n"
    for i in inouts:
        logic += f"\treal v_{i};\n"
    for i in outputs:
        logic += f"\treal v_{i};\n"
    logic += "\n\tanalog begin\n"

    # Decoding logic
    logic += "\t\tca_decoded = 0;\n"
    for i, ca in enumerate(ca_ports):
        logic += f"\t\tca_decoded = ca_decoded + (V({ca}) > 0.5 ? (1 << {i}) : 0);\n"
    logic += "\t\tba_decoded = 0;\n"
    for i, ba in enumerate(ba_ports):
        logic += f"\t\tba_decoded = ba_decoded + (V({ba}) > 0.5 ? (1 << {i}) : 0);\n"


    # Idle state
    logic += "\n\t\tif (V(idle) > 0.5) begin\n"
    for word in range(num_words):
        for bit in range(num_bits_per_word):
            logic += f"\t\t\tv_vc{word}b{bit}p = v_read;\n"
            logic += f"\t\t\tv_vc{word}b{bit}n = 0.0;\n"
    logic += "\t\tend\n"

    # Majority Logic
    logic += "\t\telse if (V(maj) > 0.5) begin\n"
    logic += f"\t\t\tif (ca_decoded < {num_words} && ba_decoded < {num_bits_per_word}) begin\n"
    logic += f"\t\t\t\tcase (ca_decoded)\n"
    for word in range(num_words):
        logic += f"\t\t\t\t\t{word}: begin\n"
        logic += f"\t\t\t\t\t\tcase (ba_decoded)\n"
        for bit in range(num_bits_per_word):
            logic += f"\t\t\t\t\t\t\t{bit}: begin\n"
            logic += f"\t\t\t\t\t\t\t\tv_vc{word}b{bit}p = (V(majp) > 0.5 ? v_write : 0.0);\n"
            logic += f"\t\t\t\t\t\t\t\tv_vc{word}b{bit}n = (V(majn) > 0.5 ? v_write : 0.0);\n"
            logic += f"\t\t\t\t\t\t\tend\n"
        logic += f"\t\t\t\t\t\tendcase\n"
        logic += f"\t\t\t\t\tend\n"
    logic += f"\t\t\t\tendcase\n"
    logic += "\t\t\tend\n"
    logic += "\t\tend\n"

    # Write Logic
    logic += "\t\telse if (V(wr) > 0.5) begin\n"
    logic += f"\t\t\tif (ca_decoded < {num_words} && ba_decoded < {num_bits_per_word}) begin\n"
    logic += f"\t\t\t\tif(V(bit_or_word)>0.5) begin\n"
    logic += f"\t\t\t\t\tcase (ca_decoded)\n"
    for word in range(num_words):
        logic += f"\t\t\t\t\t\t{word}: begin\n"
        logic += f"\t\t\t\t\t\t\tcase (ba_decoded)\n"
        for bit in range(num_bits_per_word):
            logic += f"\t\t\t\t\t\t\t\t{bit}: begin\n"
            logic += f"\t\t\t\t\t\t\t\t\tv_vc{word}b{bit}p = (V(wb0) > 0.5 ? v_write : 0.0);\n"
            logic += f"\t\t\t\t\t\t\t\t\tv_vc{word}b{bit}n = (V(wb0) > 0.5 ? 0.0 : v_write);\n"
            logic += f"\t\t\t\t\t\t\t\tend\n"
        logic += f"\t\t\t\t\t\t\tendcase\n"
        logic += f"\t\t\t\t\t\tend\n"
    logic += f"\t\t\t\t\tendcase\n"
    logic += "\t\t\t\tend\n"
    logic += "\t\t\t\telse begin\n"
    logic += "\t\t\t\t\tcase (ca_decoded)\n"
    for word in range(num_words):
        logic += f"\t\t\t\t\t\t{word}: begin\n"
        for bit in range(num_bits_per_word):
            logic += f"\t\t\t\t\t\t\tv_vc{word}b{bit}p = (V(wb{bit}) > 0.5 ? v_write : 0.0);\n"
            logic += f"\t\t\t\t\t\t\tv_vc{word}b{bit}n = (V(wb{bit}) > 0.5 ? 0.0 : v_write);\n"
        logic += f"\t\t\t\t\t\tend\n"
    logic += "\t\t\t\tendcase\n"
    logic += "\t\t\t\tend\n"
    logic += "\t\t\tend\n"
    logic += "\t\tend\n"

    # Read logic
    logic += "\t\telse begin"
    logic += f"\n\t\t\tif (ca_decoded < {num_words} && ba_decoded < {num_bits_per_word}) begin"
    logic += f"\n\t\t\t\tif (V(bit_or_word)>0.5) begin"
    logic += "\n\t\t\t\t\tcase (ca_decoded)"
    for word in range(num_words):
        logic += f"\n\t\t\t\t\t\t{word}: begin\n\t\t\t\t\t\t\tcase (ba_decoded)"
        for bit in range(num_bits_per_word):
            logic += f"\n\t\t\t\t\t\t\t\t{bit}: begin"
            logic += f"\n\t\t\t\t\t\t\t\t\t\tif(I(vc{word}b{bit}n)>650u && I(vc{word}b{bit}n)<800u) begin"
            logic += f"\n\t\t\t\t\t\t\t\t\t\t\tv_outb0 = v_write;"
            logic += f"\n\t\t\t\t\t\t\t\t\t\tend"
            logic += f"\n\t\t\t\t\t\t\t\t\t\telse begin"
            logic += f"\n\t\t\t\t\t\t\t\t\t\t\tv_outb0 = 0.0;"
            logic += f"\n\t\t\t\t\t\t\t\t\t\tend"
            logic += f"\n\t\t\t\t\t\t\t\tend"
        logic += "\n\t\t\t\t\t\t\tendcase\n\t\t\t\t\t\tend"
    logic += "\n\t\t\t\t\tendcase"
    logic += f"\n\t\t\t\tend"
    logic += "\n\t\t\t\telse begin"
    logic += "\n\t\t\t\t\tcase (ca_decoded)"
    for word in range(num_words):
        logic += f"\n\t\t\t\t\t\t{word}: begin\n\t\t\t\t\t\t\t"
        for bit in range(num_bits_per_word):
            logic += f"\n\t\t\t\t\t\t\tif(I(vc{word}b{bit}n)>650u && I(vc{word}b{bit}n)<800u)"
            logic += f"\n\t\t\t\t\t\t\t\tv_outb{bit} = v_write;"
            logic += f"\n\t\t\t\t\t\t\telse"
            logic += f"\n\t\t\t\t\t\t\t\tv_outb{bit} = 0.0;"
        logic += "\n\t\t\t\t\t\tend"
    logic += "\n\t\t\t\tendcase\n\t\t\tend\n\t\tend\n"
    logic += "\t\tend\n"

    # Continuos assignment for inouts
    for i in inouts:
        logic += f"\t\tV({i}) <+ v_{i};\n"
    logic += "\t\tV(outb0) <+ v_outb0;\n"
    for i in outputs[1:]:
        logic += f"\t\tV({i}) <+ v_{i};\n"
    logic += "\tend\n"

    footer = "endmodule\n"

    return header + io_decls + logic + footer

# Generate a 2x2-bit CAS block
veriloga_code = generate_cas_module(4, 1)

with open("CAS_full.va", "w") as f:
    f.write(veriloga_code)

print("CAS with decoding + logic saved to CAS_full.va")
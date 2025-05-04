import math
def generate_testbench(row_bits,col_bits, no_of_data_bits):
    """
    Generates a Verilog-A testbench for the RAS module.

    Args:
        no_of_address_bits (int): Number of address bits.
        no_of_data_bits (int): Number of data bits.
    """

    no_of_address_bits = row_bits + col_bits
    instruction_length = 3*(1+no_of_address_bits+no_of_data_bits)
    max_possible = 2**(col_bits+no_of_data_bits)
    final_result = ""
    if instruction_length > max_possible:
        print("Instruction length exceeds maximum possible value.")
        return
    if no_of_address_bits < 1 or no_of_data_bits < 1:
        print("Number of address bits and data bits must be at least 1.")
        return
    # Find the best possible value of instruction length
    instruction_words = math.ceil(instruction_length / (2**(no_of_data_bits)))
    # Define the parameters
    num_addr_bits = no_of_address_bits
    num_data_bits = no_of_data_bits
    num_data_outputs = 2 ** num_data_bits

    inputs = ["clk"]
    data_outputs = [f"data{i}" for i in range(num_data_outputs)]
    address_outputs = [f"addr{i}" for i in range(num_addr_bits)]
    plim = "plim"
    wr = "wr"

    # Create the Verilog-A testbench code
    tb_code = f"""`include "disciplines.vams"
`include "constants.vams"

module testbench(
\tinput electrical clk,
\toutput electrical idle,
"""
    tb_code += f"\toutput electrical {plim},\n"
    tb_code += f"\toutput electrical {wr},\n"
    for i in range(num_data_outputs):
        tb_code += f"\toutput electrical data{i},\n"
    for i in range(num_addr_bits):
        tb_code += f"\toutput electrical addr{i},\n"
    for i in range(num_data_outputs):
        tb_code += f"\tinput electrical cross_data{i},\n"
    tb_code += f"\tinput electrical instr_exec\n"
    tb_code += ");\n\n"
    tb_code += "\tinteger state = 0;\n"
    tb_code += "\treal v_idle = 1.0;\n"
    tb_code += "\treal v_plim = 0.0;\n"
    tb_code += "\treal v_wr = 0.0;\n"
    for i in range(num_data_outputs):
        tb_code += f"\treal v_data{i};\n"
    for i in range(num_addr_bits):
        tb_code += f"\treal v_addr{i};\n"
    tb_code += "\treal prev_clk;\n"

    tb_code += "\tanalog begin\n"
    tb_code += "\t\t@(initial_step) begin\n"
    tb_code += "\t\t\tprev_clk = V(clk);\n"
    tb_code += "\t\tend\n\n"

    tb_code += "\t\tif(V(clk) > 0.5 && prev_clk <= 0.5) begin\n"
    state = 0
    tb_code += "\t\t\tcase (state)\n"
    while(1):
        print("Do you want to perform any action?(y/n)")
        action = input()
        if action == 'n' or action == 'N':
            break
        elif action == 'y' or action == 'Y':
            print("Enter the action you want to perform ('w' for write, 'r' for read, 'i' for writing an instruction into crossbar, e for executing instruction):")
            action = input()
            if action == 'w':
                print(f"Enter teh address to write to (in binary {num_addr_bits} bits):")
                addr = input()
                # Perform check for address length and binary format
                if len(addr) != num_addr_bits or not all(bit in '01' for bit in addr):
                    print("Invalid address format. Please enter a binary number of the correct length.")
                    continue
                print(f"Enter the data to write (in binary {2**num_data_bits} bits):")
                data = input()
                # Perform check for data length and binary format
                if len(data) != num_data_outputs or not all(bit in '01' for bit in data):
                    print("Invalid data format. Please enter a binary number of the correct length.")
                    continue
                final_result += f"Writing data {data} to address {addr}\n"
                tb_code += f"\t\t\t\t{state}: begin\n"
                tb_code += f"\t\t\t\t\tv_plim = 0.0;\n"
                tb_code += f"\t\t\t\t\tv_wr = 1.0;\n"
                tb_code += "\t\t\t\t\tv_idle = 0.0;\n"
                for i, b in enumerate(reversed(data_outputs)):
                    tb_code += f"\t\t\t\t\tv_{b} = {data[i]};\n"
                for i, b in enumerate(reversed(address_outputs)):
                    tb_code += f"\t\t\t\t\tv_{b} = {addr[i]};\n"
                tb_code += f"\t\t\t\t\tstate = {state + 1};\n"
                tb_code += "\t\t\t\tend\n"
                state += 1
                tb_code += f"\t\t\t\t{state}: begin\n"
                tb_code += f"\t\t\t\t\tstate = {state + 1};\n"
                tb_code += "\t\t\t\tend\n"
                state += 1
                tb_code += f"\t\t\t\t{state}: begin\n"
                tb_code += f"\t\t\t\t\tstate = {state + 1};\n"
                tb_code += "\t\t\t\tend\n"
                state += 1
                tb_code += f"\t\t\t\t{state}: begin\n"
                tb_code += f"\t\t\t\t\tstate = {state + 1};\n"
                tb_code += "\t\t\t\t\tv_idle = 1.0;\n"
                tb_code += "\t\t\t\t\t$display(\"Data written successfully\");\n"
                tb_code += "\t\t\t\tend\n"
                state += 1
            elif action == 'r':
                print(f"Enter teh address to read from (in binary {num_addr_bits}):")
                addr = input()
                # Perform check for address length and binary format
                if len(addr) != num_addr_bits or not all(bit in '01' for bit in addr):
                    print("Invalid address format. Please enter a binary number of the correct length.")
                    continue
                final_result += f"Reading data from address {addr}\n"
                tb_code += f"\t\t\t\t{state}: begin\n"
                tb_code += f"\t\t\t\t\tv_plim = 0.0;\n"
                tb_code += f"\t\t\t\t\tv_wr = 0.0;\n"
                tb_code += "\t\t\t\t\tv_idle = 0.0;\n"
                for i, b in enumerate(reversed(address_outputs)):
                    tb_code += f"\t\t\t\t\tv_{b} = {addr[i]};\n"
                tb_code += f"\t\t\t\t\tstate = {state + 1};\n"
                tb_code += "\t\t\t\tend\n"
                state += 1
                tb_code += f"\t\t\t\t{state}: begin\n"
                tb_code += f"\t\t\t\t\tstate = {state + 1};\n"
                tb_code += "\t\t\t\tend\n"
                state += 1
                tb_code += f"\t\t\t\t{state}: begin\n"
                tb_code += f"\t\t\t\t\tstate = {state + 1};\n"
                tb_code += "\t\t\t\tend\n"
                state += 1
                tb_code += f"\t\t\t\t{state}: begin\n"
                tb_code += f"\t\t\t\t\tv_idle = 1.0;\n"
                tb_code += f"\t\t\t\t\tstate = {state + 1};\n"
                tb_code += "\t\t\t\tend\n"
                state += 1
                tb_code += f"\t\t\t\t{state}: begin\n"
                tb_code += f"\t\t\t\t\tstate = {state + 1};\n"
                tb_code += "\t\t\t\t\tv_idle = 1.0;\n"
                tb_code += "\t\t\t\t\t$display(\"Data read successfully\");\n"
                tb_code += "\t\t\t\t\t$display("
                for i in reversed(range(num_data_outputs)):
                    tb_code += f"V(cross_data{i})"
                    if i != 0:
                        tb_code += ", "
                tb_code += ");\n"
                tb_code += "\t\t\t\tend\n"
                state += 1
            elif action == 'i':
                print(f"Enter the starting address of the instruction to be stored (in binary {num_addr_bits}):")
                addr = input()
                # Perform check for address length and binary format
                if len(addr) != num_addr_bits or not all(bit in '01' for bit in addr):
                    print("Invalid address format. Please enter a binary number of the correct length.")
                    continue
                const_addr = int(addr,2)
                # check if the instructions fit in same row starting from the address
                check = const_addr + instruction_words - 1
                check = format(check, f'0{num_addr_bits}b')
                if check[:row_bits] != addr[:row_bits]:
                    print("The instructions do not fit in the same row. Please enter a valid address.")
                    continue
                print("Enter the type of instruction (0 MAJ, 1 AND, 2 OR, 3 NOT):")
                instr = input()
                # Perform check for instruction format
                if instr not in ['0', '1', '2', '3']:
                    print("Invalid instruction format. Please enter a valid instruction type.")
                    continue
                if(instr == '0'):
                    instr = "000"
                    print(f"Enter the word address of opearand a (in binary {num_addr_bits}):")
                    addr_a = input()
                    # Perform check for address length and binary format
                    if len(addr_a) != num_addr_bits or not all(bit in '01' for bit in addr_a):
                        print("Invalid address format. Please enter a binary number of the correct length.")
                        continue
                    instr += addr_a
                    print(f"Enter the bit address of operand a (in binary {num_data_bits}):")
                    addr_a = input()
                    # Perform check for address length and binary format
                    if len(addr_a) != num_data_bits or not all(bit in '01' for bit in addr_a):
                        print("Invalid address format. Please enter a binary number of the correct length.")
                        continue
                    instr += addr_a
                    print(f"Enter the word address of opearand b (in binary {num_addr_bits}):")
                    addr_b = input()
                    # Perform check for address length and binary format
                    if len(addr_b) != num_addr_bits or not all(bit in '01' for bit in addr_b):
                        print("Invalid address format. Please enter a binary number of the correct length.")
                        continue
                    instr += addr_b
                    print(f"Enter the bit address of operand b (in binary {num_data_bits}):")
                    addr_b = input()
                    # Perform check for address length and binary format
                    if len(addr_b) != num_data_bits or not all(bit in '01' for bit in addr_b):
                        print("Invalid address format. Please enter a binary number of the correct length.")
                        continue
                    instr += addr_b
                    print(f"Enter the word address of opearand c (in binary {num_addr_bits}):")
                    addr_c = input()
                    # Perform check for address length and binary format
                    if len(addr_c) != num_addr_bits or not all(bit in '01' for bit in addr_c):
                        print("Invalid address format. Please enter a binary number of the correct length.")
                        continue
                    instr += addr_c
                    print(f"Enter the bit address of operand c (in binary {num_data_bits}):")
                    addr_c = input()
                    # Perform check for address length and binary format
                    if len(addr_c) != num_data_bits or not all(bit in '01' for bit in addr_c):
                        print("Invalid address format. Please enter a binary number of the correct length.")
                        continue
                    instr += addr_c
                    final_result += f"Writing instruction at address {addr} to perform MAJ of the bits at address {instr[3:3+(row_bits + col_bits)] + ' ' + instr[3+(row_bits + col_bits):3+(row_bits+col_bits+num_data_bits)]},{instr[3:3+2*(row_bits + col_bits)] + ' ' + instr[3+2*(row_bits + col_bits):3+2*(row_bits+col_bits+num_data_bits)]},{instr[3:3+3*(row_bits + col_bits)] + ' ' + instr[3+3*(row_bits + col_bits):3+3*(row_bits+col_bits+num_data_bits)]} and store at {instr[3:3+3*(row_bits + col_bits)] + ' ' + instr[3+3*(row_bits + col_bits):3+3*(row_bits+col_bits+num_data_bits)]}\n"
                elif(instr == '1'):
                    instr = "001"
                    print(f"Enter the word address of opearand a (in binary {num_addr_bits}):")
                    addr_a = input()
                    # Perform check for address length and binary format
                    if len(addr_a) != num_addr_bits or not all(bit in '01' for bit in addr_a):
                        print("Invalid address format. Please enter a binary number of the correct length.")
                        continue
                    instr += addr_a
                    print(f"Enter the bit address of operand a (in binary {num_data_bits}):")
                    addr_a = input()
                    # Perform check for address length and binary format
                    if len(addr_a) != num_data_bits or not all(bit in '01' for bit in addr_a):
                        print("Invalid address format. Please enter a binary number of the correct length.")
                        continue
                    instr += addr_a
                    print(f"Enter the word address of opearand b (in binary {num_addr_bits}):")
                    addr_b = input()
                    # Perform check for address length and binary format
                    if len(addr_b) != num_addr_bits or not all(bit in '01' for bit in addr_b):
                        print("Invalid address format. Please enter a binary number of the correct length.")
                        continue
                    instr += addr_b
                    print(f"Enter the bit address of operand b (in binary {num_data_bits}):")
                    addr_b = input()
                    # Perform check for address length and binary format
                    if len(addr_b) != num_data_bits or not all(bit in '01' for bit in addr_b):
                        print("Invalid address format. Please enter a binary number of the correct length.")
                        continue
                    instr += addr_b
                    print(f"Enter the word address of opearand c (in binary {num_addr_bits}):")
                    addr_c = input()
                    # Perform check for address length and binary format
                    if len(addr_c) != num_addr_bits or not all(bit in '01' for bit in addr_c):
                        print("Invalid address format. Please enter a binary number of the correct length.")
                        continue
                    instr += addr_c
                    print(f"Enter the bit address of operand c (in binary {num_data_bits}):")
                    addr_c = input()
                    # Perform check for address length and binary format
                    if len(addr_c) != num_data_bits or not all(bit in '01' for bit in addr_c):
                        print("Invalid address format. Please enter a binary number of the correct length.")
                        continue
                    instr += addr_c
                    final_result += f"Writing instruction at address {addr} to perform AND of the bits at address {instr[3:3+(row_bits + col_bits)] + ' ' + instr[3+(row_bits + col_bits):3+(row_bits+col_bits+num_data_bits)]},{instr[3:3+2*(row_bits + col_bits)] + ' ' + instr[3+2*(row_bits + col_bits):3+2*(row_bits+col_bits+num_data_bits)]} and store at {instr[3:3+3*(row_bits + col_bits)] + ' ' + instr[3+3*(row_bits + col_bits):3+3*(row_bits+col_bits+num_data_bits)]}\n"
                elif(instr == '2'):
                    instr = "010"
                    print(f"Enter the word address of opearand a (in binary {num_addr_bits}):")
                    addr_a = input()
                    # Perform check for address length and binary format
                    if len(addr_a) != num_addr_bits or not all(bit in '01' for bit in addr_a):
                        print("Invalid address format. Please enter a binary number of the correct length.")
                        continue
                    instr += addr_a
                    print(f"Enter the bit address of operand a (in binary {num_data_bits}):")
                    addr_a = input()
                    # Perform check for address length and binary format
                    if len(addr_a) != num_data_bits or not all(bit in '01' for bit in addr_a):
                        print("Invalid address format. Please enter a binary number of the correct length.")
                        continue
                    instr += addr_a
                    print(f"Enter the word address of opearand b (in binary {num_addr_bits}):")
                    addr_b = input()
                    # Perform check for address length and binary format
                    if len(addr_b) != num_addr_bits or not all(bit in '01' for bit in addr_b):
                        print("Invalid address format. Please enter a binary number of the correct length.")
                        continue
                    instr += addr_b
                    print(f"Enter the bit address of operand b (in binary {num_data_bits}):")
                    addr_b = input()
                    # Perform check for address length and binary format
                    if len(addr_b) != num_data_bits or not all(bit in '01' for bit in addr_b):
                        print("Invalid address format. Please enter a binary number of the correct length.")
                        continue
                    instr += addr_b
                    print(f"Enter the word address of opearand c (in binary {num_addr_bits}):")
                    addr_c = input()
                    # Perform check for address length and binary format
                    if len(addr_c) != num_addr_bits or not all(bit in '01' for bit in addr_c):
                        print("Invalid address format. Please enter a binary number of the correct length.")
                        continue
                    instr += addr_c
                    print(f"Enter the bit address of operand c (in binary {num_data_bits}):")
                    addr_c = input()
                    # Perform check for address length and binary format
                    if len(addr_c) != num_data_bits or not all(bit in '01' for bit in addr_c):
                        print("Invalid address format. Please enter a binary number of the correct length.")
                        continue
                    instr += addr_c
                    final_result += f"Writing instruction at address {addr} to perform OR of the bits at address {instr[3:3+(row_bits + col_bits)] + ' ' + instr[3+(row_bits + col_bits):3+(row_bits+col_bits+num_data_bits)]},{instr[3:3+2*(row_bits + col_bits)] + ' ' + instr[3+2*(row_bits + col_bits):3+2*(row_bits+col_bits+num_data_bits)]} and store at {instr[3:3+3*(row_bits + col_bits)] + ' ' + instr[3+3*(row_bits + col_bits):3+3*(row_bits+col_bits+num_data_bits)]}\n"
                elif(instr == '3'):
                    instr = "011"
                    print(f"Enter the word address of opearand a (in binary {num_addr_bits}):")
                    addr_a = input()
                    # Perform check for address length and binary format
                    if len(addr_a) != num_addr_bits or not all(bit in '01' for bit in addr_a):
                        print("Invalid address format. Please enter a binary number of the correct length.")
                        continue
                    instr += addr_a
                    print(f"Enter the bit address of operand a (in binary {num_data_bits}):")
                    addr_a = input()
                    # Perform check for address length and binary format
                    if len(addr_a) != num_data_bits or not all(bit in '01' for bit in addr_a):
                        print("Invalid address format. Please enter a binary number of the correct length.")
                        continue
                    instr += addr_a
                    instr += format(0, f'0{num_addr_bits}b')
                    instr += format(0, f'0{num_data_bits}b')
                    print(f"Enter the word address of opearand c (in binary {num_addr_bits}):")
                    addr_c = input()
                    # Perform check for address length and binary format
                    if len(addr_c) != num_addr_bits or not all(bit in '01' for bit in addr_c):
                        print("Invalid address format. Please enter a binary number of the correct length.")
                        continue
                    instr += addr_c
                    print(f"Enter the bit address of operand c (in binary {num_data_bits}):")
                    addr_c = input()
                    # Perform check for address length and binary format
                    if len(addr_c) != num_data_bits or not all(bit in '01' for bit in addr_c):
                        print("Invalid address format. Please enter a binary number of the correct length.")
                        continue
                    instr += addr_c
                    final_result += f"Writing instruction at address {addr} to perform NOT of the bits at address {instr[3:3+(row_bits + col_bits)] + ' ' + instr[3+(row_bits + col_bits):3+(row_bits+col_bits+num_data_bits)]} and store at {instr[3:3+3*(row_bits + col_bits)] + ' ' + instr[3+3*(row_bits + col_bits):3+3*(row_bits+col_bits+num_data_bits)]}\n"
                if len(instr) != instruction_words*2**(num_data_bits):
                    instr += format(0, f'0{instruction_words*2**(num_data_bits)-len(instr)}b')
                for j in range(instruction_words):
                    data = instr[j*2**(num_data_bits):(j+1)*2**(num_data_bits)]
                    addr = format(const_addr+j, f'0{num_addr_bits}b')
                    tb_code += f"\t\t\t\t{state}: begin\n"
                    tb_code += f"\t\t\t\t\tv_plim = 0.0;\n"
                    tb_code += f"\t\t\t\t\tv_wr = 1.0;\n"
                    tb_code += "\t\t\t\t\tv_idle = 0.0;\n"
                    for i, b in enumerate(data_outputs):
                        tb_code += f"\t\t\t\t\tv_{b} = {data[i]};\n"
                    for i, b in enumerate(reversed(address_outputs)):
                        tb_code += f"\t\t\t\t\tv_{b} = {addr[i]};\n"
                    tb_code += f"\t\t\t\t\tstate = {state + 1};\n"
                    tb_code += "\t\t\t\tend\n"
                    state += 1
                    tb_code += f"\t\t\t\t{state}: begin\n"
                    tb_code += f"\t\t\t\t\tstate = {state + 1};\n"
                    tb_code += "\t\t\t\tend\n"
                    state += 1
                    tb_code += f"\t\t\t\t{state}: begin\n"
                    tb_code += f"\t\t\t\t\tstate = {state + 1};\n"
                    tb_code += "\t\t\t\tend\n"
                    state += 1
                    tb_code += f"\t\t\t\t{state}: begin\n"
                    tb_code += f"\t\t\t\t\tstate = {state + 1};\n"
                    tb_code += "\t\t\t\t\tv_idle = 1.0;\n"
                    if(j == instruction_words - 1): tb_code += "\t\t\t\t\t$display(\"Instruction written successfully\");\n"
                    tb_code += "\t\t\t\tend\n"
                    state += 1
            elif action == 'e':
                print(f"Enter the address of the instruction to be executed (in binary {num_addr_bits}):")
                addr = input()
                # Perform check for address length and binary format
                if len(addr) != num_addr_bits or not all(bit in '01' for bit in addr):
                    print("Invalid address format. Please enter a binary number of the correct length.")
                    continue
                const_addr = int(addr,2)
                # check if the instructions fit in same row starting from the address
                check = const_addr + instruction_words - 1
                check = format(check, f'0{num_addr_bits}b')
                if check[:row_bits] != addr[:row_bits]:
                    print("The instructions do not fit in the same row. Please enter a valid address.")
                    continue
                final_result += f"Executing instruction at address {addr}\n"
                tb_code += f"\t\t\t\t{state}: begin\n"
                tb_code += f"\t\t\t\t\tv_plim = 1.0;\n"
                tb_code += f"\t\t\t\t\tv_wr = 0.0;\n"
                tb_code += "\t\t\t\t\tv_idle = 0.0;\n"
                for i, b in enumerate(reversed(address_outputs)):
                    tb_code += f"\t\t\t\t\tv_{b} = {addr[i]};\n"
                tb_code += f"\t\t\t\t\tstate = {state + 1};\n"
                tb_code += "\t\t\t\tend\n"
                state += 1
                tb_code += f"\t\t\t\t{state}: begin\n"
                tb_code += "\t\t\t\t\tif(V(instr_exec) > 0.5) begin\n"
                tb_code += "\t\t\t\t\t\tv_idle = 1.0;\n"
                tb_code += "\t\t\t\t\t\tv_plim = 0.0;\n"
                tb_code += "\t\t\t\t\t\tv_wr = 0.0;\n"
                tb_code += "\t\t\t\t\t$display(\"Instruction executed successfully\");\n"
                tb_code += f"\t\t\t\t\t\tstate = {state + 1};\n"
                tb_code += "\t\t\t\t\tend\n"
                tb_code += "\t\t\t\tend\n"
                state += 1

                


    tb_code += "\t\t\tendcase\n"
    tb_code += "\t\tend\n\n"

    # Continuous assignment for inputs
    for i in range(num_data_outputs):
        tb_code += f"\t\tV(data{i}) <+ v_data{i};\n"
    for i in range(num_addr_bits):
        tb_code += f"\t\tV(addr{i}) <+ v_addr{i};\n"
    tb_code += f"\t\tV({plim}) <+ transition(v_plim,0,10n);\n"
    tb_code += f"\t\tV({wr}) <+ transition(v_wr,0,10n);\n"
    tb_code += "\t\tV(idle) <+ transition(v_idle,0,10n);\n"
    tb_code += "\t\tprev_clk = V(clk);\n\n"
    tb_code += "\tend\n\n"


    tb_code += "endmodule\n\n"
    # Write this to file
    with open("testbench.va", "w") as f:
        f.write(tb_code)
    
    print(final_result)


if __name__ == "__main__":
    generate_testbench(2, 4, 1)
    print("Testbench generated and saved as: testbench.va")

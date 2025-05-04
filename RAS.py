def generate_ras_veriloga(
    filename="RAS_generated.va",
    v_on=1.2,
    num_addr_bits=2,
    input_prefix="in",
    output_prefix="out",
    idle_signal="idle"
):
    num_outputs = 2 ** num_addr_bits
    inputs = [f"{input_prefix}{i}" for i in range(num_addr_bits)]
    outputs = [f"{output_prefix}{i}" for i in range(num_outputs)]

    port_list = ", ".join(inputs + outputs + [idle_signal])
    electricals = ", ".join(inputs + outputs + [idle_signal])

    header = f"""`include "disciplines.vams"
`include "constants.vams"

module RAS({port_list});
  parameter real v_on = {v_on};
  parameter integer no_of_bits_in_row_address = {num_addr_bits};
  input {", ".join(inputs)};
  input {idle_signal};
  output {", ".join(outputs)};

  electrical {electricals};

  analog begin
    if (V({idle_signal}) < 0.5) begin
"""

    logic = ""
    for idx in range(num_outputs):
        conditions = " && ".join(
            f"(V({inputs[bit]}) {'< 0.5' if (idx >> bit) & 1 == 0 else '>= 0.5'})"
            for bit in range(num_addr_bits)
        )
        logic += f"      if ({conditions}) begin\n"
        for i, out in enumerate(outputs):
            voltage = "v_on" if i == idx else "0.0"
            logic += f"        V({out}) <+ {voltage};\n"
        logic += "      end\n"

    reset = "\n".join([f"      V({out}) <+ 0.0;" for out in outputs])

    footer = f"""    end else begin
{reset}
    end
  end
endmodule
"""

    with open(filename, "w") as f:
        f.write(header + logic + footer)

    print(f"RAS module generated and saved as: {filename}")

generate_ras_veriloga(
    filename="RAS_full.va",
    v_on=1.2,
    num_addr_bits=2, 
    input_prefix="in",
    output_prefix="out",
    idle_signal="idle"
)

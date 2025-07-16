import tkinter as tk
from tkinter import ttk

def launch_gui(parsed_instructions, symbol_table):
    root = tk.Tk()
    root.title("Motorola 6800 Assembly Görselleştirici")

    ttk.Label(root, text="Instruction List", font=('Arial', 14, 'bold')).pack(pady=10)

    listbox = tk.Listbox(root, width=100, height=20)
    listbox.pack()

    for mnemonic, operands in parsed_instructions:
        operand_strs = []
        for op in operands:
            operand_strs.append(op['data'])
        line = f"{mnemonic.name} " + ', '.join(operand_strs)
        listbox.insert(tk.END, line)

    ttk.Label(root, text="Symbols", font=('Arial', 14, 'bold')).pack(pady=10)

    symbol_listbox = tk.Listbox(root, width=100, height=10)
    symbol_listbox.pack()

    for label, (addr, typ, val) in symbol_table.items():
        symbol_listbox.insert(tk.END, f"{label} @ {addr} ({typ}) -> {val}")

    root.mainloop()

import tkinter as tk
from tkinter import ttk, messagebox


# ========= LÓGICA (OOP) =========
class Carteira:
    def __init__(self):
        self.movimentos = []  # lista de (tipo, categoria, valor)

    def adicionar(self, tipo, categoria, valor):
        valor = float(valor)
        if tipo == "Saída":
            valor = -abs(valor)
        else:
            valor = abs(valor)
        self.movimentos.append((tipo, categoria, valor))

    def saldo(self):
        return sum(v for _, _, v in self.movimentos)

    def resumo_por_categoria(self):
        resumo = {}
        for _, cat, v in self.movimentos:
            resumo[cat] = resumo.get(cat, 0) + v
        return resumo


def dinheiro(v: float) -> str:
    s = f"{v:,.2f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


# ========= INTERFACE (GUI) =========
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Finanças Simples")
        self.geometry("760x520")
        self.minsize(720, 480)

        self.carteira = Carteira()

        # ----- Topo: inputs -----
        frame = ttk.Frame(self, padding=12)
        frame.pack(fill="x")

        ttk.Label(frame, text="Tipo").grid(row=0, column=0, sticky="w")
        self.tipo_var = tk.StringVar(value="Saída")
        self.tipo = ttk.Combobox(frame, textvariable=self.tipo_var, values=["Entrada", "Saída"], width=12, state="readonly")
        self.tipo.grid(row=1, column=0, padx=(0, 10), sticky="w")

        ttk.Label(frame, text="Categoria").grid(row=0, column=1, sticky="w")
        self.cat_var = tk.StringVar(value="Aluguel")
        self.cat = ttk.Entry(frame, textvariable=self.cat_var, width=28)
        self.cat.grid(row=1, column=1, padx=(0, 10), sticky="w")

        ttk.Label(frame, text="Valor").grid(row=0, column=2, sticky="w")
        self.valor_var = tk.StringVar()
        self.valor = ttk.Entry(frame, textvariable=self.valor_var, width=14)
        self.valor.grid(row=1, column=2, padx=(0, 10), sticky="w")

        add_btn = ttk.Button(frame, text="Adicionar", command=self.on_add)
        add_btn.grid(row=1, column=3, sticky="w")

        # ----- Meio: tabela de movimentos -----
        mid = ttk.Frame(self, padding=(12, 0, 12, 12))
        mid.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(mid, columns=("tipo", "categoria", "valor"), show="headings", height=10)
        self.tree.heading("tipo", text="Tipo")
        self.tree.heading("categoria", text="Categoria")
        self.tree.heading("valor", text="Valor")

        self.tree.column("tipo", width=90, anchor="w")
        self.tree.column("categoria", width=320, anchor="w")
        self.tree.column("valor", width=120, anchor="e")

        scrollbar = ttk.Scrollbar(mid, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # ----- Rodapé: saldo + resumo -----
        bottom = ttk.Frame(self, padding=(12, 0, 12, 12))
        bottom.pack(fill="x")

        self.saldo_label = ttk.Label(bottom, text="Saldo: R$ 0,00", font=("Segoe UI", 12, "bold"))
        self.saldo_label.pack(anchor="w")

        ttk.Label(bottom, text="Resumo por categoria:").pack(anchor="w", pady=(10, 0))
        self.resumo_text = tk.Text(bottom, height=6, wrap="word")
        self.resumo_text.pack(fill="x")
        self.resumo_text.configure(state="disabled")

        # Atalho Enter
        self.bind("<Return>", lambda _e: self.on_add())

    def on_add(self):
        tipo = self.tipo_var.get().strip()
        categoria = self.cat_var.get().strip()
        valor = self.valor_var.get().strip().replace(",", ".")

        if not categoria:
            messagebox.showwarning("Atenção", "Preencha a categoria.")
            return
        try:
            float(valor)
        except ValueError:
            messagebox.showwarning("Atenção", "Digite um valor válido (ex: 120 ou 120.50).")
            return

        self.carteira.adicionar(tipo, categoria, valor)
        # Atualiza tabela
        v = self.carteira.movimentos[-1][2]
        self.tree.insert("", "end", values=(tipo, categoria, dinheiro(v)))

        # Limpa valor e atualiza visuais
        self.valor_var.set("")
        self.atualizar_dashboard()

    def atualizar_dashboard(self):
        saldo = self.carteira.saldo()
        self.saldo_label.config(text=f"Saldo: {dinheiro(saldo)}")

        resumo = self.carteira.resumo_por_categoria()
        linhas = []
        for cat, total in sorted(resumo.items(), key=lambda x: abs(x[1]), reverse=True):
            linhas.append(f"- {cat}: {dinheiro(total)}")

        self.resumo_text.configure(state="normal")
        self.resumo_text.delete("1.0", "end")
        self.resumo_text.insert("1.0", "\n".join(linhas) if linhas else "(vazio)")
        self.resumo_text.configure(state="disabled")


if __name__ == "__main__":
    App().mainloop()


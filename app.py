class Carteira:
    def __init__(self):
        self.movimentos = []  # (categoria, valor)

    def entrada(self, valor, categoria="Entrada"):
        self.movimentos.append((categoria, float(valor)))

    def saida(self, valor, categoria="Saída"):
        self.movimentos.append((categoria, -float(valor)))

    def saldo(self):
        return sum(valor for _, valor in self.movimentos)

    def resumo_por_categoria(self):
        resumo = {}
        for categoria, valor in self.movimentos:
            resumo[categoria] = resumo.get(categoria, 0) + valor
        return resumo


def dinheiro(v):
    # formata tipo R$ 1.234,56
    s = f"{v:,.2f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


carteira = Carteira()

# Exemplos (você pode trocar pelos seus valores)
carteira.entrada(3000, "Salário")
carteira.saida(844, "Aluguel")
carteira.saida(196.76, "Luz")
carteira.saida(120, "ChatGPT")

print("✅ Saldo final:", dinheiro(carteira.saldo()))

print("\n📌 Resumo por categoria:")
for cat, total in carteira.resumo_por_categoria().items():
    print(f"- {cat}: {dinheiro(total)}")

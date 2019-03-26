# En/decodes Turing's binary format
class TuringEncoder():
	symbol_table = {}
	invert_symbol_table = {}

	def __init__(self, symbol_table):
		self.symbol_table = symbol_table
		self.invert_symbol_table = {}
		for k, v in symbol_table.items():
			self.invert_symbol_table[v] = k

	def bin_to_turing(self, line):
		l = [line[k:k+5] for k in range(0, len(line), 5)]
		encoded = "".join([self.invert_symbol_table["".join(map(str, c))] for c in l])
		return encoded

	def turing_to_bin(self, line):
		try:
			decoded = [self.symbol_table[s] for s in line]
		except Exception:
			return None

		return list(map(bool, [item for sublist in decoded for item in sublist]))

		
		

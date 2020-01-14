from framework import Visitor

# OneTimeVisitor is a visitor that will access the same node at most once
class OneTimeVisitor(Visitor):
	def __init__(self):
		super().__init__()
		self.visit_record = set()

	def enter(self, node):
		if node in self.visit_record:
			return True
		self.visit_record.add(node)
		print(node)
		return False

# Painter is a visitor that can draw a picture of the NFs
class Painter(Visitor):
	def __init__(self, pic_name = 'pic'):
		super().__init__()
		self.pic_name = pic_name
		self.idx_map = {}
		self.visit_stack = []
		from graphviz import Digraph
		self.g = Digraph(self.pic_name)

	def enter(self, node):
		# print(str(node), node.state)
		# if hasattr(node, 'conds'):
		# 	print(node.conds)
		node_idx, skip_child = len(self.idx_map), False
		if node not in self.idx_map:
			self.idx_map[node] = node_idx
			color = node.color if hasattr(node, 'color') else 'blue'
			self.g.node(str(node_idx), str(node), color = color)
		else:
			node_idx = self.idx_map[node]
			skip_child = True

		if len(self.visit_stack) > 0:
			in_node_idx = self.visit_stack[-1]
			self.g.edge(str(in_node_idx), str(node_idx), color = 'black')
		self.visit_stack.append(node_idx)
		return skip_child

	def leave(self, node):
		self.visit_stack.pop()

	def show(self):
		try:
			self.g.view()
		except Exception as e:
			pass
		import os
		os.system('rm ' + self.pic_name + '.gv')

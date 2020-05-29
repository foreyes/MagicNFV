from operator import *
from copy import deepcopy

class NFNode:
	def __init__(self):
		self._attributes = {}
		self._children = []

	def set_attributes(self, attrs):
		# 能否在硬件上执行、分支条件、需要读/写哪些字段、一定不会读/写哪些字段
		self._attributes = attrs

	def get_attributes(self):
		return self._attributes

	def set_child(self, idx, child):
		self._children[idx] = child

	# 将一个儿子设为另一个，返回是否成功
	def set_child_to_another(self, old_child, new_child):
		for i in range(len(self._children)):
			if self._children[i] is old_child:
				self._children[i] = new_child
				return True
		return False

	def get_child(self, idx):
		return self._children[idx]

	def set_children(self, children):
		self._children = children

	def get_children(self):
		from copy import copy
		return copy(self._children)

	# 给出包与当前状态，进行相应处理并返回包的出口编号。返回 -1 表示丢弃
	def solve_packet(self, packet, states):
		return 0

	def get_read_fields(self):
		return set()

	def get_write_fields(self):
		return set()

	def show(self):
		pass

# 数组的 id 用来表示 Unknown 的字段
Unknown = []
# 数组的 id 用来表示全部字段，例如 "will_read": ("global", AllFields) 表示可能会读全部的全局状态
AllFields = []

class Packet:
	def __init__(self, random_fields = True):
		self._fields = {}
		if random_fields:
			self.get_random_fields

	# TODO: 读写都加上返回是否成功
	def read_field(self, field_name, ret_unknown = False):
		if field_name not in self._fields or self._fields[field_name] is Unknown:
			if ret_unknown:
				return Unknown
			else:
				assert(False)
		# print("read packet: ", field_name, self.__fields[field_name])
		return self._fields[field_name]

	def write_field(self, field_name, value):
		# print("write packet: ", field_name, value)
		self._fields[field_name] = value
		if field_name is AllFields:
			for fn in self._fields:
				self._fields[fn] = value
		else:
			self._fields[field_name] = value

	def get_random_fields(self):
		pass


class States:
	def __init__(self):
		self._private = {}
		self._global = {}
		self._cur_conditions = []

	def init_packet_states(self):
		self._private = {}

	def add_condition(self, cond):
		self._cur_conditions.append(cond)

	def eliminate_cur_conditions_with_packet(self, packet):
		pass

	def write_packet_state(self, state_name, value):
		# print("write private: ", state_name, value)	
		if state_name is AllFields:
			for sn in self._private:
				self._private[sn] = value
		else:
			self._private[state_name] = value

	def write_global_state(self, state_name, value):
		# print("write global: ", state_name, value)
		if state_name is AllFields:
			for sn in self._global:
				self._global[sn] = value
		else:
			self._global[state_name] = value

	def read_packet_state(self, state_name, ret_unknown = False):
		if state_name not in self._private or self._private[state_name] is Unknown:
			if ret_unknown:
				return Unknown
			else:
				assert(False)
		# print("read private: ", state_name, self.__private[state_name])
		return self._private[state_name]

	def read_global_state(self, state_name, ret_unknown = False):
		if state_name not in self._global or self._global[state_name] is Unknown:
			if ret_unknown:
				return Unknown
			else:
				assert(False)
		# print("read global: ", state_name, self.__global[state_name])
		return self._global[state_name]

	# fields 是 "will_not_write" 的字段，除此之外全部置为 Unknown
	def set_packet_unknown(fields):
		if fields is AllFields:
			for key in self._private:
				self._private[key] = Unknown
			return
		for key in self._private:
			if key not in fields:
				self._private[key] = Unknown

	def set_global_unknown(fields):
		if fields is AllFields:
			for key in self._global:
				self._global[key] = Unknown
			return
		for key in self._global:
			if key not in fields:
				self._global[key] = Unknown


def set_unknown(fields, packet, states):
	all_flag_global, all_flag_private, all_flag_packet = False, False, False
	global_states, private_states, packet_fields = set(), set(), set()
	for field in fields:
		if field[0] == "packet":
			if all_flag_packet:
				continue
			if field[1] is AllFields:
				all_flag_packet = True
				packet_fields = AllFields
		elif field[0] == "global":
			if all_flag_global:
				continue
			if field[1] is AllFields:
				all_flag_global = True
				global_states = AllFields
		elif field[0] == "private":
			if all_flag_private:
				continue
			if field[1] is AllFields:
				all_flag_private = True
				private_states = AllFields

	packet.set_unknown(packet_fields)
	states.set_global_unknown(global_states)
	states.set_packet_unknown(private_states)


def write_field(field, value, packet, states):
	if field[0] == "packet":
		packet.write_field(field[1], value)
	elif field[0] == "global":
		states.write_global_state(field[1], value)
	elif field[0] == "private":
		states.write_packet_state(field[1], value)


def read_field(field, packet, states, ret_unknown = False):
	pass


def get_whole_cost(node, is_hardware = True, weight = 0):
	cost = 0
	if str(node) == "EnterHardware":
		is_hardware = True
	attrs = node.get_attributes()
	if attrs["hardware"] == False:
		is_hardware = False
	children = node.get_children()
	for child  in children:
		cost += get_whole_cost(child, is_hardware)
	if children:
		cost /= len(children)

	cur_cost = node.get_cost()
	if is_hardware:
		cur_cost *= weight
	return cost + cur_cost


class Expression:
	op_map = {"eq": eq, "==": eq, "<": lt, "<=": le, "!=": ne, ">=": ge, ">": gt, "+": add, "-": sub, "*": mul, "//": floordiv, "/": truediv, "%": mod, "**": pow, "and": and_, "or": or_, "not": not_}
	# 常数: args 为对应值; 字段: args 为字段名，形如("packet", "ip_ttl"); 参数: args 为参数列表
	def __init__(self, type = "const", args = Unknown):
		self._type = type
		self._args = args
		if type != "const" and type != "field":
			self._op = Expression.op_map[type]

	def get_type(self):
		return self._type

	def get_args(self):
		return deepcopy(self._args)

	def get_value(self, packet = None, states = None):
		if self._type == "const":
			return self._args
		if self._type == "field":
			field_type = self._args[0]
			if field_type == "packet":
				if packet is None:
					return Unknown
				return packet.read_field(self._args[1], True)
			elif field_type == "global":
				if states is None:
					return Unknown
				return states.read_global_state(self._args[1], True)
			elif field_type == "private":
				if states is None:
					return Unknown
				return states.read_packet_state(self._args[1], True)
			else:
				return Unknown

		arg1, arg2 = self._args[0].get_value(packet, states), self._args[1].get_value(packet, states)
		if arg1 is not Unknown and arg2 is not Unknown:
			# 不存在 Unknown 的参数，直接求值
			return self._op(arg1, arg2)

		if self._type == "mul" and (arg1 == 0 or arg2 == 0):
			return 0
		if self._type == "mod" and (arg2 == 1):
			return 0
		if self._type == "**" and (arg2 == 0):
			return 1
		# Unknown 本质上是 [], 其布尔值为 False
		if self._type == "or" and (arg1 or arg2):
			return self._op(arg1, arg2)
		return Unknown

	def eliminate_with_packet_and_states(self, packet, states):
		value = self.get_value(packet, states)
		if value is not Unknown:
			# 若当前可以直接求值，将其换成这个常数值
			self._type = "const"
			self._args = value
			return
		if self._type == "const" or self._type == "field":
			return
		self._args[0].eliminate_with_packet_and_states(packet, states)
		self._args[1].eliminate_with_packet_and_states(packet, states)

	# TODO: 完成这个函数
	def get_read_fields(self):
		return set()
		pass

	def get_cost(self, is_hardware):
		if self._type == "const":
			return 1
		if self._type == "field":
			return 1.5
		if is_hardware:
			return max(self._args[0].get_cost(is_hardware), self._args[1].get_cost(is_hardware))
		return self._args[0].get_cost(is_hardware) + self._args[1].get_cost(is_hardware) + 1

	def __str__(self):
		if self._type == "const":
			return str(self._args)
		if self._type == "field":
			return str(self._args[0]) + "_" + str(self._args[1])
		return str(self._args[0]) + " " + self._type + " " + str(self._args[1])


# TODO: 将 Condition 概念做好。Expression 不能 apply_to_packet_and_states 吗？如何处理合取范式？
# TODO: eq 判断时，"1" 和 1 是否相等，是否需要做统一规定？
class Condition(Expression):
	def apply_to_packet_and_states(self, packet, states):
		if self._type == "==":
			arg1, arg2 = self._args[0], self._args[1]
			if arg1.get_type() == "field" and arg2.get_type() == "const":
				return write_field(arg1.get_args(), arg2.get_value(packet, states), packet, states)
			if arg1.get_type() == "const" and arg2.get_type() == "field":
				return write_field(arg2.get_args(), arg1.get_value(packet, states), packet, states)
		if self._type == "and":
			arg1, arg2 = self._args[0], self._args[1]
			arg1.apply_to_packet_and_states(packet, states)
			arg2.apply_to_packet_and_states(packet, states)
			return
		states.add_condition(self)
		states.eliminate_cur_conditions_with_packet(packet)


class ValueSource(Expression):
	pass


class CostCalculator:
	def __init__(self):
		# 长度最大为 5，缓存
		self.rw_history = []
		self.total_cost = 0

	def read_field(self, field_name):
		# if field_name in self.rw_history:
		pass
			

class Painter:
	def __init__(self, node, pic_name = "test"):
		self.__node = node
		from graphviz import Digraph
		self.__g = Digraph(pic_name)
		self.__node_cnt = 0
		self.__node_map = {}

	def get_node_idx(self, node):
		if node not in self.__node_map:
			self.__node_map[node] = self.__node_cnt
			self.__g.node(str(self.__node_cnt), str(node), color = 'black')
			self.__node_cnt += 1
		return self.__node_map[node]

	def DFS(self, node):
		node_idx = self.get_node_idx(node)
		children = node.get_children()
		conditions = node.get_conditions() if hasattr(node, "get_conditions") else None
		for i in range(len(children)):
			child = children[i]
			if child not in self.__node_map:
				nxt_idx = self.get_node_idx(child)
				label = ""
				if conditions:
					if i < len(conditions):
						label = str(conditions[i])
					else:
						label = "else"
				self.__g.edge(str(node_idx), str(nxt_idx), color = 'black', label=label)
				self.DFS(child)
			else:
				nxt_idx = self.get_node_idx(child)
				label = ""
				if conditions:
					if i < len(conditions):
						label = str(conditions[i])
					else:
						label = "else"
				self.__g.edge(str(node_idx), str(nxt_idx), color = 'black', label=label)


	def show(self):
		self.DFS(self.__node)
		try:
			self.__g.view()
		except Exception as e:
			pass
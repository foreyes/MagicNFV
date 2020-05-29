# TODO: 加上 Cost 属性
# TODO: 实现 Codition 和 ValueSource, get_read_fields
# TODO: 实现 Field, State, Packet
# TODO: 区分 字段，包状态，全局状态

from framework import NFNode, write_field, Condition
from copy import deepcopy

class Start(NFNode):
	def __init__(self):
		super().__init__()
		# 提示不可被交换位置
		self._attributes = {"hardware": True, "will_not_read": set(), "will_not_write": set()}

	def solve_packet(self, packet, states):
		return 0

	def get_cost(self, is_hardware):
		return 0

	def __str__(self):
		return "Start"


class Discard(NFNode):
	def __init__(self):
		super().__init__()
		self._attributes = {"hardware": True, "will_read": set(), "will_write": set()}

	def solve_packet(self, packet, states):
		return -1

	def get_cost(self, is_hardware):
		return 0

	def __str__(self):
		return "Discard"


class DecIpTTL(NFNode):
	def __init__(self, dec_times = 1):
		super().__init__()
		self._attributes = {"hardware": True, "will_read": {("packet", "ip_ttl")}, "will_write": {("packet", "ip_ttl")}}
		self._dec_times = dec_times

	def solve_packet(self, packet, states):
		ip_ttl = packet.read_field("ip_ttl")
		packet.write_field("ip_ttl", ip_ttl - self._dec_times)
		return 0

	def get_cost(self, is_hardware):
		if is_hardware:
			return 1.5
		return 4

	def __str__(self):
		return "DecIpTTL_" + str(self._dec_times)


class BasicClassifier(NFNode):
	# 默认 else 是丢弃
	def __init__(self, conditions = [], children = [Discard()]):
		super().__init__()
		self._children = children
		self._attributes = {"hardware": True, "will_write": set()}
		self.set_conditions(conditions)

	def set_conditions(self, conditions):
		self._conditions = conditions
		self._attributes["will_read"] = set()
		for cond in conditions:
			self._attributes["will_read"] |= cond.get_read_fields()

	def get_conditions(self):
		return deepcopy(self._conditions)

	def solve_packet(self, packet, states):
		for i in range(len(self._conditions)):
			if self._conditions[i].check_with_packet_and_states(packet, states):
				return i
		return len(self._conditions)

	def get_cost(self, is_hardware):
		cost = 0
		for cond in self._conditions:
			cond_cost = cond.get_cost(is_hardware)
			if is_hardware:
				cost = max(cost, cond_cost)
			else:
				# 平均
				cost += cond_cost / 2
		return cost

	def __str__(self):
		return "BasicClassifier"

# 汇集点，实际是一个空的分类器，会被优化掉
class Hub(BasicClassifier):
	def __init__(self):
		super().__init__([], [])
		self._attributes = {"hardware": True, "will_read": set(), "will_write": set()}

	def __str__(self):
		return "Blank"


# "发送" 操作在模拟情形下处理为 "丢弃"，但是不能被任何操作交换位置(需读写所有字段)
class SendOut(NFNode):
	def __init__(self):
		super().__init__()
		self._attributes = {"hardware": True, "will_not_read": set(), "will_not_write": set()}

	def solve_packet(self, packet, states):
		return -1

	def get_cost(self, is_hardware):
		return 0

	def __str__(self):
		return "SendOut"

# 写一个字段
class WriteNF(NFNode):
	def __init__(self, field, value_source):
		super().__init__()
		self._field = field
		self._value_source = value_source
		self._attributes = {"hardware": True, "will_write": {field}}
		self._attributes["will_write"] = value_source.get_read_fields()

	def solve_packet(self, packet, states):
		value = self._value_source.get_value(packet, states)
		write_field(self._field, value, packet, states)
		return 0

	def get_cost(self, is_hardware):
		return 1.5 + value_source.get_cost(is_hardware)

	def __str__(self):
		return "Write\n" + str(self._field[0]) + "_" + str(self._field[1]) + " = " + str(self._value_source)


class EnterHardware(NFNode):
	def __init__(self):
		super().__init__()
		self._attributes = {"hardware": True, "will_read": set(), "will_write": set()}

	def solve_packet(self, packet, states):
		return 0

	def get_cost(self, is_hardware):
		return 0

	def __str__(self):
		return "EnterHardware"


# 多个基础操作组合起来的 NAPT
class NAPT:
	def __init__(self, mapping_info):
		self.entrance = WriteNF(("packet", "ethenet_header"), Condition("const", None))
		self.exit = WriteNF(("packet", "ethenet_header"), Condition("const", "test"))

		# # 丢弃 ip_addr
		# ip_dst = Condition("field", ("packet", "ip_dst"))
		# f = BasicClassifier([Condtion("==", (ip_dst, Condtion("const", self.ip_addr)))])
		# f.set_children(, Discard())

		# info: (ip_dst, port, ip_dst, port)
		conditions, children = [], []
		for info in mapping_info:
			cond1 = Condition("==", (Condition("field", ("packet", "ip_dst")), Condition("const", info[0])))
			cond2 = Condition("==", (Condition("field", ("packet", "tcp_port")), Condition("const", info[1])))
			cond = Condition("and", (cond1, cond2))
			conditions.append(cond)
			child1 = WriteNF(("packet", "ip_dst"), Condition("const", info[2]))
			child2 = WriteNF(("packet", "tcp_port"), Condition("const", info[3]))
			child1.set_children([child2])
			child2.set_children([self.exit])
			children.append(child1)
		children.append(Discard())

		classifier = BasicClassifier(conditions, children)
		self.entrance.set_children([classifier])








from framework import NFNode

class SampleFirewall(NFNode):
	def __init__(self):
		super().__init__()
		# 提示可能需要读所有字段，但不会写任何字段
		self._attributes = {"hardware": False, "will_not_read": set(), "will_write": set()}

	def solve_packet(self, packet, states):
		ip_src = packet.read_field("ip_src")
		if ip_src != "127.0.0.1":
			return 1
		return 0

	def __str__(self):
		return "SampleFirewall"


class SampleLoadBalance(NFNode):
	def __init__(self):
		super().__init__()
		# 提示不会读任何字段，但是会写 ip_dst
		self._attributes = {"hardware": False, "will_read": set(), "will_write": {("packet", "ip_dst")}}

	def solve_packet(self, packet, states):
		ip_dst_list = ["192.168.0.5", "192.168.0.6", "192.168.0.7", "192.168.0.8"]
		from random import choice
		ip_dst = choice(ip_dst_list)
		packet.write_field("ip_dst", ip_dst)
		return 0

	def __str__(self):
		return "SampleLoadBalance"
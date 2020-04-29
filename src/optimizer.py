from framework import Packet, States, Condition, Unknown, AllFields, write_field, set_unknown
from basic_hardware_NFs import *
from copy import deepcopy

################################### 路径拆分
def split_path(root_node):
	node_set = {root_node}
	def DFS(node):
		nonlocal node_set
		new_children = []
		for child in node.get_children():
			if child in node_set:
				child = deepcopy(child)
			node_set.add(child)
			new_children.append(child)
			DFS(child)
		node.set_children(new_children)

	DFS(root_node)


################################### 路径整合
def set_unknown_fields_with_attrs(packet, states, attrs):
	if "will_not_write" in attrs:
		set_unknown(attrs["will_not_write"], packet, states)
	elif "will_write" in attrs:
		for field in attrs["will_write"]:
			write_field(field, Unknown, packet, states)


def handle_classifier(classifier, packet, states):
	classifier.info_after_node = (deepcopy(packet), deepcopy(states))

	i = 0
	# TODO: 关于分支的更新处理，有点麻烦。在 DFS 过程中分支也有权修改或者删除自己，这个需要集中想一想
	# 暂时先每次重新拉取最新的 children
	while i < len(classifier.get_children()):
		packet, states = deepcopy(classifier.info_after_node)
		children = classifier.get_children()
		conditions = classifier.get_conditions()

		children[i].father = classifier
		if i != len(children) - 1:
			# 不是 else 分支
			conditions[i].eliminate_with_packet_and_states(packet, states)
			cond_res = conditions[i].get_value(packet, states)
			if cond_res is Unknown:
				conditions[i].apply_to_packet_and_states(packet, states)
			else:
				# 分支结果确定了
				if cond_res:
					# 该分支恒为 True，删除该分支的条件以及后续分支
					children = children[:i+1]
					conditions = conditions[:i]
				else:
					# 该分支恒为 False，删除该分支，继续处理下一分支
					children = children[:i] + children[i+1:]
					conditions = conditions[:i] + conditions[i+1:]
					classifier.set_children(children)
					classifier.set_conditions(conditions)
					continue

		if len(children) == 1:
			# 只剩下一个分支了
			children[0].father = classifier.father
			classifier.father.set_child_to_another(classifier, children[0]) 
			DFS_for_info(children[0], packet, states)
			return
		# 更新分类器的条件和子节点
		classifier.set_children(children)
		classifier.set_conditions(conditions)
		# 遍历分支
		DFS_for_info(children[i], packet, states)
		i += 1

	# 若该分类器的每一个分支都是 Discard, 删除该分类器，并再次 DFS Discard
	children = classifier.get_children()
	assert(len(children) > 0)
	all_children_are_discard = True
	for child in children:
		if not isinstance(child, Discard):
			all_children_are_discard = False
			break
	if all_children_are_discard:
		child = children[0]
		child.father = classifier.father
		classifier.father.set_child_to_another(classifier, child)
		# TODO: check 一下，下面这一行好像不需要
		packet, states = deepcopy(classifier.info_after_node)
		DFS_for_info(child, packet, states)
		return

	# 若分类器后面几个节点都是 Discard, 将他们合并
	lst_valid_pos = -1
	for i in range(len(children)):
		if not isinstance(children[i], Discard):
			lst_valid_pos = i
	if lst_valid_pos != len(children) - 1:
		children = children[:lst_valid_pos + 2]
		conditions = classifier.get_conditions()[:lst_valid_pos + 1]
		classifier.set_children(children)
		classifier.set_conditions(conditions)


def handle_discard(discard, packet, states):
	def no_such_type_field_in_list(field_type, lst):
		for item in lst:
			if item[0] == field_type:
				return False;
		return True

	discard.set_children([])
	# 直到是分支节点为止，如果当前节点不写 global 状态就删掉
	current = discard
	while current.father and len(current.get_children()) <= 1:
		if current is discard:
			current = current.father
			continue

		can_delete = False
		attrs = current.get_attributes()
		if "will_not_write" in attrs:
			can_delete = ("global", AllFields) in attrs["will_not_write"]
		elif "will_write" in attrs:
			can_delete = no_such_type_field_in_list("global", attrs["will_write"])
		if can_delete:
			assert(len(current.get_children()) == 1)
			child = current.get_children()[0]
			child.father = current.father
			current.father.set_child_to_another(current, child)
		
		current = current.father


# 通过 DFS 找出每个节点前后的状态，同时找出每个节点的父亲节点
def DFS_for_info(node, packet, states):
	print(str(node))
	node.info_before_node = (deepcopy(packet), deepcopy(states))

	if isinstance(node, BasicClassifier):
		return handle_classifier(node, packet, states)
	if isinstance(node, Discard):
		return handle_discard(node, packet, states)

	out_idx = None
	try:
		# out_idx 为包的去向
		out_idx = node.solve_packet(packet, states)
	except Exception as e:
		# 出现 Exception 表示 solve_packet 时试图读取一个 "Unknown" 或者不存在的字段
		set_unknown_fields_with_attrs(packet, states, node.get_attributes())

	node.info_after_node = (deepcopy(packet), deepcopy(states))	

	# 若在预处理期就能确定包的去向，将其他所有分支设为 Discard
	children = node.get_children()

	if out_idx is not None:
		for i in range(len(children)):
			if i != out_idx:
				node.set_child(i, Discard())
		# out_idx 为 -1 表示要把包丢弃
		if out_idx == -1:
			return
		child = children[out_idx]
		child.father = node
		return DFS_for_info(child, packet, states)

	for child in children:
		packet, states = deepcopy(node.info_after_node)
		child.father = node
		DFS_for_info(child, packet, states)


def path_arrange(root_node):
	root_node.father = None
	pseudo_packet, pseudo_states = Packet(), States()
	# 测试属性
	pseudo_packet.write_field("ip_ttl", 10)
	DFS_for_info(root_node, pseudo_packet, pseudo_states)


################################### 判断冲突
# a 在 b 上面
# TODO: 完善下面几个判断
def check_write_conflict(write1, write2):
	return False

def check_read_write_conflict(read, write):
	return False

def are_nodes_conflicted(a, b):
	# 当前俩软件功能之间不支持交换
	# TODO: 完善这个
	if (not a.get_attributes()["hardware"]) and (not b.get_attributes()["hardware"]):
		return True

	read_a, read_b = a.get_read_fields(), b.get_read_fields()
	write_a, write_b = a.get_write_fields(), b.get_write_fields()
	if check_write_conflict(write_a, write_b):
		return True
	if check_read_write_conflict(read_a, write_b) or check_read_write_conflict(read_b, write_a):
		return True
	a_children = a.get_children()
	if len(a_children) > 1:
		# 若 A 存在分支
		# 简化问题: 除 B 所在的分支外全部是 Discard 才能交换
		# TODO: 完善该部分逻辑
		conflict = False
		for child in a_children:
			if (child is not b) and (not isinstance(child, Discard)):
				conflict = True
				break
		if conflict:
			return True

	return False


################################### 硬件前提
# 思路: 每个分支先遍历，遍历完再统一合并，然后再往上提
# TODO: 重构为 DFS 找出硬件分支上提的顺序，然后按照顺序 Solve() 一下。当前的 DFS 方法可能有问题，会在 DFS 过程中修改整个结构。

# 返回是否需要停止 DFS。 
def DFS(node):
	children = node.get_children()
	# DFS 过程中 child 可能会变，但是依然按照原来的 children 顺序遍历即可
	for child in children:
		DFS(child)
	if not isinstance(node, BasicClassifier):
		# 该节点不是硬件分类器，结束
		return

	# 该节点为硬件分类器，尝试合并分支里的硬件分类器，并上提
	old_conditions, old_children = node.get_conditions(), node.get_children()
	new_conditions, new_children = [], []

	for i in range(len(old_children)):
		child  = old_children[i]
		original_condition = None
		if i != len(old_children) - 1:
			original_condition = old_conditions[i]

		if isinstance(child, BasicClassifier):
			# 将下面的分类器里每一个 Condition 用 and 合并进来
			for cond in child.get_conditions():
				if original_condition is not None:
					new_conditions.append(Condition("and", (original_condition, cond)))
				else:
					new_conditions.append(cond)
			if original_condition is not None:
				# 非原 else 分支的话，需要添加对应下面分类器 else 分支的条件
				new_conditions.append(original_condition)

			# 将下面的分类器里每一个 children 加进来
			new_children += child.get_children()
		else:
			# 下面不是硬件分类器，condition 和 children 保持不变
			new_children.append(child)
			if original_condition is not None:
				new_conditions.append(original_condition)

	node.set_conditions(new_conditions)
	node.set_children(new_children)

	# 开始尝试上提
	while (node.father.father is not None) and not are_nodes_conflicted(node.father, node):
		# 当 father 不是 Start，而且 node 和 father 不产生交换冲突，进行上提
		fat = node.father
		old_children = node.get_children()
		if len(fat.get_children()) <= 1:
			# father 没有分支，可以直接往前提
			node.father = fat.father
			node.father.set_child_to_another(fat, node)
			# 将 fat 拷贝多份（清除连接的边，并进行深拷贝），往每个分支放一份
			fat.set_children([])
			fat.father = None
			for child in old_children:
				# 如果 child 是 Discard 就算了，不用下推了
				if isinstance(child, Discard):
					continue
				copy_fat = deepcopy(fat)

				copy_fat.father = node
				node.set_child_to_another(child, copy_fat)

				child.father = copy_fat
				copy_fat.set_children([child])
		else:
			# father 有多个分支，目前当且仅当 father 其他的分支全是 Discard
			# TODO: improve it's logic
			node.father = fat.father
			node.father.set_child_to_another(fat, node)
			# 将 fat 拷贝多份（清除连接 node 的边，并进行深拷贝），往每个分支放一份
			fat.set_child_to_another(node, None)
			fat.father = None
			for child in old_children:
				# 如果 child 是 Discard 就算了，不用下推了
				if isinstance(child, Discard):
					continue
				copy_fat = deepcopy(fat)

				copy_fat.father = node
				node.set_child_to_another(child, copy_fat)

				child.father = copy_fat
				copy_fat.set_child_to_another(None, child)


def hardware_classifier_pull_up(root_node):
	DFS(root_node)

################################### 软件功能顺序调换
# 一遍 DFS 找出每个路径上第一个和最后一个软件功能

# 软件功能不能提到分支前。

first_softwares, last_softwares = set(), set()
software_dfs_stack = []

def DFS2(node):
	if node.get_attributes()["hardware"] == False:
		# 软件功能
		software_dfs_stack.append(node)

	children = node.get_children()
	if len(children) == 0:
		# 叶子节点
		if len(software_dfs_stack) >= 1:
			first = software_dfs_stack[0]
			if first not in first_softwares:
				first_softwares.add(first)
		if len(software_dfs_stack) >= 2:
			last = software_dfs_stack[-1]
			if last not in last_softwares:
				last_softwares.add(last)

	for child in children:
		DFS2(child)

	if node.get_attributes()["hardware"] == False:
		software_dfs_stack.pop()

def push_down(node):
	pass

def pull_up(node):
	is_branch = len(node.get_children()) > 1
	while node.father.father is not None and not are_nodes_conflicted(node.father, node):
		# 软件功能不要提到分支前
		if len(node.father.get_children()) > 1:
			break
		fat = node.father
		node.father = fat.father
		fat.father.set_child_to_another(fat, node)

		if not is_branch:
			child = node.get_children()[0]

			fat.father = node
			node.set_children([fat])

			child.father = fat
			fat.set_children([child])
		else:
			fat.father = None
			fat.set_children([])

			old_children = node.get_children()
			for child in old_children:
				copy_fat = deepcopy(fat)

				copy_fat.father = node
				node.set_child_to_another(child, copy_fat)

				child.father = copy_fat
				copy_fat.set_children([child])

def software_arrange(root_node):
	DFS2(root_node)
	print("push down:")
	for node in first_softwares:
		print(str(node))
		push_down(node)
	print("pull up:")
	for node in last_softwares:
		print(str(node))
		pull_up(node)
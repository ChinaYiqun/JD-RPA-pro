# 研究院提示词
# 用户原始命令为：认真观察'在线咨询'的列表是否存在用户消息，点击第一个用户消息。参考操作步骤为:\n如果列表里面有用户消息，只需要点击第 一个用户，在finished action里面content为'已经点击'。\n\n如果'在线咨询'的列表为空，不存在用户消息，不要做任何操作，在finished action里面content为'无历史消息'
from client import test_plan_action

# SMB 提示词
#
task_prompt = '''
用户原始命令为：认真观察左侧'在线咨询'的列表是否存在用户消息，点击第一个用户消息。参考操作步骤为:
如果列表里面有用户消息，只需要点击第 一个用户。
如果左侧'在线咨询'的下面的无用户消息，返回  "无历史消息"

'''
test_plan_action(r"../assert/hangup_click_frist_message_step_1.png",task_prompt)
test_plan_action(r"../assert/hangup_click_frist_message_step_2.png",task_prompt)

# 研究院提示词
# 用户原始命令为：认真观察'在线咨询'的列表是否存在用户消息，点击第一个用户消息。
# 参考操作步骤为:\n如果列表里面有用户消息，只需要点击第一个用户，在finished action里面content为'已经点击'。
# \n\n如果'在线咨询'的列表为空，不存在用户消息，不要做任何操作，在finished action里面content为'无历史消息'

# 没有用户消息是返回terminate还是answer
from client import test_plan_action

# SMB 提示词
task_prompt = '''
用户原始命令为：认真观察'在线咨询'的列表是否存在用户消息，点击第一个用户消息。
参考操作步骤为:1.如果列表里面有用户消息，只需要点击第一个用户，返回action为'left_click'，coordinate为[x, y]。
2.如果'在线咨询'的列表为空，不存在用户消息，返回action为'answer'，text为'无搜索结果'。
3.判断是否完成任务，如果完成，返回action为'terminate'，status为'success'，否则返回action为'terminate'，status为'failure'。
按照如下格式返回动作： 
<tool_call>
{"name": "computer_use", "arguments": {"action": "left_click", "coordinate": [x, y]}}
</tool_call>
或者
<tool_call>
{"name": "computer_use", "arguments": {"action": "answer", "text": "无搜索结果"}}
</tool_call>
或者
<tool_call>
{"name": "computer_use", "arguments": {"action": "terminate", "status": "success"}}
</tool_call>
'''

test_plan_action(r"../assert/reception_click_first_message_1.png",task_prompt)
# 返回terminate
test_plan_action(r"../assert/reception_click_first_message_success.png",task_prompt)

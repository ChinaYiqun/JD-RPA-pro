# 研究院提示词
# 用户原始命令为：点击搜索框下方第一个搜索到的消息。
# \n参考操作步骤为:\n点击搜索框下方第一个搜索到的消息，如果没有搜索结果在finished action里面content为'无搜索 结果'。
from client import test_plan_action

# SMB 提示词
#
task_prompt = '''
点击搜索框下方第一个搜索到的消息，返回action为'left_click'，coordinate为[x, y]。
如果成功点击搜索到的第一条消息，返回action为'terminate'，status为'success';如果没有搜索结果，返回action为'terminate'，status为'failure'。
按照如下格式返回动作：
<tool_call>
{"name": "computer_use", "arguments": {"action": "left_click", "coordinate": [x, y]}}
</tool_call>
或者
<tool_call>
{"name": "computer_use", "arguments": {"action": "terminate", "status": "success"}}
</tool_call>
'''

test_plan_action(r"../assert/search_first_message_1.png",task_prompt)
# 返回terminate
test_plan_action(r"../assert/search_first_message_noresult.png",task_prompt)


# 研究院提示词
# 用户原始命令为：点击'聊天记录/顾客'搜索栏。\n参考操作步骤为:\n点击界面中间的'聊天记录/顾客'搜索栏，
# 若没有搜索栏，在finished action里面content为'窗口错误'。
from client import test_plan_action

# SMB 提示词
# 
task_prompt = '''
点击界面中的'聊天记录/顾客'搜索栏，返回action为'left_click'，coordinate为[x, y]；若没有搜索栏或者已经完成点击搜索栏，返回action为'terminate'，status为'success'。
按照如下格式返回动作：
<tool_call>
{"name": "computer_use", "arguments": {"action": "left_click", "coordinate": [x, y]}}
</tool_call>
或者
<tool_call>
{"name": "computer_use", "arguments": {"action": "terminate", "status": "success"}}
</tool_call>
'''

test_plan_action(r"../assert/click_search_1.png",task_prompt)
# 返回terminate
test_plan_action(r"../assert/click_search_2.png",task_prompt)


# 研究院提示词
# 用户原始命令为：点击搜索框下方第一个搜索到的消息。
# \n参考操作步骤为:\n点击搜索框下方第一个搜索到的消息，如果没有搜索结果在finished action里面content为'无搜索 结果'。
from client import test_plan_action

# SMB 提示词
#
task_prompt = '''
用户原始命令为：点击搜索框下方第一行选项栏中的'顾客'，点击'顾客'选项栏下方搜索到的第一位顾客的用户名。
参考操作步骤为:
第1步:点击搜索框下方第一行选项栏中的顾客'，
第2步：点击'顾客'选项栏下方搜索到的第一位顾客的用户名。

整体执行成功返回action为'terminate'，status为'success';如果失败 ，返回action为'terminate'，status为'failure'。
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


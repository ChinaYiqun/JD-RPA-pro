from client import test_plan_action

# SMB 提示词
#
task_prompt = '''
请你关注客服聊天软件的左上角，我需要将当前客服的在线状态从挂起状态转为接待状态。
点击当前状态标识‘挂起’打开菜单，在状态调整菜单的三种可能中找到'接待'，点击‘接待’设置新状态。
参考操作步骤为:
第1步:当状态为'挂起'时，点击'挂起'打开状态调整菜单，返回action为'left_click'，coordinate为[x, y]。
第2步:在状态调整菜单的三种可能中找到'接待'，点击带有绿色小圆点的'接待'按钮，，返回action为'left_click'，coordinate为[x, y]。
第3步：判断状态设置是否成功设置为接待状态，返回action为'terminate'，status为'success'。否则返回action为'terminate'，status为'failure'。
按照如下格式返回动作：
<tool_call>
{"name": "computer_use", "arguments": {"action": "left_click", "coordinate": [x, y]}}
</tool_call>
或者
<tool_call>
{"name": "computer_use", "arguments": {"action": "terminate", "status": "success"}}
</tool_call>
'''


test_plan_action(r"../assert/guaqi1.png",task_prompt)
test_plan_action(r"../assert/zhuangtai1.png",task_prompt)
# 返回terminate
test_plan_action(r"../assert/jiedai1.png",task_prompt)

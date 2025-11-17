from client import test_plan_action

# SMB 提示词
#
task_prompt = '''
点击当前状态标识‘接待’打开菜单，在状态调整菜单的三种可能中找到'挂起'，点击‘挂起’设置新状态。
参考操作步骤为:
第1步:当状态为'离线'或'接待'时，点击'离线'或'接待'打开状态调整菜单；返回action为'left_click'，coordinate为[x, y]；
第2步:在状态调整菜单的三种可能中找到'挂起'，必须点击带有红 色小圆点的'挂起'字样；返回action为'left_click'，coordinate为[x, y]；
第3步：判断状态设置是否成功，如果成功返回action为'terminate'，status为'success'，否则返回action为'terminate'，status为'failure'。
按照如下格式返回动作：
<tool_call>
{"name": "computer_use", "arguments": {"action": "left_click", "coordinate": [x, y]}}
</tool_call>
或者
<tool_call>
{"name": "computer_use", "arguments": {"action": "terminate", "status": "success"}}
</tool_call>
'''
test_plan_action(r"../assert/jiedai1.png",task_prompt)
test_plan_action(r"../assert/zhuangtai1.png",task_prompt)
# 返回terminate
test_plan_action(r"../assert/guaqi1.png",task_prompt)
# 用户原始命令为：判断是否有窗口遮挡咚咚界面（如广告、消息通知、消息提醒等），有的话必须点击叉号关闭该弹窗，无叉号时，认真观察，根据窗口信息点击稍后考试，稍后 清理或稍后回复等关闭。

from client import test_plan_action
task_prompt = '''
用户原始命令为：判断是否有窗口遮挡咚咚界面（如广告、消息通知、消息提醒等），有的话必须点击叉号关闭该弹窗，无叉号时，认真观察，根据窗口信息点击稍后考试，稍后 清理或稍后回复等关闭。
如果有这样的窗口返回action为'left_click'，coordinate为[x, y]；
判断是否返回弹出窗口坐标，若成功返回action为'terminate'，status为'success'。否则返回action为'terminate'，status为'failure'。
按照如下格式返回动作：
<tool_call>
{"name": "computer_use", "arguments": {"action": "left_click", "coordinate": [x, y]}}
</tool_call>
或者
<tool_call>
{"name": "computer_use", "arguments": {"action": "terminate", "status": "success"}}
</tool_call>
'''
test_plan_action(r"../assert/pop_up_close.png",task_prompt)
# 返回terminate
test_plan_action(r"../assert/pop_up_close.png",task_prompt)
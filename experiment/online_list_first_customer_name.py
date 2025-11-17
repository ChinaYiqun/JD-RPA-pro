# 用户原始命令为：认真观察在线咨询列表中第一位顾客的名字，在finished action里面content为第一个用户的名称。\n参考操作步骤为:\n第1步:认 真观察在线咨询列表中第一位顾客的名字，在finished action里面content为第一个用户的名称。
from client import test_plan_action
task_prompt = '''
不进行任何操作，返回在线咨询列表中第一位顾客的名字，
返回action为'answer'，text为第一个用户的名称。如果成功返回用户名称，返回action为'terminate'，status为'success'。
格式参考
 <tool_call>
{"name": "computer_use", "arguments": {"action": "answer", "text": "第一个用户的名称"}}
</tool_call>
或者
<tool_call>
{"name": "computer_use", "arguments": {"action": "terminate", "status": "success"}}
</tool_call>
'''
test_plan_action(r"../assert/online_list_first_customer_name.png",task_prompt)
# 返回terminate 
test_plan_action(r"../assert/online_list_first_customer_name.png",task_prompt)
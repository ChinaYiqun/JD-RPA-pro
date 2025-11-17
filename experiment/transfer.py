# "用户原始命令为：将客户转接给指定组，在‘指定咨询组’栏下，双击需要转接的‘兜底咨询组’。\n 参考操作步骤为:\n第1步：点击‘指定咨询组’，第2步：必须找到‘兜底咨询组’  字样，并双击‘兜底咨询组’；\n第3步：完成以上动作后，如果窗口显示‘成功转给其他同事’，任务完成，在finished action里面content为'转接完成'；若显示转接失败，关闭转接窗口，在finished action里面content为'转接失败'。


from client import test_plan_action
task_prompt = '''
用户原始命令为：将客户转接给指定组，在‘指定咨询组’栏下，双击需要转接的‘兜底咨询组’。
参考操作步骤为:
    第1步：点击‘指定咨询组’，
    第2步：必须找到‘兜底咨询组’  字样，并双击‘兜底咨询组’；
    第3步：完成以上动作后，如果窗口显示‘成功转给其他同事’，
    任务完成，在terminate里面status为success;
    若显示转接失败，关闭转接窗口，在terminate里面status为 failure'
'''

test_plan_action(r"../assert/transfer_step_1.png",task_prompt)
test_plan_action(r"../assert/transfer_step_2.png", task_prompt)

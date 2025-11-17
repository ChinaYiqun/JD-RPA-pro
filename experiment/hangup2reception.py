from client import test_plan_action

# SMB 提示词
#
task_prompt = '''
请你关注客服聊天软件的左上角，我需要将当前客服的在线状态从挂机状态转为接待状态。
用户原始命令为：点击当前状态标识‘挂起’打开菜单，在状态调整菜单的三种可能中找到'接待'，点击‘接待’设置新状态，必须设置为带有绿色小圆点的‘接待’。（状态显示位于  店铺头像右侧，店铺名下方，有三种可能'接待'、'离线'、'挂起'）\n
参考操作步骤为:\n
第1步:当状态为'挂起'时，点击'挂起'打开状态调整菜单；\n
第2步:在状态调整菜单的三种可能中找到'接待'，必须点击下带有绿色小圆点的'接待'按钮；\n
第3步：判断状态设置是否成功，只有在店铺名下显示绿色的带打勾号的绿色圆形且文字显示为接待才算完成，完成后在finished action里面content为'状态设置完成'
'''
test_plan_action(r"C:\lenovo\JD-RPA-pro\assert\guaqi1.png",task_prompt)
test_plan_action(r"C:\lenovo\JD-RPA-pro\assert\zhuangtai1.png",task_prompt)
test_plan_action(r"C:\lenovo\JD-RPA-pro\assert\jiedai1.png",task_prompt)

from client import test_plan_action

# SMB 提示词
#
task_prompt = '''
用户原始命令为：点击当前状态标识‘接待’打开菜单，在状态调整菜单的三种可能中找到'挂起'，点击‘挂起’设置新状态，（状态显示位于店铺头像右侧，店铺名下方，有三种可  能'接待'、'离线'、'挂起'）\n
参考操作步骤为:\n
第1步:当状态为'离线'或'接待'时，点击'离线'或'接待'打开状态调整菜单；\n
第2步:在状态调整菜单的三种可能中找到'挂起'，必须点击带有红 色小圆点的'挂起'字样；\n
第3步：判断状态设置是否成功，完成后在finished action里面content为'状态设置完成'
'''
test_plan_action(r"C:\lenovo\JD-RPA-pro\assert\jiedai1.png",task_prompt)
test_plan_action(r"C:\lenovo\JD-RPA-pro\assert\zhuangtai1.png",task_prompt)
test_plan_action(r"C:\lenovo\JD-RPA-pro\assert\guaqi1.png",task_prompt)
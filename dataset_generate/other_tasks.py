tasks_dict = {
        "open_merchant_backend": '''
    请你操作客服工作台，在左侧工具栏中找到并打开“商家后台”。
    用户原始命令为：在左侧工具栏中找到‘工具’选项，点击‘工具’，之后在常用工具中打开‘商家后台’。
    参考操作步骤为:
    第1步: 在左侧垂直工具栏中查找“工具”文字或图标，点击该按钮，返回action为"left_click"，coordinate为[x, y]；
    第2步: 等待常用工具面板展开后，在列表中查找“商家后台”，点击该项，返回action为"left_click"，coordinate为[x, y]；
    第3步: 若成功打开商家后台页面或触发跳转，返回action为"terminate"，status为"success"；若未找到“工具”或“商家后台”，返回action为"terminate"，status为"failure"。
    按照如下格式返回动作：
    <tool_call>
    {"name": "computer_use", "arguments": {"action": "left_click", "coordinate": [x, y]}}
    </tool_call>
    或者
    <tool_call>
    {"name": "computer_use", "arguments": {"action": "terminate", "status": "success"}}
    </tool_call>
    ''',

        "open_data_table": '''
    请你操作客服工作台，在左侧工具栏中找到并打开“数据”文字或图标，查看数据报表，查看完后点击“接待”返回聊天界面。
    用户原始命令为：点击左侧工具栏中的‘数据’图标以查看数据报表。
    参考操作步骤为:
    第1步: 在左侧垂直工具栏中查找“数据”文字或对应的图标，点击该按钮，返回action为"left_click"，coordinate为[x, y]；
    第2步: 等待数据报表页面加载，确认界面显示个人数据、实时数据、日报或月报等内容；
    第3步: 再次在左侧工具栏中查找“接待”文字或带有灰色笑脸的“接待”图标，点击该项以返回聊天主界面，返回action为"left_click"，coordinate为[x, y]；
    第4步: 若成功完成“数据”查看并返回“接待”界面，返回action为"terminate"，status为"success"；若任一环节未找到对应入口（“数据”或“接待”），返回action为"terminate"，status为"failure"。
    按照如下格式返回动作：
    <tool_call>
    {"name": "computer_use", "arguments": {"action": "left_click", "coordinate": [x, y]}}
    </tool_call>
    或者
    <tool_call>
    {"name": "computer_use", "arguments": {"action": "terminate", "status": "success"}}
    </tool_call>
    ''',

        "list_product": '''
    请你操作京东商家后台，在商品列表页中找到“相框”，在商品列表页中点击“上架商品”，完成上架操作后依次点击“确定”、“关闭”按钮，若商品显示“上架中”状态或者操作中出现了下架商品选项的文子或者按钮，代表完成。
    用户原始命令为：将商品“相册”上架。
    参考操作步骤为:
    第1步: 在商品列表页的“操作”列中找到“上架商品”链接，点击该按钮，返回action为"left_click"，coordinate为[x, y]；
    第2步: 弹出确认对话框“确定完成上架吗？”，点击“确定”按钮，返回action为"left_click"，coordinate为[x, y]；
    第3步: 成功弹出“商品操作成功”提示框，点击“关闭”按钮，返回action为"left_click"，coordinate为[x, y]；
    第4步: 若商品显示“上架中”状态或者操作中出现了下架商品选项的文子或者按钮，代表完成，返回action为"terminate"，status为"success"；若任一环节失败（如未找到按钮、跳转异常），返回action为"terminate"，status为"failure"。
    按照如下格式返回动作：
    <tool_call>
    {"name": "computer_use", "arguments": {"action": "left_click", "coordinate": [x, y]}}
    </tool_call>
    或者
    <tool_call>
    {"name": "computer_use", "arguments": {"action": "terminate", "status": "success"}}
    </tool_call>
    ''',

        "delist_product": '''
    请你操作京东商家后台，在商品列表页中找到“相框”，点击“下架商品”按钮，完成下架操作后依次点击“确定”、“关闭”按钮，若商品显示“自主下架”状态或者操作中出现了上架商品选项的文子或者按钮，代表完成。
    用户原始命令为：将商品“相册”下架。
    参考操作步骤为:
    第1步: 在商品列表页的“操作”列中找到“下架商品”链接，点击该按钮，返回action为"left_click"，coordinate为[x, y]；
    第2步: 弹出确认对话框“确定完成下架吗？”，点击“确定”按钮，返回action为"left_click"，coordinate为[x, y]；
    第3步: 成功弹出“商品操作成功”提示框，点击“关闭”按钮，返回action为"left_click"，coordinate为[x, y]；
    第4步: 返回主页面后，若商品显示“自主下架”状态或者操作中出现了上架商品选项的文子或者按钮，代表完成，返回action为"terminate"，status为"success"；若任一环节失败（如未找到按钮、跳转异常），返回action为"terminate"，status为"failure"。
    按照如下格式返回动作：
    <tool_call>
    {"name": "computer_use", "arguments": {"action": "left_click", "coordinate": [x, y]}}
    </tool_call>
    或者
    <tool_call>
    {"name": "computer_use", "arguments": {"action": "terminate", "status": "success"}}
    </tool_call>
    ''',

        "check_new_message_in_online_consultation": '''
    用户原始命令为：判断左侧在线咨询下面是否有新消息
    如果有这样的窗口返回action为'left_click'，coordinate为[x, y]；
    判断是点击成功，若点击返回action为'terminate'，status为'success'。有任何执行失败返回action为'terminate'，status为'failure'。
    按照如下格式返回动作：
    <tool_call>
    {"name": "computer_use", "arguments": {"action": "left_click", "coordinate": [x, y]}}
    </tool_call>
    或者
    <tool_call>
    {"name": "computer_use", "arguments": {"action": "terminate", "status": "success"}}
    </tool_call>
    ''',

    "click_i_know_right_panel": '''
    用户原始命令为：
    step1 点击右侧优惠券
    step2 点击管理优惠券
    step3 点击界面右侧的“我知道了”
    如果有这样的按钮返回action为'left_click'，coordinate为[x, y]；
    判断是点击成功，若点击返回action为'terminate'，status为'success'。有任何执行失败返回action为'terminate'，status为'failure'。
    按照如下格式返回动作：
    <tool_call>
    {"name": "computer_use", "arguments": {"action": "left_click", "coordinate": [x, y]}}
    </tool_call>
    或者
    <tool_call>
    {"name": "computer_use", "arguments": {"action": "terminate", "status": "success"}}
    </tool_call>
    ''',

    "click_service_order_and_input": '''
    用户原始命令为：Step1 点击界面右侧的服务单，Step 2 再点击请输入服务单编号
    如果有这样的按钮返回action为'left_click'，coordinate为[x, y]；
    判断是点击成功，若点击返回action为'terminate'，status为'success'。有任何执行失败返回action为'terminate'，status为'failure'。
    按照如下格式返回动作：
    <tool_call>
    {"name": "computer_use", "arguments": {"action": "left_click", "coordinate": [x, y]}}
    </tool_call>
    或者
    <tool_call>
    {"name": "computer_use", "arguments": {"action": "terminate", "status": "success"}}
    </tool_call>
    ''',

    "click_phone_and_close_popup": '''
    用户原始命令为：Step1 点击界面中的电话按钮，Step 2 关闭弹窗 Step3 停止任务
    如果有这样的按钮返回action为'left_click'，coordinate为[x, y]；
    判断是点击成功，若点击返回action为'terminate'，status为'success'。有任何执行失败返回action为'terminate'，status为'failure'。
    按照如下格式返回动作：
    <tool_call>
    {"name": "computer_use", "arguments": {"action": "left_click", "coordinate": [x, y]}}
    <tool_call>
    或者
    <tool_call>
    {"name": "computer_use", "arguments": {"action": "terminate", "status": "success"}}
    </tool_call>
    ''',

    "click_clock_and_recent_consultation": '''
    用户原始命令为：Step1 点击界面左上方的时钟按钮，Step 2 点击最近联系人 Step3 停止任务
    如果有这样的按钮返回action为'left_click'，coordinate为[x, y]；
    判断是点击成功，若点击返回action为'terminate'，status为'success'。有任何执行失败返回action为'terminate'，status为'failure'。
    按照如下格式返回动作：
    <tool_call>
    {"name": "computer_use", "arguments": {"action": "left_click", "coordinate": [x, y]}}
    </tool_call>
    或者
    <tool_call>
    {"name": "computer_use", "arguments": {"action": "terminate", "status": "success"}}
    </tool_call>
    ''',

    "toggle_layout_compact_to_normal": '''
    用户原始命令为：Step1 点击界面左紧凑布局，Step 2 点击最近常规布局 Step3 停止任务
    如果有这样的按钮返回action为'left_click'，coordinate为[x, y]；
    判断是点击成功，若点击返回action为'terminate'，status为'success'。有任何执行失败返回action为'terminate'，status为'failure'。
    按照如下格式返回动作：
    <tool_call>
    {"name": "computer_use", "arguments": {"action": "left_click", "coordinate": [x, y]}}
    </tool_call>
    或者
    <tool_call>
    {"name": "computer_use", "arguments": {"action": "terminate", "status": "success"}}
    </tool_call>
    ''',

    "select_enter_to_send_message": '''
    用户原始命令为：Step1 点解界面中的小爱心，Step 2 选择按Enter 发送消息 Step3 停止任务
    如果有这样的按钮返回action为'left_click'，coordinate为[x, y]；
    判断是点击成功，若点击返回action为'terminate'，status为'success'。有任何执行失败返回action为'terminate'，status为'failure'。
    按照如下格式返回动作：
    <tool_call>
    {"name": "computer_use", "arguments": {"action": "left_click", "coordinate": [x, y]}}
    </tool_call>
    或者
    <tool_call>
    {"name": "computer_use", "arguments": {"action": "terminate", "status": "success"}}
    </tool_call>
    ''',

    "click_check_subsidy_and_close": '''
    用户原始命令为：Step1 点击界面右侧的“查询国补资格”，Step 2 关闭弹窗 Step3 停止任务
    如果有这样的按钮返回action为'left_click'，coordinate为[x, y]；
    判断是点击成功，若点击返回action为'terminate'，status为'success'。有任何执行失败返回action为'terminate'，status为'failure'。
    按照如下格式返回动作：
    <tool_call>
    {"name": "computer_use", "arguments": {"action": "left_click", "coordinate": [x, y]}}
    <tool_call>
    或者
    <tool_call>
    {"name": "computer_use", "arguments": {"action": "terminate", "status": "success"}}
    </tool_call>
    ''',

    "open_robot_chat": '''
    用户原始命令为：Step1 点击官方，Step 2 群聊 Step3 停止任务
    如果有这样的按钮返回action为'left_click'，coordinate为[x, y]；
    判断是点击成功，若点击返回action为'terminate'，status为'success'。有任何执行失败返回action为'terminate'，status为'failure'。
    按照如下格式返回动作：
    <tool_call>
    {"name": "computer_use", "arguments": {"action": "left_click", "coordinate": [x, y]}}
    <tool_call>
    或者
    <tool_call>
    {"name": "computer_use", "arguments": {"action": "terminate", "status": "success"}}
    </tool_call>
    '''
}
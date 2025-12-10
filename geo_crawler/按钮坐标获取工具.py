import cv2
import pyautogui
# 假设这是你的原始图片和缩放比例
original_img = cv2.imread(r'C:\Users\zhaoz\Desktop\JD-RPA-pro\geo_crawler\c.jpg')  # 替换为你的图片路径
scale = 0.55  # 缩放比例，根据你提供的信息设置

# 根据缩放比例调整显示尺寸
display_img = cv2.resize(original_img, (int(original_img.shape[1] * scale), int(original_img.shape[0] * scale)))

clicked_coords = None  # 用于存储点击位置的坐标


def callback_wrapper(event, x_disp, y_disp, flags, param):
    global clicked_coords
    if event == cv2.EVENT_LBUTTONDOWN:
        # 将显示坐标转换回原始图像坐标
        x_orig = int(x_disp / scale)
        y_orig = int(y_disp / scale)  # 计算原始图像中的y坐标
        clicked_coords = (x_orig, y_orig)
        print(f"原始图片点击位置: ({x_orig}, {y_orig})")
        SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()  # 获取当前屏幕分辨率
        print(f"相对位置: ({x_orig/SCREEN_WIDTH}, {y_orig/SCREEN_HEIGHT})")

        # 在 display_img 上画点（用 display 坐标）
        img_disp_copy = display_img.copy()
        cv2.circle(img_disp_copy, (x_disp, y_disp), 10, (0, 255, 0), 3)
        cv2.imshow("Click on Image", img_disp_copy)


# 创建窗口并绑定回调函数
cv2.namedWindow('Click on Image')
cv2.setMouseCallback('Click on Image', callback_wrapper)

while True:
    cv2.imshow("Click on Image", display_img)
    key = cv2.waitKey(1) & 0xFF
    if key == 27 or key == ord('q'):  # 按下 ESC 或 q 键退出
        break

cv2.destroyAllWindows()
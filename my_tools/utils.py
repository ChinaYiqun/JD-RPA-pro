import os
import shutil


def clear(task_dir):
    """
    清空指定目录中的所有文件和子目录。
    如果目录不存在，则自动创建该目录。
    """
    # 如果目录不存在，先创建它
    if not os.path.exists(task_dir):
        os.makedirs(task_dir)
        return  # 目录是新建的，无需清理

    # 如果存在，则清空内容
    for file in os.listdir(task_dir):
        file_path = os.path.join(task_dir, file)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            # 可选：记录或打印错误，避免一个文件失败导致整个函数崩溃
            print(f"Warning: Failed to delete {file_path}: {e}")
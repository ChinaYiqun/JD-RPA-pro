import logging


def setup_logger(name=None):
    """
    配置并返回一个logger实例，确保日志能正常输出到控制台和文件
    兼容Python 2语法
    """
    # 获取logger实例（避免使用root logger，减少冲突）
    logger_name = name or __name__
    logger = logging.getLogger(logger_name)

    # 避免重复添加handler（多次调用时防止日志重复输出）
    if logger.handlers:
        return logger

    # 设置日志级别（DEBUG级别最低，确保所有级别日志都能被捕获）
    logger.setLevel(logging.DEBUG)

    # 定义日志格式（包含时间、logger名称、级别、消息）
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    # 配置控制台输出handler（StreamHandler）
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)  # 控制台输出所有级别日志
    stream_handler.setFormatter(formatter)  # 应用格式

    # 配置文件输出handler（FileHandler，兼容Python 2，不使用encoding参数）
    file_handler = logging.FileHandler('app.log', encoding='utf-8')
    file_handler.setLevel(logging.INFO)  # 文件只记录INFO及以上级别
    file_handler.setFormatter(formatter)  # 应用格式

    # 将handler添加到logger
    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)

    return logger


# 测试代码
if __name__ == '__main__':
    # 获取配置好的logger
    logger = setup_logger()

    # 输出不同级别的日志（验证是否正常打印）
    logger.debug('这是DEBUG级日志（仅控制台显示）')
    logger.info('这是INFO级日志（控制台和文件都显示）')
    logger.warning('这是WARNING级日志')
    logger.error('这是ERROR级日志')
    logger.critical('这是CRITICAL级日志')
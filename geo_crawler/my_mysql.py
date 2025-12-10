import pymysql
from pymysql.err import OperationalError, ProgrammingError, InterfaceError


def create_collections_table(cursor, conn):
    """
    独立的collections表创建函数（存在则删除原表后重建）
    :param cursor: 数据库游标对象
    :param conn: 数据库连接对象
    """
    # 1. 检查表是否存在
    check_table_sql = """
        SELECT COUNT(*) 
        FROM information_schema.TABLES 
        WHERE TABLE_SCHEMA = DATABASE() 
          AND TABLE_NAME = 'collections'
    """
    cursor.execute(check_table_sql)
    table_exists = cursor.fetchone()[0] > 0

    # 2. 存在则删除原表（注意：会丢失所有数据！）
    if table_exists:
        print("  检测到collections表已存在，即将删除原表并重建（数据会全部丢失）！")
        drop_table_sql = "DROP TABLE IF EXISTS collections"
        cursor.execute(drop_table_sql)
        conn.commit()
        print(" 原collections表已删除")

    # 3. 新建collections表（严格匹配字段结构）
    create_table_sql = """
        CREATE TABLE collections (
            id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '唯一自增ID，主键',
            query_id BIGINT NOT NULL COMMENT '关联问句ID（外键，指向queries表）',
            query_text LONGTEXT NOT NULL COMMENT '问句文本',
            platform ENUM('Grok', 'ChatGPT', 'Claude', 'Gemini', 'Perplexity', 'Doubao','Copilot', 'Other') NOT NULL COMMENT 'AI平台来源',
            content LONGTEXT NOT NULL COMMENT '原始模型回复内容（完整文本，包括HTML标签或Markdown）',
            clean_text TEXT NOT NULL COMMENT '清理后的纯文本（去除HTML标签、提取核心内容，便于NLP分析）',
            content_analysis JSON NOT NULL COMMENT '回复内容分析结果，结构化JSON',
            annotation_analysis JSON NOT NULL COMMENT '对引用/注解内容进行结构化分析，数组形式',
            annotations JSON NOT NULL COMMENT '引用/注解数组（从AI搜索中获得的回复引用）',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL COMMENT '采集/存储时间（UTC标准化）',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NOT NULL COMMENT '最后更新时间'
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI回复内容采集表';
    """
    cursor.execute(create_table_sql)
    conn.commit()
    print(" collections表重建成功！")

    # 4. 验证表结构
    cursor.execute("DESC collections")
    print("\n 新建的collections表结构：")
    for field in cursor.fetchall():
        print(f"   {field[0]}: {field[1]} ")


def insert_sample_data(cursor, conn):
    """
    插入样例数据到collections表
    :param cursor: 数据库游标对象
    :param conn: 数据库连接对象
    """
    # 样例数据准备（JSON字段需转为合法JSON字符串，暂未填充的字段设为基础JSON结构）
    sample_data = {
        "query_id": 0,
        "query_text": "最近5000以内的笔记本电脑梯队咋样，哪款性价比最稳？",
        "platform": "Grok",
        "content": "5000元以内的笔记本市场可以清晰地分为四个梯队，第一梯队是综合性能与品控双优的机型，比如联想小新Pro14锐龙版，搭载AMD 7840HS处理器，2.8K 120Hz屏幕，续航表现优秀；第二梯队是偏向性价比的高配置机型，如红米Book Pro15，屏幕素质突出但散热中规中矩；第三梯队是入门级办公本，满足基础文档处理；第四梯队是小众品牌机型，价格极低但品控风险较高。整体来看，联想小新Pro14锐龙版在5000元内性价比最稳，兼顾性能、屏幕和售后。",
        "clean_text": "",  # 暂时不填充，使用空字符串
        "content_analysis": "{}",  # 空JSON对象（符合JSON字段要求）
        "annotation_analysis": "[]",  # 空JSON数组（符合JSON字段要求）
        "annotations": '[{"url":"https://m.sohu.com/a/962298392_121830331/"}]'  # 注解数据JSON数组
    }

    # 插入SQL（created_at/updated_at使用默认值CURRENT_TIMESTAMP）
    insert_sql = """
        INSERT INTO collections (
            query_id, query_text, platform, content, 
            clean_text, content_analysis, annotation_analysis, annotations
        ) VALUES (
            %(query_id)s, %(query_text)s, %(platform)s, %(content)s,
            %(clean_text)s, %(content_analysis)s, %(annotation_analysis)s, %(annotations)s
        )
    """

    try:
        # 执行插入操作
        cursor.execute(insert_sql, sample_data)
        conn.commit()
        print("\n 样例数据插入成功！")

        # 验证插入结果（查询刚插入的数据）
        cursor.execute("""
            SELECT id, query_id, query_text, platform, created_at, annotations 
            FROM collections 
            WHERE query_id = %(query_id)s
        """, {"query_id": sample_data["query_id"]})

        inserted_data = cursor.fetchone()
        if inserted_data:
            print(f"\n 插入数据验证：")
            print(f"   自增ID：{inserted_data[0]}")
            print(f"   问句ID：{inserted_data[1]}")
            print(f"   问句文本：{inserted_data[2][:50]}...")  # 截断长文本便于展示
            print(f"   平台：{inserted_data[3]}")
            print(f"   创建时间：{inserted_data[4]}")
            print(f"   注解数据：{inserted_data[5]}")

    except Exception as e:
        conn.rollback()  # 插入失败回滚事务
        print(f"\n 样例数据插入失败：{e}")


def connect_mysql_and_manage_table():
    """
    主函数：连接数据库 + 建表 + 插入样例数据
    返回：数据库连接对象（成功）/ None（失败）
    """
    # 数据库连接配置
    db_config = {
        "host": "124.223.85.176",
        "port": 3306,
        "user": "smb",
        "password": "lenovo@123",
        "database": "mydatabase",
        "charset": "utf8mb4",
        "connect_timeout": 10
    }

    conn = None
    cursor = None  # 单独声明游标变量，避免finally中引用未定义的变量
    try:
        # 建立数据库连接
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()
        print(" 数据库连接成功！")

        # # 1. 创建/重建collections表
        # create_collections_table(cursor, conn)
        #
        # # 2. 插入样例数据
        # insert_sample_data(cursor, conn)

        return conn

    except OperationalError as e:
        print(f" 连接失败：{e}")
        print("可能原因：IP/端口错误、用户名/密码错误、数据库不存在、服务器防火墙限制等")
    except ProgrammingError as e:
        print(f" SQL执行/删表/建表错误：{e}")
        print("可能原因：SQL语法错误、JSON类型不兼容（MySQL < 5.7）、用户无删表/建表权限")
    except InterfaceError as e:
        print(f" 数据库接口错误：{e}")
    except Exception as e:
        print(f" 未知错误：{e}")
    finally:
        # 关闭游标（连接返回给调用方）
        if cursor:
            try:
                cursor.close()
            except Exception as e:
                print(f"关闭游标失败：{e}")
    return None


if __name__ == "__main__":
    # 执行主逻辑
    db_conn = connect_mysql_and_manage_table()

    # 业务操作完成后关闭连接
    if db_conn:
        try:
            db_conn.close()
            print("\n🔌 数据库连接已关闭")
        except Exception as e:
            print(f"关闭连接失败：{e}")
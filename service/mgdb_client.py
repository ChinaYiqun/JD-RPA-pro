import os
import sys
import datetime
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
from configs import mongodb_config


class MongoDBClient:
    def __init__(self, host=mongodb_config.IP, port=mongodb_config.PORT, db_name='rpa_db',
                 collection_name='task_history'):
        """初始化MongoDB连接"""
        try:
            self.client = MongoClient(host, port, serverSelectionTimeoutMS=5000)
            self.client.admin.command('ping')  # 验证连接
            self.db = self.client[db_name]
            self.collection = self.db[collection_name]
            # 检查并创建tid字段的索引（如果不存在）
            self.collection.create_index("tid", background=True)  # background=True 表示后台创建，不阻塞其他操作
            print(f"✅ 成功连接到MongoDB: {host}:{port}/{db_name}.{collection_name}")
        except ConnectionFailure:
            print(f"❌ MongoDB连接失败: {host}:{port}")
            raise  # 抛出异常以便上层处理

    def get_history(self, tid):
        """获取指定任务ID的历史记录"""
        doc = self.collection.find_one({'tid': tid})
        return doc.get('history', []) if doc else []

    def save_history(self, tid, history):
        """保存/更新任务历史记录"""
        self.collection.update_one(
            {'tid': tid},
            {'$set': {
                'history': history,
                'updated_at': datetime.datetime.now()
            }},
            upsert=True
        )

    def clear_history(self, tid):
        """删除指定任务ID的历史记录"""
        result = self.collection.delete_one({'tid': tid})
        print(f"🗑️ 已删除任务ID {tid} 的历史记录，共删除 {result.deleted_count} 条记录")
        return result.deleted_count > 0  # 返回是否成功删除（True表示存在并删除，False表示不存在）

    def clear_all_history(self):
        """删除集合中所有任务历史记录"""
        result = self.collection.delete_many({})  # 删除所有文档
        print(f"🗑️ 已清空所有任务历史记录，共删除 {result.deleted_count} 条记录")
        return result.deleted_count  # 返回删除的记录数

    def clear_tmp_history(self):
        """删除前缀为'tmp__'的临时任务历史记录"""
        # 使用正则表达式匹配tid以"tmp__"开头的文档
        result = self.collection.delete_many({"tid": {"$regex": "^tmp__"}})
        print(f"🗑️ 已清空tmp前缀临时记录，共删除 {result.deleted_count} 条记录")
        return result.deleted_count  # 返回删除的记录数

    # 根据前缀名查询所有历史记录
    def query_history_by_prefix(self, prefix):
        """查询所有tid以指定前缀开头的历史记录"""
        cursor = self.collection.find({"tid": {"$regex": f"^{prefix}"}})
        # 返回一个dict ,key 为tid ，value 为  doc.get('history', []) 的值
        return {doc['tid']: doc.get('history', []) for doc in cursor}

    def get_document_count(self):
        """获取集合中所有文档的总数"""
        return self.collection.count_documents({})

    def get_total_data_size_mb(self):
        """获取集合中所有文档的总数据大小（MB）"""
        # 获取集合统计信息
        stats = self.db.command("collstats", self.collection.name)
        # 提取文档数据总大小（字节），默认为0
        data_size_bytes = stats.get("size", 0)
        # 转换为MB（1MB = 1024*1024字节）并保留两位小数
        data_size_mb = round(data_size_bytes / (1024 * 1024), 2)
        return data_size_mb

    # todo ttl 过期机制


    # todo 使用定时任务（Cron + Python）定期查询过期数据/ 同步到hdfs中持久化

if __name__ == '__main__':
    mg = MongoDBClient()
    print(mg.get_document_count())
    print(mg.get_total_data_size_mb())

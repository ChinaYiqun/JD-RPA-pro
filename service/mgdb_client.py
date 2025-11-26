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
                'updated_at': datetime.datetime.now(),
                'expire_at': datetime.datetime.now() + datetime.timedelta(hours=72)
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
        result = self.collection.delete_many({"tid": {"$regex": "^tmp"}})
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

    def migrate_collection(self, new_collection_name, copy_indexes=True, verify_migration=True):
        """
        将当前集合（默认task_history）的数据迁移到新集合

        参数:
            new_collection_name: 新集合名称（字符串）
            copy_indexes: 是否复制原集合的索引到新集合（默认True）
            verify_migration: 是否验证迁移结果（默认True）

        返回:
            dict: 迁移结果，包含原集合名、新集合名、迁移文档数、验证结果（如果开启）
        """
        # 1. 检查新集合是否存在，不存在则创建（MongoDB会自动创建，此处仅打印提示）
        if new_collection_name not in self.db.list_collection_names():
            print(f"📁 新集合 '{new_collection_name}' 不存在，将自动创建")
        else:
            print(f"📁 新集合 '{new_collection_name}' 已存在，数据将追加（如需覆盖请先手动删除）")

        # 2. 迁移数据：使用聚合管道的$out操作（原子性强，效率高）
        try:
            print(f"🚀 开始迁移数据：从 '{self.collection.name}' 到 '{new_collection_name}'")
            # $out会自动创建新集合，若已存在则追加数据
            migration_result = self.collection.aggregate([
                {"$out": new_collection_name}
            ])
            # 聚合管道无返回结果，需通过计数验证迁移数量
            migrated_count = self.db[new_collection_name].count_documents({})
            print(f"✅ 数据迁移完成，新集合共 {migrated_count} 条文档")

        except Exception as e:
            print(f"❌ 数据迁移失败：{str(e)}")
            raise

        # 3. 复制索引（如需保留原索引结构）
        if copy_indexes:
            print(f"🔍 开始复制原集合 '{self.collection.name}' 的索引到新集合")
            try:
                # 获取原集合的所有索引（排除默认的_id索引，MongoDB会自动为新集合创建）
                indexes = self.collection.index_information()
                index_count = 0
                for idx_name, idx_info in indexes.items():
                    if idx_name == '_id_':  # 跳过默认_id索引
                        continue
                    # 复制索引（保留原索引参数，如background、unique等）
                    self.db[new_collection_name].create_index(
                        idx_info['key'],
                        name=idx_name,
                        background=idx_info.get('background', False),
                        unique=idx_info.get('unique', False),
                        sparse=idx_info.get('sparse', False)
                    )
                    index_count += 1
                print(f"✅ 索引复制完成，共复制 {index_count} 个索引")
            except Exception as e:
                print(f"⚠️  索引复制失败：{str(e)}，但数据迁移已完成")

        # 4. 验证迁移结果（可选）
        verification_result = True
        if verify_migration:
            print(f"🔧 开始验证迁移结果")
            original_count = self.collection.count_documents({})
            new_count = self.db[new_collection_name].count_documents({})
            # 验证迁移数量是否匹配（若新集合原有数据，此处会不相等，属于正常情况）
            if original_count == new_count:
                print(f"✅ 迁移验证通过：原集合 {original_count} 条，新集合 {new_count} 条（数量完全匹配）")
            else:
                print(
                    f"⚠️  迁移验证警告：原集合 {original_count} 条，新集合 {new_count} 条（数量不匹配，可能新集合原有数据）")
                verification_result = False

        # 5. 删除原集合数据（迁移完成后清空）
        try:
            print(f"🗑️ 开始删除原集合 '{self.collection.name}' 的数据")
            delete_result = self.collection.delete_many({})
            print(f"✅ 原集合数据删除完成，共删除 {delete_result.deleted_count} 条文档")
        except Exception as e:
            print(f"❌ 原集合数据删除失败：{str(e)}，请手动清理")
            raise

        # 6. 返回迁移结果
        return {
            "original_collection": self.collection.name,
            "new_collection": new_collection_name,
            "migrated_document_count": migrated_count,
            "indexes_copied": copy_indexes,
            "verification_passed": verification_result
        }


if __name__ == '__main__':
    mg = MongoDBClient()
    print(mg.get_document_count())
    print(mg.get_total_data_size_mb())

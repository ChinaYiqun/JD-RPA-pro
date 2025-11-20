import os
import shutil
import sys



current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
from service.mgdb_client import MongoDBClient

client = MongoDBClient()
history_sample = client.get_history("default_task_")
print(history_sample)
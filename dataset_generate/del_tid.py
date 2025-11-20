import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
from service.mgdb_client import MongoDBClient
target_phase = "select_enter_to_send_message"
MongoDBClient().clear_history(tid=f"yq_{target_phase}")

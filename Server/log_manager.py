# import json
# from datetime import datetime
# class LogManager:
#     def __init__(self, filename):
#         self.filename = filename
#     def add_log(self, message, user_id, log_type):
#         log_entry = {
#             "timestamp": datetime.now().isoformat(),
#             "message": message,
#             "user_id": user_id,
#             "type": log_type
#         }
#
#         try:
#             with open(self.filename, 'r+') as file:
#                 logs = json.load(file)
#                 logs.append(log_entry)
#                 file.seek(0)
#                 json.dump(logs, file, indent=2)
#         except FileNotFoundError:
#             with open(self.filename, 'w') as file:
#                 json.dump([log_entry], file, indent=2)
#
#     def get_logs(self, start_date=None, end_date=None):
#         with open(self.filename, 'r') as file:
#             logs = json.load(file)
#
#         if start_date and end_date:
#             return [log for log in logs if start_date <= log['timestamp'] <= end_date]
#         return logs
#
#     def analyze_logs(self, analysis_type, start_date=None, end_date=None):
#         logs = self.get_logs(start_date, end_date)
#
#         if analysis_type == 'user_activity':
#             user_activity = {}
#             for log in logs:
#                 user_id = log['user_id']
#                 user_activity[user_id] = user_activity.get(user_id, 0) + 1
#             return {"user_activity": user_activity}
#
#         elif analysis_type == 'log_types':
#             log_types = {}
#             for log in logs:
#                 log_type = log['type']
#                 log_types[log_type] = log_types.get(log_type, 0) + 1
#             return {"log_types": log_types}
#
#         else:
#             return {
#                 "total_logs": len(logs),
#                 "date_range": {
#                     "start": logs[0]['timestamp'] if logs else None,
#                     "end": logs[-1]['timestamp'] if logs else None
#                 }
#             }
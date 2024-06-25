import uuid
from flask import Flask, request, jsonify
import json
from datetime import datetime

app = Flask(__name__)
class JSONDatabase:
    def __init__(self, filename):
        self.filename = filename

    def load_data(self):
        with open(self.filename, 'r') as f:
            return json.load(f)

    def save_data(self, data):
        with open(self.filename, 'w') as f:
            json.dump(data, f, indent=2)

class LogManager:
    def __init__(self, filename):
        self.filename = filename

    def get_the_logs(self):
        with open(self.filename, 'r') as file:
            logs = json.load(file)
        return logs

    def analyze_logs(self, analysis_type, start_date=None, end_date=None):
        logs = self.get_logs(start_date, end_date)

        if analysis_type == 'user_activity':
            user_activity = {}
            for log in logs:
                user_id = log['user_id']
                user_activity[user_id] = user_activity.get(user_id, 0) + 1
            return {"user_activity": user_activity}

        elif analysis_type == 'log_types':
            log_types = {}
            for log in logs:
                log_type = log['type']  # Assuming 'type' field in logs
                log_types[log_type] = log_types.get(log_type, 0) + 1
            return {"log_types": log_types}

        else:
            return {
                "total_logs": len(logs),
                "date_range": {
                    "start": logs[0]['timestamp'] if logs else None,
                    "end": logs[-1]['timestamp'] if logs else None
                }
            }

    def add_log(self, level, component, message, user_id):
        log_entry = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "level": level,  # INFO, ERROR, etc.
            "component": component,
            "message": message,
            "user_id": user_id
        }

        with open(self.filename, 'r+') as file:
            logs = json.load(file)
            logs.append(log_entry)
            file.seek(0)
            json.dump(logs, file, indent=2)

        return log_entry

log_manager = LogManager('logs.json')
db = JSONDatabase('db.json')



def get_user_by_username(username):
    data = db.load_data()
    for user in data['users']:
        if user['username'].casefold() == username.casefold():
            return user
    return None


def get_asset_by_name(assetname):
    data = db.load_data()
    return next((asset for asset in data['assets'] if asset['name'].casefold() == assetname.casefold()), None)


@app.route("/")
def home():
    return "Welcome to the API"


@app.route("/api")
def api_home():
    return "API Home"


@app.route('/api/login', methods=['POST'])
def login():
    print("Hello")
    data = request.get_json()
    username = data.get('username').strip()
    password = data.get('password').strip()
    user = get_user_by_username(username)
    print(user)
    if user and user['password'] == password:
        log_manager.add_log('INFO', 'authentication', f"User {user['id']} logged in", user['id'])
        return jsonify({"message": f"{user['role'].capitalize()} logged in successfully", "user_id": user['id'],
                        "role": user['role']}), 200
    else:
        log_manager.add_log('WARNING', 'authentication', f"Failed login attempt for username: {username}", None)
        return jsonify({"message": "Invalid username or password"}), 401


@app.route('/api/employee/search_asset', methods=['POST'])
def search_asset():
    asset_name = request.args.get('asset_name')
    # Search for the asset in your database
    asset = get_asset_by_name(asset_name)
    if asset:
        return jsonify({"asset_id": asset['id']}), 200
    else:
        return jsonify({"message": "Asset not found"}), 404


@app.route('/api/employee/request_asset', methods=['POST'])
def request_asset():
    employee_id = request.args.get('user_id')
    asset_id = request.args.get('asset_id')
    all_data = db.load_data()
    asset = next((a for a in all_data['assets'] if a['id'].casefold() == asset_id.casefold()), None)
    if not asset:
        log_manager.add_log('ERROR', 'asset_management', f"Asset not found: {asset_id}", employee_id)
        return jsonify({"status": "failure", "message": "Asset not found"}), 404

    new_request = {
        "id": f"R{len(all_data['requests']) + 1:03d}",
        "employee_id": employee_id,
        "asset_id": asset_id,
        "status": "pending",
        "type": "request",
        "request_date": datetime.now().isoformat()
    }
    all_data['requests'].append(new_request)
    db.save_data(all_data)

    log_manager.add_log('INFO', 'asset_management', f"Asset request submitted for {asset_id} by {employee_id}",
                        employee_id)
    return jsonify({"status": "success", "message": "Asset request submitted"})


@app.route('/api/employee/release_asset', methods=['POST'])
def release_asset():
    employee_id = request.args.get('user_id')
    asset_id = request.args.get('asset_id')
    all_data = db.load_data()
    asset = next((a for a in all_data['tagged'] if a['asset_id'] == asset_id and a['employee_assigned'] == employee_id),
                 None)
    if not asset:
        log_manager.add_log('ERROR', 'asset_management', f"Asset {asset_id} not found or not assigned to {employee_id}",
                            employee_id)
        return jsonify({"status": "failure", "message": "Asset not found or not assigned to this employee"}), 404

    new_request = {
        "id": f"R{len(all_data['requests']) + 1:03d}",
        "employee_id": employee_id,
        "asset_id": asset_id,
        "status": "pending",
        "type": "release",
        "request_date": datetime.now().isoformat()
    }
    all_data['requests'].append(new_request)
    db.save_data(all_data)

    log_manager.add_log('INFO', 'asset_management', f"Asset {asset_id} released by {employee_id}", employee_id)
    return jsonify({"status": "success", "message": "Asset released"})


@app.route('/api/employee/view_tagged_assets', methods=['GET'])
def view_tagged_assets():
    employee_id = request.args.get('employee_id')
    all_data = db.load_data()
    tagged_assets = [asset for asset in all_data['tagged'] if asset['employee_assigned'] == employee_id]

    log_manager.add_log('INFO', 'asset_management', f"Tagged assets viewed by {employee_id}", employee_id)
    return jsonify(tagged_assets)


@app.route('/api/admin/add_asset', methods=['POST'])
def add_asset():
    data = request.get_json()
    asset_name = data.get('asset_name')
    asset_id = data.get('asset_id')
    admin_id = data.get('admin_id')

    if not asset_name or not asset_id:
        log_manager.add_log('ERROR', 'asset_management', f"Invalid asset details provided by admin {admin_id}",
                            admin_id)
        return jsonify({"message": "Invalid asset details"}), 400

    all_data = db.load_data()
    new_asset = {
        "id": asset_id,
        "name": asset_name,
        "status": "available",
        "assigned_to": None
    }
    all_data['assets'].append(new_asset)
    db.save_data(all_data)

    log_manager.add_log('INFO', 'asset_management', f"Asset {asset_id} added by admin {admin_id}", admin_id)
    return jsonify({"message": f"Asset {asset_name} added successfully"}), 200


@app.route('/api/admin/remove_asset', methods=['POST'])
def remove_asset():
    data = request.get_json()
    asset_id = data.get('asset_id')
    remove_count = int(data.get('remove_count', 1))
    admin_id = data.get('admin_id')

    all_data = db.load_data()
    asset = next((a for a in all_data['assets'] if a['id'] == asset_id), None)

    if not asset:
        log_manager.add_log('ERROR', 'asset_management', f"Asset {asset_id} not found for removal by admin {admin_id}",
                            admin_id)
        return jsonify({"message": "Asset not found"}), 404

    current_count = int(asset['count'])
    if current_count < remove_count:
        log_manager.add_log('ERROR', 'asset_management', f"Insufficient asset count for {asset_id} by admin {admin_id}",
                            admin_id)
        return jsonify({"message": "Insufficient asset count"}), 400

    if current_count == remove_count:
        all_data['assets'] = [a for a in all_data['assets'] if a['id'] != asset_id]
        message = f"Asset {asset['name']} completely removed"
    else:
        asset['count'] = str(current_count - remove_count)
        message = f"Removed {remove_count} of asset {asset['name']}"

    db.save_data(all_data)

    log_manager.add_log('INFO', 'asset_management', f"{message} by admin {admin_id}", admin_id)
    return jsonify({"message": message}), 200


@app.route('/api/admin/add_employee', methods=['POST'])
def add_employee():
    data = request.get_json()
    employee_name = data.get('employee_name')
    employee_id = data.get('employee_id')
    employee_password = data.get('employee_password')
    admin_id = data.get('admin_id')

    if not employee_name or not employee_id or not employee_password:
        log_manager.add_log('ERROR', 'user_management', f"Invalid employee details provided by admin {admin_id}",
                            admin_id)
        return jsonify({"message": "Invalid employee details"}), 400

    all_data = db.load_data()
    if any(u['id'] == employee_id for u in all_data['users']):
        log_manager.add_log('ERROR', 'user_management',
                            f"Employee ID {employee_id} already exists, attempted by admin {admin_id}", admin_id)
        return jsonify({"message": "Employee ID already exists"}), 400

    new_employee = {
        "id": employee_id,
        "name": employee_name,
        "password": employee_password,
        "role": "employee"
    }
    all_data['users'].append(new_employee)
    db.save_data(all_data)

    log_manager.add_log('INFO', 'user_management', f"Employee {employee_id} added by admin {admin_id}", admin_id)
    return jsonify({"message": f"Employee {employee_name} added successfully"}), 200


@app.route('/api/admin/remove_employee', methods=['POST'])
def remove_employee():
    data = request.get_json()
    employee_id = data.get('employee_id')
    admin_id = data.get('admin_id')

    all_data = db.load_data()
    employee = next((u for u in all_data['users'] if u['id'] == employee_id and u['role'] == 'employee'), None)

    if not employee:
        log_manager.add_log('ERROR', 'user_management',
                            f"Employee {employee_id} not found for removal by admin {admin_id}", admin_id)
        return jsonify({"message": "Employee not found"}), 404

    all_data['users'] = [u for u in all_data['users'] if u['id'] != employee_id]
    db.save_data(all_data)

    log_manager.add_log('INFO', 'user_management', f"Employee {employee_id} removed by admin {admin_id}", admin_id)
    return jsonify({"message": f"Employee {employee['name']} removed successfully"}), 200


@app.route('/api/admin/view_requests', methods=['GET'])
def view_requests():
    all_data = db.load_data()
    requests = all_data.get('requests', [])

    # Format the requests for display
    formatted_requests = []
    for req in requests:
        formatted_req = {
            "Request ID": req['id'],
            "Employee ID": req['employee_id'],
            "Asset ID": req['asset_id'],
            "Status": req['status'],
            "Type": req['type'],
            "Request Date": req['request_date']
        }
        formatted_requests.append(formatted_req)

    return jsonify({"requests": formatted_requests})

@app.route('/logs', methods=['GET'])
def get_logs():
    start_date = datetime.strptime((request.args.get('start_date')[0:10]),"%Y-%m-%d")
    end_date = datetime.strptime((request.args.get('end_date')[0:10]),"%Y-%m-%d")
    log_type = request.args.get('log_type')
    logs=log_manager.get_the_logs()
    print(start_date,end_date,log_type)
    print("Hello",logs)
    filtered_logs = [
        log for log in logs if
        (start_date <= datetime.strptime(log['timestamp'][0:10], "%Y-%m-%d") <= end_date) and
        (log_type == 'All' or log_type.casefold() == log['level'].casefold())
    ]
    print("Hi",filtered_logs)
    # Remaining to print filtered logs:
    # Just printed all of the logs
    return jsonify(logs)


@app.route('/analyze_logs', methods=['GET'])
def analyze_logs():
    analysis_type = request.args.get('analysis_type')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    analysis_result = log_manager.analyze_logs(analysis_type, start_date, end_date)
    return jsonify(analysis_result)

if __name__ == '__main__':
    app.run(debug=True)

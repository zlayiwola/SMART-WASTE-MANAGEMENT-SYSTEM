from flask import Flask, jsonify, render_template, request, url_for, flash, redirect
from flask_pymongo import PyMongo
from pymongo import MongoClient
import requests
import os
from datetime import datetime
from urllib.parse import unquote
from bson.objectid import ObjectId, InvalidId
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import User, get_user, create_user



app = Flask(__name__)
# to generate a secret key for security
app.secret_key = os.urandom(24)

# MongoDB configuration
app.config["MONGO_URI"] = "mongodb://localhost:27017/smart_waste_db"
mongo = PyMongo(app)
bins_collection = mongo.db.bins
deleted_bins_collection = mongo.db.deleted_bins

client = MongoClient('mongodb://localhost:27017/')
db = client['smart_bin_db']
reports_collection = db['reports']
users_collection = db['users']

BLYNK_TOKEN = 'nhwFbjB_SAqcHh1SWAdCJTUyvZKeo1v5'
BLYNK_BASE_URL = f'https://blynk.cloud/external/api'

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    user_data = users_collection.find_one({'_id': ObjectId(user_id)})
    if user_data:
        return User(user_data)
    return None

# Initialize database
def init_db():
    # Create an initial admin user
    if not users_collection.find_one({'username': 'admin'}):
        create_user('admin', 'password', 'manager')
        print("Admin user created")

def get_blynk_data(pin):
    url = f'{BLYNK_BASE_URL}/get?token={BLYNK_TOKEN}&pin={pin}'
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from Blynk: {e}")
        return None

def is_blynk_online():
    try:
        response = requests.get(f'{BLYNK_BASE_URL}/isHardwareConnected?token={BLYNK_TOKEN}')
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

# this is the route to the homepage of the blynk admin dashboard
@app.route('/')
def home():
    return render_template('index.html')


# to fetch all the deleted bin data
@app.route('/deleted-bins')
def deleted_bins():
    return render_template('deleted_bins.html')

@app.route('/api/bin-data', methods=['GET'])
def get_bin_data():
    # Check if Raspberry Pi is connected to Blynk
    if not is_blynk_online():
        return jsonify({'status': 'error', 'message': 'Raspberry Pi is not connected to Blynk'}), 503

    try:
        # Fetch data from Blynk only if online
        bin_level = get_blynk_data('V0')
        bin_distance = get_blynk_data('V1')
        latitude = get_blynk_data('V2')
        longitude = get_blynk_data('V3')

        # Check if data was successfully fetched
        if bin_level is None or bin_distance is None or latitude is None or longitude is None:
            return jsonify({'status': 'error', 'message': 'Failed to fetch data from Blynk'}), 500

        # Generate a unique identifier for this bin's data
        timestamp = datetime.utcnow().isoformat()
        unique_id = f"{latitude}-{longitude}-{timestamp}"

        # Check if the data already exists to avoid duplicates
        existing_entry = bins_collection.find_one({'unique_id': unique_id})

        if not existing_entry:
            # Insert new bin data into MongoDB
            bin_data = {
                'unique_id': unique_id,
                'timestamp': timestamp,
                'bin_level': bin_level,
                'bin_distance': bin_distance,
                'latitude': latitude,
                'longitude': longitude,
                'status': 'reported'
            }
            bins_collection.insert_one(bin_data)

        # Return all bin data
        all_data = list(bins_collection.find().sort('timestamp', -1))
        
        # Convert ObjectId to string for JSON serialization
        for data in all_data:
            data['_id'] = str(data['_id'])

        return jsonify(all_data)
    except Exception as e:
        print(f"Error in /api/bin-data: {e}")
        return jsonify({'status': 'error', 'message': 'Internal Server Error'}), 500

@app.route('/api/delete-bin/<bin_id>', methods=['DELETE'])
def delete_bin(bin_id):
    try:
        object_id = ObjectId(bin_id)
    except InvalidId:
        return jsonify({'status': 'error', 'message': 'Invalid bin ID format'}), 400

    bin_data = bins_collection.find_one_and_delete({'_id': object_id})
    if bin_data:
        bin_data['deleted_at'] = datetime.now().isoformat()
        deleted_bins_collection.insert_one(bin_data)
        return jsonify({'status': 'success'}), 200
    else:
        return jsonify({'status': 'error', 'message': 'Bin not found'}), 404

# to update the blynk data status on the dashboard
@app.route('/api/update-bin', methods=['POST'])
def update_bin():
    try:
        data = request.get_json()
        timestamp = data.get('timestamp')
        new_status = data.get('status')

        result = bins_collection.update_one(
            {'timestamp': timestamp},
            {'$set': {'status': new_status}}
        )

        if result.matched_count > 0:
            return jsonify({'status': 'success'}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Bin not found'}), 404
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/deleted-bins-data', methods=['GET'])
def get_deleted_bins_data():
    try:
        deleted_bins = list(deleted_bins_collection.find({}, {'_id': 0}))
        return jsonify(deleted_bins), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# to fetch all the bin data that has been resolved
@app.route('/resolved')
def resolved_bins_page():
    return render_template('resolved.html')

@app.route('/api/resolved-bins', methods=['GET'])
def get_resolved_bins():
    try:
        resolved_bins = list(bins_collection.find({'status': 'resolved'}))
        for bin in resolved_bins:
            bin['_id'] = str(bin['_id'])
        return jsonify(resolved_bins), 200
    except Exception as e:
        print(f"Error fetching resolved bins: {e}")
        return jsonify({'status': 'error', 'message': 'Internal Server Error'}), 500
    
# to fecth all the bin data that is in progress
@app.route('/in-progress')
def in_progress_bins_page():
    return render_template('in_progress.html')

@app.route('/api/in-progress-bins', methods=['GET'])
def get_in_progress_bins():
    try:
        # Fetch all bins with status "inprogress"
        in_progress_bins = list(bins_collection.find({'status': 'inprogress'}))
        
        # Convert ObjectId to string for JSON serialization
        for bin in in_progress_bins:
            bin['_id'] = str(bin['_id'])

        return jsonify(in_progress_bins), 200
    except Exception as e:
        print(f"Error fetching in-progress bins: {e}")
        return jsonify({'status': 'error', 'message': 'Internal Server Error'}), 500

@app.route('/reportedbinhomepage', endpoint='reportedbinhomepage')
@login_required
def reportedbinhomepage():
    reports = list(reports_collection.find({}).sort("timestamp", -1))
    return render_template('reportedbinhomepage.html', bins=[], reports=reports)


# user can report bin problem
@app.route('/report-bin', methods=['GET', 'POST'])
@login_required
def report():
    if request.method == 'POST':
        location = request.form['location']
        problem = request.form['problem']
        timestamp = datetime.now()
        reports_collection.insert_one({
            'location': location,
            'problem': problem,
            'timestamp': timestamp,
            'status': 'Reported',
            'user_id': current_user.id  # Store user ID who reported the problem
        })
        flash('Your problem has been successfully submitted!', 'success')
        return redirect(url_for('reportedbinhomepage'))
    return render_template('report_bin.html')

# Admin dashboard route
@app.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'manager':
        flash('Access denied!', 'danger')
        return redirect(url_for('index'))
    reports = list(reports_collection.find({}).sort("timestamp", -1))
    return render_template('admin.html', reports=reports)

#update the user reported waste
@app.route('/update_status/<report_id>', methods=['POST'])
@login_required
def update_status(report_id):
    if current_user.role != 'manager':
        flash('Access denied!', 'danger')
        return redirect(url_for('index'))
    print(f"Updating status for report ID: {report_id}")  # Debug print
    new_status = request.form['status']
    print(f"New status: {new_status}")  # Debug print

    reports_collection.update_one({'_id': ObjectId(report_id)}, {'$set': {'status': new_status}})
    
    # Notify user about status update
    report = reports_collection.find_one({'_id': ObjectId(report_id)})
    if 'user_id' in report:
        user = users_collection.find_one({'_id': ObjectId(report['user_id'])})
        if user:
            flash(f"User {user['username']} has been notified about the status update to: {new_status}", 'info')
    else:
        flash('No user associated with this report.', 'warning')

    return redirect(url_for('admin_dashboard'))

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = get_user(username)
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('reportedbinhomepage'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html')

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))

# Educative information route
@app.route('/info')
def info():
    return render_template('info.html')

if __name__ == '__main__':
    app.run(debug=True)

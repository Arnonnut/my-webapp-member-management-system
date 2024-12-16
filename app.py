from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os
import pymysql
from datetime import datetime

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = 'your_secret_key'

# Configurations
UPLOAD_FOLDER = 'static/images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Database Configuration
db = pymysql.connect(
    host="localhost",
    user="root",
    password="",
    database="member_system"
)

# Function to calculate age
def calculate_age(dob):
    today = datetime.today()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    return age

# Route: Home Page - Display Members
@app.route('/')
def index():
    query = request.args.get('query', '')
    cursor = db.cursor(pymysql.cursors.DictCursor)

    if query:
        cursor.execute("""
            SELECT * FROM members 
            WHERE first_name LIKE %s OR last_name LIKE %s 
            ORDER BY dob
        """, (f"%{query}%", f"%{query}%"))
    else:
        cursor.execute("SELECT * FROM members ORDER BY dob")

    members = cursor.fetchall()
    for member in members:
        member['age'] = calculate_age(member['dob'])
    return render_template('index.html', members=members, query=query)

# Route: Add New Member
@app.route('/add', methods=['POST'])
def add_member():
    prefix = request.form['prefix']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    dob = request.form['dob']  # รับฟอร์แมต YYYY-MM-DD โดยตรง

    # จัดการไฟล์รูปภาพ
    profile_image = request.files['profile_image']
    if profile_image and profile_image.filename != '':
        filename = secure_filename(profile_image.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        profile_image.save(image_path)
        db_image_path = f"images/{filename}"
    else:
        db_image_path = None

    # เพิ่มข้อมูลสมาชิกลงในฐานข้อมูล
    try:
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO members (prefix, first_name, last_name, dob, profile_image) 
            VALUES (%s, %s, %s, %s, %s)
        """, (prefix, first_name, last_name, dob, db_image_path))
        db.commit()
        flash("Member added successfully!")
    except Exception as e:
        flash(f"Error adding member: {e}")
    return redirect(url_for('index'))

# Route: Delete Member
@app.route('/delete/<int:id>', methods=['POST'])
def delete_member(id):
    try:
        cursor = db.cursor()
        cursor.execute("DELETE FROM members WHERE id = %s", (id,))
        db.commit()
        flash("Member deleted successfully!")
    except Exception as e:
        flash(f"Error deleting member: {e}")
    return redirect(url_for('index'))

# Main Function
if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)
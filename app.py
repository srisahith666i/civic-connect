from flask import Flask, redirect, render_template, request, url_for, session, send_from_directory
import os
import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Bhavya@2006",   
    database="complaint_db"
)

cursor = conn.cursor()

app = Flask(__name__)
app.secret_key = "mysecretkey"  

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/resident')
def resident():
    return render_template('resident.html')

@app.route('/admin')
def admin():
    status = request.args.get('status')

    if status:
        cursor.execute("SELECT * FROM complaints WHERE status=%s", (status,))
    else:
        cursor.execute("""
        SELECT complaints.*, workers.name, workers.phone
        FROM complaints
        LEFT JOIN workers ON complaints.worker_id = workers.id
        """)

    complaints = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM complaints WHERE status='Pending'")
    pending = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM complaints WHERE status='In Progress'")
    in_progress = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM complaints WHERE status='Resolved'")
    resolved = cursor.fetchone()[0]

    return render_template('admin.html', complaints=complaints, pending=pending, in_progress=in_progress, resolved=resolved)

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/complaint')
def complaint():
    return render_template('complaint.html')

@app.route('/uploads/<filename>')
def get_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/submit-complaint', methods=['POST'])
def submit_complaint():
    complaint_type = request.form['type']
    address = request.form.get('address')  # Get address from form, default to empty string if not provided
    date = request.form.get('date')
    phone = session.get('phone') 
    if not phone: # Get phone from session
        return redirect('/')
    days = request.form.get('days')

    image = request.files.get('image')
    filename = image.filename

    filename = None

    if image and image.filename != "":
        filename = image.filename
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    if not address or not date or not days:
        return render_template('complaint.html', error="Please fill all fields!")


    query = """
    INSERT INTO complaints (type, address, date, phone, days, status, image)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    values = (complaint_type, address, date, phone, days, "Pending", filename)

    cursor.execute(query, values)
    conn.commit()

    return redirect(url_for('dashboard'))

@app.route('/register-user', methods=['POST'])
def register_user():
    name = request.form['name']
    age = request.form['age']
    gender = request.form['gender']
    phone = request.form.get('phone')

    if not phone.isdigit() or len(phone) != 10:
        return render_template('login.html', error="Enter valid 10 digit phone number")
    
    email = request.form['email']
    address = request.form['address']
    house_type = request.form['house_type']
    password = request.form['password']


    # 🔥 Insert into DB
    query = """
    INSERT INTO users (name, age, gender, phone, email, address, house_type, password)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    values = (name, age, gender, phone, email, address, house_type, password)

    cursor.execute(query, values)
    conn.commit()

    return redirect('/register?success=1')

@app.route('/delete/<int:id>')
def delete(id):
    query = "DELETE FROM complaints WHERE id=%s"
    cursor.execute(query, (id,))
    conn.commit()

    return redirect('/admin')

@app.route('/update/<int:id>', methods=['POST'])
def update(id):
    status = request.form.get('status')
    worker_id = request.form.get('worker_id')

    if status == "Resolved":
        cursor.execute("""
            UPDATE complaints 
            SET status=%s, worker_id=%s, resolved_at=NOW()
            WHERE id=%s
        """, (status, worker_id, id))
    else:
        cursor.execute("""
            UPDATE complaints 
            SET status=%s, worker_id=%s
            WHERE id=%s
        """, (status, worker_id, id))

    conn.commit()

    return redirect('/admin')

@app.route('/login', methods=['POST'])
def login_user():
    role = request.form['role']
    username = request.form['username']
    password = request.form['password']

    if role == "user":
        if not username.isdigit() or len(username) != 10:
            return render_template('login.html', error="Enter valid 10 digit phone number")

    if role == "user":
        query = "SELECT * FROM users WHERE phone=%s AND password=%s"
        cursor.execute(query, (username, password))
        user = cursor.fetchone()

        if user:
            session['phone'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Invalid user credentials")

    elif role == "admin":
        query = "SELECT * FROM admin WHERE username=%s AND password=%s"
        cursor.execute(query, (username, password))
        admin = cursor.fetchone()

        if admin:
            return redirect(url_for('admin'))
        else:
            return render_template('login.html', error="Invalid admin credentials")

@app.route('/dashboard')
def dashboard():

    phone = session.get('phone')

    if not phone:
        return redirect(url_for('login'))

    # 🔥 Get user details
    cursor.execute("SELECT * FROM users WHERE phone=%s", (phone,))
    user = cursor.fetchone()

    # 🔥 Get complaints
    cursor.execute("SELECT * FROM complaints WHERE phone=%s", (phone,))
    complaints = cursor.fetchall()

    # 🔥 Stats
    cursor.execute("SELECT COUNT(*) FROM complaints WHERE phone=%s", (phone,))
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM complaints WHERE phone=%s AND status='Pending'", (phone,))
    pending = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM complaints WHERE phone=%s AND status='Resolved'", (phone,))
    resolved = cursor.fetchone()[0]

    return render_template(
        'dashboard.html',
        user=user,
        complaints=complaints,
        total=total,
        pending=pending,
        resolved=resolved
    )

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/admin-complaint/<int:id>')
def admin_complaint(id):

    cursor.execute("SELECT * FROM complaints WHERE id=%s", (id,))
    complaint = cursor.fetchone()

    cursor.execute("SELECT * FROM workers")
    workers = cursor.fetchall()

    return render_template(
        'admin_complaint.html',
        complaint=complaint,
        workers=workers
    )

    return render_template('admin_complaint.html', complaint=complaint)

if __name__ == '__main__':
    app.run(debug=True)


from flask import Flask, render_template, request, redirect, url_for, session
import pymysql
import bcrypt

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='',
        database='registration',
        cursorclass=pymysql.cursors.DictCursor
    )

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT todo_id, title, is_done, created_at FROM todos WHERE user_id = %s ORDER BY todo_id DESC",
            (session['user_id'],)
        )
        todos = cursor.fetchall()
    conn.close()
    
    return render_template('todos.html', todos=todos, name=session.get('name'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password').encode('utf-8')
        
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT user_id, name, password_hash FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
        conn.close()
        
        if user and bcrypt.checkpw(password, user['password_hash'].encode('utf-8')):
            session['user_id'] = user['user_id']
            session['name'] = user['name']
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Invalid email or password")
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            return render_template('register.html', error="Passwords do not match")
            
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO users (email, name, password_hash) VALUES (%s, %s, %s)",
                    (email, name, hashed_password)
                )
                conn.commit()
            conn.close()
            
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT user_id, name FROM users WHERE email = %s", (email,))
                user = cursor.fetchone()
            conn.close()
            
            session['user_id'] = user['user_id']
            session['name'] = user['name']
            return redirect(url_for('index'))
            
        except pymysql.err.IntegrityError:
            return render_template('register.html', error="Email Already Exists")
            
    return render_template('register.html')

@app.route('/add_todo', methods=['POST'])
def add_todo():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    title = request.form.get('title')
    if title:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO todos (user_id, title) VALUES (%s, %s)", (session['user_id'], title))
            conn.commit()
        conn.close()
    return redirect(url_for('index'))

@app.route('/update_todo/<int:todo_id>', methods=['POST'])
def update_todo(todo_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    title = request.form.get('title')
    is_done = 1 if request.form.get('is_done') else 0
    
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            "UPDATE todos SET title = %s, is_done = %s WHERE todo_id = %s AND user_id = %s",
            (title, is_done, todo_id, session['user_id'])
        )
        conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete_todo/<int:todo_id>', methods=['POST'])
def delete_todo(todo_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM todos WHERE todo_id = %s AND user_id = %s", (todo_id, session['user_id']))
        conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
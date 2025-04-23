from flask import Flask, render_template, redirect, request, url_for

app = Flask(__name__)


users_db = {}


@app.route('/')
def index():
    return redirect(url_for('login')) 


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        form_type = request.form['form_type'] 
        username = request.form['username']
        password = request.form['password']

        if form_type == 'login':
    
            if username in users_db and users_db[username] == password:
                return redirect('/dashboard')  
            else:
                return "Giriş hatalı! Kullanıcı adı veya şifre yanlış.", 400
        
        elif form_type == 'register':
     
            if username in users_db:
                return "Bu kullanıcı adı zaten var!", 400 
            users_db[username] = password
            return redirect('/dashboard')  

    return render_template('login.html')


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if request.method == 'POST':

        car = request.form['car']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        return render_template('confirmation.html', car=car, start_date=start_date, end_date=end_date)
    return render_template('dashboard.html')


@app.route('/confirmation', methods=['POST'])
def confirmation():
    car = request.form['car']
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    return render_template('confirmation.html', car=car, start_date=start_date, end_date=end_date)


@app.route('/complete', methods=['POST'])
def complete():

    return "Kiralama işleminiz tamamlandı. Teşekkür ederiz!"

if __name__ == '__main__':
    app.run(debug=True)

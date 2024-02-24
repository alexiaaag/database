from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash 
app = Flask(__name__)
from flask import redirect
# Secret key for sessions
app.secret_key = 'your_secret_key'

# MySQL configurations
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '2912'
app.config['MYSQL_DB'] = 'testdb'

mysql = MySQL(app)

@app.route('/home')
def home():
    if 'loggedin' in session:
        return render_template('index.html', username=session['username'])
    return redirect(url_for('login'))

@app.route('/home_admin')
def home_admin():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    query = "SELECT "\
        "c.Nume_Client, "\
        "c.Prenume_Client, "\
        "c.Numar_Telefon, "\
        "c.Adresa_Email, "\
        "comenzi.Adresa_Livrare, "\
        "produse.Nume_Produs, "\
        "comenzi_produse.Cantitate "\
        "FROM  "\
        "clienti c "\
        "JOIN  "\
        "comenzi ON c.Client_ID = comenzi.Client_ID "\
        "JOIN  "\
        "comenzi_produse ON comenzi.Comanda_ID = comenzi_produse.Comanda_ID "\
        "JOIN  "\
        "produse ON comenzi_produse.Produs_ID = produse.Produs_ID "\
        "WHERE  "\
        "comenzi.Status_Comanda = 'In procesare'; "\
    
    try:
        cursor.execute(query)
        home_admin = cursor.fetchall()
        return render_template('index_admin.html', home_admin=home_admin)
    except Exception as e:
        return f'Eroare la interogarea bazei de date: {str(e)}'
    finally:
        cursor.close()

@app.route('/')
def index():
    return render_template('index_select_role.html')

@app.route('/index_select_role', methods=['GET', 'POST'])
def index_select_role():
    if request.method == 'POST':
        role = request.form['role']
        if role == 'client':
            return redirect(url_for('login'))
        elif role == 'admin':
            return redirect(url_for('login_admin'))
    return render_template('index_select_role.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        try:
            cursor.execute('SELECT * FROM login WHERE username = %s AND password = %s', (username, password,))
            account = cursor.fetchone()
            if account:
                session['loggedin'] = True
                session['id'] = account['id']
                session['username'] = account['username']
                formatted_login_date = account['login_date'].strftime('%Y-%m-%d %H:%M:%S')
                session['last_login_date'] = formatted_login_date
                cursor.execute('UPDATE login SET login_date = %s WHERE username = %s', (datetime.now(), username))
                mysql.connection.commit()

                msg = 'Login successful!'
                return redirect(url_for('home'))
            else:
                 msg = 'Login failed. Check your username and password.'
        except Exception as e:
            print('Error executing SQL query:', str(e))
        finally:
            cursor.close()
    return render_template('login.html', msg=msg)

@app.route('/login_admin', methods=['GET', 'POST'])
def login_admin():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        try:
            cursor.execute('SELECT * FROM admin WHERE username = %s AND password = %s', (username, password,))
            account = cursor.fetchone()
            if account:
                session['loggedin'] = True
                session['id'] = account['id']
                session['username'] = account['username']
                mysql.connection.commit()
                msg = 'Login successful!'
                return redirect(url_for('home_admin'))
            else:
                msg = 'Login failed. Check your username and password.'
        except Exception as e:
            print('Error executing SQL query:', str(e))
        finally:
            cursor.close()
    return render_template('login_admin.html', msg=msg)

# Add a logout route if needed
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        try:
            cursor.execute('SELECT * FROM login WHERE username = %s', (username,))
            account = cursor.fetchone()
            if account:
                msg = 'Account already exists!'
            elif not re.match(r'[A-Za-z0-9]+', username):
                msg = 'Username must contain only characters and numbers!'
            elif not username or not password:
                msg = 'Please fill out the form!'
            else:
                cursor.execute('INSERT INTO login (username, password) VALUES (%s, %s)', (username, password))
                mysql.connection.commit()
                msg = 'You have successfully registered!'
        except Exception as e:
            msg = 'Error executing SQL query: {}'.format(str(e))
        finally:
            cursor.close()
    elif request.method == 'POST':
        msg = 'Please fill out the form!'
    return render_template('register.html', msg=msg)


@app.route('/delete_account', methods=['POST'])
def delete_account():
    if 'loggedin' in session:
        option = request.form.get('submit_button')  # Obțineți valoarea butonului apăsat

        if option == 'Yes, Delete My Account':
            # Utilizatorul a confirmat ștergerea contului
            username = session['username']
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            try:
                cursor.execute('DELETE FROM login WHERE username = %s', (username,))
                mysql.connection.commit()
                session.pop('loggedin', None)
                session.pop('id', None)
                session.pop('username', None)
                msg = 'Your account has been deleted successfully.'
                return render_template('login.html', msg=msg)
            except Exception as e:
                msg = 'Error executing SQL query: {}'.format(str(e))
            finally:
                cursor.close()
        elif option == 'No, Cancel':
            # Utilizatorul a anulat ștergerea contului, redirecționați-l la pagina de index
            return redirect(url_for('home'))

    # Dacă nu este o cerere POST sau dacă nu sunteți autentificat, redirecționați către pagina de login
    return redirect(url_for('login'))


@app.route('/confirm_delete_account')
def confirm_delete_account():
    if 'loggedin' in session:
        username = session.get('username')
        return render_template('confirm_delete_account.html', username=username)
    else:
        return redirect(url_for('login'))


# Adaugă această rută pentru afișarea paginii de schimbare a parolei
@app.route('/change_password_page')
def change_password_page():
    if 'loggedin' in session:
        return render_template('change_password.html', username=session['username'])
    else:
        return redirect(url_for('login'))

# Ruta pentru actualizarea parolei în baza de date
@app.route('/change_password', methods=['POST'])
def change_password():
    if 'loggedin' in session:
        if request.method == 'POST':
            current_password = request.form['current_password']
            new_password = request.form['new_password']
            confirm_password = request.form['confirm_password']

            # Verificați dacă parola curentă este corectă
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            try:
                cursor.execute('SELECT * FROM login WHERE username = %s AND password = %s',
                               (session['username'], current_password,))
                account = cursor.fetchone()

                if account:
                    # Verificați dacă parola nouă coincide cu confirmarea parolei
                    if new_password == confirm_password:
                        # Actualizați parola în baza de date
                        cursor.execute('UPDATE login SET password = %s WHERE username = %s',
                                       (new_password, session['username'],))
                        mysql.connection.commit()
                        return render_template('change_password_result.html', success=True)
                    else:
                        return render_template('change_password_result.html', success=False, message='Parola nouă și confirmarea parolei nu coincid.')
                else:
                    return render_template('change_password_result.html', success=False, message='Parola curentă incorectă.')
            except Exception as e:
                return render_template('change_password_result.html', success=False, message='Eroare la execuția interogării SQL: {}'.format(str(e)))
            finally:
                cursor.close()
        else:
            return render_template('change_password_result.html', success=False, message='Metoda incorectă pentru accesarea acestei rute.')
    else:
        return redirect(url_for('login'))

@app.route('/products')
def products():
    # Cod pentru afișarea produselor
    return render_template('products.html')

@app.route('/laptopuri')
def laptopuri():
    # Cod pentru afișarea laptopurilor din baza de date cu JOIN
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    query = "SELECT Nume_Produs , Descriere , Pret , Culoare , Greutate "\
        "FROM produse "\
        "JOIN categorii ON produse.Categorie_ID = categorii.Categorie_ID "\
        "AND categorii.Nume_Categorie = 'Laptopuri' AND produse.Stoc > 0;"
    

    try:
        cursor.execute(query)
        laptopuri = cursor.fetchall()
        return render_template('laptopuri.html', laptopuri=laptopuri)
    except Exception as e:
        return f'Eroare la interogarea bazei de date: {str(e)}'
    finally:
        cursor.close()

@app.route('/tablete')
def tablete():
    # Cod pentru afișarea tabletelor din baza de date cu JOIN
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    query = "SELECT Nume_Produs, Descriere, Pret , Culoare , Greutate "\
        "FROM produse "\
        "JOIN categorii ON produse.Categorie_ID = categorii.Categorie_ID "\
        "AND categorii.Nume_Categorie = 'Tablete' AND produse.Stoc > 0;"
    

    try:
        cursor.execute(query)
        tablete = cursor.fetchall()
        return render_template('tablete.html', tablete=tablete)
    except Exception as e:
        return f'Eroare la interogarea bazei de date: {str(e)}'
    finally:
        cursor.close()

@app.route('/accesorii')
def accesorii():
    # Cod pentru afișarea laptopurilor din baza de date cu JOIN
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    query = "SELECT Nume_Produs, Descriere, Pret , Culoare , Greutate "\
        "FROM produse "\
        "JOIN categorii ON produse.Categorie_ID = categorii.Categorie_ID "\
        "AND categorii.Nume_Categorie = 'Accesorii' AND produse.Stoc > 0;"
    

    try:
        cursor.execute(query)
        accesorii = cursor.fetchall()
        return render_template('accesorii.html', accesorii=accesorii)
    except Exception as e:
        return f'Eroare la interogarea bazei de date: {str(e)}'
    finally:
        cursor.close()

@app.route('/products_admin')
def products_admin():
    # Cod pentru afișarea produselor
    return render_template('products_admin.html')

@app.route('/reviews_admin')
def reviews_admin():
    # Cod pentru afișarea recenziilor
    return render_template('reviews_admin.html')

@app.route('/laptopuri_admin')
def laptopuri_admin():
    # Cod pentru afișarea laptopurilor din baza de date cu JOIN
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    query = "SELECT "\
    "p.Produs_ID, "\
    "p.Nume_Produs, "\
    "p.Stoc, "\
    "p.Localizare_Stoc, "\
    "( "\
    "    SELECT pr.Nume_Producator "\
    "    FROM producator pr "\
    "    WHERE pr.ProducatorID = p.Producator_ID "\
    ") AS Nume_Producator, "\
    "( "\
    "    SELECT pr.Adresa "\
    "    FROM producator pr "\
    "    WHERE pr.ProducatorID = p.Producator_ID "\
    ") AS Adresa, "\
    "( "\
    "    SELECT pr.Numar_Telefon "\
    "    FROM producator pr "\
    "    WHERE pr.ProducatorID = p.Producator_ID "\
    ") AS Numar_Telefon, "\
    "( "\
    "    SELECT pr.Adresa_Email "\
    "    FROM producator pr "\
    "    WHERE pr.ProducatorID = p.Producator_ID "\
    ") AS Adresa_Email "\
    "FROM "\
    "produse p "\
    "WHERE "\
    "p.Categorie_ID = ( "\
    "    SELECT c.Categorie_ID "\
    "    FROM categorii c "\
    "    WHERE c.Nume_Categorie = 'Laptopuri' "\
    ") "\
    "AND p.Stoc > 0; "

    

    try:
        cursor.execute(query)
        laptopuri_admin = cursor.fetchall()
        return render_template('laptopuri_admin.html', laptopuri_admin=laptopuri_admin)
    except Exception as e:
        return f'Eroare la interogarea bazei de date: {str(e)}'
    finally:
        cursor.close()

@app.route('/tablete_admin')
def tablete_admin():
    # Cod pentru afișarea tabletelor din baza de date cu JOIN
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    query = "SELECT "\
    "p.Produs_ID, "\
    "p.Nume_Produs, "\
    "p.Stoc, "\
    "p.Localizare_Stoc, "\
    "( "\
    "    SELECT pr.Nume_Producator "\
    "    FROM producator pr "\
    "    WHERE pr.ProducatorID = p.Producator_ID "\
    ") AS Nume_Producator, "\
    "( "\
    "    SELECT pr.Adresa "\
    "    FROM producator pr "\
    "    WHERE pr.ProducatorID = p.Producator_ID "\
    ") AS Adresa, "\
    "( "\
    "    SELECT pr.Numar_Telefon "\
    "    FROM producator pr "\
    "    WHERE pr.ProducatorID = p.Producator_ID "\
    ") AS Numar_Telefon, "\
    "( "\
    "    SELECT pr.Adresa_Email "\
    "    FROM producator pr "\
    "    WHERE pr.ProducatorID = p.Producator_ID "\
    ") AS Adresa_Email "\
    "FROM "\
    "produse p "\
    "WHERE "\
    "p.Categorie_ID = ( "\
    "    SELECT c.Categorie_ID "\
    "    FROM categorii c "\
    "    WHERE c.Nume_Categorie = 'Tablete' "\
    ") "\
    "AND p.Stoc > 0; "
    

    try:
        cursor.execute(query)
        tablete_admin = cursor.fetchall()
        return render_template('tablete_admin.html', tablete_admin=tablete_admin)
    except Exception as e:
        return f'Eroare la interogarea bazei de date: {str(e)}'
    finally:
        cursor.close()

@app.route('/accesorii_admin')
def accesorii_admin():
    # Cod pentru afișarea accesoriilor din baza de date cu JOIN
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    query ="SELECT "\
    "p.Nume_Produs, "\
    "p.Stoc, "\
    "p.Localizare_Stoc, "\
    "pr.Nume_Producator, "\
    "pr.Adresa, "\
    "pr.Numar_Telefon, "\
    "pr.Adresa_Email "\
    "FROM  "\
    "produse p "\
    "JOIN  "\
    "producator pr ON p.Producator_ID = pr.ProducatorID "\
    "JOIN  "\
    "categorii c ON p.Categorie_ID = c.Categorie_ID "\
    "WHERE  "\
    "c.Nume_Categorie = 'Accesorii' "\
    "AND p.Stoc > 0; "\

    

    try:
        cursor.execute(query)
        accesorii_admin = cursor.fetchall()
        return render_template('accesorii_admin.html', accesorii_admin=accesorii_admin)
    except Exception as e:
        return f'Eroare la interogarea bazei de date: {str(e)}'
    finally:
        cursor.close()

@app.route('/reviews')
def reviews():
    # Cod pentru afișarea laptopurilor din baza de date cu JOIN
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    selected_producer = request.args.get('producator', 'HP')
    query = f"SELECT "\
        "    r.Comentariu, "\
        "    c.Nume_Client, "\
        "    c.Prenume_Client, "\
        "    p.Nume_Produs, "\
        "    p.Pret "\
        "FROM "\
        "    recenzii r "\
        "JOIN "\
        "    clienti c ON r.Client_ID = c.Client_ID "\
        "JOIN "\
        "    produse p ON r.Produs_ID = p.Produs_ID "\
        "JOIN "\
        "    producator pr ON p.Producator_ID = pr.ProducatorID "\
        f"WHERE pr.Nume_Producator = '{selected_producer}' "\
        "ORDER BY "\
        "    p.Pret DESC;"
    try:
        cursor.execute(query)
        reviews = cursor.fetchall()
        return render_template('reviews.html', reviews=reviews)
    except Exception as e:
        return f'Eroare la interogarea bazei de date: {str(e)}'
    finally:
        cursor.close()

@app.route('/vanzari_2023')
def vanzari_2023():
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    query="SELECT "\
    "Nume_Produs, "\
    "( "\
    "    SELECT Nume_Categorie "\
    "    FROM categorii "\
    "    WHERE categorii.Categorie_ID = produse.Categorie_ID "\
    ") AS Nume_Categorie, "\
    "Pret, "\
    " ( "\
    "    SELECT comenzi.Data_Plasarii "\
    "    FROM comenzi "\
    "    WHERE comenzi.Comanda_ID = ( "\
    "        SELECT comenzi_produse.Comanda_ID "\
    "        FROM comenzi_produse "\
    "        WHERE comenzi_produse.Produs_ID = produse.Produs_ID "\
    "    ) "\
    ") AS Data_Plasarii "\
    "    FROM "\
    "    produse "\
    "    WHERE "\
    "    Produs_ID IN ( "\
    "    SELECT "\
    "        Produs_ID "\
    "    FROM "\
    "        comenzi_produse "\
    "    WHERE "\
    "        Comanda_ID IN ( "\
    "            SELECT "\
    "                Comanda_ID "\
    "            FROM "\
    "                comenzi "\
    "            WHERE "\
    "               YEAR(Data_Plasarii) = 2023 "\
    "        ) "\
    ");  "\

    try:
        cursor.execute(query)
        vanzari_2023 = cursor.fetchall()
        return render_template('vanzari_2023.html', vanzari_2023=vanzari_2023)
    except Exception as e:
        return f'Eroare la interogarea bazei de date: {str(e)}'
    finally:
        cursor.close()

@app.route('/vanzari_2024')
def vanzari_2024():
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    query= " SELECT "\
     " (SELECT Nume_Client FROM clienti WHERE Client_ID = (SELECT Client_ID FROM comenzi WHERE Comanda_ID = cp.Comanda_ID)) AS Nume_Client, "\
     " (SELECT Prenume_Client FROM clienti WHERE Client_ID = (SELECT Client_ID FROM comenzi WHERE Comanda_ID = cp.Comanda_ID)) AS Prenume_Client, "\
     " (SELECT Nume_Producator FROM producator WHERE ProducatorID = (SELECT Producator_ID FROM produse WHERE Produs_ID = cp.Produs_ID)) AS Nume_Producator "\
     " FROM "\
     " comenzi_produse cp "\
     " WHERE "\
     " cp.Comanda_ID IN ( "\
        "  SELECT Comanda_ID "\
        "  FROM comenzi "\
         " WHERE Pret_Total > 500 AND Data_Plasarii BETWEEN '2023-12-01' AND '2024-01-31' "\
     " ); "


    try:
        cursor.execute(query)
        vanzari_2024 = cursor.fetchall()
        return render_template('vanzari_2024.html', vanzari_2024=vanzari_2024)
    except Exception as e:
        return f'Eroare la interogarea bazei de date: {str(e)}'
    finally:
        cursor.close()

@app.route('/clienti_fideli')
def clienti_fideli():
  
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    query = " SELECT c.Nume_Client, c.Prenume_Client, SUM(cast(cp.Cantitate as float) * p.Pret) as Total_Comenzi "\
    "FROM clienti c "\
    "JOIN comenzi co ON c.Client_ID = co.Client_ID "\
    "JOIN comenzi_produse cp ON co.Comanda_ID = cp.Comanda_ID "\
    "JOIN produse p ON cp.Produs_ID = p.Produs_ID "\
    "GROUP BY c.Client_ID "\
    "ORDER BY Total_Comenzi DESC; "\
    
    try:
        cursor.execute(query)
        clienti_fideli = cursor.fetchall()
        return render_template('clienti_fideli.html', clienti_fideli=clienti_fideli)
    except Exception as e:
        return f'Eroare la interogarea bazei de date: {str(e)}'
    finally:
        cursor.close()

def get_categories():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute("SELECT Categorie_ID, Nume_Categorie FROM categorii")
        categories = cursor.fetchall()
        return categories
    except Exception as e:
        return f'Eroare la obținerea categoriilor: {str(e)}'
    finally:
        cursor.close()

def get_producers():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute("SELECT ProducatorID, Nume_Producator FROM producator")
        producers = cursor.fetchall()
        return producers
    except Exception as e:
        return f'Eroare la obținerea producătorilor: {str(e)}'
    finally:
        cursor.close()

@app.route('/insert_product', methods=['GET', 'POST'])
def insert_product():
    if request.method == 'POST':
        categorie_id = request.form['categorie_id']
        producator_id = request.form['producator_id']
        nume_produs = request.form['nume_produs']
        descriere = request.form['descriere']
        pret = request.form['pret']
        stoc = request.form['stoc']
        localizare_stoc = request.form['localizare_stoc']
        culoare = request.form['culoare']
        greutate = request.form['greutate']

        try:
            cursor = mysql.connection.cursor()
            query = "INSERT INTO produse (Categorie_ID, Producator_ID, Nume_Produs, Descriere, Pret, Stoc, Localizare_Stoc, Culoare, Greutate) "\
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
            values = (categorie_id, producator_id, nume_produs, descriere, pret, stoc, localizare_stoc, culoare, greutate)
            cursor.execute(query, values)
            mysql.connection.commit()  # Folosiți metoda commit() pe obiectul conexiunii
            return redirect(url_for('insert_product'))
        except Exception as e:
            return f'Eroare la inserarea datelor în baza de date: {str(e)}'
        finally:
            cursor.close()

    return render_template('insert_product.html', categories=get_categories(), producers=get_producers())


from flask import request

@app.route('/scade_stoc/<int:produs_id>', methods=['GET', 'POST'])
def scade_stoc(produs_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Verificați dacă stocul este mai mare decât 0 înainte de actualizare
        cursor.execute("SELECT Stoc FROM produse WHERE Produs_ID = %s", (produs_id,))
        stoc = cursor.fetchone()['Stoc']
        if stoc > 0:
            # Actualizați stocul
            cursor.execute("UPDATE produse SET Stoc = Stoc - 1 WHERE Produs_ID = %s", (produs_id,))
            mysql.connection.commit()
            return redirect(url_for('laptopuri_admin'))
        else:
            flash('Stocul este epuizat.')
            return redirect(url_for('laptopuri_admin'))
    except Exception as e:
        flash(f'Eroare la actualizarea stocului: {str(e)}')
        return redirect(url_for('laptopuri_admin'))
    finally:
        cursor.close()

@app.route('/sterge_produs/<int:produs_id>', methods=['POST'])
def sterge_produs(produs_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute("DELETE FROM produse WHERE Produs_ID = %s", (produs_id,))
        mysql.connection.commit()
        return redirect(url_for('tablete_admin'))
    except Exception as e:
        return f'Eroare la ștergerea produsului: {str(e)}'
    finally:
        cursor.close()
from flask import request

@app.route('/check_order_status', methods=['GET', 'POST'])
def check_order_status():
    if request.method == 'POST':
        numar_telefon = request.form['numar_telefon']
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        query = (
        "SELECT "
        "(SELECT Nume_Client FROM clienti WHERE Numar_Telefon = %s) AS Nume_Client, "
        "(SELECT Prenume_Client FROM clienti WHERE Numar_Telefon = %s) AS Prenume_Client, "
        "co.Status_Comanda, "
        "(SELECT Data_Plasarii FROM comenzi WHERE Comanda_ID = co.Comanda_ID) AS Data_Plasarii "
        "FROM comenzi co "
        "WHERE co.Client_ID = (SELECT Client_ID FROM clienti WHERE Numar_Telefon = %s)"
        )

        try:
            cursor.execute(query, (numar_telefon, numar_telefon, numar_telefon))
            result = cursor.fetchall()
            client_info = {
                'Nume_Client': result[0]['Nume_Client'],
                'Prenume_Client': result[0]['Prenume_Client']
            }
            return render_template('order_status.html', result=result, client_info=client_info )
        except Exception as e:
            return f'Eroare la interogarea bazei de date: {str(e)}'
        finally:
            cursor.close()

    return render_template('order_status.html', result=result, client_info=client_info)

@app.route('/depozite')
def depozite():
  
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    query = """
            SELECT
                pr.Nume_Producator,
                pr.Numar_Telefon,
                pr.Adresa_Email,
                pr.Adresa,
                p.Nume_Produs,
                p.Stoc,
                p.Localizare_Stoc
            FROM
                producator pr
            JOIN
                produse p ON pr.ProducatorID = p.Producator_ID
            JOIN
                categorii c ON p.Categorie_ID = c.Categorie_ID
            WHERE
                p.Stoc > 0
                AND p.Localizare_Stoc = 'Depozit C'
                AND c.Nume_Categorie = 'laptopuri';
        """
    
    try:
        cursor.execute(query)
        depozite = cursor.fetchall()
        return render_template('depozite.html', depozite=depozite)
    except Exception as e:
        return f'Eroare la interogarea bazei de date: {str(e)}'
    finally:
        cursor.close()


if __name__ == "__main__":
    app.run(host="localhost", port=int("5000"))

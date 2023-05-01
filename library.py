from flask import Flask,flash,redirect,render_template,url_for,request,jsonify,abort
from flask_mysqldb import MySQL
from datetime import date
from datetime import datetime
from threading import Thread
from secretconfig import secret_key
from py_mail import mail_sender
import smtplib
import stripe
from email.message import EmailMessage
from otp import genotp
from sdmail import sendmail
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from tokenreset import token
stripe.api_key="sk_test_51Mvx6sSDC3PstyYY7JzUe34lTgv89Lf1lSFsuQmWUYmrtowck13jeONs5HAamjtgkzB3A0984wmezJQTH00ocCnh008nj8bsw9"
app=Flask(__name__)
app.secret_key='*67@ouihfg'
app.config['MYSQL_HOST'] ='localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD']='Admin'
app.config['MYSQL_DB']='library'
mysql=MySQL(app)
def background_task():
    with app.app_context():
        cursor=mysql.connection.cursor()
        cursor.execute("select rent_id,due_date from rent")
        data=cursor.fetchall()
        cursor.close()
        if len(data)!=0:
            for i in data:
                cursor=mysql.connection.cursor()
                today=date.today()
                current_date=datetime.strptime(f'{str(today.day)}-{str(today.month)}-{str(today.year)}','%d-%m-%Y')
                due_date=i[1]
                due_date1=datetime.strptime(f'{str(due_date.day)}-{str(due_date.month)}-{str(due_date.year)}','%d-%m-%Y')
                diff=(current_date-due_date1).days
                if diff>0:
                    per_day=100
                    fine=diff*per_day
                    cursor.execute('update rent set fine=%s where rent_id=%s',[fine,i[0]])
                    mysql.connection.commit()
                    cursor.close()

@app.route('/')
def home():
    return render_template('homepage.html')


@app.route('/adminlogin')
def login():
    return render_template('adminlogin.html')
@app.route('/create',methods=['GET','POST'])
def create():
    cursor=mysql.connection.cursor()
    cursor.execute('SELECT count(*) from admin')
    result=int(cursor.fetchone()[0])
    cursor.close()
    if result>0:
        return render_template('noadmin.html')
    else:
        if request.method=='POST':
            key=request.form['key']
            user=request.form['user']
            password=request.form['password']
            email=request.form['email']
            email='santhoshirowthu@gmail.com'
            otp=genotp()
            subject='Thanks for registering'
            body = 'your one time password is '+otp
            sendmail(email,subject,body)
            return render_template('otp.html',otp=otp,key=key,user=user,email=email,password=password)
        return render_template('create.html')
@app.route('/otp/<otp>/<user>/<password>/<email>',methods=['POST','GET'])
def otp(otp,user,password,email):
    if request.method=='POST':
        uotp=request.form['otp']
        if otp==uotp:
            cursor=mysql.connection.cursor()
            lst=[user,password,email]
            query='insert into admin(USERNAME,PASSWORD,EMAIL)values(%s,%s,%s)'
            cursor.execute(query,lst)
            mysql.connection.commit()
            cursor.close()
            flash('Details registered')
            return redirect(url_for('adminlogin'))
        else:
            flash('Wrong otp')
            return render_template('otp.html',otp=otp,user=user,email=email,password=password)
    return redirect(url_for('mainpage'))

@app.route('/validate',methods=['POST'])
def validate():
    user=request.form['user']
    password=request.form['password']
    cursor=mysql.connection.cursor()
    cursor.execute('SELECT username,PASSWORD from admin')
    data=cursor.fetchall()[0]
    userid=data[0]
    admin_password=data[1]
    cursor.close()
    if user==userid and password==admin_password:
        return redirect(url_for('adminlogin'))
    else:
        return redirect(url_for('login'))
@app.route('/mainpage')
def adminlogin():
    cursor=mysql.connection.cursor()
    cursor.execute('SELECT book_id,book_title from library')
    books=cursor.fetchall()
    cursor.close()
    return render_template('admin.html',books=books)
@app.route('/deletebook',methods=['POST'])
def delete():
    if request.method=='POST':
        print(request.form)
        s=request.form['option'].split()
        cursor=mysql.connection.cursor()
        cursor.execute('delete from library where book_id=%s',[s[0]])
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('adminlogin'))

@app.route('/clearsuggestions')
def clear():
    cursor=mysql.connection.cursor()
    cursor.execute('delete from suggestions')
    mysql.connection.commit()
    return redirect(url_for('adminlogin'))
    cursor.close()


@app.route('/addbook',methods=['GET','POST'])
def addbook():
    if request.method=='POST':
        id1=request.form['id']
        title=request.form['title']
        author=request.form['author']
        genre=request.form['genre']
        copies=request.form['copies']
        price=request.form['price']
        cursor=mysql.connection.cursor()
        cursor.execute('insert into library(book_id,book_title,author,genre,copies,status,book_price,rented,underreplacement) values(%s,%s,%s,%s,%s,%s,%s,%s,%s)',[id1,title,author,genre,copies,f'{copies} Available',price,0,0])
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('adminlogin'))
    return render_template('addbook.html')

@app.route('/viewbooks')
def view():
    cursor=mysql.connection.cursor()
    cursor.execute('SELECT * from library order by date')
    books=cursor.fetchall()
    cursor.close()
    return render_template('table.html',books=books)

@app.route('/rentalstatus')
def status_rent():
    cursor=mysql.connection.cursor()
    cursor.execute('SELECT rent.rent_id,rent.student_id,rent.section,rent.book_id,rent.book_name,rent.from_date,rent.due_date,rent.fine from rent')
    rids=cursor.fetchall()
    return render_template('rentalstats.html',rids=rids)

@app.route('/viewsuggestions')
def viewsuggestions():
    cursor=mysql.connection.cursor()
    cursor.execute('SELECT * from suggestions')
    suggestions=cursor.fetchall()
    cursor.close()
    return render_template('suggestion.html',ids=suggestions)
@app.route('/viewbookstudent')
def view1():
    cursor=mysql.connection.cursor()
    cursor.execute('SELECT * from library order by date')
    books=cursor.fetchall()
    cursor.close()
    return render_template('table1.html',books=books)

@app.route('/rent_search',methods=['POST'])
def search_rentbar():
    if request.method=='POST':
        data=request.form['ids']
        cursor=mysql.connection.cursor()
        cursor.execute('select count(*) from rent where rent_id=%s',[data])
        count=int(cursor.fetchone()[0])
        cursor.close()
        if count==0:
            return render_template('rentalstats2.html',data='empty')
        else:
            cursor=mysql.connection.cursor()
            cursor.execute('select * from rent where rent_id=%s',[data])
            count=cursor.fetchall()
            cursor.close()
            return render_template('rentalstats2.html',data=count)

@app.route('/booksearch',methods=['POST'])
def booksearch():
    if request.method=='POST':
        data=request.form['ids']
        cursor=mysql.connection.cursor()
        cursor.execute('select count(*) from library where book_id=%s',[data])
        count=int(cursor.fetchone()[0])
        cursor.close()
        if count==0:
            return render_template('searchbar_books.html',data='empty')
        else:
            cursor=mysql.connection.cursor()
            cursor.execute('select * from library where book_id=%s',[data])
            count=cursor.fetchall()
            cursor.close()
            return render_template('searchbar_books.html',data=count)
@app.route('/searchbar',methods=['GET','POST'])
def search():
    if request.method=='POST':
        data=request.form['ids']
        cursor=mysql.connection.cursor()
        cursor.execute('select count(*) from suggestions where id=%s',[data])
        count=int(cursor.fetchone()[0])
        cursor.close()
        if count==0:
            return render_template('search.html',data='empty')
        else:
            cursor=mysql.connection.cursor()
            cursor.execute('select * from suggestions where id=%s',[data])
            count=cursor.fetchall()
            cursor.close()
            return render_template('search.html',data=count)
@app.route('/searchbarusers',methods=['POST'])
def usersearch():
    if request.method=='POST':
        data=request.form['ids']
        cursor=mysql.connection.cursor()
        cursor.execute('select count(*) from library where book_id=%s',[data])
        count=int(cursor.fetchone()[0])
        cursor.close()
        if count==0:
            return render_template('searchbar_users.html',data='empty')
        else:
            cursor=mysql.connection.cursor()
            cursor.execute('select * from library where book_id=%s',[data])
            count=cursor.fetchall()
            print(count)
            cursor.close()
            return render_template('searchbar_users.html',data=count)
@app.route('/addsuggestion',methods=['GET','POST'])
def suggestions():
    if request.method=="POST":
        student_id=request.form['id']
        section=request.form['section']
        suggestion=request.form['text']
        cursor=mysql.connection.cursor()
        cursor.execute('INSERT INTO suggestions values(%s,%s,%s)',[student_id,section,suggestion])
        mysql.connection.commit()
        return redirect(url_for('home'))
    return render_template('review.html')
@app.route('/update',methods=['POST'])
def update1():
    option1=request.form['id1'].split()[0]
    return redirect(url_for('update',id1=option1))
@app.route('/update/<id1>',methods=['GET','POST'])
def update(id1):
    cursor=mysql.connection.cursor()
    cursor.execute('SELECT * FROM library where book_id=%s',[id1])
    option=cursor.fetchall()
    print(option)
    id1=option[0][0]
    title=option[0][1]
    author=option[0][2]
    price=option[0][3]
    genre=option[0][4]
    copies=option[0][7]
    cursor.close()
    if request.method=='POST':
        id2=request.form['id']
        title2=request.form['title']
        author2=request.form['author']
        price2=request.form['price']
        genre2=request.form['genre']
        copies2=request.form['copies']
        cursor=mysql.connection.cursor()
        cursor.execute('SELECT rented,underreplacement from library where book_id=%s',[id2])
        details=cursor.fetchall()[0]
        copies_new=int(copies2)-(int(details[0])+int(details[1]))
        if copies_new<0:
            return render_template('updatestop.html')
        else:
            new_status_copies='0 NOT-AVAILABLE' if copies_new==0 else f"{copies_new} Availabe"
            cursor.execute('update library set book_id=%s,book_title=%s,author=%s,genre=%s,copies=%s,status=%s,book_price=%s where book_id=%s',[id2,title2,author2,genre2,copies2,new_status_copies,price2,id1])
            mysql.connection.commit()
            return redirect(url_for('adminlogin'))
    return render_template('update.html',id1=id1,title=title,author=author,price=price,genre=genre,copies=copies)
@app.route('/rental',methods=['GET','POST'])
def rental():
    cursor=mysql.connection.cursor()
    cursor.execute('SELECT book_id,book_title from library where status!=%s',['0 NOT-AVAILABLE'])
    books=cursor.fetchall()
    cursor.close()
    if request.method=='POST':
        id1=request.form['id'].split()[0]
        name1=' '.join(request.form['id'].split()[1:])
        email=request.form['email']
        stud_id=request.form['stud_id']
        section=request.form['section']
        date1=request.form['date']
        cursor=mysql.connection.cursor()
        cursor.execute('SELECT rented from library where book_id=%s',[id1])
        rented=int(cursor.fetchone()[0])
        cursor.execute('SELECT email from admin')
        email_from=cursor.fetchone()[0]
        cursor.execute('SELECT count(*) from rent where student_id=%s',[stud_id])
        count=int(cursor.fetchone()[0])
        print(count)
        cursor.execute('SELECT status from library where book_id=%s',[id1])
        result=cursor.fetchone()[0]
        print(result)
        cursor.close()
        if count>=3:
            return render_template('student.html')
        else:
            cursor=mysql.connection.cursor()
            score=int(result.split()[0])-1
            status='0 NOT-AVAILABLE' if score==0 else f"{score} Availabe"
            rented=rented+1
            cursor.execute('update library set status=%s,rented=%s where book_id=%s',[status,rented,id1])
            cursor.execute('insert into rent(student_Id,section,book_id,book_name,due_date,fine,email,from_date) values(%s,%s,%s,%s,%s,%s,%s,%s)',[stud_id,section,id1,name1,date1,0,email,date.today()])
            mysql.connection.commit()
            cursor.close()
            subject=f'Due date for rented book {name1}'
            body=f'Thanks for visiting the central library.\n\n\nDue date for returning this book is {date}\nkindly return the book with in rental period to avoid unecessary fines.\n\n\n\nHappy reading!'
            try:
                sendmail(email,subject,body)
            except Exception as e:
                print(e)
                return render_template('check.html')
            return redirect(url_for('adminlogin'))
    return render_template('updaterent.html',books=books)
@app.route('/choose',methods=['POST'])
def choose():
    choice=request.form['option']
    if choice=='Rent A Book':
        return redirect(url_for('rental'))
    elif choice=='Retrieve From Rent':
        return redirect(url_for('retreiverent'))
    elif choice=='Under Replacement':
        return redirect(url_for('replacement'))
    elif choice=='Retrieve From Replacement':
        return redirect(url_for('retrievefromreplace'))
@app.route('/forgetpassword',methods=['GET','POST'])
def password():
    if request.method=='POST':
        email=request.form['email']
        cursor=mysql.connection.cursor()
        cursor.execute('select email from admin')
        data=cursor.fetchall()
        if (email,) in data:
            cursor.execute('select email from admin where email=%s',[email])
            data=cursor.fetchone()[0]
            cursor.close()
            subject='reset password for {data}'
            body=f'Reset the password using{request.host+url_for("createpassword",token=token(email,360))}'
            sendmail(data,body,subject)
            flash('Reset link send to your mail')
            return redirect(url_for('home'))
        else:
            return 'Invalid email'
    return render_template('forget.html')
@app.route('/createpassword/<token>',methods=['GET','POST'])
def createpassword(token):
    try:
        s=Serializer(app.config['SECRET_KEY'])
        email=s.loads(token)['user']
        if request.method=='POST':
            npass=request.form['npassword']
            cpass=request.form['cpassword']
            if npass==cpass:
                cursor=mysql.connection.cursor()
                cursor.execute('update admin set password=%s where email=%s',[npass,email])
                mysql.connection.commit()
                return 'password reset successfully'
            else:
                return 'password mismatch'
        return render_template('newpassword.html')
    except Exception as e:
        print(e)
        return 'Link expired try again'
@app.route('/retrieverent',methods=['GET','POST'])
def retreiverent():
    cursor=mysql.connection.cursor()
    cursor.execute('SELECT rent_id,student_id,book_id,book_name from rent')
    rentid=cursor.fetchall()
    cursor.close()
    if request.method=='POST':
        id1=request.form['rentid'].split()
        cursor=mysql.connection.cursor()
        cursor.execute('SELECT EMAIL from rent where rent_id=%s',[id1[0]])
        email=cursor.fetchone()[0]
        print(email)
        cursor.execute('SELECT email from admin')
        details=cursor.fetchall()[0]
        email_from=details[0]
        cursor.execute('DELETE FROM rent where rent_id=%s',[id1[0]])
        mysql.connection.commit()
        cursor.execute('SELECT STATUS from library where book_id=%s',[id1[2]])
        status=cursor.fetchall()[0]
        score=status[0].split()[0]
        new_status=int(score)+1
        fresh_status=f'{new_status} Available'
        cursor.execute('SELECT rented from library where book_id=%s',[id1[2]])
        rented=int(cursor.fetchone()[0])
        new_rent=rented-1
        cursor.execute('update library set status=%s,rented=%s where book_id=%s',[fresh_status,new_rent,id1[2]])
        mysql.connection.commit()
        subject=f'Book Return Successful'
        body=f'You have successfully returned {id1[3]}\n\n\nHappy Reading!'
        cursor.close()
        try:
            sendmail(email,subject,body)
        except Exception as e:
            print(e)
            return render_template('check2.html')
        return redirect(url_for('adminlogin'))
    return render_template('updatestatus.html',rentid=rentid)
@app.route('/replacement',methods=['GET','POST'])
def replacement():
    cursor=mysql.connection.cursor()
    cursor.execute('SELECT book_id,book_title from library where status!=%s',['0 NOT-AVAILABLE'])
    books=cursor.fetchall()
    cursor.close()
    if request.method=='POST':
        cursor=mysql.connection.cursor()
        id1=request.form['id'].split()[0]
        cursor.execute('SELECT status from library where book_id=%s',[id1])
        result=cursor.fetchone()[0]
        score=int(result.split()[0])-1
        status='0 NOT-AVAILABLE' if score==0 else f"{score} Availabe"
        cursor.execute('SELECT underreplacement from library where book_id=%s',[id1])
        r_score=int(cursor.fetchone()[0])+1
        cursor.execute('UPDATE library set status=%s,underreplacement=%s where book_id=%s',[status,r_score,id1])
        mysql.connection.commit()
        return redirect(url_for('adminlogin'))
    return render_template('replacement.html',books=books)
@app.route('/retrievefromreplacement',methods=['GET','POST'])
def retrievefromreplace():
    cursor=mysql.connection.cursor()
    cursor.execute('SELECT book_id,book_title from library where underreplacement!=0')
    books=cursor.fetchall()
    if request.method=="POST":
        id1=request.form['id'].split()[0]
        cursor=mysql.connection.cursor()
        cursor.execute('SELECT status from library where book_id=%s',[id1])
        result=cursor.fetchone()[0]
        score=int(result.split()[0])+1
        fresh_status=f'{score} Available'
        cursor.execute('SELECT underreplacement from library where book_id=%s',[id1])
        under=int(cursor.fetchone()[0])-1
        cursor.execute('UPDATE library set status=%s,underreplacement=%s where book_id=%s',[fresh_status,under,id1])
        mysql.connection.commit()
        return redirect(url_for('adminlogin'))
    return render_template('fromreplacement.html',books=books)
@app.route('/payments',methods=['GET','POST'])
def payments():
    background_task()
    cursor=mysql.connection.cursor()
    cursor.execute('SELECT * from rent where fine>0')
    rentids1=cursor.fetchall()
    rentids=0 if len(rentids1)==0 else rentids1
    return render_template('payment.html',rentids=rentids)
@app.route('/pay/<rentid>/<studid>/<fine>',methods=['GET','POST'])
def pay(rentid,studid,fine):
    checkout_session=stripe.checkout.Session.create(
        success_url=request.host_url+url_for('success_pay',rentid=rentid,fine=fine),
        line_items=[
            {
                'price_data': {
                    'product_data': {
                        'name': f'payment of rent id:{rentid}',
                    },
                    'unit_amount': int(fine)*100,
                    'currency': 'inr',
                 },
                'quantity': 1,
            },
            ],
        mode="payment",)
    return redirect(checkout_session.url)
@app.route('/success/<rentid>/<fine>')
def success_pay(rentid,fine):
    cursor=mysql.connection.cursor()
    cursor.execute('SELECT rent_id from rent')
    data=cursor.fetchall()
    cursor.execute('select email from rent where rent_id=%s',[rentid])
    email=cursor.fetchone()[0]
    cursor.execute('select student_id from rent where rent_id=%s',[rentid])
    studid=cursor.fetchone()[0]
    cursor.execute('select book_name from rent where rent_id=%s',[rentid])
    book_name=cursor.fetchone()[0]
    cursor.execute('SELECT email from admin')
    details=cursor.fetchall()[0]
    email_from=details[0]
    cursor.execute('select book_id from rent where rent_id=%s',[rentid])
    book_id=cursor.fetchone()[0]
    cursor.close()
    print(data)
    print(type(rentid))
    if (int(rentid),) in data:
        cursor=mysql.connection.cursor()
        cursor.execute('delete from rent where rent_id=%s',[rentid])
        mysql.connection.commit()
        subject=f'Payment of rupees {fine} successfull for rent id:{rentid}'
        body=f'You have successfully paid the book rental fine of rupees {fine} for {book_name}\n\nHappy Reading!'
        try:
            mail_sender(email_from,email,subject,body,)
        except Exception as e:
            print(e)
            return render_template('check3.html')
        cursor.execute('SELECT STATUS from library where book_id=%s',[book_id])
        status=cursor.fetchall()[0]
        score=status[0].split()[0]
        new_status=int(score)+1
        fresh_status=f'{new_status} Available'
        cursor.execute('SELECT rented from library where book_id=%s',[book_id])
        rented=int(cursor.fetchone()[0])
        new_rent=rented-1
        cursor.execute('update library set status=%s,rented=%s where book_id=%s',[fresh_status,new_rent,book_id])
        mysql.connection.commit()
        flash('Payment successfull')
        return redirect(url_for('home'))
    else:
        abort(404,description="Page not found")
    app.run(debug=True,use_reloader=True)

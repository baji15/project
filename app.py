from flask import Flask,request,render_template,redirect,url_for,flash,session
import mysql.connector
from otp import genotp
from cmail import sendmail
from stoken import encode,decode
from flask_session import Session
import flask_excel as excel
import re
app=Flask(__name__)
excel.init_excel(app)
app.config['SESSION_TYPE']='filesystem'
app.secret_key='Upendra'
mytdb=mysql.connector.connect(host='localhost',user='root',password='Baji@1626',db='snaproject')
Session(app)
@app.route('/')
def home():
    return render_template('welcome.html')
@app.route('/create',methods=['GET','POST'])
def create():
    if request.method=='POST':
        print(request.form)
        username=request.form['username']
        email=request.form['email']
        password=request.form['password']
        cpassword=request.form['Confirm password']
        cursor=mytdb.cursor()
        cursor.execute('select count(useremail) from users where useremail=%s',[email])
        result=cursor.fetchone()
        print(result)
        if result[0]==0:
            gotp=genotp()
            udata={'username':username,'email':email,'pword':password,'otp':gotp}
            print(gotp)
            subject='OTP For Simple Notes Manager'
            body=f'otp for registration of simple notes manager {gotp} '
            sendmail(to=email,subject=subject,body=body)
            flash('OTP has to given Mail.')
            return redirect(url_for('otp',enudata=encode(data=udata)))
        elif result[0]>0:
            flash('email already existed')
            return redirect(url_for('login'))
        else:
            return 'Something Wrong'
    return render_template('create.html')
@app.route('/otp/<enudata>',methods=['GET','POST'])
def otp(enudata):
    if request.method=='POST':
        uotp=request.form['OTP']
        try:
            dudata=decode(data=enudata)
        except Exception as e:
            print(e)
            return 'something went wrong'
        else:
            if dudata['otp']==uotp:
                cursor=mytdb.cursor()
                cursor.execute('insert into users(username,useremail,password) values(%s,%s,%s)',[dudata['username'],dudata['email'],dudata['pword']])
                mytdb.commit()
                cursor.close()
                flash('registration Successful')
                return redirect(url_for('login'))
            else:
                return 'otp was wrong pls register again'
    return render_template('otp.html')
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=="POST":
        email=request.form['email']
        pword=request.form['password']
        cursor=mytdb.cursor(buffered=True)
        cursor.execute('select count(useremail) from users where useremail=%s',[email])
        bdata=cursor.fetchone() #(1,) or (0,)
        if bdata[0]==1:
            cursor.execute('select password from users where useremail=%s',[email])
            bpassword=cursor.fetchone() #(0x31323300000000000000)
            if pword==bpassword[0].decode('utf-8'):
                print(session)
                session['user']=email
                print(session)
                return redirect(url_for('dashboard'))
            else:
                flash('password is wrong')
                return redirect(url_for('login'))
        elif bdata[0]==0:
            flash('email not existed')
            return redirect(url_for('create'))
        else:
            return 'something went wrong'
    return render_template('login.html')
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')
@app.route('/addnotes',methods=['GET','POST'])
def addnotes():
    if request.method=='POST':
        title=request.form['title']
        description=request.form['description']
        cursor=mytdb.cursor(buffered=True)
        cursor.execute('select user_id from users where useremail=%s',[session.get('user_id')])
        uid=cursor.fetchone()
        if uid:
            try:
                cursor.execute('insert into notes(title,ndescription,user_id) values(%s,%s,%s)',[title,description,uid[0]])
                mytdb.commit()
                cursor.close()
            except Exception as e:
                print(e)
                flash('Duplicate Title Entry')
                return redirect(url_for('dashboard'))
            else:
                flash('Notes Added Successfully')
                return redirect(url_for('dashboard'))
        else:
            return 'Something Went Wrong'
    return render_template('addnotes.html')
@app.route('/viewallnotes',methods=['GET','POST'])
def viewallnotes():
    try:
        cursor=mytdb.cursor(buffered=True)
        cursor.execute('select user_id from users where useremail=%s',[session.get('user')])
        uid=cursor.fetchone()
        cursor.execute('select nid,title,create_at from notes where user_id=%s',[uid[0]])
        ndata=cursor.fetchall()
    except Exception as e:
        print(e)
        flash('No Data Found')
        return redirect(url_for('dashboard'))
    else:
        return render_template('viewallnotes.html',ndata=ndata)
@app.route('/viewnotes/<nid>')
def viewnotes(nid):
    try:

        cursor=mytdb.cursor(buffered=True)
        cursor.execute('select * from notes where nid=%s',[nid])
        ndata=cursor.fetchone()
    except Exception as e:
        print(e)
        flash('No Data Found')
        return redirect(url_for('dashboard'))
    else:
        return render_template('viewnotes.html',ndata=ndata)
@app.route('/updatenotes/<nid>',methods=['GET','POST'])
def updatenotes(nid):
    cursor=mytdb.cursor(buffered=True)
    cursor.execute('select * from notes where nid=%s',[nid])
    ndata=cursor.fetchone()
    if request.method=='POST':
        title=request.form['title']
        description=request.form['description']
        cursor=mytdb.cursor(buffered=True)
        cursor.execute('update notes set title=%s,ndescription=%s where nid=%s',[title,description,nid])
        mydb.commit()
        cursor.close()
        flash('notes added successfully')
        return redirect(url_for('viewnotes',nid=nid))
    return render_template('updatenotes.html',ndata=ndata)
@app.route('/delete/<nid>')
def delete(nid):
    try:
        cursor=mytdb.cursor(buffered=True)
        cursor.execute('delete from notes where nid=%s',[nid])
        mytdb.commit()
        cursor.close()
    except Exception as e:
        print(e)
        flash('could not delete the data')
        return redirect(url_for('viewallnotes'))
    else:
        flash('Notes deleted Successfully')
        return redirect(url_for('viewallnotes'))
@app.route('/uploadfiles',methods=['GET','POST'])
def uploadfiles():
    if request.method=='POST':
        filedata=request.files['file']
        fname=filedata.filename
        fdata=filedata.read()
        try:
            cursor=mytdb.cursor(buffered=True)
            cursor.execute('select userid from users where useremail=%s',[session.get('user')])
            uid=cursor.fetchone()
            cursor.execute('insert into filedata(filename,fdata,added_by) values(%s,%s,%s)',[fname,fdata,uid[0]])
            mytdb.commit()
        except Exception as e:
            print(e)
            flash("couldn't upload file" )
            return redirect(url_for('dashboard'))
        else:
            flash('file uploaded successfully')
            return redirect(url_for('dashboard'))
    return render_template('uploadfiles.html')
@app.route('/allfiles')
def allfiles():
    try:
        cursor=mytdb.cursor(buffered=True)
        cursor.execute('select user_id from users where useremail=%s',[session.get('user')])
        uid=cursor.fetchone()
        cursor.execute('select fid,filename,create_at from filedata where added_by=%s',[uid[0]])
        ndata=cursor.fetchall()
    except Exception as e:
        print(e)
        flash('No Data Found')
        return redirect(url_for('dashboard'))
    else:
        return render_template('allfiles.html',ndata=ndata)
@app.route('/viewfiles/<fid>')
def viewfiles(fid):
    try:
        cursor=mytdb.cursor(buffered=True)
        cursor.execute('select filename,fdata fromfiledata where fid=%s',[fid])
        fdata=cursor.fetchone()
        bytes_data=BytesIOfdata([1])
        return send_file(bytes_data,download_name=fdata[0],as_attachment=False)
    except Exception as e:
        print(e)
        flash("couldn't open the file")
        return redirect(url_for('dashboard'))
@app.route('/downloadfiles/<fid>')
def downloadfiles(fid):
    try:
        cursor=mytdb.cursor(buffered=True)
        cursor.execute('select filename,fdata fromfiledata where fid=%s',[fid])
        fdata=cursor.fetchone()
        bytes_data=BytesIO(data([1]))
        return send_file(bytes_data,download_name=fdata[0],as_attachment=True)
    except Exception as e:
        print(e)
        flash("couldn't open the file")
        return redirect(url_for('dashboard'))
@app.route('/getexceldata')
def getexceldata():
    try:
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select userid from user where useremail=%s',[session.get('user')])
        uid = cursor.fetchone()
        cursor.execute('select nid,title,ndecription,create_at from notes where userid=%s',[uid[0]])
    except Exception as e:
        print(e)
        flash('No data found')
        return redirect(url_for('dashboard'))
    else:
        array_data = [list(i) for i in ndata]
        columns = ['Notesid','Title','Context','Creted_Time']
        array_data.insert(0,columns)
        return excel.make_response_from_array(array_data,'xlsx',filename='notesdata')
@app.route('/search',methods=['GET','POST'])
def search():
    if session.get('user'):
        try:
            if request.method=='POST':
                sdata=request.form['sname']
                strg=['A-Za-z0-9']
                pattern=re.compile(f'^{strg}',re.IGNORECASE)
                if (pattern.match(sdata)):
                    cursor=mytdb.cursor(buffered=True)
                    cursor.execute('select * from notes where nid like %s or title like %s or ndescription like %s or create_at like %s',[sdata+'%',sdata+'%',sdata+'%',sdata+'%'])
                    sdata=cursor.fetchall()
                    cursor.close()
                    return render_template('dashboard.html',sdata=sdata)
                else:
                    flash('No Data Found')
                    return redirect(url_for('dashboard'))
            else:
                return redirect(url_for('dashboard'))
        except Exception as e:
            print(e)
            flash("can't find anything")
            return redirect(url_for('dashboard'))
    else:
        return render_template(url_for('login'))
app.run(use_reloader=True)
import os #디렉토리 절대 경로
from flask import Flask, request
from flask import render_template #template폴더 안에 파일을 쓰겠다
from flask import redirect #리다이렉트
from flask_sqlalchemy import SQLAlchemy
from Models import db
from Models import User
from Models import Vm
from flask import session #세션
from flask_wtf.csrf import CSRFProtect #csrf
from form import RegisterForm, LoginForm, VmForm
import sqlite3
from datetime import datetime,timedelta
from dateutil.relativedelta import *

SECRET_KEY = os.urandom(32)
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

@app.route('/')
def mainpage():
    userid = session.get('userid',None)
    if userid == None:
        return render_template('main.html', userid=userid)
    with sqlite3.connect("db.sqlite") as con:
        cur = con.cursor()
        cur.execute(f"SELECT userid,email,point FROM user_table WHERE userid = '{userid}'")
        info = cur
        con.commit()
    return render_template('index.html',userid=userid,info=info)
    

@app.route('/register/', methods=['GET', 'POST']) #GET(정보보기), POST(정보수정) 메서드 허용
def register():
    form = RegisterForm()

    if form.validate_on_submit(): #유효성 검사. 내용 채우지 않은 항목이 있는지까지 체크
        userid = form.data.get('userid')
        email = form.data.get('email')
        password = form.data.get('password')
        usertable = User(userid,email,password)
        db.session.add(usertable) #DB저장
        db.session.commit() #변동사항 반영
        return redirect('/login')
    return render_template('register.html', form=form) #form이 어떤 form인지 명시한다

@app.route('/login', methods=['GET','POST'])  
def login():
    form = LoginForm() #로그인폼 
    if form.validate_on_submit(): #유효성 검사
        print('{}가 로그인 했습니다'.format(form.data.get('userid')))
        session['userid']=form.data.get('userid') #form에서 가져온 userid를 세션에 저장
        return redirect('/') #성공하면 main.html로
    return render_template('login.html', form=form)

@app.route('/logout', methods=['GET'])
def logout():
    session.pop('userid', None)
    return redirect('/')

@app.route('/point', methods=['GET','POST'])  
def point():
    userid = session.get('userid',None)
    if userid == None:
        return render_template('login.html', userid=userid)
    with sqlite3.connect("db.sqlite") as con:
        cur = con.cursor()
        cur.execute(f"SELECT userid,email,point FROM user_table WHERE userid = '{userid}'")
        info = cur
        con.commit()
    return render_template('point.html',userid=userid, info=info)

@app.route('/create', methods=['GET','POST'])  
def create():
    userid = session.get('userid',None)
    if userid == None:
        return render_template('login.html', userid=userid)
    form = VmForm()
    if form.validate_on_submit():
        userid = session.get('userid',None)
        service_num = request.form['spec']
        host_id = request.form['name']
        host_pw = request.form['vm_password']
        auto = request.form['auto_extend']
        end_time = datetime.today().date() + relativedelta(years= +1)
        #hyper-v실행(나중에 아이피받아오기)
        new_vm = Vm(userid,host_id,host_pw,end_time,service_num,auto)
        db.session.add(new_vm) #DB저장
        db.session.commit() #변동사항 반영
    else:
        return render_template('create.html',userid=userid)

if __name__ == "__main__":
    #데이터베이스---------
    basedir = os.path.abspath(os.path.dirname(__file__)) #현재 파일이 있는 디렉토리 절대 경로
    dbfile = os.path.join(basedir, 'db.sqlite') #데이터베이스 파일을 만든다

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + dbfile
    app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True #사용자에게 정보 전달완료하면 teadown. 그 때마다 커밋=DB반영
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False #추가 메모리를 사용하므로 꺼둔다
    app.config['SECRET_KEY']='asdfasdfasdfqwerty' #해시값은 임의로 적음

    csrf = CSRFProtect()
    csrf.init_app(app)

    db.init_app(app) #app설정값 초기화
    db.app = app #Models.py에서 db를 가져와서 db.app에 app을 명시적으로 넣는다
    db.create_all() #DB생성
    app.run(host="127.0.0.1", port=5000, debug=True)

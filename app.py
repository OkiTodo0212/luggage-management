from flask import Flask, render_template, request, redirect, url_for
from models import db, Luggage ,Person
from flask_mail import Mail, Message
from datetime import datetime
import pytz
from sqlalchemy import desc

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///luggage.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Flask-Mailの設定
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  
app.config['MAIL_PORT'] = 587                  
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'okitodo0212@gmail.com'
app.config['MAIL_PASSWORD'] = 'hord okux wuop cwzt'
app.config['MAIL_DEFAULT_SENDER'] = 'okitodo0212@gmail.com'

mail = Mail(app)

@app.before_request
def create_tables():
    db.create_all()

@app.route('/')
def index():
    people = Person.query.all()
    people_with_luggage_and_mail = [
        person for person in people if person.luggage_all != 0 or person.mail_all != 0
    ]

    # 各 Person の luggage の中で最も新しい time_add を基準にソート
    people_with_luggage_and_mail_sorted = sorted(
        people_with_luggage_and_mail,
        key=lambda person: max(luggage.time_add for luggage in person.luggage),
        reverse=True  # 新しい順にソートするために reverse=True
    )

    # luggage_all と mail_all が 0 の Person をフィルタリング
    people_without_luggage_and_mail = [
        person for person in people if person.luggage_all == 0 and person.mail_all == 0
    ]

    # 最終的な結果を結合
    sorted_people = people_with_luggage_and_mail_sorted + people_without_luggage_and_mail
    return render_template('index.html', people=sorted_people)

@app.route('/search', methods=['GET', 'POST'])
def search():
    results = []
    if request.method == 'POST':
        query = request.form.get('query')
        results = Person.query.filter(
            (Person.dormitory.like(f'%{query}%')) |
            (Person.last_name.like(f'%{query}%')) |
            (Person.first_name.like(f'%{query}%')) |
            (Person.furigana.like(f'%{query}%')) |
            (Person.room_number.like(f'%{query}%'))
        ).all()
    return render_template('index.html',results = results)


@app.route('/registration',methods=['GET', 'POST'])
def user_regist():
    if request.method == 'POST':
        dormitory = request.form['dormitory']
        room_number = request.form['room_number']
        last_name = request.form['last_name']
        first_name = request.form['first_name']
        furigana = request.form['furigana']
        email = request.form['email']
        
        # 新しいユーザーのインスタンスを作成
        new_person = Person(dormitory=dormitory,room_number=room_number,last_name=last_name, first_name=first_name, furigana=furigana, email=email)
 
        # データベースに保存
        db.session.add(new_person)
        db.session.commit()
        #send_email('登録完了のお知らせ',new_person.email,'荷物管理アプリに登録完了しました')
        return redirect(url_for('index'))
    return render_template('registration.html')

@app.route('/add/<int:id>', methods=['GET', 'POST'])
def add_luggage(id):
    if request.method == 'POST':
        luggage_quantity = int(request.form['luggage_quantity']) if request.form['luggage_quantity'] else 0
        mail_quantity = int(request.form['mail_quantity']) if request.form['mail_quantity'] else 0
        if ((luggage_quantity==0) & (mail_quantity==0)):
            return redirect(url_for('index'))
        remarks = request.form['remarks']

        new_luggage = Luggage(
            luggage_quantity=luggage_quantity,
            mail_quantity=mail_quantity,
            remarks=remarks,
            person_id = id,
            time_add=datetime.now(pytz.timezone('Asia/Tokyo'))
        )
        db.session.add(new_luggage)
        update_datanum(id)
        person = Person.query.get_or_404(id)
        #send_email('荷物が届きました',person.email,f"新しい荷物が届きました。\n\n荷物：{luggage_quantity}件　郵便：{mail_quantity}件\n備考：{remarks}")    

        return redirect(url_for('index'))

    return render_template('add_luggage.html',id=id)

@app.route('/receive/<int:id>', methods=['GET', 'POST'])
def receive_luggage(id):
   if request.method == 'POST':
       luggage_ids = request.form.getlist('luggage_ids')
       luggage_ids_int = [int(id) for id in luggage_ids]

       for luggage_id in luggage_ids_int:
           luggage = Luggage.query.get_or_404(luggage_id)
           luggage.flag_received=True
           luggage.time_receive=datetime.now(pytz.timezone('Asia/Tokyo'))
           db.session.commit()
           update_datanum(luggage.person_id)
        
       return redirect(url_for('receive_luggage',id=id))
   luggages_received = Luggage.query.filter((Luggage.person_id == id) & (Luggage.flag_received == True)).order_by(desc(Luggage.time_receive)).all()
   luggages_not_received = Luggage.query.filter((Luggage.person_id == id)&(Luggage.flag_received==False)).order_by(desc(Luggage.time_add)).all()
   return render_template('receive_luggage.html',luggages_received=luggages_received,luggages_not_received=luggages_not_received,id=id)


def send_email(title,recipients,mail_body):
    
    msg = Message(title,
                  recipients=[recipients])  # 受信者のメールアドレスを指定
    msg.body = mail_body
    mail.send(msg)
    return

def update_datanum(id):
    person = Person.query.get_or_404(id)
    person.luggage_all = db.session.query(db.func.sum(Luggage.luggage_quantity)).filter((Luggage.person_id == id)&(Luggage.flag_received==False)).scalar()
    if person.luggage_all == None: person.luggage_all = 0
    person.mail_all = db.session.query(db.func.sum(Luggage.mail_quantity)).filter((Luggage.person_id == id)&(Luggage.flag_received==False)).scalar()
    if person.mail_all == None: person.mail_all = 0
    db.session.commit()
    return


if __name__ == '__main__':
    app.run(debug=True)

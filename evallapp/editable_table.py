from flask import Flask, render_template, request, abort
from flask_sqlalchemy import SQLAlchemy

import random
import sys
from faker import Faker


def create_fake_users(n):
    """Generate fake users."""
    faker = Faker()
    for i in range(n):
        user = User(name=faker.name(),
                    age=random.randint(20, 80),
                    address=faker.address().replace('\n', ', '),
                    phone=faker.phone_number(),
                    email=faker.email())
        db.session.add(user)
    db.session.commit()
    print(f'Added {n} fake users to the database.')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

with app.app_context():
    class User(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(64), index=True)
        age = db.Column(db.Integer, index=True)
        address = db.Column(db.String(256))
        phone = db.Column(db.String(20))
        email = db.Column(db.String(120))

        def to_dict(self):
            return {
                'id': self.id,
                'name': self.name,
                'age': self.age,
                'address': self.address,
                'phone': self.phone,
                'email': self.email
            }
    #db.drop_all()
    db.create_all()
    #create_fake_users(10)

@app.route('/')
def index():
    return render_template('editable_table.html')


@app.route('/api/data')
def data():
    query = User.query

    # search filter
    search = request.args.get('search')

    if search:
        query = query.filter(db.or_(
            User.name.like(f'%{search}%'),
            User.email.like(f'%{search}%')
        ))
    total = query.count()

    # sorting
    sort = request.args.get('sort')
    if sort:
        order = []
        for s in sort.split(','):
            direction = s[0]
            name = s[1:]
            if name not in ['name', 'age', 'email']:
                name = 'name'
            col = getattr(User, name)
            if direction == '-':
                col = col.desc()
            order.append(col)
        if order:
            query = query.order_by(*order)

    # pagination
    start = request.args.get('start', type=int, default=-1)
    length = request.args.get('length', type=int, default=-1)
    if start != -1 and length != -1:
        query = query.offset(start).limit(length)
    r = {
        'data': [user.to_dict() for user in query],
        'total': total,
    }

    print(r)

    # response
    return r


@app.route('/api/data', methods=['POST'])
def update():
    data = request.get_json()
    if 'id' not in data:
        abort(400)
    user = User.query.get(data['id'])
    for field in ['name', 'age', 'address', 'phone', 'email']:
        if field in data:
            setattr(user, field, data[field])
    db.session.commit()
    return '', 204


if __name__ == '__main__':
    app.run()

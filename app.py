from datetime import datetime
from flask import Flask, render_template, request
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, scoped_session
from sqlalchemy import Column, String, Integer, create_engine, ForeignKey, DateTime
from sqlalchemy_utils.types.choice import ChoiceType
from werkzeug.utils import redirect

engine = create_engine('sqlite:///taxi.db')

Base = declarative_base()


class Orders(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True, comment='order ID')
    address_from = Column(String(140), nullable=False, comment='Address from')
    address_to = Column(String(140), nullable=False, comment='Address to')
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    driver_id = Column(Integer, ForeignKey('drivers.id'), nullable=False)
    date_created = Column(DateTime, default=datetime.now, nullable=False)
    status = Column(ChoiceType([('not_accepted', 'not_accepted'), ('in_progress', 'in_progress'), ('done', 'done'),
                                ('cancelled', 'cancelled')], impl=String()), comment='Order status')

    def __repr__(self):
        return '<Orders(id={0}, address_from={1}, address_to={2}, client_id={3}, driver_id={4}, date_created={5}, ' \
               'status={6})>'.format(
            self.id,
            self.address_from,
            self.address_from,
            self.client_id,
            self.driver_id,
            self.date_created,
            self.status,
        )


class Clients(Base):
    __tablename__ = 'clients'

    id = Column(Integer, primary_key=True, comment='client ID')
    name = Column(String(140), nullable=False, comment='Client name')
    is_vip = Column(ChoiceType([('True', 'True'), ('False', 'False')], impl=bool()), comment='VIP')
    orders = relationship('Orders')

    def __repr__(self):
        return '<Clients(id={0}, name={1}, is_vip={2})>'.format(
            self.id,
            self.name,
            self.is_vip,
        )


class Drivers(Base):
    __tablename__ = 'drivers'

    id = Column(Integer, primary_key=True, comment='driver ID')
    name = Column(String(140), nullable=False, comment='driver name')
    car = Column(String(140), nullable=False, comment='driver car')
    orders = relationship('Orders')

    def __repr__(self):
        return '<Drivers(id={0}, name={1}, car={2})>'.format(
            self.id,
            self.name,
            self.car,

        )


Base.metadata.create_all(engine)  # Create DB if it doesnt exist

app = Flask(__name__)

Session = scoped_session(sessionmaker(autoflush=True, autocommit=False, bind=engine))


@app.route('/')
def index():
    """Открывает главную страницу"""
    return render_template('index.html')


@app.route('/client')
def client():
    """Открывает страницу для взаимодействия с клиентами в БД"""
    return render_template('client.html')


@app.route('/new_client', methods=['POST', 'GET'])
def new_client():
    """Открывает страницу для создания нового клиента"""
    if request.method == 'POST':
        name = request.form['name']
        is_vip = request.form['is_vip']
        client1 = Clients(name=name, is_vip=is_vip)
        try:
            Session.add(client1)
            Session.commit()
            return 'Клиент добавлен'
        except:
            return 'ERROR in new_client'
        finally:
            Session.close()


@app.route('/driver')
def driver():
    """Открывает страницу для взаимодействия с водителями в БД"""
    return render_template('driver.html')


@app.route('/new_driver', methods=['POST', 'GET'])
def new_driver():
    """Открывает страницу для создания нового клиента"""
    if request.method == 'POST':
        name = request.form['name']
        car = request.form['car']
        driver1 = Drivers(name=name, car=car)
        try:
            Session.add(driver1)
            Session.commit()
            return 'Водитель добавлен'
        except:
            return 'ERROR in new_driver'
        finally:
            Session.close()


@app.route('/order')
def find():
    """Открывает страницу для взаимодействия с заказами"""
    return render_template('order.html')


@app.route('/add_order', methods=['POST', 'GET'])
def new_order():
    """Открывает страницу для создания нового заказа"""
    if request.method == 'POST':
        address_from = request.form['address_from']
        address_to = request.form['address_to']
        order = Orders(address_from=address_from, address_to=address_to, status='not_accepted', client_id=0,
                       driver_id=0)
        try:
            Session.add(order)
            Session.commit()
            return 'Заказ добавлен!'
        except:
            return 'Error in new_order'
        finally:
            Session.close()


@app.route('/show_order', methods=['POST', 'GET'])
def show_order():
    """Открывает страницу для при поиске заказа"""
    if request.method == 'POST':
        order_id = request.form['order_id']
        order_by_id = Session.query(Orders) \
            .filter(Orders.id == order_id) \
            .all()
        if not order_by_id:
            return '<h1>Нет такого заказа в БД</h1>'
        return render_template('show_order.html', order_by_id=order_by_id)


@app.route('/show_order/<int:id>/cancel', methods=['POST', 'GET'])
def cancel_order(id: int):
    """Открывает страницу для отмены заказа"""
    try:
        cond = Session.query(Orders.status) \
            .filter(Orders.id == id) \
            .first()
        if cond.status == 'not_accepted' or cond.status == 'in_progress':
            Session.query(Orders) \
                .filter(Orders.id == id) \
                .update({Orders.status: 'cancelled'})
            Session.commit()
            return redirect('/')
        else:
            return 'Заказ не может быть отменен, т.к. завершен или уже отменен'
    except:
        return 'Error happend during cancelling'


@app.route('/show_order/<int:id>/change', methods=['POST', 'GET'])
def change_order(id: int):
    """Открывает страницу для изменения заказа"""
    try:
        ch_client = request.form['Client_id']
        ch_driver = request.form['Driver_id']
        time = datetime.now()
        cond = Session.query(Orders.status) \
            .filter(Orders.id == id) \
            .first()
        if cond.status == 'not_accepted':
            Session.query(Orders) \
                .filter(Orders.id == id) \
                .update({'client_id': ch_client, 'driver_id': ch_driver, 'date_created': time, 'status': 'in_progress'})
            Session.commit()
            return redirect('/')
        else:
            return 'Заказ не может быть изменен, т.к. завершен, отменен или в процессе'
    except:
        return 'Error happend in change_order'


@app.route('/show_client', methods=['POST', 'GET'])
def show_client():
    """Открывает страницу для отображения информции о клиенте при поиске"""
    if request.method == 'POST':
        client_id = request.form['client_id']
        client_by_id = Session.query(Clients) \
            .filter(Clients.id == client_id) \
            .all()
        if not client_by_id:
            return '<h1>Нет такого клиента</h1>'
        return render_template('show_client.html', client_by_id=client_by_id)


@app.route('/show_client/<int:id>/del', methods=['POST', 'GET'])
def delete_client(id: int):
    """Открывает страницу при удалении клиента"""
    try:
        Session.query(Clients) \
            .filter(Clients.id == id) \
            .delete()
        Session.commit()
        return redirect('/')
    except:
        return 'Error happend in delete_client'


@app.route('/show_driver', methods=['POST', 'GET'])
def show_driver():
    """Открывает страницу для отображения информции о водителе при поиске"""
    if request.method == 'POST':
        driver_id = request.form['driver_id']
        driver_by_id = Session.query(Drivers) \
            .filter(Drivers.id == driver_id) \
            .all()
        if not driver_by_id:
            return '<h1>Нет такого водителя</h1>'
        return render_template('show_driver.html', driver_by_id=driver_by_id)


@app.route('/show_driver/<int:id>/del', methods=['POST', 'GET'])
def delete_driver(id: int):
    """Открывает страницу при удалении водителя"""
    try:
        Session.query(Drivers) \
            .filter(Drivers.id == id) \
            .delete()
        Session.commit()
        return redirect('/')
    except:
        return 'Error happend in delete_driver'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

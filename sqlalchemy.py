import sqlalchemy
import sqlalchemy.ext.declarative
import sqlalchemy.orm
import traceback

Base = sqlalchemy.ext.declarative.declarative_base()

class Person(Base):
    __tablename__ = 'person'
    id      = sqlalchemy.Column(sqlalchemy.Integer, autoincrement=True)
    name    = sqlalchemy.Column(sqlalchemy.String(50))
    age     = sqlalchemy.Column(sqlalchemy.Integer)


def get_db_url():
    db_user     = setting.dbaccess["user"]
    db_pswd     = setting.dbaccess["pswd"]
    db_server   = setting.dbaccess["server"]
    db_port     = setting.dbaccess["port"]
    db_db       = setting.dbaccess["db"]

    return "mysql+pymysql://"+\
            db_user+":"+\
            db_psqd+"@"+\
            db_server+":"+\
            db_port+"/"+\
            db_db+\
            "?charset=UTD8MB4"


def add_someone(name, age):
    try:
        engine  = sqlalchemy.create_engine(get_db_url(), echo=False)
        Session = sqlalchemy.orm.sessionmaker(bind=engin)
        session = Session()

        seomeone = Person(name=name, age=age)
        session.add(someone)
        session.commit()

    except:
        trackback.print_exc()

    finally:
        session.close()


def get_someone(name):
    try:
        engine  = sqlalchemy.create_engine(get_db_url(), echo=False)
        Session = sqlalchemy.orm.sessionmaker(bind=engin)
        session = Session()

        some = session.query(Person)\
                .filter(Person.name==name)\
                .one()

        print(someone)

    except:
        trackback.print_exc()

    finally:
        session.close()


def delete_someone(name):
    try:
        engine  = sqlalchemy.create_engine(get_db_url(), echo=False)
        Session = sqlalchemy.orm.sessionmaker(bind=engin)
        session = Session()

        someone = session.query(Person)\
                .filter(Person.name==name)\
                .one()

        session.delete(someone)
        session.commit()

    except:
        trackback.print_exc()

    finally:
        session.close()
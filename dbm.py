# coding: utf-8
from sqlalchemy import Column, DateTime, ForeignKey, ForeignKeyConstraint, Index, Integer, String, Text, Time
from sqlalchemy import create_engine
from sqlalchemy.schema import FetchedValue
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base



Base = declarative_base()
engine = create_engine("mysql://root:0000@localhost/DRSLR_V2", encoding='utf8', echo=True)
Session = sessionmaker(bind=engine)
sess = Session()

class CategoryLaw(Base):
    __tablename__ = 'CategoryLaw'

    law_id = Column(Integer, primary_key=True)
    applied_date = Column(DateTime)
    minimum_wage = Column(Integer)
    law_02 = Column(Integer)
    law_03 = Column(Integer)
    created_time = Column(String(45), server_default=FetchedValue())
    updated_time = Column(String(45))


class Daily(Base):
    __tablename__ = 'Daily'

    daliy_id = Column(Integer, primary_key=True, nullable=False)
    tc_id = Column(ForeignKey('timecard.tc_id'), index=True)
    wcond_id = Column(ForeignKey('workcondition.wcond_id'), nullable=False, index=True)
    target_ym = Column(String(6), primary_key=True, nullable=False)
    target_date = Column(String(2), primary_key=True, nullable=False)
    work_start = Column(DateTime)
    work_end = Column(DateTime)
    rest_start = Column(DateTime)
    rest_end = Column(DateTime)
    actual_worktime = Column(Time)
    contract_worktime = Column(Time)
    over_worktime = Column(Time)
    night_worktime = Column(Time)
    actual_dailypay = Column(Integer)
    contract_dailypay = Column(Integer)
    minimum_dailypay = Column(Integer)
    created_time = Column(DateTime, server_default=FetchedValue())
    updated_time = Column(DateTime)

    tc = relationship('Timecard', primaryjoin='Daily.tc_id == Timecard.tc_id', backref='dailies')
    wcond = relationship('Workcondition', primaryjoin='Daily.wcond_id == Workcondition.wcond_id', backref='dailies')


class FAQ(Base):
    __tablename__ = 'FAQ'

    id = Column(Integer, primary_key=True)
    group = Column(Integer)
    sequence = Column(Integer)
    level = Column(Integer)
    title = Column(String(45))
    content = Column(Text)
    active = Column(Integer)
    created_time = Column(String(45))
    updated_time = Column(String(45))


class Monthly(Base):
    __tablename__ = 'Monthly'

    monthly_id = Column(Integer, primary_key=True)
    wcond_id = Column(ForeignKey('workcondition.wcond_id'), nullable=False, index=True)
    create_time = Column(DateTime, server_default=FetchedValue())
    update_time = Column(DateTime)

    wcond = relationship('Workcondition', primaryjoin='Monthly.wcond_id == Workcondition.wcond_id', backref='monthlies')


class TermsAgreement(Base):
    __tablename__ = 'TermsAgreement'

    terms_id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    terms_01 = Column(Integer)
    terms_02 = Column(Integer)
    terms_03 = Column(Integer)
    created_time = Column(DateTime, server_default=FetchedValue())
    updated_time = Column(DateTime)


class TimeCard(Base):
    __tablename__ = 'TimeCard'

    tc_id = Column(Integer, primary_key=True, nullable=False)
    wcond_id = Column(ForeignKey('workcondition.wcond_id'), nullable=False, index=True)
    target_ym = Column(String(6), primary_key=True, nullable=False)
    target_date = Column(String(2), primary_key=True, nullable=False)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    rest_start_time = Column(DateTime)
    rest_end_time = Column(DateTime)
    created_time = Column(DateTime, server_default=FetchedValue())
    updated_time = Column(DateTime)

    wcond = relationship('Workcondition', primaryjoin='TimeCard.wcond_id == Workcondition.wcond_id', backref='time_cards')


class TimeCardMemo(Base):
    __tablename__ = 'TimeCardMemo'
    __table_args__ = (
        ForeignKeyConstraint(['tc_id', 'target_ym', 'target_date'], ['timecard.tc_id', 'timecard.target_ym', 'timecard.target_date']),
        Index('fk_TimeCardMemo_TimeCard1_idx', 'tc_id', 'target_ym', 'target_date')
    )

    tcmemo_id = Column(Integer, primary_key=True)
    tc_id = Column(Integer, nullable=False)
    target_ym = Column(String(6), nullable=False)
    target_date = Column(String(2), nullable=False)
    article = Column(Text)
    having_photo = Column(String(255))
    created_time = Column(DateTime, server_default=FetchedValue())
    updated_time = Column(DateTime)

    tc = relationship('Timecard', primaryjoin='and_(TimeCardMemo.tc_id == Timecard.tc_id, TimeCardMemo.target_ym == Timecard.target_ym, TimeCardMemo.target_date == Timecard.target_date)', backref='time_card_memos')


class User(Base):
    __tablename__ = 'User'

    user_id = Column(Integer, primary_key=True)
    user_name = Column(String(16))
    email = Column(String(255))
    birth = Column(Integer)
    sex = Column(Integer)
    password = Column(String(32))
    user_status = Column(Integer, nullable=False, server_default=FetchedValue())
    created_time = Column(DateTime, server_default=FetchedValue())
    updated_time = Column(DateTime)


class WorkCondition(Base):
    __tablename__ = 'WorkCondition'

    wcond_id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey('user.user_id'), nullable=False, index=True)
    wp_id = Column(ForeignKey('workplace.wp_id'), nullable=False, index=True)
    cont_id = Column(ForeignKey('workcontract.cont_id'), index=True)
    start_work_date = Column(String(8))
    start_work_time = Column(Time)
    end_work_time = Column(Time)
    start_rest_time = Column(Time)
    end_rest_time = Column(Time)
    amount_work_time = Column(Time)
    amount_rest_time = Column(Time)
    hourly_pay = Column(Integer)
    monthly_pay = Column(Integer)
    payday = Column(String(4))
    pay_type = Column(String(45))
    wcond_status = Column(Integer, nullable=False, server_default=FetchedValue())
    created_time = Column(DateTime, server_default=FetchedValue())
    updated_time = Column(DateTime)

    cont = relationship('Workcontract', primaryjoin='WorkCondition.cont_id == Workcontract.cont_id', backref='work_conditions')
    user = relationship('User', primaryjoin='WorkCondition.user_id == User.user_id', backref='work_conditions')
    wp = relationship('Workplace', primaryjoin='WorkCondition.wp_id == Workplace.wp_id', backref='work_conditions')


class WorkContract(Base):
    __tablename__ = 'WorkContract'

    cont_id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey('user.user_id'), nullable=False, index=True)
    wp_id = Column(ForeignKey('workplace.wp_id'), nullable=False, index=True)
    contract_01 = Column(Integer)
    contract_02 = Column(Integer)
    contract_03 = Column(Integer)
    contract_04 = Column(Integer)
    contract_05 = Column(Integer)
    cont_status = Column(Integer, nullable=False, server_default=FetchedValue())
    having_photo = Column(String(255))
    created_time = Column(DateTime, server_default=FetchedValue())
    updated_time = Column(DateTime)

    user = relationship('User', primaryjoin='WorkContract.user_id == User.user_id', backref='work_contracts')
    wp = relationship('Workplace', primaryjoin='WorkContract.wp_id == Workplace.wp_id', backref='work_contracts')


class WorkPlace(Base):
    __tablename__ = 'WorkPlace'

    wp_id = Column(Integer, primary_key=True)
    wp_name = Column(String(45))
    address = Column(String(255))
    kakao_place_id = Column(String(45))
    road_address = Column(String(255))
    category_name = Column(String(255))
    phone = Column(String(255))
    bjd_code = Column(String(10))
    building_name = Column(String(255))
    business_code = Column(String(45))
    owner = Column(String(45))
    over_5employee = Column(Integer, server_default=FetchedValue())
    x = Column(Text)
    y = Column(Text)
    created_time = Column(DateTime, server_default=FetchedValue())
    updated_time = Column(DateTime)


class Yearly(Base):
    __tablename__ = 'Yearly'

    yearly_id = Column(Integer, primary_key=True)
    wcond_id = Column(ForeignKey('workcondition.wcond_id'), nullable=False, index=True)
    create_time = Column(DateTime, server_default=FetchedValue())
    update_time = Column(DateTime)

    wcond = relationship('Workcondition', primaryjoin='Yearly.wcond_id == Workcondition.wcond_id', backref='yearlies')


class Timecard(Base):
    __tablename__ = 'timecard'

    tc_id = Column(Integer, primary_key=True, nullable=False)
    wcond_id = Column(ForeignKey('workcondition.wcond_id'), nullable=False, index=True)
    target_ym = Column(String(6), primary_key=True, nullable=False)
    target_date = Column(String(2), primary_key=True, nullable=False)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    rest_start_time = Column(DateTime)
    rest_end_time = Column(DateTime)
    created_time = Column(DateTime, server_default=FetchedValue())
    updated_time = Column(DateTime)

    wcond = relationship('Workcondition', primaryjoin='Timecard.wcond_id == Workcondition.wcond_id', backref='timecards')


class User(Base):
    __tablename__ = 'user'

    user_id = Column(Integer, primary_key=True)
    user_name = Column(String(16))
    email = Column(String(255))
    birth = Column(Integer)
    sex = Column(Integer)
    password = Column(String(32))
    user_status = Column(Integer, nullable=False, server_default=FetchedValue())
    created_time = Column(DateTime, server_default=FetchedValue())
    updated_time = Column(DateTime)


class Workcondition(Base):
    __tablename__ = 'workcondition'

    wcond_id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey('user.user_id'), nullable=False, index=True)
    wp_id = Column(ForeignKey('workplace.wp_id'), nullable=False, index=True)
    cont_id = Column(ForeignKey('workcontract.cont_id'), index=True)
    start_work_date = Column(String(8))
    start_work_time = Column(Time)
    end_work_time = Column(Time)
    start_rest_time = Column(Time)
    end_rest_time = Column(Time)
    amount_work_time = Column(Time)
    amount_rest_time = Column(Time)
    hourly_pay = Column(Integer)
    monthly_pay = Column(Integer)
    payday = Column(String(4))
    pay_type = Column(String(45))
    wcond_status = Column(Integer, nullable=False, server_default=FetchedValue())
    created_time = Column(DateTime, server_default=FetchedValue())
    updated_time = Column(DateTime)

    cont = relationship('Workcontract', primaryjoin='Workcondition.cont_id == Workcontract.cont_id', backref='workconditions')
    user = relationship('User', primaryjoin='Workcondition.user_id == User.user_id', backref='workconditions')
    wp = relationship('Workplace', primaryjoin='Workcondition.wp_id == Workplace.wp_id', backref='workconditions')


class Workcontract(Base):
    __tablename__ = 'workcontract'

    cont_id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey('user.user_id'), nullable=False, index=True)
    wp_id = Column(ForeignKey('workplace.wp_id'), nullable=False, index=True)
    contract_01 = Column(Integer)
    contract_02 = Column(Integer)
    contract_03 = Column(Integer)
    contract_04 = Column(Integer)
    contract_05 = Column(Integer)
    cont_status = Column(Integer, nullable=False, server_default=FetchedValue())
    having_photo = Column(String(255))
    created_time = Column(DateTime, server_default=FetchedValue())
    updated_time = Column(DateTime)

    user = relationship('User', primaryjoin='Workcontract.user_id == User.user_id', backref='workcontracts')
    wp = relationship('Workplace', primaryjoin='Workcontract.wp_id == Workplace.wp_id', backref='workcontracts')


class Workplace(Base):
    __tablename__ = 'workplace'

    wp_id = Column(Integer, primary_key=True)
    wp_name = Column(String(45))
    address = Column(String(255))
    kakao_place_id = Column(String(45))
    road_address = Column(String(255))
    category_name = Column(String(255))
    phone = Column(String(255))
    bjd_code = Column(String(10))
    building_name = Column(String(255))
    business_code = Column(String(45))
    owner = Column(String(45))
    over_5employee = Column(Integer, server_default=FetchedValue())
    x = Column(Text)
    y = Column(Text)
    created_time = Column(DateTime, server_default=FetchedValue())
    updated_time = Column(DateTime)


if __name__ == '__main__':
    # mydb = init_db_config()
    # curs = mydb.cursor()
    # wcd_id = 2
    # for i in range(1,31):
    #     tc_res = get_timecard(curs,201906,i,wcd_id)
    #
    #
    # print(tc_res)
    #
    # # mydb.commit()
    # mydb.close()
    our_user = sess.query(User).all()
    # for instance in sess.query(dbm.User).order_by(dbm.User.id):
    #    print(instance.user_name, instance.user_id)
    # user_res = User.query.first()
    print(our_user.__dict__)
    sess.close()
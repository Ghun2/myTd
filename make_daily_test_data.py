import MySQLdb as sql
import MySQLdb.cursors
from pprint import pprint
from datetime import timedelta
import calendar
import time
# import dbm
# from sqlalchemy.orm import sessionmaker

# Session = sessionmaker(bind=dbm.engine)
# sess = Session()


def init_db_config():
    db = sql.connect(host="localhost",user="root",
                      passwd="0000",db="DRSLR_V3",cursorclass=MySQLdb.cursors.DictCursor)
    return db


def get_time_card(cur, target_ym, target_date, wcond):
    # print(target_ym,target_date,wcond)
    cur.execute("""
        SELECT * FROM TimeCard
        WHERE
        target_ym = {0} and
        target_date = {1} and
        wcond_id = {2}
        ;
        """.format(target_ym,target_date,wcond))

    return cur.fetchall()


def get_work_condition(cur, wcond):
    cur.execute("""
            SELECT * FROM WorkCondition
            WHERE
            wcond_id = {0}
            ;
            """.format(wcond))

    return cur.fetchall()


def get_category_law(cur):
    cur.execute("""
            SELECT * FROM CategoryLaw
            ;
            """)

    return cur.fetchall()


def calculate_daily(curs, timecard, workcondition, categorylaw):
    tablename = "Daily"

    daily = {
        "daliy_id":"",
        "wcond_id":"",
        "target_ym":"",
        "target_date":"",
        "work_start":"",
        "work_end":"",
        "actual_work_time":"",
        "contract_work_time":"",
        "actual_rest_time":"",
        "contract_rest_time":"",
        "over_work_time":"",
        # "night_work_time":"",
        # "holiday_work_time":"",
        "actual_work_pay":"",
        "contract_work_pay":"",
        "minimum_work_pay":"",
        "over_work_pay":"",
        # "night_work_pay":"",
        # "holiday_work_pay":""
    }

    # Time 타입 null (00:00:00)
    null_time = timedelta(seconds=0)

    # -START 초기화
    st_tc = list(filter(lambda timecard: timecard['type_code'] == 1, timecard))[0]
    et_tc = list(filter(lambda timecard: timecard['type_code'] == 2, timecard))[0]

    if list(filter(lambda timecard: timecard['type_code'] == 3, timecard)) and list(filter(lambda timecard: timecard['type_code'] == 4, timecard)):
        rst_tc = list(filter(lambda timecard: timecard['type_code'] == 3, timecard))[0]
        ret_tc = list(filter(lambda timecard: timecard['type_code'] == 4, timecard))[0]

        art = ret_tc["in_time"] - rst_tc["in_time"]
    else:
        art = workcondition["amount_rest_time"]

    awt = (et_tc["in_time"] - st_tc["in_time"]) - art
    cwt = workcondition["amount_work_time"]

    awp = round(convert_timedelta_to_float_hour(awt) * workcondition["hourly_pay"])
    cwp = round(convert_timedelta_to_float_hour(cwt) * workcondition["hourly_pay"])
    mwp = round(convert_timedelta_to_float_hour(awt) * categorylaw["minimum_wage"])

    t_ym = st_tc["target_ym"]
    t_dt = st_tc["target_date"]
    w_id = st_tc["wcond_id"]
    # -END 초기화

    # 실제 근무 시작/종료 계산용 시간 (Type:timedelta)
    st_delta = timedelta(hours=st_tc["in_time"].hour, minutes=st_tc["in_time"].minute)
    et_delta = timedelta(days=et_tc["in_time"].day) - timedelta(days=st_tc["in_time"].day) + timedelta(hours=et_tc["in_time"].hour,minutes=et_tc["in_time"].minute)

    # 연장 근무 시간/급여 (Type:(owt=)timedelta , (owp=)int)
    owt = et_delta - workcondition["end_work_time"] if et_delta > workcondition["end_work_time"] else null_time
    owp = (convert_timedelta_to_float_hour(owt) * workcondition["hourly_pay"]) * 0.5 if owt is not null_time else 0

    # 실제/야간 근무시간 범위 (Type:(class)TimeRange)
    at_range = TimeRange(st_delta,et_delta)
    nt_range = TimeRange(timedelta(hours=22),timedelta(hours=30))

    # 실제근무시간 중 야간 근무시간 범위/급여 (Type:(ant=class)TimeRange , (anp=)int)
    ant = at_range.get_overlapped_range(nt_range).duration if at_range.is_overlapped(nt_range) else null_time
    anp = (convert_timedelta_to_float_hour(ant) * workcondition["hourly_pay"]) * 0.5 if ant is not null_time else 0

    # -START 할당
    daily["daliy_id"] = "-".join([t_ym[2:]+t_dt,str(w_id),"1"])
    daily["wcond_id"] = w_id
    daily["target_ym"] = t_ym
    daily["target_date"] = t_dt
    daily["work_start"] = st_tc["in_time"]
    daily["work_end"] = et_tc["in_time"]
    daily["actual_work_time"] = awt
    daily["contract_work_time"] = cwt
    daily["actual_rest_time"] = art
    daily["contract_rest_time"] = workcondition["amount_rest_time"]
    daily["over_work_time"] = owt
    daily["night_work_time"] = ant
    daily["holiday_work_time"] = null_time
    daily["actual_work_pay"] = awp
    daily["contract_work_pay"] = cwp
    daily["minimum_work_pay"] = mwp
    daily["over_work_pay"] = round(owp)
    daily["night_work_pay"] = round(anp)
    daily["holiday_work_pay"] = 0

    daily["total_work_pay"] = daily["actual_work_pay"] + daily["over_work_pay"] + daily["night_work_pay"] + daily["holiday_work_pay"]
    # -END 할당

    insert_calculated_daily(curs, tablename, daily)


def insert_calculated_daily(curs, tablename, caled):
    # sql = "INSERT INTO tablename (%s) VALUES (%s)", (caled.keys(), caled.values())
    # print(sql)
    # curs.execute('INSERT INTO tablename (%s) VALUES (%s)', (caled.keys(), caled.values()))

    columns = ','.join(caled.keys())
    placeholders = ','.join(['%s'] * len (caled))
    query = "insert into %s (%s) values (%s)" % (tablename, columns, placeholders)
    curs.execute(query, caled.values())


def convert_timedelta_to_float_hour(num):
    return num.seconds / 3600


class TimeRange:
    def __init__(self, start, end):
        self.start = start
        self.end = end
        self.duration = self.end - self.start

    def is_overlapped(self, time_range):
        if max(self.start, time_range.start) < min(self.end, time_range.end):
            return True
        else:
            return False

    def get_overlapped_range(self, time_range):
        if not self.is_overlapped(time_range):
            return

        if time_range.start >= self.start:
            if self.end >= time_range.end:
                return TimeRange(time_range.start, time_range.end)
            else:
                return TimeRange(time_range.start, self.end)
        elif time_range.start < self.start:
            if time_range.end >= self.end:
                return TimeRange(self.start, self.end)
            else:
                return TimeRange(self.start, time_range.end)

    # def __repr__(self):
    #     return '{0} ------> {1}'.format(*[time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(d))
    #                                       for d in [self.start, self.end]])


if __name__ == '__main__':
    mydb = init_db_config()
    curs = mydb.cursor()
    wcd_id = 4
    ym = 201907
    year = int(str(ym)[:4])
    month = int(str(ym)[4:])
    wc_res = get_work_condition(curs, wcd_id)
    cl_res = get_category_law(curs)
    thismonthlastday =calendar.monthrange(year, month)[1]
    for i in range(1,thismonthlastday+1):
        tc_res = get_time_card(curs, ym, i, wcd_id)
        if len(tc_res) < 1 : continue
        # pprint(tc_res)
        # cd_ = list(filter(lambda tc_res: tc_res['type_code'] == 4, tc_res))[0]
        # pprint(cd_)
        calculate_daily(curs, tc_res, wc_res[0], cl_res[0])
        # break

    mydb.commit()
    mydb.close()
    # our_user = sess.query(dbm.User).all()
    # for instance in sess.query(dbm.User).order_by(dbm.User.id):
    #    print(instance.user_name, instance.user_id)
    # user_res = User.query.first()
    # print(our_user.__dict__)
    # sess.close()

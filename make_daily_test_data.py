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
                      passwd="0000",db="DRSLR_V7",cursorclass=MySQLdb.cursors.DictCursor)
    return db


def get_time_card(cur, target_ym, target_date, cont_id):
    cur.execute("""
        SELECT * FROM TimeCard
        WHERE
        target_ym = {0} 
        and target_date = {1}
        and cont_id = {2}
        ;
        """.format(target_ym,target_date,cont_id))

    return cur.fetchall()


def get_time_card_distinc(cur, target_ym, cont_id):
    cur.execute("""
        SELECT target_date FROM TimeCard
        WHERE
        target_ym = {0} and
        cont_id = {1}
        group by target_ym,target_date
        ;
        """.format(target_ym, cont_id))

    return cur.fetchall()


def get_work_condition(cur, wcond):
    cur.execute("""
            SELECT * FROM WorkCondition
            WHERE
            wcond_id = {0}
            ;
            """.format(wcond))

    return cur.fetchall()


def get_work_contract(cur, cont):
    cur.execute("""
            SELECT * FROM WorkContract
            WHERE
            cont_id = {0}
            ;
            """.format(cont))

    return cur.fetchall()


def get_absent(cur, target_ym ,cont):
    cur.execute("""
        select * 
        from WorkCondition as wc
        where cont_id = {1} 
        and target_ym = {0}
        and target_date 
        not in 
        (
            select
            tc.target_date 
            from TimeCard as tc 
            where tc.cont_id = {1} 
            and tc.target_ym = {0}
            and tc.target_ym = wc.target_ym 
            and tc.target_date = wc.target_date
        );
    """.format(target_ym, cont))

    return cur.fetchall()


# update_weekly(curs,ct_id,target_ym,)

def update_weekly(cur, cont_id, target_ym, week_num, cawt, cawp):
    cur.execute("""
            UPDATE Weekly
            set 
            total_time = TIMEDIFF(total_time, "{3}") , total_pay = total_pay - {4} , holy_dnum = 0 , weekly_pay = 0
            WHERE
            cont_id = {0} 
            and target_ym = {1} 
            and week_num = {2} ;
            """.format(cont_id,target_ym,week_num,cawt,int(cawp)))

    return cur.fetchall()


def update_daily(cur,d_id):
    cur.execute("""
            UPDATE Daily
            set 
            total_pay = total_pay - over_pay
            and over_time = holy_time
            and over_pay = holy_pay
            and holy_pay = 0
            and holy_time = "00:00"
            WHERE
            daily_id = {0}
            ;
            """.format(d_id))

    return cur.fetchall()


def get_weekly(cur, cont_id, target_ym, week_num):
    cur.execute("""
            SELECT * FROM Weekly
            WHERE
            cont_id = {0} and
            target_ym = {1} and
            week_num = {2}
            ;
            """.format(cont_id,target_ym,week_num))

    return cur.fetchall()


def get_daily_weekholy(cur,cont_id,target_ym,week_num,day_num):
    cur.execute("""
             SELECT daily_id FROM Daily
             WHERE
             cont_id = {0}
             and target_ym = {1}
             and week_num = {2}
             and day_num = {3}
             ;
             """.format(cont_id,target_ym,week_num,day_num))

    return cur.fetchall()


def get_category_law(cur):
    cur.execute("""
            SELECT * FROM CategoryLaw
            ;
            """)

    return cur.fetchall()


def calculate_daily_over(curs, timecard):
    tablename = "Daily"
    daily = {}
    null_time = timedelta(seconds=0)
    eight_time = timedelta(hours=8)
    # 야간 근무 범위 22시 ~ 익일 06시
    nt_range = TimeRange(timedelta(hours=22), timedelta(hours=30))
    # 야간 휴식
    rt_nt = null_time

    workcontract = get_work_contract(curs,timecard[0]["cont_id"])[0]

# -START 초기화
    st_tc = list(filter(lambda timecard: timecard['type_code'] == 1, timecard))[0]
    et_tc = list(filter(lambda timecard: timecard['type_code'] == 2, timecard))[0]

    if list(filter(lambda timecard: timecard['type_code'] == 3, timecard)) and list(filter(lambda timecard: timecard['type_code'] == 4, timecard)):
        rst_tc = list(filter(lambda timecard: timecard['type_code'] == 3, timecard))[0]
        ret_tc = list(filter(lambda timecard: timecard['type_code'] == 4, timecard))[0]

        art = ret_tc["in_time"] - rst_tc["in_time"]

        # 실제 휴식 시작/종료 계산용 시간 (Type:timedelta)
        rst_delta = timedelta(days=ret_tc["in_time"].day - st_tc["in_time"].day ,hours=rst_tc["in_time"].hour, minutes=rst_tc["in_time"].minute)
        ret_delta = timedelta(days=ret_tc["in_time"].day - st_tc["in_time"].day ,hours=ret_tc["in_time"].hour, minutes=ret_tc["in_time"].minute)

        rt_nt = TimeRange(rst_delta, ret_delta).get_overlapped_range(nt_range)

        if rt_nt is None:
            rt_nt = null_time
        else:
            rt_nt = rt_nt.duration

    else:
        art = null_time

    awt = (et_tc["in_time"] - st_tc["in_time"]) - art
    awp = convert_timedelta_to_float_hour(awt) * workcontract["hourly_pay"]

    t_ym = st_tc["target_ym"]
    t_dt = st_tc["target_date"]
    w_id = st_tc["wcond_id"]
    c_id = st_tc["cont_id"]

    target_cld = calendar.monthcalendar(int(t_ym[:4]), int(t_ym[4:6]))

    for i, v in enumerate(target_cld):
        for j, vv in enumerate(v):
            if vv == int(t_dt):
                week_num = i+1
                day_num = j+1


    # 실제 근무 시작/종료 계산용 시간 (Type:timedelta)
    st_delta = timedelta(hours=st_tc["in_time"].hour, minutes=st_tc["in_time"].minute)
    et_delta = timedelta(days=et_tc["in_time"].day) - timedelta(days=st_tc["in_time"].day) + timedelta(hours=et_tc["in_time"].hour,minutes=et_tc["in_time"].minute)

    if day_num == workcontract["week_holiday"] :
        hwt = awt
        hwp = convert_timedelta_to_float_hour(awt) * workcontract["hourly_pay"] * 0.5

        # 연장 근무 시간/급여 (Type:(owt=)timedelta , (owp=)int)
        owt = awt - eight_time if awt > eight_time else null_time
        owp = (convert_timedelta_to_float_hour(owt) * workcontract["hourly_pay"]) * 0.5 if owt is not null_time else 0
    else :
        hwt = null_time
        hwp = 0
        # 연장 근무 시간/급여 (Type:(owt=)timedelta , (owp=)int)
        owt = awt
        owp = (convert_timedelta_to_float_hour(owt) * workcontract["hourly_pay"]) * 0.5

    # 실제/야간 근무시간 범위 (Type:(class)TimeRange)
    at_range = TimeRange(st_delta,et_delta)
    # nt_range = TimeRange(timedelta(hours=22),timedelta(hours=30))

    # 실제근무시간 중 야간 근무시간 범위/급여 (Type:(ant=class)TimeRange , (anp=)int)
    ant = at_range.get_overlapped_range(nt_range).duration - rt_nt if at_range.is_overlapped(nt_range) else null_time
    anp = (convert_timedelta_to_float_hour(ant) * workcontract["hourly_pay"]) * 0.5 if ant is not null_time else 0

    # -START 할당
    daily["daily_id"] = "-".join([t_ym[2:]+t_dt,str(c_id),str(w_id),"2"])
    daily["wcond_id"] = w_id
    daily["cont_id"] = c_id
    daily["target_ym"] = t_ym
    daily["target_date"] = t_dt
    daily["week_num"] = week_num
    daily["day_num"] = day_num
    daily["work_start"] = st_tc["in_time"]
    daily["work_end"] = et_tc["in_time"]
    daily["act_work_time"] = awt
    daily["cont_work_time"] = null_time
    daily["act_rest_time"] = art
    daily["cont_rest_time"] = null_time
    daily["over_time"] = owt
    daily["night_time"] = ant
    daily["holy_time"] = hwt
    daily["tardy_time"] = null_time
    daily["act_work_pay"] = awp
    daily["cont_work_pay"] = 0
    # daily["minimum_work_pay"] = mwp
    daily["over_pay"] = owp # round(owp)
    daily["night_pay"] = anp # round(anp)
    daily["holy_pay"] = hwp
    daily["tardy_pay"] = 0

    daily["total_pay"] = daily["act_work_pay"] + daily["over_pay"] + daily["night_pay"] + daily["holy_pay"] + daily["tardy_pay"]
    # -END 할당

    insert_calculated_daily(curs, tablename, daily)


def calculate_daily(curs, timecard, workcondition, categorylaw):
    tablename = "Daily"

    if workcondition is None :
        pass

    daily = {}

    # Time 타입 null (00:00:00)
    null_time = timedelta(seconds=0)
    # 야간 근무 범위 22시 ~ 익일 06시
    nt_range = TimeRange(timedelta(hours=22), timedelta(hours=30))
    # 야간 휴식
    rt_nt = null_time

    # -START 초기화
    st_tc = list(filter(lambda timecard: timecard['type_code'] == 1, timecard))[0]
    et_tc = list(filter(lambda timecard: timecard['type_code'] == 2, timecard))[0]

    if list(filter(lambda timecard: timecard['type_code'] == 3, timecard)) and list(filter(lambda timecard: timecard['type_code'] == 4, timecard)):
        rst_tc = list(filter(lambda timecard: timecard['type_code'] == 3, timecard))[0]
        ret_tc = list(filter(lambda timecard: timecard['type_code'] == 4, timecard))[0]

        art = ret_tc["in_time"] - rst_tc["in_time"]

        add_owt = workcondition["arest_time"] - art if art < workcondition["arest_time"] else null_time

        # 실제 휴식 시작/종료 계산용 시간 (Type:timedelta)
        rst_delta = timedelta(days=ret_tc["in_time"].day - st_tc["in_time"].day ,hours=rst_tc["in_time"].hour, minutes=rst_tc["in_time"].minute)
        ret_delta = timedelta(days=ret_tc["in_time"].day - st_tc["in_time"].day ,hours=ret_tc["in_time"].hour, minutes=ret_tc["in_time"].minute)

        rt_nt = TimeRange(rst_delta,ret_delta).get_overlapped_range(nt_range)

        if rt_nt is None: rt_nt = null_time
        else : rt_nt = rt_nt.duration

    else:
        # art = workcondition["amount_rest_time"]

        # 최현욱 검증 수정 0805 휴게시간이 안찍혀있다면 계약된 휴식시간만큼 0.5
        art = null_time
        add_owt = workcondition["arest_time"]

    awt = (et_tc["in_time"] - st_tc["in_time"]) - art
    cwt = workcondition["awork_time"]

    # awp = round(convert_timedelta_to_float_hour(awt) * workcondition["hourly_pay"])
    # cwp = round(convert_timedelta_to_float_hour(cwt) * workcondition["hourly_pay"])
    awp = convert_timedelta_to_float_hour(awt) * workcondition["hourly_pay"]
    cwp = convert_timedelta_to_float_hour(cwt) * workcondition["hourly_pay"]

    # mwp = round(convert_timedelta_to_float_hour(awt) * categorylaw["minimum_wage"])

    t_ym = st_tc["target_ym"]
    t_dt = st_tc["target_date"]
    w_id = st_tc["wcond_id"]
    c_id = workcondition["cont_id"]
    # -END 초기화

    # 실제 근무 시작/종료 계산용 시간 (Type:timedelta)
    st_delta = timedelta(hours=st_tc["in_time"].hour, minutes=st_tc["in_time"].minute)
    et_delta = timedelta(days=et_tc["in_time"].day) - timedelta(days=st_tc["in_time"].day) + timedelta(hours=et_tc["in_time"].hour,minutes=et_tc["in_time"].minute)

    add_owt += workcondition["start_time"] - st_delta if workcondition["start_time"] > st_delta else null_time

    # 연장 근무 시간/급여 (Type:(owt=)timedelta , (owp=)int)
    # owt = et_delta - workcondition["end_work_time"] if et_delta > workcondition["end_work_time"] else null_time
    # 최현욱 검증 수정 0805 휴게시간이 안찍혀있다면 계약된 휴식시간만큼 0.5
    owt = (et_delta - workcondition["end_time"]) + add_owt if et_delta > workcondition["end_time"] else null_time + add_owt
    owp = (convert_timedelta_to_float_hour(owt) * workcondition["hourly_pay"]) * 0.5 if owt is not null_time else 0

    # 실제/야간 근무시간 범위 (Type:(class)TimeRange)
    at_range = TimeRange(st_delta,et_delta)
    # nt_range = TimeRange(timedelta(hours=22),timedelta(hours=30))

    # 실제근무시간 중 야간 근무시간 범위/급여 (Type:(ant=class)TimeRange , (anp=)int)
    ant = at_range.get_overlapped_range(nt_range).duration - rt_nt if at_range.is_overlapped(nt_range) else null_time
    anp = (convert_timedelta_to_float_hour(ant) * workcondition["hourly_pay"]) * 0.5 if ant is not null_time else 0

    # 지각 , 휴업 , 기타 수당 체크
    # IF 계약된출근시간 - 실제출근시간 > 0 : tardy_code 1 = 0 , 2 = 0.7 * hourly_pay * 늦은시간 , 3 = 1 * hourly_pay * 늦은시간
    if workcondition["tardy_code"] != 1 and \
            (st_delta + timedelta(days=st_tc["in_time"].day)) > (timedelta(days=int(workcondition["target_date"])) + workcondition["start_time"]):
        twt = (st_delta + timedelta(days=st_tc["in_time"].day)) - (timedelta(days=int(workcondition["target_date"])) + workcondition["start_time"])
        twp = convert_timedelta_to_float_hour(twt) * workcondition["hourly_pay"] if workcondition["tardy_code"] == 3 \
            else (convert_timedelta_to_float_hour(twt) * workcondition["hourly_pay"]) * 0.7
    else :
        twt = null_time
        twp = 0


    # -START 할당
    daily["daily_id"] = "-".join([t_ym[2:]+t_dt,"2",str(c_id),str(w_id),"1"])
    daily["wcond_id"] = w_id
    daily["cont_id"] = c_id
    daily["target_ym"] = t_ym
    daily["target_date"] = t_dt
    daily["week_num"] = workcondition["week_num"]
    daily["day_num"] = workcondition["day_num"]
    daily["work_start"] = st_tc["in_time"]
    daily["work_end"] = et_tc["in_time"]
    daily["act_work_time"] = awt
    daily["cont_work_time"] = null_time
    daily["act_rest_time"] = art
    daily["cont_rest_time"] = workcondition["arest_time"]
    daily["over_time"] = owt
    daily["night_time"] = ant
    daily["holy_time"] = null_time
    daily["tardy_time"] = twt
    daily["act_work_pay"] = awp
    daily["cont_work_pay"] = cwp
    # daily["minimum_work_pay"] = mwp
    daily["over_pay"] = owp # round(owp)
    daily["night_pay"] = anp # round(anp)
    daily["holy_pay"] = 0
    daily["tardy_pay"] = twp

    daily["total_pay"] = daily["act_work_pay"] + daily["over_pay"] + daily["night_pay"] + daily["holy_pay"] + daily["tardy_pay"]

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
    return num.total_seconds() / 3600


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
    ct_id = 7
    ym = 201907
    # year = int(str(ym)[:4])
    # month = int(str(ym)[4:])
    wcd_res = get_work_condition(curs, ct_id)
    tc_res_dst = get_time_card_distinc(curs, ym, ct_id)
    cl_res = get_category_law(curs)
    # thismonthlastday =calendar.monthrange(year, month)[1]
    # print(wcd_res)




    for tc in tc_res_dst:
        tc_res = get_time_card(curs,ym,tc["target_date"],ct_id)
        wcd_res = get_work_condition(curs,tc_res[0]["wcond_id"])
        if len(wcd_res) >= 1 :
            calculate_daily(curs, tc_res, wcd_res[0], cl_res)
        else :
            calculate_daily_over(curs,tc_res)


    absents = get_absent(curs,ym,ct_id)
    if absents is not None :
        for ab in absents :
            awt = ab["awork_time"]
            awp = convert_timedelta_to_float_hour(awt) * ab["hourly_pay"]
            wk = get_weekly(curs, ct_id, ym, ab["week_num"])[0]
            if wk["holy_dnum"] != 0:
                d_id = get_daily_weekholy(curs,ct_id,ym,ab["week_num"],wk["holy_dnum"])
                if len(d_id) > 0:
                    update_daily(curs, d_id[0])
            update_weekly(curs,ct_id,ym,ab["week_num"],awt,awp)


    # for wcd in wcd_res:
    #     ym = wcd["work_date"][:6]
    #     day = wcd["work_date"][6:]
    #     tc_res = get_time_card(curs, ym, day, wcd["wcond_id"])
    #     if len(tc_res) < 1 : continue
    #     # pprint(tc_res)
    #     # cd_ = list(filter(lambda tc_res: tc_res['type_code'] == 4, tc_res))[0]
    #     # pprint(cd_)
    #     calculate_daily(curs, tc_res, wcd, cl_res)
    #     # break

    mydb.commit()
    mydb.close()
    # our_user = sess.query(dbm.User).all()
    # for instance in sess.query(dbm.User).order_by(dbm.User.id):
    #    print(instance.user_name, instance.user_id)
    # user_res = User.query.first()
    # print(our_user.__dict__)
    # sess.close()

import MySQLdb as sql
import MySQLdb.cursors
from pprint import pprint
import calendar
import random
from datetime import datetime, timedelta


def init_db_config():
    db = sql.connect(host="localhost",user="root",
                      passwd="0000",db="DRSLR_V7",cursorclass=MySQLdb.cursors.DictCursor)
    # cur = db.cursor()
    return db
# cur.execute("SELECT * FROM TimeCard")
# res = cur.fetchall()


def get_work_condition(cur, wcont, uid):
    cur.execute("""
            SELECT * FROM WorkCondition
            WHERE
            cont_id = {0}
            ;
            """.format(wcont,uid))

    return cur.fetchall()


def get_work_contract(cur, cont):
    cur.execute("""
            SELECT * FROM WorkContract
            WHERE
            cont_id = {0}
            ;
            """.format(cont))

    return cur.fetchall()


def init_work_contract_to_condition(curs, uid, wpid, cont):
    tablename = "WorkCondition"

    wcont = get_work_contract(curs, cont)[0]
    start_date = wcont["cont_date"]
    start_ym = start_date[:6]
    target_cld = calendar.monthcalendar(int(start_date[:4]),int(start_date[4:6]))
    # pprint(target_cld)
    # pprint(wcont)

    for i,v in enumerate(target_cld):
        week_num = i+1
        total_weektime = timedelta(seconds=0)
        for_wkp = timedelta(seconds=0)
        weekly_item = {}

        chk_limit_time = timedelta(hours=8)

        for j,a in enumerate(v):
            if a is 0 : continue
            day_num = j+1
            nowd = wcont[str(day_num)+"_start_pot"]
            # print(day_num,a,nowd)
            if nowd is None : continue
            strit = str(a) if a >= 10 else "0" + str(a)
            wcond_item = make_condition_item(wcont,start_ym,strit,week_num,day_num)
            # str(day) if day >= 10 else "0" + str(day)
            worktime = wcont[str(day_num) + "_end_pot"] - wcont[str(day_num) + "_start_pot"] - wcont[str(day_num)+"_rest_aot"]
            for_wkp += worktime if worktime < chk_limit_time else chk_limit_time
            total_weektime += worktime

            insert_target_data(curs, tablename, wcond_item)

        weekly_item["cont_id"] = wcont["cont_id"]
        weekly_item["target_ym"] = start_ym
        weekly_item["week_num"] = week_num
        weekly_item["total_time"] = total_weektime
        weekly_item["total_pay"] = convert_timedelta_to_float_hour(total_weektime) * int(wcont["hourly_pay"])
        weekly_item["holy_dnum"] = wcont["week_holiday"]
        if for_wkp < timedelta(hours=15) :
            weekly_item["weekly_pay"] = 0
        else:
            if for_wkp > timedelta(hours=40) : cal_wkp = timedelta(hours=40)
            else : cal_wkp = for_wkp

            weekly_item["weekly_pay"] = convert_timedelta_to_float_hour(cal_wkp)/40 * 8 * 8350

        insert_target_data(curs,"Weekly",weekly_item)


def make_condition_item(wcont,target_ym,target_date,week_num,day_num):
    item = {}
    item["user_id"] = wcont["user_id"]
    item["wp_id"] = wcont["wp_id"]
    item["cont_id"] = wcont["cont_id"]
    item["target_ym"] = target_ym
    item["target_date"] = target_date
    item["week_num"] = week_num
    item["day_num"] = day_num
    item["start_time"] = wcont[str(day_num)+"_start_pot"]
    item["end_time"] = wcont[str(day_num)+"_end_pot"]
    item["arest_time"] = wcont[str(day_num) + "_rest_aot"]
    item["awork_time"] = item["end_time"] - item["start_time"] - item["arest_time"]
    item["hourly_pay"] = wcont["hourly_pay"]

    return item


# requirement : WorkCondition(유저+사업장 = 근무조건) 테스트 데이터 생성기 TimeCard
def make_time_card(curs, cont_id, wcond, case) :
    # pprint(wcond)
    sw_day = wcond["target_ym"]
    sw_time = wcond["start_time"]
    ew_time = wcond["end_time"]
    # rsw_time = wcond["start_rest_time"]
    # rew_time = wcond["end_rest_time"]
    wcond_id = wcond["wcond_id"]
    rt_aot = wcond["arest_time"]

    # 하루 당 코드 네개 / 각 코드별 기능 - 출근 1 퇴근 2 휴시 3 휴끝 4
    # 시작 날 ex) 201906 + 01 뒤에 일자 자르고 201906은 target_ym 으로
    # 01~09 앞에 prefix 0 붙혀 줘야 함
    # 01~30 or ~31 lv1 loop
    #   평일만 Insert / lib - datetime . weekday() return if 0~4 평일 else 5,6 주말
    # type code 1~4 lv2 loop
    #   in_time 분단위 랜덤 0~9분

    ym = wcond["target_ym"]
    # ym = str(int(ym) + 1)
    year = int(ym[:4])
    month = int(ym[4:6])
    # month += 1
    day = wcond["target_date"]

    # it = 1
    # thismonthlastday = calendar.monthrange(year, month)[1]

    if case == 1:
    # while it <= thismonthlastday :
        target_full_date = datetime(year, month, int(day))

        # strit = str(day) if day >= 10 else "0" + str(day)
        strit = day
        tc = {}

        tc["cont_id"] = cont_id
        tc["wcond_id"] = wcond_id
        tc["target_ym"] = ym

        tc["target_date"] = strit

        # code 1 출근
        # tc["in_time"] = target_full_date + sw_time + timedelta(minutes=random.randrange(30))
        # 상수 값
        tc["in_time"] = target_full_date + sw_time
        tc["type_code"] = 1
        insert_target_data(curs,"TimeCard",tc)
        # pprint(tc)

        # if rsw_time and rew_time:
        # code 3 휴식 시작
        tc["in_time"] = target_full_date + timedelta(hours=19)
        tc["type_code"] = 3
        insert_target_data(curs,"TimeCard",tc)
        # pprint(tc)
        # code 4 휴식 종료
        tc["in_time"] = target_full_date + timedelta(hours=19,minutes=30)
        tc["type_code"] = 4
        insert_target_data(curs,"TimeCard",tc)
        # END IF

        # if rsw_time and rew_time:
        #     # code 3 휴식 시작
        #     tc["in_time"] = target_full_date + rsw_time + timedelta(minutes=random.randrange(30))
        #     tc["type_code"] = 3
        #     insert_target_data(curs, "TimeCard", tc)
        #     # pprint(tc)
        #     # code 4 휴식 종료
        #     tc["in_time"] = target_full_date + rew_time + timedelta(minutes=random.randrange(30))
        #     tc["type_code"] = 4
        #     insert_target_data(curs, "TimeCard", tc)
        # END IF

        # code 2 퇴근
        # tc["in_time"] = target_full_date + ew_time + timedelta(minutes=random.randrange(30))
        # 상수 값
        tc["in_time"] = target_full_date + ew_time
        tc["type_code"] = 2
        insert_target_data(curs,"TimeCard",tc)
        # pprint(tc)
        # it += 1


def insert_target_data(curs, tablename, caled):
    columns = ','.join(caled.keys())
    placeholders = ','.join(['%s'] * len (caled))
    query = "insert into %s (%s) values (%s)" % (tablename, columns, placeholders)
    curs.execute(query, caled.values())


def convert_timedelta_to_float_hour(num):
    return num.total_seconds() / 3600


if __name__ == '__main__':
    my_db = init_db_config()
    curs = my_db.cursor()
    wct_id = 7
    user_id = 5
    wp_id = 5
    # ym = 201905

    # init_work_contract_to_condition(curs,user_id,wp_id,wct_id)
    wcond = get_work_condition(curs,wct_id,user_id)
    for cond in wcond:
        make_time_card(curs,wct_id,cond,1)

    my_db.commit()
    my_db.close()


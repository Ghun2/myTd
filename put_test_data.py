import MySQLdb as sql
import MySQLdb.cursors
from pprint import pprint
import calendar
import random
from datetime import datetime, timedelta


def init_db_config():
    db = sql.connect(host="localhost",user="root",
                      passwd="0000",db="DRSLR_V4",cursorclass=MySQLdb.cursors.DictCursor)
    # cur = db.cursor()
    return db
# cur.execute("SELECT * FROM TimeCard")
# res = cur.fetchall()


def get_work_condition(cur, wcond, uid):
    cur.execute("""
            SELECT * FROM WorkCondition
            WHERE
            wcond_id = {0} OR 
            user_id = {1}
            ;
            """.format(wcond,uid))

    return cur.fetchall()


def get_work_contract(cur, uid, wpid):
    cur.execute("""
            SELECT * FROM WorkContract
            WHERE
            user_id = {0} OR 
            wp_id = {1}
            ;
            """.format(uid,wpid))

    return cur.fetchall()


def init_work_contract_to_condition(curs, uid, wpid):
    tablename = "WorkCondition"

    wcont = get_work_contract(curs, uid, wpid)[0]
    start_date = wcont["cont_date"]
    start_ym = start_date[:6]
    target_cld = calendar.monthcalendar(int(start_date[:4]),int(start_date[4:6]))
    # pprint(target_cld)
    # pprint(wcont)
    for i,v in enumerate(target_cld):
        week_num = i+1
        # print(week_num,v)
        for j,a in enumerate(v):
            if a is 0 : continue
            day_num = j+1
            nowd = wcont[str(day_num)+"_start_pot"]
            # print(day_num,a,nowd)
            if nowd is None : continue
            strit = str(a) if a >= 10 else "0" + str(a)
            wcond_item = make_condition_item(wcont,start_ym+strit,week_num,day_num)

            insert_target_data(curs,tablename,wcond_item)


    # return wcont

def make_condition_item(wcont,work_date,week_num,day_num):
    item = {}
    item["user_id"] = wcont["user_id"]
    item["wp_id"] = wcont["wp_id"]
    item["cont_id"] = wcont["cont_id"]
    item["work_date"] = work_date
    item["week_num"] = week_num
    item["day_num"] = day_num
    item["start_work_time"] = wcont[str(day_num)+"_start_pot"]
    item["end_work_time"] = wcont[str(day_num)+"_end_pot"]
    item["amount_rest_time"] = wcont[str(day_num) + "_rest_aot"]
    item["amount_work_time"] = item["end_work_time"] - item["start_work_time"] - item["amount_rest_time"]
    item["hourly_pay"] = wcont["hourly_pay"]

    return item


# requirement : WorkCondition(유저+사업장 = 근무조건) 테스트 데이터 생성기 TimeCard
def insert_time_card(curs, wcond, case) :
    # pprint(wcond)
    sw_day = wcond["start_work_date"]
    sw_time = wcond["start_work_time"]
    ew_time = wcond["end_work_time"]
    rsw_time = wcond["start_rest_time"]
    rew_time = wcond["end_rest_time"]
    wcond_id = wcond["wcond_id"]

    # 하루 당 코드 네개 / 각 코드별 기능 - 출근 1 퇴근 2 휴시 3 휴끝 4
    # 시작 날 ex) 201906 + 01 뒤에 일자 자르고 201906은 target_ym 으로
    # 01~09 앞에 prefix 0 붙혀 줘야 함
    # 01~30 or ~31 lv1 loop
    #   평일만 Insert / lib - datetime . weekday() return if 0~4 평일 else 5,6 주말
    # type code 1~4 lv2 loop
    #   in_time 분단위 랜덤 0~9분

    ym = sw_day[:6]
    ym = str(int(ym) + 1)
    year = int(sw_day[:4])
    month = int(sw_day[4:6])
    month += 1
    day = int(sw_day[6:])

    it = 1
    thismonthlastday = calendar.monthrange(year, month)[1]

    if case == 1:
        while it <= thismonthlastday :
            target_full_date = datetime(year, month, it)

            if target_full_date.weekday() in [5,6]: it+=1; continue

            strit = str(it) if it >= 10 else "0" + str(it)
            tc = {}

            tc["wcond_id"] = wcond_id
            tc["target_ym"] = ym

            tc["target_date"] = strit

            # code 1 출근
            tc["in_time"] = target_full_date + sw_time + timedelta(minutes=random.randrange(30))
            tc["type_code"] = 1
            insert_target_data(curs,"TimeCard",tc)
            # pprint(tc)

            if rsw_time and rew_time:
                # code 3 휴식 시작
                tc["in_time"] = target_full_date + rsw_time + timedelta(minutes=random.randrange(30))
                tc["type_code"] = 3
                insert_target_data(curs,"TimeCard",tc)
                # pprint(tc)
                # code 4 휴식 종료
                tc["in_time"] = target_full_date + rew_time + timedelta(minutes=random.randrange(30))
                tc["type_code"] = 4
                insert_target_data(curs,"TimeCard",tc)
            # pprint(tc)
            # code 2 퇴근
            tc["in_time"] = target_full_date + ew_time + timedelta(minutes=random.randrange(30))
            tc["type_code"] = 2
            insert_target_data(curs,"TimeCard",tc)
            # pprint(tc)
            it += 1


def insert_target_data(curs, tablename, caled):
    columns = ','.join(caled.keys())
    placeholders = ','.join(['%s'] * len (caled))
    query = "insert into %s (%s) values (%s)" % (tablename, columns, placeholders)
    curs.execute(query, caled.values())


if __name__ == '__main__':
    my_db = init_db_config()
    curs = my_db.cursor()
    wcd_id = 6
    user_id = 7
    wp_id = 8
    # ym = 201905

    init_work_contract_to_condition(curs,user_id,wp_id)
    # pprint(wcres)
    # wcond = get_work_condition(curs,wcd_id,user_id)
    # pprint(wcond)
    # insert_time_card(curs,wcond[0],1)

    my_db.commit()
    my_db.close()


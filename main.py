import json,pymysql,time
from flask import Flask
from flask import request,redirect
import datetime
import yaml
import time

app = Flask(__name__)

db_config = None
with open("config.yml", "r") as file:
    config = yaml.safe_load(file)
    db_config = config['mysql']     

def auth(token):
    if token is None:
        return False

    if token == "123":
        return True
    else:
        return False

def log(token,endpoint,response):
    conn = pymysql.connect(**db_config) #setup our credentials
    cur = conn.cursor(pymysql.cursors.DictCursor)
    sql = 'INSERT INTO `mhikei_api_logs` (`endpoint`,`token`,`response`,`dt`) VALUES (%s,%s,%s,%s)'
    dt = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cur.execute(sql,(endpoint,token,response,dt))
    conn.commit()
    cur.close()
    conn.close()

def create_log_table():
    conn = pymysql.connect(**db_config)
    cur = conn.cursor()

    sql = """
    CREATE TABLE IF NOT EXISTS mhikei_api_logs (
        id INT AUTO_INCREMENT PRIMARY KEY,
        endpoint VARCHAR(100),
        token VARCHAR(100),
        response VARCHAR(50),
        dt DATETIME
    )
    """
    cur.execute(sql)
    cur.close()
    conn.close()
    
    
@app.route("/", methods=['GET','POST'])
def root():
    res = {} 
    res['code'] = 2
    res['msg'] = 'No endpoint specified'
    res['req'] = '/'
    return json.dumps(res,indent=4)
    #return '<b>hello</b>'

@app.route("/getData", methods=['GET'])
def getData():
        res = {}
        res['req'] = '/getData'
        
        token = request.args.get('key')
        start = request.args.get('start')
        end = request.args.get('end')
        
        if not auth(token):
         res['code'] = 0
         res['msg'] = 'auth error'
         res['sqltime'] = 0
         log(token, res['req'], '401')
         return json.dumps(res, indent=4)
  
        if not start or not end:
         res['code'] = 0
         res['msg'] = 'start and end dates are required'
         res['sqltime'] = 0
         log(token, res['req'], '400')
         return json.dumps(res, indent=4)

        try:
                start_dt = datetime.datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
                end_dt = datetime.datetime.strptime(end, '%Y-%m-%d %H:%M:%S')

        except ValueError:
                res['code'] = 0
                res['msg'] = 'Invalid date format. Use YYYY-MM-DD HH:MM:SS'
                res['sqltime'] = 0
                log(token, res['req'], '400')
                return json.dumps(res, indent=4)
    
        if start_dt > end_dt:
         res['code'] = 0
         res['msg'] = 'Start date cannot be later than end date'
         res['sqltime'] = 0
         log(token, res['req'], '400')
         return json.dumps(res, indent=4)
    
        print("DEBUG: Reached database query")
        conn = pymysql.connect(**db_config)
        cur = conn.cursor(pymysql.cursors.DictCursor)

        sql = """
                        SELECT *
                        FROM class_datapoints
                        WHERE date_time BETWEEN %s AND %s
                        ORDER BY date_time
                        LIMIT 500
                        """

        query_start = time.perf_counter()
        cur.execute(sql, (start_dt, end_dt))
        items = cur.fetchall()
        sqltime = time.perf_counter() - query_start

        cur.close()
        conn.close()
                    
        res['code'] = 1
        res['msg'] = 'ok'
        res['sqltime'] = sqltime
        res['results'] = items
        res['num_results'] = len(items)

        log(token, res['req'], '200')
        return json.dumps(res, indent=4, default=str)
    


@app.route("/countInPolygon", methods=['GET'])
def countInPolygon():
    res = {}
    res['req'] = '/countInPolygon'

    token = request.args.get('key')
    polygon = request.args.get('polygon')

    if not auth(token):
        res['code'] = 0
        res['msg'] = 'auth error'
        res['sqltime'] = 0
        log(token, res['req'], '401')
        return json.dumps(res, indent=4)

    if not polygon:
        res['code'] = 0
        res['msg'] = 'polygon is required'
        res['sqltime'] = 0
        log(token, res['req'], '400')
        return json.dumps(res, indent=4)

    try:
        points = []
        for pair in polygon.split(','):
            coords = pair.strip().split()
            if len(coords) != 2:
                raise ValueError("Invalid coordinates")
            x, y = map(float, coords)
            points.append((x, y))

        if len(points) < 4 or points[0] != points[-1]:
            raise ValueError("Polygon must be closed")

        coordinates = ','.join(
            f'{x} {y}' for x, y in points
        )
        polygon_wkt = f'POLYGON(({coordinates}))'

    except ValueError:
        res['code'] = 0
        res['msg'] = 'Invalid polygon format'
        res['sqltime'] = 0
        log(token, res['req'], '400')
        return json.dumps(res, indent=4)

    conn = pymysql.connect(**db_config)
    cur = conn.cursor()

    sql = """
        SELECT COUNT(*)
        FROM class_datapoints
        WHERE ST_Within(
            geo_point,
            ST_GeomFromText(%s, 0)
        )
    """

    query_start = time.time()
    cur.execute(sql, (polygon_wkt,))
    count = cur.fetchone()[0]
    sqltime = time.time() - query_start

    cur.close()
    conn.close()

    res['code'] = 1
    res['msg'] = 'ok'
    res['sqltime'] = sqltime
    res['count'] = count

    log(token, res['req'], '200')
    return json.dumps(res, indent=4)


@app.route("/getAvgSpeedByFlight", methods=['GET'])
def getAvgSpeedByFlight():
    res = {}
    res['req'] = '/getAvgSpeedByFlight'

    token = request.args.get('key')
    start = request.args.get('start')
    end = request.args.get('end')

    if not auth(token):
        res['code'] = 0
        res['msg'] = 'auth error'
        res['sqltime'] = 0
        log(token, res['req'], '401')
        return json.dumps(res, indent=4)

    # Dates are optional
    try:
        start_dt = (
            datetime.datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
            if start else None
        )
        end_dt = (
            datetime.datetime.strptime(end, '%Y-%m-%d %H:%M:%S')
            if end else None
        )
    except ValueError:
        res['code'] = 0
        res['msg'] = 'Invalid date format. Use YYYY-MM-DD HH:MM:SS'
        res['sqltime'] = 0
        log(token, res['req'], '400')
        return json.dumps(res, indent=4)

    if start_dt and end_dt and start_dt > end_dt:
        res['code'] = 0
        res['msg'] = 'Start date cannot be later than end date'
        res['sqltime'] = 0
        log(token, res['req'], '400')
        return json.dumps(res, indent=4)

    sql = """
        SELECT flight_num, AVG(gs) AS avg_speed
        FROM class_datapoints
    """

    conditions = []
    params = []

    if start_dt:
        conditions.append("date_time >= %s")
        params.append(start_dt)

    if end_dt:
        conditions.append("date_time <= %s")
        params.append(end_dt)

    if conditions:
        sql += " WHERE " + " AND ".join(conditions)

    sql += """
        GROUP BY flight_num
        ORDER BY flight_num
        LIMIT 500
    """

    conn = pymysql.connect(**db_config)
    cur = conn.cursor(pymysql.cursors.DictCursor)

    query_start = time.time()
    cur.execute(sql, tuple(params))
    items = cur.fetchall()
    sqltime = time.time() - query_start

    cur.close()
    conn.close()

    res['code'] = 1
    res['msg'] = 'ok'
    res['sqltime'] = sqltime
    res['results'] = items
    res['num_results'] = len(items)

    log(token, res['req'], '200')
    return json.dumps(res, indent=4, default=str)


if __name__ == "__main__":
    create_log_table()
    app.run(host='127.0.0.1', debug=True)
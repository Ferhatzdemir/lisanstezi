# anahtar değer şeklinde gelen veriyi bölmemize sağlar
import json
import sqlite3
# tarih zaman Kütüphanesi
from datetime import datetime, timedelta, timezone

# vericekmeye yardımcı olan kütüphane
import requests
from flask import Flask, request, render_template

app = Flask(__name__)

DB_LOCATION = "sensor.db"

# openweathermap.org kayıt olarak aldığımız anahtar
API_KEY = '10d816fd2ad802ecc70b04f152c75208'
SEHIR_ISMI = 'Isparta'


def create_tables():
    sql_queries = [
        'CREATE TABLE IF NOT EXISTS "sensorveri" ("ID"	INTEGER,"deger"	INTEGER,"tarih"	TEXT,PRIMARY KEY("ID" AUTOINCREMENT))',
        'CREATE TABLE IF NOT EXISTS "sarjveri" ("ID"	INTEGER,"sarjdeger"	INTEGER,"tarih"	TEXT,PRIMARY KEY("ID" AUTOINCREMENT))',
        'CREATE TABLE IF NOT EXISTS "sureveri" ("ID"	INTEGER,"suredeger"	INTEGER,"tarih"	TEXT)']

    con = sqlite3.connect(DB_LOCATION)
    cur = con.cursor()
    for query in sql_queries:
        cur.execute(query)


def kelvin_to_celcius(kelvin_degree):
    return round((kelvin_degree - 273.15), 2)


@app.route("/bulanik/")
def baslangic():
    # hangi şehirin havadurumunu istediğimizi tanımlıyoruz
    # SEHIR_ISMI=input("Şehir İsmi Giriniz")
    # istek atacağımız url
    orgin_url = f'http://api.openweathermap.org/data/2.5/weather?q={SEHIR_ISMI}&appid={API_KEY}'
    # response değeri tanımlayarak istek yapıyoruz
    response = requests.get(orgin_url)
    # veriyi jsonlaştırıyoruz
    json_response = json.loads(response.text)
    # Hava Durumunun nasıl olduğunu çekiyoruz
    sky_description = json_response['weather'][0]['description']
    # hava durumunun ingilizceden türkçeye ceviriyoruz
    sky_types = ['clear sky', 'few clouds', 'overcast clouds', 'scattered clouds', 'broken clouds', 'shower rain',
                 'rain', 'thunderstorm', 'snow', 'mist', 'light rain']
    sky_types_tr = ['Güneşli', 'Az Bulutlu', 'Çok Bulutlu(Kapalı)', 'Alçak Bulutlu', 'Yer Yer Açık Bulutlu',
                    'Sağanak Yağmurlu', 'Yağmurlu', 'Gök Gürültülü Fırtına', 'Karlı', 'Sisli', 'Hafif Yağmurlu']
    for i in range(len(sky_types)):
        if sky_description == sky_types[i]:
            sky_description = sky_types_tr[i]

    # For temp: Kelvin to Celcius:
    # Sıcaklık bilgisini Kelvin den Celcius a çevirir ve aşağıdaki değişkenlerin içine atar.
    temp = kelvin_to_celcius(json_response['main']['temp'])  # Genel sıcaklık
    feels_temp = kelvin_to_celcius(json_response['main']['feels_like'])  # hissedilen
    temp_min = kelvin_to_celcius(json_response['main']['temp_min'])  # Minimum
    temp_max = kelvin_to_celcius(json_response['main']['temp_max'])  # Maksimum
    cloud_rate = json_response['clouds']['all']  # bulutluluk oranı
    humidity = json_response['main']['humidity']  # nem oranı
    sunset_unix = json_response["sys"]["sunset"]  # gün batımı
    sunrise_unix = json_response["sys"]["sunrise"]  # gün doğusu
    datatime = json_response["dt"]  # veriyi aldığımız saati alıyoruz

    # unix saati GTC tarzına çeviriyoruz
    sunset = datetime.fromtimestamp(sunset_unix).strftime(' %H:%M:%S')
    sunrise = datetime.fromtimestamp(sunrise_unix).strftime(' %H:%M:%S')
    datatime_real = datetime.fromtimestamp(datatime).strftime('%d-%m-%y %H:%M:%S')

    import skfuzzy as fuzz
    import numpy as np
    from skfuzzy import control as ctrl

    b = ctrl.Antecedent(np.arange(0, 101, 1), 'bulut')
    s = ctrl.Antecedent(np.arange(0, 101, 1), 'sarj')
    t = ctrl.Consequent(np.arange(0, 13, 1), 'sure')

    b['Acik'] = fuzz.trimf(b.universe, [0, 0, 10])
    b['Az'] = fuzz.trimf(b.universe, [5, 10, 25])
    b['Parcali'] = fuzz.trimf(b.universe, [15, 38, 60])
    b['Bulutlu'] = fuzz.trimf(b.universe, [50, 68, 85])
    b['Kapali'] = fuzz.trimf(b.universe, [80, 100, 100])

    s['CD'] = fuzz.trimf(s.universe, [0, 13, 25])
    s['D'] = fuzz.trimf(s.universe, [20, 33, 45])
    s['I'] = fuzz.trimf(s.universe, [40, 55, 70])
    s['Y'] = fuzz.trimf(s.universe, [60, 73, 85])
    s['CY'] = fuzz.trimf(s.universe, [80, 100, 100])

    t['CK'] = fuzz.trimf(t.universe, [1, 1, 3])
    t['K'] = fuzz.trimf(t.universe, [2, 3, 5])
    t['O'] = fuzz.trimf(t.universe, [4, 5, 7])
    t['U'] = fuzz.trimf(t.universe, [6, 8, 10])
    t['CU'] = fuzz.trimf(t.universe, [8, 12, 12])

    rule1 = ctrl.Rule(b['Acik'] & s['CD'], t['O'])
    rule2 = ctrl.Rule(b['Acik'] & s['D'], t['O'])
    rule3 = ctrl.Rule(b['Acik'] & s['I'], t['K'])
    rule4 = ctrl.Rule(b['Acik'] & s['Y'], t['CK'])
    rule5 = ctrl.Rule(b['Acik'] & s['CY'], t['CK'])
    rule6 = ctrl.Rule(b['Az'] & s['CD'], t['O'])
    rule7 = ctrl.Rule(b['Az'] & s['D'], t['O'])
    rule8 = ctrl.Rule(b['Az'] & s['I'], t['K'])
    rule9 = ctrl.Rule(b['Az'] & s['Y'], t['K'])
    rule10 = ctrl.Rule(b['Az'] & s['CY'], t['CK'])
    rule11 = ctrl.Rule(b['Parcali'] & s['CD'], t['U'])
    rule12 = ctrl.Rule(b['Parcali'] & s['D'], t['U'])
    rule13 = ctrl.Rule(b['Parcali'] & s['I'], t['O'])
    rule14 = ctrl.Rule(b['Parcali'] & s['Y'], t['K'])
    rule15 = ctrl.Rule(b['Parcali'] & s['CY'], t['K'])
    rule16 = ctrl.Rule(b['Bulutlu'] & s['CD'], t['CU'])
    rule17 = ctrl.Rule(b['Bulutlu'] & s['D'], t['U'])
    rule18 = ctrl.Rule(b['Bulutlu'] & s['I'], t['O'])
    rule19 = ctrl.Rule(b['Bulutlu'] & s['Y'], t['O'])
    rule20 = ctrl.Rule(b['Bulutlu'] & s['CY'], t['K'])
    rule21 = ctrl.Rule(b['Kapali'] & s['CD'], t['CU'])
    rule22 = ctrl.Rule(b['Kapali'] & s['D'], t['U'])
    rule23 = ctrl.Rule(b['Kapali'] & s['I'], t['U'])
    rule24 = ctrl.Rule(b['Kapali'] & s['Y'], t['O'])
    rule25 = ctrl.Rule(b['Kapali'] & s['CY'], t['O'])

    altitude_ctrl = ctrl.ControlSystem([
        rule1, rule2, rule3, rule4, rule5, rule6, rule7, rule8, rule9, rule10, rule11, rule12, rule13, rule14, rule15,
        rule16, rule17, rule18, rule19, rule20, rule21, rule22, rule23, rule24, rule25
    ])

    altitude_sim = ctrl.ControlSystemSimulation(altitude_ctrl)
    sarj = request.args.get("sarj")

    altitude_sim.input['bulut'] = cloud_rate
    altitude_sim.input['sarj'] = float(sarj)
    altitude_sim.compute()
    x = altitude_sim.output['sure']

    return str(int(x * 3600 * 1000))


@app.route("/")
def anasayfa():
    return render_template("index.html")


@app.route("/sensorveri")
def sensorverigetir():
    create_tables()
    con = sqlite3.connect(DB_LOCATION)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("SELECT*FROM sensorveri ORDER BY tarih DESC")
    rows = cur.fetchall()
    return render_template("sensorveri.html", rows=rows)


@app.route("/sarjveri")
def sarjverigetir():
    create_tables()
    con = sqlite3.connect(DB_LOCATION)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("SELECT * FROM sarjveri ORDER BY tarih DESC")
    rows = cur.fetchall()
    return render_template("sarjveri.html", rows=rows)


@app.route("/sureveri")
def sureverigetir():
    create_tables()
    con = sqlite3.connect(DB_LOCATION)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("SELECT * FROM sureveri ORDER BY tarih DESC")
    rows = cur.fetchall()
    return render_template("sureveri.html", rows=rows)




@app.route("/sensoradd", methods=["GET"])
def sensoradd():
    if request.method == "GET":
        time = datetime.now(timezone.utc) + timedelta(hours=3)
        tarih = time.strftime("%d/%m/%Y %H:%M:%S")
        sensordeger = request.args.get("sensordeger")

        with sqlite3.connect(DB_LOCATION) as con:
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute("INSERT INTO sensorveri (deger,tarih) VALUES (?,?)", (sensordeger, tarih))
            con.commit()

    return "Success"


@app.route("/sarjadd", methods=["GET"])
def sarjadd():
    if request.method == "GET":
        time = datetime.now(timezone.utc) + timedelta(hours=3)
        tarih = time.strftime("%d/%m/%Y %H:%M:%S")
        sarjdeger = request.args.get("sarjdeger")

        with sqlite3.connect(DB_LOCATION) as con:
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute("INSERT INTO sarjveri (sarjdeger,tarih) VALUES (?,?)", (sarjdeger, tarih))
            con.commit()

    return "Success"


if __name__ == "__main__":
    app.run()

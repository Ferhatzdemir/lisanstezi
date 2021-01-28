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
    e = ctrl.Antecedent(np.arange(1.8, 3.8, 0.2), 'esp')
    m = ctrl.Antecedent(np.arange(0.0, 1.0, 0.1), 'mppt')
    t = ctrl.Consequent(np.arange(0, 25, 2), 'sure')

    b['A'] = fuzz.trimf(b.universe, [0, 0, 35])
    b['L'] = fuzz.trimf(b.universe, [0, 35, 70])
    b['P'] = fuzz.trimf(b.universe, [35, 70, 100])
    b['K'] = fuzz.trimf(b.universe, [70, 100, 100])

    e['CA'] = fuzz.trimf(e.universe, [1.8, 1.8, 2.4])
    e['A'] = fuzz.trimf(e.universe, [1.8, 2.4, 3.0])
    e['F'] = fuzz.trimf(e.universe, [2.4, 3.0, 3.6])
    e['CF'] = fuzz.trimf(e.universe, [3.0, 3.6, 3.6])

    m['CK'] = fuzz.trimf(m.universe, [0.0, 0.0, 0.3])
    m['K'] = fuzz.trimf(m.universe, [0.0, 0.3, 0.6])
    m['I'] = fuzz.trimf(m.universe, [0.3, 0.6, 0.9])
    m['CI'] = fuzz.trimf(m.universe, [0.6, 0.9, 0.9])

    s['CD'] = fuzz.trimf(s.universe, [0, 0, 25])
    s['D'] = fuzz.trimf(s.universe, [0, 25, 50])
    s['Y'] = fuzz.trimf(s.universe, [25, 50, 75])
    s['CY'] = fuzz.trimf(s.universe, [50, 75, 100])

    t['CK'] = fuzz.trimf(t.universe, [0, 0, 8])
    t['K'] = fuzz.trimf(t.universe, [0, 8, 16])
    t['U'] = fuzz.trimf(t.universe, [8, 16, 24])
    t['CU'] = fuzz.trimf(t.universe, [16, 24, 24])
    """
    import itertools
    c=itertools.combinations([b['A'],b['L'],b['P'],b['K'],e['CA'],e['A'],e['F'],e['CF'],m['CK'],m['K'],m['I'],m['CI'],s['CD'],s['D'],s['Y'],s['CY'],t['CK'],t['K'],t['U'],t['CU']], 4)
    for i in list(c):
        print ("rule = ctrl.Rule(" + str(i) + ")")
    """

    rule1 = ctrl.Rule(b['A'] & s['CD'] & e['CA'] & m['CK'], t['CU'])
    rule2 = ctrl.Rule(b['A'] & s['CD'] & e['CA'] & m['K'], t['CU'])
    rule3 = ctrl.Rule(b['A'] & s['CD'] & e['CA'] & m['I'], t['U'])
    rule4 = ctrl.Rule(b['A'] & s['CD'] & e['CA'] & m['CI'], t['U'])
    rule5 = ctrl.Rule(b['A'] & s['CD'] & e['A'] & m['CK'], t['CU'])
    rule6 = ctrl.Rule(b['A'] & s['CD'] & e['A'] & m['K'], t['U'])
    rule7 = ctrl.Rule(b['A'] & s['CD'] & e['A'] & m['I'], t['U'])
    rule8 = ctrl.Rule(b['A'] & s['CD'] & e['A'] & m['CI'], t['U'])
    rule9 = ctrl.Rule(b['A'] & s['CD'] & e['F'] & m['CK'], t['CU'])
    rule10 = ctrl.Rule(b['A'] & s['CD'] & e['F'] & m['K'], t['CU'])
    rule11 = ctrl.Rule(b['A'] & s['CD'] & e['F'] & m['I'], t['U'])
    rule12 = ctrl.Rule(b['A'] & s['CD'] & e['F'] & m['CI'], t['U'])
    rule13 = ctrl.Rule(b['A'] & s['CD'] & e['CF'] & m['CK'], t['CU'])
    rule14 = ctrl.Rule(b['A'] & s['CD'] & e['CF'] & m['K'], t['CU'])
    rule15 = ctrl.Rule(b['A'] & s['CD'] & e['CF'] & m['I'], t['CU'])
    rule16 = ctrl.Rule(b['A'] & s['CD'] & e['CF'] & m['CI'], t['U'])
    rule17 = ctrl.Rule(b['A'] & s['D'] & e['CA'] & m['CK'], t['U'])
    rule18 = ctrl.Rule(b['A'] & s['D'] & e['CA'] & m['K'], t['U'])
    rule19 = ctrl.Rule(b['A'] & s['D'] & e['CA'] & m['I'], t['U'])
    rule20 = ctrl.Rule(b['A'] & s['D'] & e['CA'] & m['CI'], t['K'])
    rule21 = ctrl.Rule(b['A'] & s['D'] & e['A'] & m['CK'], t['U'])
    rule22 = ctrl.Rule(b['A'] & s['D'] & e['A'] & m['K'], t['U'])
    rule23 = ctrl.Rule(b['A'] & s['D'] & e['A'] & m['I'], t['U'])
    rule24 = ctrl.Rule(b['A'] & s['D'] & e['A'] & m['CI'], t['U'])
    rule25 = ctrl.Rule(b['A'] & s['D'] & e['F'] & m['CK'], t['U'])
    rule26 = ctrl.Rule(b['A'] & s['D'] & e['F'] & m['K'], t['U'])
    rule27 = ctrl.Rule(b['A'] & s['D'] & e['F'] & m['I'], t['U'])
    rule28 = ctrl.Rule(b['A'] & s['D'] & e['F'] & m['CI'], t['U'])
    rule29 = ctrl.Rule(b['A'] & s['D'] & e['CF'] & m['CK'], t['CU'])
    rule30 = ctrl.Rule(b['A'] & s['D'] & e['CF'] & m['K'], t['CU'])
    rule31 = ctrl.Rule(b['A'] & s['D'] & e['CF'] & m['I'], t['U'])
    rule32 = ctrl.Rule(b['A'] & s['D'] & e['CF'] & m['CI'], t['K'])
    rule33 = ctrl.Rule(b['A'] & s['Y'] & e['CA'] & m['CK'], t['K'])
    rule34 = ctrl.Rule(b['A'] & s['Y'] & e['CA'] & m['K'], t['K'])
    rule35 = ctrl.Rule(b['A'] & s['Y'] & e['CA'] & m['I'], t['CK'])
    rule36 = ctrl.Rule(b['A'] & s['Y'] & e['CA'] & m['CI'], t['CK'])
    rule37 = ctrl.Rule(b['A'] & s['Y'] & e['A'] & m['CK'], t['K'])
    rule38 = ctrl.Rule(b['A'] & s['Y'] & e['A'] & m['K'], t['K'])
    rule39 = ctrl.Rule(b['A'] & s['Y'] & e['A'] & m['I'], t['CK'])
    rule40 = ctrl.Rule(b['A'] & s['Y'] & e['A'] & m['CI'], t['CK'])
    rule41 = ctrl.Rule(b['A'] & s['Y'] & e['F'] & m['CK'], t['K'])
    rule42 = ctrl.Rule(b['A'] & s['Y'] & e['F'] & m['K'], t['K'])
    rule43 = ctrl.Rule(b['A'] & s['Y'] & e['F'] & m['I'], t['K'])
    rule44 = ctrl.Rule(b['A'] & s['Y'] & e['F'] & m['CI'], t['CK'])
    rule45 = ctrl.Rule(b['A'] & s['Y'] & e['CF'] & m['CK'], t['K'])
    rule46 = ctrl.Rule(b['A'] & s['Y'] & e['CF'] & m['K'], t['K'])
    rule47 = ctrl.Rule(b['A'] & s['Y'] & e['CF'] & m['I'], t['K'])
    rule48 = ctrl.Rule(b['A'] & s['Y'] & e['CF'] & m['CI'], t['CK'])
    rule49 = ctrl.Rule(b['A'] & s['CY'] & e['CA'] & m['CK'], t['K'])
    rule50 = ctrl.Rule(b['A'] & s['CY'] & e['CA'] & m['K'], t['CK'])
    rule51 = ctrl.Rule(b['A'] & s['CY'] & e['CA'] & m['I'], t['CK'])
    rule52 = ctrl.Rule(b['A'] & s['CY'] & e['CA'] & m['CI'], t['CK'])
    rule53 = ctrl.Rule(b['A'] & s['CY'] & e['A'] & m['CK'], t['CK'])
    rule54 = ctrl.Rule(b['A'] & s['CY'] & e['A'] & m['K'], t['CK'])
    rule55 = ctrl.Rule(b['A'] & s['CY'] & e['A'] & m['I'], t['CK'])
    rule56 = ctrl.Rule(b['A'] & s['CY'] & e['A'] & m['CI'], t['CK'])
    rule57 = ctrl.Rule(b['A'] & s['CY'] & e['F'] & m['CK'], t['K'])
    rule58 = ctrl.Rule(b['A'] & s['CY'] & e['F'] & m['K'], t['K'])
    rule59 = ctrl.Rule(b['A'] & s['CY'] & e['F'] & m['I'], t['K'])
    rule60 = ctrl.Rule(b['A'] & s['CY'] & e['F'] & m['CI'], t['CK'])
    rule61 = ctrl.Rule(b['A'] & s['CY'] & e['CF'] & m['CK'], t['CK'])
    rule62 = ctrl.Rule(b['A'] & s['CY'] & e['CF'] & m['K'], t['CK'])
    rule63 = ctrl.Rule(b['A'] & s['CY'] & e['CF'] & m['I'], t['CK'])
    rule64 = ctrl.Rule(b['A'] & s['CY'] & e['CF'] & m['CI'], t['CK'])
    rule65 = ctrl.Rule(b['L'] & s['CD'] & e['CA'] & m['CK'], t['CU'])
    rule66 = ctrl.Rule(b['L'] & s['CD'] & e['CA'] & m['K'], t['CU'])
    rule67 = ctrl.Rule(b['L'] & s['CD'] & e['CA'] & m['I'], t['U'])
    rule68 = ctrl.Rule(b['L'] & s['CD'] & e['CA'] & m['CI'], t['U'])
    rule69 = ctrl.Rule(b['L'] & s['CD'] & e['A'] & m['CK'], t['U'])
    rule70 = ctrl.Rule(b['L'] & s['CD'] & e['A'] & m['K'], t['U'])
    rule71 = ctrl.Rule(b['L'] & s['CD'] & e['A'] & m['I'], t['U'])
    rule72 = ctrl.Rule(b['L'] & s['CD'] & e['A'] & m['CI'], t['U'])
    rule73 = ctrl.Rule(b['L'] & s['CD'] & e['F'] & m['CK'], t['CU'])
    rule74 = ctrl.Rule(b['L'] & s['CD'] & e['F'] & m['K'], t['CU'])
    rule75 = ctrl.Rule(b['L'] & s['CD'] & e['F'] & m['I'], t['CU'])
    rule76 = ctrl.Rule(b['L'] & s['CD'] & e['F'] & m['CI'], t['U'])
    rule77 = ctrl.Rule(b['L'] & s['CD'] & e['CF'] & m['CK'], t['CU'])
    rule78 = ctrl.Rule(b['L'] & s['CD'] & e['CF'] & m['K'], t['CU'])
    rule79 = ctrl.Rule(b['L'] & s['CD'] & e['CF'] & m['I'], t['CU'])
    rule80 = ctrl.Rule(b['L'] & s['CD'] & e['CF'] & m['CI'], t['U'])
    rule81 = ctrl.Rule(b['L'] & s['D'] & e['CA'] & m['CK'], t['U'])
    rule82 = ctrl.Rule(b['L'] & s['D'] & e['CA'] & m['K'], t['U'])
    rule83 = ctrl.Rule(b['L'] & s['D'] & e['CA'] & m['I'], t['U'])
    rule84 = ctrl.Rule(b['L'] & s['D'] & e['CA'] & m['CI'], t['K'])
    rule85 = ctrl.Rule(b['L'] & s['D'] & e['A'] & m['CK'], t['U'])
    rule86 = ctrl.Rule(b['L'] & s['D'] & e['A'] & m['K'], t['U'])
    rule87 = ctrl.Rule(b['L'] & s['D'] & e['A'] & m['I'], t['K'])
    rule88 = ctrl.Rule(b['L'] & s['D'] & e['A'] & m['CI'], t['K'])
    rule89 = ctrl.Rule(b['L'] & s['D'] & e['F'] & m['CK'], t['U'])
    rule90 = ctrl.Rule(b['L'] & s['D'] & e['F'] & m['K'], t['U'])
    rule91 = ctrl.Rule(b['L'] & s['D'] & e['F'] & m['I'], t['U'])
    rule92 = ctrl.Rule(b['L'] & s['D'] & e['F'] & m['CI'], t['K'])
    rule93 = ctrl.Rule(b['L'] & s['D'] & e['CF'] & m['CK'], t['CU'])
    rule94 = ctrl.Rule(b['L'] & s['D'] & e['CF'] & m['K'], t['U'])
    rule95 = ctrl.Rule(b['L'] & s['D'] & e['CF'] & m['I'], t['U'])
    rule96 = ctrl.Rule(b['L'] & s['D'] & e['CF'] & m['CI'], t['U'])
    rule97 = ctrl.Rule(b['L'] & s['Y'] & e['CA'] & m['CK'], t['K'])
    rule98 = ctrl.Rule(b['L'] & s['Y'] & e['CA'] & m['K'], t['K'])
    rule99 = ctrl.Rule(b['L'] & s['Y'] & e['CA'] & m['I'], t['K'])
    rule100 = ctrl.Rule(b['L'] & s['Y'] & e['CA'] & m['CI'], t['CK'])
    rule101 = ctrl.Rule(b['L'] & s['Y'] & e['A'] & m['CK'], t['K'])
    rule102 = ctrl.Rule(b['L'] & s['Y'] & e['A'] & m['K'], t['K'])
    rule103 = ctrl.Rule(b['L'] & s['Y'] & e['A'] & m['I'], t['CK'])
    rule104 = ctrl.Rule(b['L'] & s['Y'] & e['A'] & m['CI'], t['CK'])
    rule105 = ctrl.Rule(b['L'] & s['Y'] & e['F'] & m['CK'], t['K'])
    rule106 = ctrl.Rule(b['L'] & s['Y'] & e['F'] & m['K'], t['K'])
    rule107 = ctrl.Rule(b['L'] & s['Y'] & e['F'] & m['I'], t['K'])
    rule108 = ctrl.Rule(b['L'] & s['Y'] & e['F'] & m['CI'], t['CK'])
    rule109 = ctrl.Rule(b['L'] & s['Y'] & e['CF'] & m['CK'], t['U'])
    rule110 = ctrl.Rule(b['L'] & s['Y'] & e['CF'] & m['K'], t['K'])
    rule111 = ctrl.Rule(b['L'] & s['Y'] & e['CF'] & m['I'], t['K'])
    rule112 = ctrl.Rule(b['L'] & s['Y'] & e['CF'] & m['CI'], t['K'])
    rule113 = ctrl.Rule(b['L'] & s['CY'] & e['CA'] & m['CK'], t['K'])
    rule114 = ctrl.Rule(b['L'] & s['CY'] & e['CA'] & m['K'], t['CK'])
    rule115 = ctrl.Rule(b['L'] & s['CY'] & e['CA'] & m['I'], t['CK'])
    rule116 = ctrl.Rule(b['L'] & s['CY'] & e['CA'] & m['CI'], t['CK'])
    rule117 = ctrl.Rule(b['L'] & s['CY'] & e['A'] & m['CK'], t['K'])
    rule118 = ctrl.Rule(b['L'] & s['CY'] & e['A'] & m['K'], t['K'])
    rule119 = ctrl.Rule(b['L'] & s['CY'] & e['A'] & m['I'], t['CK'])
    rule120 = ctrl.Rule(b['L'] & s['CY'] & e['A'] & m['CI'], t['CK'])
    rule121 = ctrl.Rule(b['L'] & s['CY'] & e['F'] & m['CK'], t['K'])
    rule122 = ctrl.Rule(b['L'] & s['CY'] & e['F'] & m['K'], t['K'])
    rule123 = ctrl.Rule(b['L'] & s['CY'] & e['F'] & m['I'], t['K'])
    rule124 = ctrl.Rule(b['L'] & s['CY'] & e['F'] & m['CI'], t['CK'])
    rule125 = ctrl.Rule(b['L'] & s['CY'] & e['CF'] & m['CK'], t['K'])
    rule126 = ctrl.Rule(b['L'] & s['CY'] & e['CF'] & m['K'], t['K'])
    rule127 = ctrl.Rule(b['L'] & s['CY'] & e['CF'] & m['I'], t['CK'])
    rule128 = ctrl.Rule(b['L'] & s['CY'] & e['CF'] & m['CI'], t['CK'])
    rule129 = ctrl.Rule(b['P'] & s['CD'] & e['CA'] & m['CK'], t['CU'])
    rule130 = ctrl.Rule(b['P'] & s['CD'] & e['CA'] & m['K'], t['CU'])
    rule131 = ctrl.Rule(b['P'] & s['CD'] & e['CA'] & m['I'], t['U'])
    rule132 = ctrl.Rule(b['P'] & s['CD'] & e['CA'] & m['CI'], t['U'])
    rule133 = ctrl.Rule(b['P'] & s['CD'] & e['A'] & m['CK'], t['CU'])
    rule134 = ctrl.Rule(b['P'] & s['CD'] & e['A'] & m['K'], t['U'])
    rule135 = ctrl.Rule(b['P'] & s['CD'] & e['A'] & m['I'], t['U'])
    rule136 = ctrl.Rule(b['P'] & s['CD'] & e['A'] & m['CI'], t['U'])
    rule137 = ctrl.Rule(b['P'] & s['CD'] & e['F'] & m['CK'], t['CU'])
    rule138 = ctrl.Rule(b['P'] & s['CD'] & e['F'] & m['K'], t['CU'])
    rule139 = ctrl.Rule(b['P'] & s['CD'] & e['F'] & m['I'], t['CU'])
    rule140 = ctrl.Rule(b['P'] & s['CD'] & e['F'] & m['CI'], t['U'])
    rule141 = ctrl.Rule(b['P'] & s['CD'] & e['CF'] & m['CK'], t['CU'])
    rule142 = ctrl.Rule(b['P'] & s['CD'] & e['CF'] & m['K'], t['CU'])
    rule143 = ctrl.Rule(b['P'] & s['CD'] & e['CF'] & m['I'], t['U'])
    rule144 = ctrl.Rule(b['P'] & s['CD'] & e['CF'] & m['CI'], t['U'])
    rule145 = ctrl.Rule(b['P'] & s['D'] & e['CA'] & m['CK'], t['CU'])
    rule146 = ctrl.Rule(b['P'] & s['D'] & e['CA'] & m['K'], t['U'])
    rule147 = ctrl.Rule(b['P'] & s['D'] & e['CA'] & m['I'], t['U'])
    rule148 = ctrl.Rule(b['P'] & s['D'] & e['CA'] & m['CI'], t['K'])
    rule149 = ctrl.Rule(b['P'] & s['D'] & e['A'] & m['CK'], t['U'])
    rule150 = ctrl.Rule(b['P'] & s['D'] & e['A'] & m['K'], t['U'])
    rule151 = ctrl.Rule(b['P'] & s['D'] & e['A'] & m['I'], t['U'])
    rule152 = ctrl.Rule(b['P'] & s['D'] & e['A'] & m['CI'], t['U'])
    rule153 = ctrl.Rule(b['P'] & s['D'] & e['F'] & m['CK'], t['U'])
    rule154 = ctrl.Rule(b['P'] & s['D'] & e['F'] & m['K'], t['U'])
    rule155 = ctrl.Rule(b['P'] & s['D'] & e['F'] & m['I'], t['U'])
    rule156 = ctrl.Rule(b['P'] & s['D'] & e['F'] & m['CI'], t['U'])
    rule157 = ctrl.Rule(b['P'] & s['D'] & e['CF'] & m['CK'], t['CU'])
    rule158 = ctrl.Rule(b['P'] & s['D'] & e['CF'] & m['K'], t['CU'])
    rule159 = ctrl.Rule(b['P'] & s['D'] & e['CF'] & m['I'], t['U'])
    rule160 = ctrl.Rule(b['P'] & s['D'] & e['CF'] & m['CI'], t['U'])
    rule161 = ctrl.Rule(b['P'] & s['Y'] & e['CA'] & m['CK'], t['K'])
    rule162 = ctrl.Rule(b['P'] & s['Y'] & e['CA'] & m['K'], t['K'])
    rule163 = ctrl.Rule(b['P'] & s['Y'] & e['CA'] & m['I'], t['K'])
    rule164 = ctrl.Rule(b['P'] & s['Y'] & e['CA'] & m['CI'], t['CK'])
    rule165 = ctrl.Rule(b['P'] & s['Y'] & e['A'] & m['CK'], t['K'])
    rule166 = ctrl.Rule(b['P'] & s['Y'] & e['A'] & m['K'], t['K'])
    rule167 = ctrl.Rule(b['P'] & s['Y'] & e['A'] & m['I'], t['K'])
    rule168 = ctrl.Rule(b['P'] & s['Y'] & e['A'] & m['CI'], t['CK'])
    rule169 = ctrl.Rule(b['P'] & s['Y'] & e['F'] & m['CK'], t['U'])
    rule170 = ctrl.Rule(b['P'] & s['Y'] & e['F'] & m['K'], t['K'])
    rule171 = ctrl.Rule(b['P'] & s['Y'] & e['F'] & m['I'], t['K'])
    rule172 = ctrl.Rule(b['P'] & s['Y'] & e['F'] & m['CI'], t['K'])
    rule173 = ctrl.Rule(b['P'] & s['Y'] & e['CF'] & m['CK'], t['U'])
    rule174 = ctrl.Rule(b['P'] & s['Y'] & e['CF'] & m['K'], t['U'])
    rule175 = ctrl.Rule(b['P'] & s['Y'] & e['CF'] & m['I'], t['K'])
    rule176 = ctrl.Rule(b['P'] & s['Y'] & e['CF'] & m['CI'], t['K'])
    rule177 = ctrl.Rule(b['P'] & s['CY'] & e['CA'] & m['CK'], t['U'])
    rule178 = ctrl.Rule(b['P'] & s['CY'] & e['CA'] & m['K'], t['K'])
    rule179 = ctrl.Rule(b['P'] & s['CY'] & e['CA'] & m['I'], t['K'])
    rule180 = ctrl.Rule(b['P'] & s['CY'] & e['CA'] & m['CI'], t['CK'])
    rule181 = ctrl.Rule(b['P'] & s['CY'] & e['A'] & m['CK'], t['K'])
    rule182 = ctrl.Rule(b['P'] & s['CY'] & e['A'] & m['K'], t['K'])
    rule183 = ctrl.Rule(b['P'] & s['CY'] & e['A'] & m['I'], t['K'])
    rule184 = ctrl.Rule(b['P'] & s['CY'] & e['A'] & m['CI'], t['CK'])
    rule185 = ctrl.Rule(b['P'] & s['CY'] & e['F'] & m['CK'], t['K'])
    rule186 = ctrl.Rule(b['P'] & s['CY'] & e['F'] & m['K'], t['K'])
    rule187 = ctrl.Rule(b['P'] & s['CY'] & e['F'] & m['I'], t['K'])
    rule188 = ctrl.Rule(b['P'] & s['CY'] & e['F'] & m['CI'], t['CK'])
    rule189 = ctrl.Rule(b['P'] & s['CY'] & e['CF'] & m['CK'], t['K'])
    rule190 = ctrl.Rule(b['P'] & s['CY'] & e['CF'] & m['K'], t['K'])
    rule191 = ctrl.Rule(b['P'] & s['CY'] & e['CF'] & m['I'], t['K'])
    rule192 = ctrl.Rule(b['P'] & s['CY'] & e['CF'] & m['CI'], t['CK'])
    rule193 = ctrl.Rule(b['K'] & s['CD'] & e['CA'] & m['CK'], t['CU'])
    rule194 = ctrl.Rule(b['K'] & s['CD'] & e['CA'] & m['K'], t['CU'])
    rule195 = ctrl.Rule(b['K'] & s['CD'] & e['CA'] & m['I'], t['CU'])
    rule196 = ctrl.Rule(b['K'] & s['CD'] & e['CA'] & m['CI'], t['U'])
    rule197 = ctrl.Rule(b['K'] & s['CD'] & e['A'] & m['CK'], t['CU'])
    rule198 = ctrl.Rule(b['K'] & s['CD'] & e['A'] & m['K'], t['CU'])
    rule199 = ctrl.Rule(b['K'] & s['CD'] & e['A'] & m['I'], t['U'])
    rule200 = ctrl.Rule(b['K'] & s['CD'] & e['A'] & m['CI'], t['U'])
    rule201 = ctrl.Rule(b['K'] & s['CD'] & e['F'] & m['CK'], t['CU'])
    rule202 = ctrl.Rule(b['K'] & s['CD'] & e['F'] & m['K'], t['CU'])
    rule203 = ctrl.Rule(b['K'] & s['CD'] & e['F'] & m['I'], t['CU'])
    rule204 = ctrl.Rule(b['K'] & s['CD'] & e['F'] & m['CI'], t['CU'])
    rule205 = ctrl.Rule(b['K'] & s['CD'] & e['CF'] & m['CK'], t['CU'])
    rule206 = ctrl.Rule(b['K'] & s['CD'] & e['CF'] & m['K'], t['CU'])
    rule207 = ctrl.Rule(b['K'] & s['CD'] & e['CF'] & m['I'], t['CU'])
    rule208 = ctrl.Rule(b['K'] & s['CD'] & e['CF'] & m['CI'], t['CU'])
    rule209 = ctrl.Rule(b['K'] & s['D'] & e['CA'] & m['CK'], t['CU'])
    rule210 = ctrl.Rule(b['K'] & s['D'] & e['CA'] & m['K'], t['CU'])
    rule211 = ctrl.Rule(b['K'] & s['D'] & e['CA'] & m['I'], t['U'])
    rule212 = ctrl.Rule(b['K'] & s['D'] & e['CA'] & m['CI'], t['U'])
    rule213 = ctrl.Rule(b['K'] & s['D'] & e['A'] & m['CK'], t['CU'])
    rule214 = ctrl.Rule(b['K'] & s['D'] & e['A'] & m['K'], t['CU'])
    rule215 = ctrl.Rule(b['K'] & s['D'] & e['A'] & m['I'], t['U'])
    rule216 = ctrl.Rule(b['K'] & s['D'] & e['A'] & m['CI'], t['K'])
    rule217 = ctrl.Rule(b['K'] & s['D'] & e['F'] & m['CK'], t['CU'])
    rule218 = ctrl.Rule(b['K'] & s['D'] & e['F'] & m['K'], t['CU'])
    rule219 = ctrl.Rule(b['K'] & s['D'] & e['F'] & m['I'], t['CU'])
    rule220 = ctrl.Rule(b['K'] & s['D'] & e['F'] & m['CI'], t['U'])
    rule221 = ctrl.Rule(b['K'] & s['D'] & e['CF'] & m['CK'], t['CU'])
    rule222 = ctrl.Rule(b['K'] & s['D'] & e['CF'] & m['K'], t['CU'])
    rule223 = ctrl.Rule(b['K'] & s['D'] & e['CF'] & m['I'], t['CU'])
    rule224 = ctrl.Rule(b['K'] & s['D'] & e['CF'] & m['CI'], t['CU'])
    rule225 = ctrl.Rule(b['K'] & s['Y'] & e['CA'] & m['CK'], t['U'])
    rule226 = ctrl.Rule(b['K'] & s['Y'] & e['CA'] & m['K'], t['K'])
    rule227 = ctrl.Rule(b['K'] & s['Y'] & e['CA'] & m['I'], t['K'])
    rule228 = ctrl.Rule(b['K'] & s['Y'] & e['CA'] & m['CI'], t['CK'])
    rule229 = ctrl.Rule(b['K'] & s['Y'] & e['A'] & m['CK'], t['U'])
    rule230 = ctrl.Rule(b['K'] & s['Y'] & e['A'] & m['K'], t['U'])
    rule231 = ctrl.Rule(b['K'] & s['Y'] & e['A'] & m['I'], t['K'])
    rule232 = ctrl.Rule(b['K'] & s['Y'] & e['A'] & m['CI'], t['CK'])
    rule233 = ctrl.Rule(b['K'] & s['Y'] & e['F'] & m['CK'], t['U'])
    rule234 = ctrl.Rule(b['K'] & s['Y'] & e['F'] & m['K'], t['U'])
    rule235 = ctrl.Rule(b['K'] & s['Y'] & e['F'] & m['I'], t['U'])
    rule236 = ctrl.Rule(b['K'] & s['Y'] & e['F'] & m['CI'], t['K'])
    rule237 = ctrl.Rule(b['K'] & s['Y'] & e['CF'] & m['CK'], t['CU'])
    rule238 = ctrl.Rule(b['K'] & s['Y'] & e['CF'] & m['K'], t['U'])
    rule239 = ctrl.Rule(b['K'] & s['Y'] & e['CF'] & m['I'], t['U'])
    rule240 = ctrl.Rule(b['K'] & s['Y'] & e['CF'] & m['CI'], t['K'])
    rule241 = ctrl.Rule(b['K'] & s['CY'] & e['CA'] & m['CK'], t['K'])
    rule242 = ctrl.Rule(b['K'] & s['CY'] & e['CA'] & m['K'], t['K'])
    rule243 = ctrl.Rule(b['K'] & s['CY'] & e['CA'] & m['I'], t['CK'])
    rule244 = ctrl.Rule(b['K'] & s['CY'] & e['CA'] & m['CI'], t['CK'])
    rule245 = ctrl.Rule(b['K'] & s['CY'] & e['A'] & m['CK'], t['K'])
    rule246 = ctrl.Rule(b['K'] & s['CY'] & e['A'] & m['K'], t['K'])
    rule247 = ctrl.Rule(b['K'] & s['CY'] & e['A'] & m['I'], t['K'])
    rule248 = ctrl.Rule(b['K'] & s['CY'] & e['A'] & m['CI'], t['CK'])
    rule249 = ctrl.Rule(b['K'] & s['CY'] & e['F'] & m['CK'], t['U'])
    rule250 = ctrl.Rule(b['K'] & s['CY'] & e['F'] & m['K'], t['U'])
    rule251 = ctrl.Rule(b['K'] & s['CY'] & e['F'] & m['I'], t['U'])
    rule252 = ctrl.Rule(b['K'] & s['CY'] & e['F'] & m['CI'], t['K'])
    rule253 = ctrl.Rule(b['K'] & s['CY'] & e['CF'] & m['CK'], t['U'])
    rule254 = ctrl.Rule(b['K'] & s['CY'] & e['CF'] & m['K'], t['K'])
    rule255 = ctrl.Rule(b['K'] & s['CY'] & e['CF'] & m['I'], t['K'])
    rule256 = ctrl.Rule(b['K'] & s['CY'] & e['CF'] & m['CI'], t['K'])

    b.view()
    s.view()
    e.view()
    m.view()
    t.view()

    altitude_ctrl = ctrl.ControlSystem([

        rule1, rule2, rule3, rule4, rule5, rule6, rule7, rule8, rule9, rule10, rule11, rule12, rule13, rule14, rule15,
        rule16, rule17, rule18, rule19, rule20, rule21, rule22, rule23, rule24, rule25, rule26, rule27, rule28, rule29,
        rule30, rule31, rule32, rule33, rule34, rule35, rule36, rule37, rule38, rule39, rule40, rule41, rule42, rule43,
        rule44, rule45, rule46, rule47, rule48, rule49, rule50, rule51, rule52, rule53, rule54, rule55, rule56, rule57,
        rule58, rule59, rule60, rule61, rule62, rule63, rule64, rule65, rule66, rule67, rule68, rule69, rule70, rule71,
        rule72, rule73, rule74, rule75, rule76, rule77, rule78, rule79, rule80, rule81, rule82, rule83, rule84, rule85,
        rule86, rule87, rule88, rule89, rule90, rule91, rule92, rule93, rule94, rule95, rule96, rule97, rule98, rule99,
        rule100, rule101, rule102, rule103, rule104, rule105, rule106, rule107, rule108, rule109, rule110, rule111,
        rule112, rule113, rule114, rule115, rule116, rule117, rule118, rule119, rule120, rule121, rule122, rule123,
        rule124, rule125, rule126, rule127, rule128, rule129, rule130, rule131, rule132, rule133, rule134, rule135,
        rule136, rule137, rule138, rule139, rule140, rule141, rule142, rule143, rule144, rule145, rule146,
        rule147, rule148, rule149, rule150, rule151, rule152, rule153, rule154, rule155, rule156, rule157, rule158,
        rule159, rule160, rule161, rule162, rule163, rule164, rule165, rule166, rule167, rule168, rule169, rule170,
        rule171, rule172, rule173, rule174, rule175, rule176, rule177, rule178, rule179, rule180, rule181, rule182,
        rule183, rule184, rule185, rule186, rule187, rule188, rule189, rule190, rule191, rule192, rule193, rule194,
        rule195, rule196, rule197, rule198, rule199, rule200, rule201, rule202, rule203, rule204, rule205, rule206,
        rule207, rule208, rule209, rule210, rule211, rule212, rule213, rule214, rule215, rule216, rule217, rule218,
        rule219, rule220, rule221, rule222, rule223, rule224, rule225, rule226, rule227, rule228, rule229, rule230,
        rule231, rule232, rule233, rule234, rule235, rule236, rule237, rule238, rule239, rule240, rule241, rule242,
        rule243, rule244, rule245, rule246, rule247, rule248, rule249, rule250, rule251, rule252, rule253, rule254,
        rule255, rule256

    ])

    altitude_sim = ctrl.ControlSystemSimulation(altitude_ctrl)






    t.view(sim=altitude_sim)
    import random
    mppt = random.random()
    esp = random.uniform(1.8, 3.6)
    #mppt = request.args.get("mppt")
    #esp = request.args.get("esp")
    altitude_sim.input['bulut'] = cloud_rate
    sarj = request.args.get("sarj")
    altitude_sim.input['mppt'] =mppt
    altitude_sim.input['esp'] = esp
    altitude_sim.input['sarj'] = float(sarj)
    altitude_sim.compute()
    x = altitude_sim.output['sure']
    y=str(int(x * 3600 * 1000))
    sicaklik=str(temp)

    return (y,sicaklik)


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

    

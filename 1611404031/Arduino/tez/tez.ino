#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
const char* ssid     = "TTNET_ZyXEL_HACA";
const char* password = "F3rh4tzd3m1r";
String url = "http://ferhatozdemir.pythonanywhere.com/bulanik/?sarj=";
String url2 = "http://ferhatozdemir.pythonanywhere.com/sarjadd?sarjdeger=";
String url3 = "http://ferhatozdemir.pythonanywhere.com/sensoradd?sensordeger=";
int sensordeger;
#define pil A0

// 860 max - 4.20 V
// 614 min - 3.0 v

int min_deger = 614;
float yuzde = 0;
float deger = 0; 
int mili=1000;
int gerilim = 0;

void setup() {
  Serial.begin(115200);
  Serial.println("");
  Serial.print("Bağlanılıyor ");
  Serial.print(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi bağlantısı kuruldu.");
  Serial.println("Yerel IP adresi: ");
  Serial.print(WiFi.localIP());
  Serial.println("");
}

void loop() {
  unsigned long sure = 0;
  //sensordeger = analogRead(3);
    sensordeger=random(100, 103);

   Serial.println(sensordeger, DEC);              // prints the value read
   Serial.println(" PPM");
   gerilim = analogRead(pil);

  if(gerilim >= 860)
    gerilim = 860;

  if(gerilim <= 614)
    gerilim = 614;

   yuzde = gerilim - min_deger;
   deger = (100.00/246.00) * yuzde;
   Serial.println("sarjdegeri");
   Serial.println(deger);
 
  if (WiFi.status() == WL_CONNECTED) {
  HTTPClient http;
    http.begin(url+deger);
    int httpCode = http.GET();
    if (httpCode > 0) {
      String payload = http.getString();
      sure = payload.toInt();
      Serial.println("Sayfa yanıtı:");
      Serial.println(sure);
    }
    
    http.end();
      HTTPClient http2;
    http2.begin(url2+deger);
    int http2Code = http2.GET();
    if (http2Code > 0) {
      String sonuc = http2.getString();
      
     
      Serial.println("Sayfa yanıtı:");
      Serial.println(sonuc);
    }
    
    http2.end();

    HTTPClient http3;
    http3.begin(url3+sensordeger);
    int http3Code = http3.GET();
    if (http3Code > 0) {
      String sonuc1 = http3.getString();
      
     
      Serial.println("Sayfa yanıtı:");
      Serial.println(sonuc1);
    }
    
    http3.end();
  }
  delay(sure); 
}

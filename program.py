import machine
import network # Přidáno
import math    # Přidáno
import ujson   # Přidáno
import usocket as socket
from umqtt.simple import MQTTClient
from umqtt.simple import MQTTException
import time
import creds

__MQTT_PUB_TOPIC_1__ = b"v1/devices/me/telemetry"

# Piny - sjednoceno na název 'adc', který používá funkce
adc = machine.ADC(26)

mqtterrortable=["Connection Accepted", "Connection Refused, Unacceptable Protocol Version","Connection Refused, Identifier Rejected","Connection Refused, Server Unavailable", "Connection Refused, Bad Username or Password", "Connection Refused, Not Authorized"]

# Initialize MQTT Client
keepalive_seconds = 60 # seconds
client = MQTTClient(creds._MQTT_CLIENT_ID_, creds._MQTT_REMOTE_SERVER_IP_, user=creds._MQTT_ACCESS_TOKEN_, password=creds._MQTT_PASSWORD_, keepalive=keepalive_seconds, port=creds._MQTT_REMOTE_SERVER_PORT_)

# Power Measurement Konstanty
VOLTAGE_RMS = 230.0
V_REF = 3.3
ADC_MAX = 65535
OFFSET = 32767
CALIBRATION_FACTOR = 30.0

# Globální proměnné pro energii
total_energy_kwh = 0.0
last_measure_time = 0

# Wi-Fi Setup
wlan = network.WLAN(network.STA_IF)
wlan.active(False)
time.sleep(1)
wlan.active(True)
time.sleep(0.5)
wlan.connect(creds.WIFI_SSID, creds.WIFI_PWD)

def measure_rms_current(sample_time_ms=100):
    sum_sq = 0.0
    samples = 0
    start_time = time.ticks_ms()
    
    while time.ticks_diff(time.ticks_ms(), start_time) < sample_time_ms:
        adc_val = adc.read_u16()
        shifted_val = adc_val - OFFSET
        sum_sq += shifted_val * shifted_val
        samples += 1
        
    if samples == 0:
        return 0.0
        
    rms_adc = math.sqrt(sum_sq / samples)
    rms_voltage = (rms_adc / ADC_MAX) * V_REF
    rms_current = rms_voltage * CALIBRATION_FACTOR
    return rms_current

def calculate_power(current_rms):
    power_w = VOLTAGE_RMS * current_rms
    power_kw = power_w / 1000.0
    return power_kw

# Check and wait for WiFi connection.
isReady = False
while (not isReady):
    print("WIFI STATUS CONNECTED: " + str(wlan.isconnected()))
    if(wlan.isconnected()):
        isReady = True
    time.sleep_ms(500)

print("IP Adresa:", wlan.ifconfig()[0])

# Connect to server
try:
    client.connect()
    # Zakomentováno, protože topics nebyly definovány. 
    # Odkomentujte, až budete řešit zpětné ovládání z Thingsboardu (RPC/Shared attributes)
    # client.subscribe(__MQTT_SUB_TOPIC_1__) 
except MQTTException as mqtte:
    print("MQTTException : " + str(mqtte)  + " - " + mqtterrortable[int(str(mqtte))])
except Exception as e:
    print("Other Error:", e)

mqtt_ctr = 0
print("Entering infinite loop")
seconds_counter = 0

# Inicializace času před vstupem do smyčky
last_measure_time = time.ticks_ms()

while True:
    try:
        # client.check_msg() # Odkomentujte, až budete přijímat zprávy (např. vynulování kWh)
        
        mqtt_ctr += 1
        seconds_counter += 1
        
        if mqtt_ctr >= (keepalive_seconds - 2) / 0.1:
            mqtt_ctr = 0
            client.ping()
            
        # Publish message to topic (cca každé 3 vteřiny)
        if seconds_counter >= 3 / 0.1:
            seconds_counter = 0
            
            # 1. Změření proudu a výpočet výkonu
            current = measure_rms_current()
            if current < 0.05: # Filtrace šumu u nuly
                current = 0.0
            power_kw = calculate_power(current)
            
            # 2. Výpočet času uplynulého od posledního měření
            current_time = time.ticks_ms()
            delta_t_ms = time.ticks_diff(current_time, last_measure_time)
            last_measure_time = current_time
            
            # 3. Převod delta času na hodiny a přičtení k celkové energii
            # ms -> hodiny: děleno (1000 * 3600)
            delta_t_hours = delta_t_ms / 3600000.0
            total_energy_kwh += (power_kw * delta_t_hours)
            
            # 4. Sestavení JSON payloadu přesně tak, jak to Thingsboard očekává
            json_string = {
                "power_kw": power_kw,
                "total_energy_kwh": total_energy_kwh,
                "current_A": current # Můžete posílat i proud pro lepší diagnostiku
            }
            json_payload = ujson.dumps(json_string)
            
            # 5. Odeslání
            client.publish(__MQTT_PUB_TOPIC_1__, json_payload)
            print("Odesláno:", json_payload)
            
    except KeyboardInterrupt:
        print("Keyboard Interrupt.")
        break
    except Exception as exception:
        print("Error: " + str(exception))
    
    time.sleep(0.1)

time.sleep(1)
print("Disconnect from MQTT")
client.disconnect()
time.sleep(1)
print("Disconnect from WiFi")
wlan.disconnect()
time.sleep(1)
print("Deactivate WiFi")
wlan.active(False)
time.sleep(0.5)
print("End of program")
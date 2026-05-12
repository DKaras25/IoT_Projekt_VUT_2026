import machine
import network 
import math    
import ujson   
import usocket as socket
from umqtt.simple import MQTTClient
from umqtt.simple import MQTTException
import time
import creds
import ahtx0
from machine import Pin, I2C
import simulation


class Parameters():
    autoMode = True
    total_energy_kwh = 0
    currentPercent = 0
    mqqtclient = 0
    __MQTT_PUB_TOPIC_1__ = b"v1/devices/me/telemetry"
    __MQTT_SUB_TOPIC_1__ = b"v1/devices/me/attributes"
    __MQTT_SUB_TOPIC_2__ = b"v1/devices/me/rpc/request/+"
    __MQTT_SUB_TOPIC_3__ = b"v1/devices/me/rpc/request/"

    def setTotalEnergy(self, js):
        self.total_energy_kwh = js["total_energy_kwh"]

    def setAutoMode(self, js):
        if js["method"] == "autoMode":
            self.autoMode = not js["params"]

    def setCurrentPercent(self, js):
        if js["method"] == "setPercent":
            self.currentPercent = js["params"]

    def sendCurrentPercent(self, js):
        json_string = {
            "getPercent": self.currentPercent
        }
        json_payload = ujson.dumps(json_string)

        # 5. Odeslání
        client.publish(self.__MQTT_SUB_TOPIC_3__, json_payload)

    def on_message_callback(self, topic, msg):
        print((topic, msg))
        js = ujson.loads(msg)
        print(js)
        if self.__MQTT_SUB_TOPIC_1__ in topic:
            self.setTotalEnergy(js)
        elif self.__MQTT_SUB_TOPIC_3__ in topic:
            self.setAutoMode(js)
            self.setCurrentPercent(js)


adc = machine.ADC(26)
pin = machine.Pin(15)

frequency = 10  # Hz
duty_cycle = 35768  # 0-65535
percent = 0  # %

# Setup sensor
i2c1 = I2C(1, scl=Pin(3), sda=Pin(2), freq=400000)
tmp_sensor = ahtx0.AHT20(i2c1)
tmp_sensor.initialize()


def get_pwm_percent(temp):
    if myObj.autoMode is True:
        if (temp > 20 and temp <= 25):
            return 30
        elif (temp > 25 and temp <= 30):
            return 70
        elif temp > 30:
            return 100
        else:
            return 10
    else:
        return myObj.currentPercent


mqtterrortable = ["Connection Accepted", "Connection Refused, Unacceptable Protocol Version",
                  "Connection Refused, Identifier Rejected", "Connection Refused, Server Unavailable",
                  "Connection Refused, Bad Username or Password", "Connection Refused, Not Authorized"]

# Initialize MQTT Client
keepalive_seconds = 60  # seconds
client = MQTTClient(creds._MQTT_CLIENT_ID_, creds._MQTT_REMOTE_SERVER_IP_, user=creds._MQTT_ACCESS_TOKEN_,
                    password=creds._MQTT_PASSWORD_, keepalive=keepalive_seconds, port=creds._MQTT_REMOTE_SERVER_PORT_)

# Power Measurement Konstanty
VOLTAGE_RMS = 230.0
V_REF = 3.3
ADC_MAX = 65535
OFFSET = 32767
CALIBRATION_FACTOR = 20.0

myObj = Parameters()  #################################
myObj.mqqtclient = client
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

    # --- SIMULAČNÍ PARAMETRY ---
    vteriny = time.ticks_ms() / 1000.0
    # Amplituda kolísá mezi cca 5000 a 30000 (jednotky ADC)
    sim_amplitude = 17500 + 12500 * math.sin(vteriny / 5.0) 
    sim_frequency = 50  # 50 Hz síť

    while time.ticks_diff(time.ticks_ms(), start_time) < sample_time_ms:
        # --- REÁLNÉ MĚŘENÍ (ZAKOMENTOVÁNO) ---
        # adc_val = adc.read_u16()
        # shifted_val = adc_val - OFFSET

        # --- SIMULACE (AKTIVNÍ) ---
        # Musíme předat aktuální čas v mikrosekundách, aby sinusovka "běžela"
        t_now = time.ticks_us() / 1000000.0
        shifted_val = simulation.generate_sine_wave(sim_amplitude, sim_frequency, t_now)

        

        sum_sq += shifted_val * shifted_val
        samples += 1

    if samples == 0:
        print("nula samplu")
        return 0.0

    rms_adc = math.sqrt(sum_sq / samples)
    rms_voltage = (rms_adc / ADC_MAX) * V_REF
    rms_current = rms_voltage * CALIBRATION_FACTOR
    print(rms_current)
    print("vypocteno")
    return rms_current


def calculate_power(current_rms):
    power_w = VOLTAGE_RMS * current_rms
    print(power_w)
    print("vykon")
    power_kw = power_w / 1000.0
    return power_kw


def getTemp():
    temp = tmp_sensor.temperature
    percent = get_pwm_percent(temp)
    duty_cycle = int(percent / 100 * 65535)

    machine.PWM(pin, freq=frequency, duty_u16=duty_cycle)

    print("Teplota:", temp, "°C,", "PWM:", percent, "%")

    return percent


def setTotalEnergy(js):
    total_energy_kwh = js["total_energy_kwh"]
    print(total_energy_kwh)


client.set_callback(myObj.on_message_callback)

# Check and wait for WiFi connection.
isReady = False
while (not isReady):
    print("WIFI STATUS CONNECTED: " + str(wlan.isconnected()))
    if (wlan.isconnected()):
        isReady = True
    time.sleep_ms(500)

print("IP Adresa:", wlan.ifconfig()[0])

# Connect to server
try:
    client.connect()
    client.subscribe(myObj.__MQTT_SUB_TOPIC_1__)
    client.subscribe(myObj.__MQTT_SUB_TOPIC_2__)
except MQTTException as mqtte:
    print("MQTTException : " + str(mqtte) + " - " + mqtterrortable[int(str(mqtte))])
except Exception as e:
    print("Other Error:", e)

mqtt_ctr = 0
print("Entering infinite loop")
seconds_counter = 0

last_measure_time = time.ticks_ms()
total_energy_kwh = 0
autoMode = True

while True:
    try:
        client.check_msg()  # Odkomentujte, až budete přijímat zprávy (např. vynulování kWh)

        mqtt_ctr += 1
        seconds_counter += 1

        if mqtt_ctr >= (keepalive_seconds - 2) / 0.1:
            mqtt_ctr = 0
            client.ping()

        # Publish message to topic (cca každé 3 vteřiny)
        if seconds_counter >= 3 / 0.1:
            seconds_counter = 0

            # 1. Změření proudu a výpočet výkonu
            current = measure_rms_current(100)
            if current < 0.05:  # Filtrace šumu u nuly
                current = 0.0
            temp = calculate_power(current)
            print(temp)
            power_kw = temp

            # 2. Výpočet času uplynulého od posledního měření
            current_time = time.ticks_ms()
            delta_t_ms = time.ticks_diff(current_time, last_measure_time)
            last_measure_time = current_time

            # 3. Převod delta času na hodiny a přičtení k celkové energii
            # ms -> hodiny: děleno (1000 * 3600)
            delta_t_hours = delta_t_ms / 3600000.0
            myObj.total_energy_kwh += (power_kw * delta_t_hours)  

            # 4. Sestavení JSON payloadu přesně tak, jak to Thingsboard očekává
            json_string = {
                "power_kw": power_kw,
                "total_energy_kwh": myObj.total_energy_kwh,  
                "temperature": tmp_sensor.temperature,
                "pwm": getTemp()
            }
            json_payload = ujson.dumps(json_string)

            # 5. Odeslání
            client.publish(myObj.__MQTT_PUB_TOPIC_1__, json_payload)
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

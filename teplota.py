import time

pin = machine.Pin(15)
frequency = 10 #Hz
duty_cycle = 35768 #0-65535
percent = 0 #%
temp = 19 # teplota (°C)


    
def get_pwm_percent(temp):
    if (temp > 20 and temp <=25):
        return 30
    elif (temp > 20 and temp <=25):
        return 50
    elif (temp > 25 and temp <=30):
        return 70
    elif temp > 30:
        return 100
    else:
      return 10
    
  #simulace
while True:
    #temp = i2c1.readfrom(56,7)
    percent = get_pwm_percent(temp)
    duty_cycle = int(percent / 100 * 65535) 
    
    pwm = machine.PWM(pin, freq = frequency, duty_u16 = duty_cycle)
    
    print("Teplota:", temp, "°C,", "PWM:", percent, "%")
    time.sleep(1)
 

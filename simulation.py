import math
import time

def generate_sine_wave(amplitude, frequency, time):
    if frequency <= 0:
        raise ValueError("Invalid values.")

    current_amplitude = amplitude * math.sin(2 * math.pi * frequency * time)
    return current_amplitude

# showcase, basic python ma jiny TIME, takze nefuguje time.ticks() a jine, v ukazce resen tedy jinak

# Parameters
amplitude = 10      # Max value
frequency = 0.1      # Hz


ref_time = time.perf_counter()
# ref_time = time.ticks()
print(ref_time)
while True:
    ti = time.perf_counter() - ref_time
    # temp = time.ticks()
    # t = time.ticks_diff(ref_time,temp)
    I_val = math.fabs(generate_sine_wave(amplitude, frequency, ti))
    print("I:"+str(I_val))
    time.sleep(0.1)

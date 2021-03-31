import smbus
import time
from time import sleep
import sys
import numpy as np
import math
from scipy.fft import rfft, rfftfreq
from matplotlib import pyplot as plt
#import pandas as pd
import csv

bus = smbus.SMBus(1)

EARTH_GRAVITY_MS2 = 9.80665
SCALE_MULTIPLIER = 0.004

DATA_FORMAT = 0x31
BW_RATE = 0x2C
POWER_CTL = 0x2D

BW_RATE_1600HZ = 0x0F
BW_RATE_800HZ = 0x0E
BW_RATE_400HZ = 0x0D
BW_RATE_200HZ = 0x0C
BW_RATE_100HZ = 0x0B
BW_RATE_50HZ = 0x0A
BW_RATE_25HZ = 0x09

RANGE_2G = 0x00
RANGE_4G = 0x01
RANGE_8G = 0x02
RANGE_16G = 0x03

fifo_stream = 0x00

MEASURE = 0x08
AXES_DATA = 0x32

AXES_ctr = 0x38
AXES_sts = 0x39

SAMPLE_RATE = 3200
DURATION = 3

class ADXL345:
    address = None

    def __init__(self, address=0x53):
        self.address = address
        #self.read()
        self.set_bandwidth_rate(BW_RATE_1600HZ)
        self.set_range(RANGE_16G)
        self.enable_measurement()
        

    def enable_measurement(self):
        bus.write_byte_data(self.address, POWER_CTL, MEASURE)

    def set_bandwidth_rate(self, rate_flag):
        bus.write_byte_data(self.address, BW_RATE, rate_flag)

    
    def read(self):
        val = bus.read_i2c_block_data(self.address, AXES_ctr)
        print(val)
        #bus.write_byte_data(self.address, AXES_ctr, fifo_stream)
        val = bus.read_i2c_block_data(self.address, AXES_sts, 8)
        print(val)
        val = bus.read_i2c_block_data(self.address, AXES_ctr)
        print(val)
    
    def set_range(self, range_flag):
        value = bus.read_byte_data(self.address, DATA_FORMAT)

        value &= ~0x0F
        value |= range_flag
        value |= 0x08

        bus.write_byte_data(self.address, DATA_FORMAT, value)

    def get_axes(self, gforce=False):
        bytes = bus.read_i2c_block_data(self.address, AXES_DATA, 6)

        x = bytes[0] | (bytes[1] << 8)
        if x & (1 << 16 - 1):
            x = x - (1 << 16)

        y = bytes[2] | (bytes[3] << 8)
        if y & (1 << 16 - 1):
            y = y - (1 << 16)

        z = bytes[4] | (bytes[5] << 8)
        if z & (1 << 16 - 1):
            z = z - (1 << 16)

        x = x * SCALE_MULTIPLIER
        y = y * SCALE_MULTIPLIER
        z = z * SCALE_MULTIPLIER

        if gforce is False:
            x = x * EARTH_GRAVITY_MS2
            y = y * EARTH_GRAVITY_MS2
            z = z * EARTH_GRAVITY_MS2

        x = round(x, 4)
        y = round(y, 4)
        z = round(z, 4)

        return {"x": x, "y": y, "z": z}

acc = ADXL345()
N = SAMPLE_RATE * DURATION
time.sleep(2)
print(acc.get_axes())
try:
    listx, listy, listz, reslist =[],[],[], []
    x,y,z,b = 0,0,0,0
    for i in range (1,N + 1):
        b = acc.get_axes()
        listx.append(b["x"]),listy.append(b["y"]),listz.append(b["z"])
        time.sleep(0.0003125)
    #print(z/3200)
    #print(listx)
        
    for i,j,k in zip(listx,listy,listz):
        reslist.append(math.sqrt((i*i)+(j*j)+(k*k)))
    fname = "data4.csv"    
    fields = ["X","Y","Z","RES"]
    with open(fname, 'w') as csvfile:
        csvwriter = csv.writer(csvfile)

        csvwriter.writerow(fields)
        for i in range(0,len(listx)):
            row = []
            row.append(listx[i])
            row.append(listy[i])
            row.append(listz[i])
            row.append(reslist[i])
            csvwriter.writerow(row)

    yf = rfft(listz)
    xf = rfftfreq(N, 1 / SAMPLE_RATE)
    yf[0 : 10] = 0
    plt.plot(xf, np.abs(yf))
    
    plt.show()
#     time.sleep(2)
    plt.clf()

    
except KeyboardInterrupt:
    sys.exit()
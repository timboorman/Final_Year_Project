"""
The ``Geyser_Funcs`` module contains functions for creating geyser software
models in order to calculate energy.
"""

import csv
import gModels as Geyser
import myModels as models
import Cost_Funcs as cf
import datetime as dt
import numpy as np

endOfDay = dt.time(hour=23,minute=59)
def SetupGeyser(startTemp=50):
    thermalRes = 1/1.429756
    volume = 150

    g = Geyser.ewhModel_one(thermal_resistance=thermalRes, tank_volume = volume,
    t_initial=startTemp)
    g.setAmbTemp(26)
    g.setInletTemp(18)
    return g

def Runner(Filename):
    '''
    Function to run specified .csv file and return minute by minute date per day
    for volume consumption of a geyser.

    Args:
        Filename (string):
            Input form 'Filename.csv'. Name of file containing water consumption
            data.

    Returns:
        tstamp (array[days,minutes]):
            Array containing timestamps for volume data also returned.
        vol (array[days,minutes]):
            Array containing water consumption data per day, per minute.
    '''
    vtotal = 0.0
    vcollect = []
    tcollect = []
    tstamp = []
    vol = []

    GeyserOn = False
    with open(Filename, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        time = [] # list for timestamps
        volume = [] # list for volumes (at 1h intervals)
        for row in reader:
            time.append(int(row['time']))            #
            volume.append(float(row['Hm'])) # fill lists

    time = time[1:]
    volume = volume[1:]
    #Prepare arrays for minute interval slots
    start = dt.datetime.utcfromtimestamp(time[0])
    start = models.datetime_from_utc_to_local(start.replace(second=0))
    end = dt.datetime.utcfromtimestamp(time[-1])
    end = models.datetime_from_utc_to_local(end.replace(second=0))

    new_time = [start + dt.timedelta(minutes=x) for x in range(0, round((end-start).total_seconds()/60))]
    full_vol = np.zeros(len(new_time))
    #Populate volumes in appropriate place
    full_vol[0] = volume[0]
    for i in range(len(volume)):
        try:
            if i > 0:
                full_vol[int(math.ceil((time[i]-time[0])/60))] = volume[i] # index = time from start (mins)
        except:
            pass

    for i in range(full_vol.size):
        #get current timestamp
        date = new_time[i]

        #end of day
        if(date.time() == dt.time(hour=0,minute=0)):
            tstamp.append(tcollect)
            vol.append(vcollect)
            vcollect = []
            tcollect = []
            vcollect.append(full_vol[i])
            tcollect.append(date)

        else:
            vcollect.append(full_vol[i])
            tcollect.append(date)

    vol = np.array(vol[71:-60])
    tstamp = np.array(tstamp[71:-60])

    return tstamp, vol

def Simulator(geyser_vol):
    '''
    Simulator used with "Runner" method. Returned volume from Runner is used
    to calculate energy usage with water consumption pattern in a geyser with
    thermostat set to 70 degrees (C).

    Args:
        geyser_vol (array[days, minutes]):
            Array containing water consumption data per day, per minute.

    Returns:
        energy (array[days, minutes]):
            Array containing energy consumption data per day, per minute.
        temp (array[days, minutes]):
            Array containing temperature in geyser per day, per minute.
    '''
    Geyser = SetupGeyser()
    energy = np.zeros_like(geyser_vol)
    temp = np.zeros_like(geyser_vol)
    Geyser_Rating = 2 # kW
    Run_Time = 1 # in mins
    total = 0
    SET_TEMP = 70
    HIGH_RAIL = SET_TEMP+2
    LOW_RAIL = SET_TEMP-2

    for i in range(geyser_vol.shape[0]): # Days
        for j in range(geyser_vol.shape[1]): # minutes
            Geyser.stepVolume(geyser_vol[i,j])
            currTemp = Geyser.getOutletTemp()

            if(currTemp >= HIGH_RAIL):
                Geyser.GeyserOn = False
                Geyser.stepTimeDecay(Run_Time*60)

            elif(currTemp >= LOW_RAIL and currTemp < HIGH_RAIL):
                if(Geyser.GeyserOn == True):
                    Geyser.stepTime(Run_Time*60, Geyser_Rating)
                    total += Geyser_Rating
                else:
                    Geyser.stepTimeDecay(Run_Time*60)

            elif(currTemp <= LOW_RAIL):
                Geyser.GeyserOn = True
                Geyser.stepTime(Run_Time*60, Geyser_Rating)
                total += Geyser_Rating

            energy[i,j] = total
            total = 0
            temp[i,j] = currTemp

    energy = energy/60 # for kWh

    return energy, temp

def BiGeyser(volume, tStamps, excess):
    '''
    Simulates operation of duel thermostat geyser set to 50 degrees (C) with max
    limit of 85 degrees (C) with solar supply.

    Interacts with data produced by FiveMinSolarRunner in "myModels.py" which
    compares solar supply to required energy consumption to get excess solar
    supply and interacts with "Runner" to get water consumption and timestamps.

    Args:
        volume (array[days,5min_intervals]):
            Array containing volume consumption data per day, per 5 min interval.
        tStamps (array[days,5min_intervals]):
            Array containing timestamps per day, per 5 min interval.
        excess (array[days,5min_intervals]):
            Array containing solar energy available to geyser per day, per 5 min
            interval.

    Returns:
        mains (array[days,5min_intervals]):
            Grid energy consumption data per day, per 5 min interval.
        solar:
            Solar energy consumption data per day, per 5 min interval.
        gTemp:
            Geyser temperature data per day, per 5 min interval.
    '''
    gModel = SetupGeyser()
    GeyserOn = False
    NUM_MINS=5
    G_RATING=2 # kW

    SET_TEMP = 60
    LOW_RAIL = SET_TEMP-2
    HIGH_RAIL = SET_TEMP+2

    SET_TEMP_2 = 50
    HIGH_RAIL_2 = SET_TEMP_2 + 2
    LOW_RAIL_2 = SET_TEMP_2 - 2

    mains = []
    solar = []
    gTemp = []

    mains_collector = []
    solar_collector = []
    tcollect = []

    mains_total = 0.0
    solar_total = 0.0

    for i in range(volume.shape[0]): # Days
        for j in range(volume.shape[1]): # 5 min interval
            date = tStamps[i,j]
            gModel.stepVolume(volume[i,j])
            currTemp = gModel.getOutletTemp()
            tcollect.append(currTemp)
            # remove seconds from timestamp
            #date -= dt.timedelta(seconds=date.time().second)
            stepAmount = 0
            if(excess[i,j] > 0):
                if(excess[i,j] > 2):
                    stepAmount=2
                else:
                    stepAmount=excess[i,j]

            if(date.time() >= dt.time(hour=2, minute=0) and date.time() < dt.time(hour=6,minute=0)): # Pre Heat condition
                if(currTemp < LOW_RAIL):
                    GeyserOn = True
                    gModel.stepTime(NUM_MINS*60, G_RATING) # Run Geyser for 5 mins
                    mains_total += G_RATING

                elif(currTemp >= LOW_RAIL and currTemp < SET_TEMP):
                    if(GeyserOn == True):
                        gModel.stepTime(NUM_MINS*60, G_RATING) # Run Geyser for 5 mins
                        mains_total += G_RATING
                    if(GeyserOn == False):
                        gModel.stepTimeDecay(NUM_MINS*60) # Decay

                elif(currTemp > SET_TEMP):
                    GeyserOn = False
                    gModel.stepTimeDecay(5*60) # Temp decay for 5 mins

            elif(date.time() >= dt.time(hour=6,minute=0)): # If in scheduled time slot

                if(currTemp < 48): # temp < 48
                    if(excess[i,j] > 0):
                        gModel.stepTime(NUM_MINS*60, stepAmount)
                        solar_total += stepAmount
                    else:
                        GeyserOn = True
                        gModel.stepTime(NUM_MINS*60, G_RATING)
                        mains_total += G_RATING

                elif(currTemp >= 87):
                    gModel.stepTimeDecay(NUM_MINS*60)
                    if(GeyserOn==True):
                        GeyserOn=False

                elif(currTemp >= 83):
                    if(excess[i,j] > 0): # if solar supply
                        gModel.stepTime(NUM_MINS*60, stepAmount)
                        solar_total += stepAmount
                    else: # no solar supply
                        gModel.stepTimeDecay(NUM_MINS*60)

                elif(currTemp >= 52 and currTemp < 83):
                    if(excess[i,j] > 0):
                        gModel.stepTime(NUM_MINS*60, stepAmount)
                        solar_total += stepAmount
                    else:
                        gModel.stepTimeDecay(NUM_MINS*60)
                        GeyserOn = False

                elif(currTemp >= 48 and currTemp < 52):
                    if(excess[i,j] > 0):
                        gModel.stepTime(NUM_MINS*60, stepAmount)
                        solar_total += stepAmount
                    else:
                        if(GeyserOn):
                            gModel.stepTime(NUM_MINS*60, G_RATING)
                            mains_total += G_RATING
                        else:
                            gModel.stepTimeDecay(NUM_MINS*60)


            else:
                gModel.stepTimeDecay(NUM_MINS*60) # Temp decay for 5 mins

            mains_collector.append(mains_total)
            solar_collector.append(solar_total)
            mains_total = 0
            solar_total = 0

        mains.append(mains_collector)
        solar.append(solar_collector)
        gTemp.append(tcollect)
        mains_collector = []
        solar_collector = []
        tcollect = []

    mains = np.array(mains)
    solar = np.array(solar)
    gTemp = np.array(gTemp)
    mains = mains/12
    solar = solar/12

    return mains, solar, gTemp,

def PrintSched(Filename):
    '''
    Basic method for printing out .csv geyser water consumption schedule

    args:
        Filename (string):
            Of the form 'Filename.csv'.
    '''
    volumeTotals = []

    with open(Filename, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        time = []
        volume = []
        for row in reader:
            time.append(row['time'])
            volume.append(float(row['volume']))
        indexFlag = False
        totalVolume = 0
        for i in range(len(volume)):
            if(volume[i] > 0):
                if(indexFlag == False):
                    indexFlag = True
                    start = i
                    totalVolume = volume[i] #Start summing volume in slot
                else:
                    totalVolume+=volume[i] #While flag is set, sum volume

            if(volume[i] < 0 and indexFlag == True):
                print("----------------------------------------------")
                print("On from %s to %s" %(time[start], time[i-1]))
                print("Volume consumed in operation slot: %.2f" %(totalVolume))
                print("----------------------------------------------")
                indexFlag=False
                volumeTotals.append(totalVolume)

def findFirstDate(dateArray, keyDate):
    '''
    Function to find start first date in array - used in matching array starts
    and ends
    '''
    for i in range(dateArray.shape[1]):
        print("Current: %s"%dt.datetime.utcfromtimestamp(dateArray[0,i]).date())
        print("Looking for: %s"%keyDate.date())
        if  dt.datetime.utcfromtimestamp(dateArray[0,i]).date() == keyDate.date():
            return i
        else: pass
    print("Error: Did not find date")

"""
The ``myModels`` module contains functions for calculating solar power
available in the Launch Lab, Stellenbosch and other simulations used in
the EE final year project.
"""

import math
import numpy as np
import datetime as dt
import time
from dateutil import tz
import csv
import Cost_Funcs as cf
import Geyser_Funcs as gf
import matplotlib.pyplot as plt
import pandas as pd
import pvlib
from pvlib.location import Location

# PR = 4%(low rad.) + 0.41*temp.(temp loss) + 2% (dust) + 2.5% (inverter) + 6% (cables)

def CalcSolPow(startDay, endDay):
    """
    Determine power from solar radiation per day from one date to another

    Parameters
    ----------
    startDay : datetime object
        Start date for calculation of solar irradiation

    endDay : datetime object
        End date for calculation of solar irradiation

    Returns
    -------
    solarPow : numpy array, shape: (#days between start and end day,
                                     hours in day = 24)
        Calculated power supplied from solar panel per hour per day

    Reference:
    ----------
    https://stackoverflow.com/questions/44952762/pvlib-dc-power-from-irradiation-simple-calculation
    Used as reference for solar panel calculations and use of pvlib
    https://photovoltaic-software.com/PV-solar-energy-calculation.php
    Used for calculation of PV system output energy

    Citation for  PvLib:
    William F. Holmgren, Clifford W. Hansen, and Mark A. Mikofski.
    "pvlib python: a python package for modeling solar energy systems."
    Journal of Open Source Software, 3(29), 884, (2018). https://doi.org/10.21105/joss.00884
    """
    #-----[Canadian Solar CS6U-330P] & ------
    PANEL_AREA = 1.960 * 0.992 # m^2
    NUMBER_OF_PANELS = 150 # 300
    ROOF_AREA = 1995 # m^2


    dates = []
    maxi = []
    dayAmount = (endDay-startDay).days
    solarPow = np.zeros((dayAmount+1,24))

    for i in range(dayAmount+1):
        stellies = Location(-33.925146, 18.865785, 'Africa/Johannesburg', 136, 'LaunchLab')
        times = pd.date_range(start=startDay+dt.timedelta(days=i),
                            end=startDay+dt.timedelta(days=i, hours=23, minutes=59),
                            freq='60min')
        ephem_data = pvlib.solarposition.spa_python(times, stellies.latitude, stellies.longitude)
        dni_extra = pvlib.irradiance.extraradiation (times)
        irrad_data = stellies.get_clearsky(times)
        AM = pvlib.atmosphere.relativeairmass(ephem_data['apparent_zenith'])
        total = pvlib.irradiance.total_irrad(40, 180,
                ephem_data['apparent_zenith'], ephem_data['azimuth'],
                dni=irrad_data['dni'], ghi=irrad_data['ghi'],
                dhi=irrad_data['dhi'], airmass=AM,
                surface_type='urban', model='isotropic',
                dni_extra=dni_extra)
        poa = total['poa_global'].values
        Ans=(poa/1000)*330*NUMBER_OF_PANELS*1.3 # in Whrs
        solarPow[i,:] = Ans
        dates.append(times)
        maxi.append(max(Ans))
    return solarPow, dates, maxi

def FiveMinSolarRunner(normal_data, sol):
    """
    Method used in comparing normal energy consumption data to supply of solar
    energy to return excess solar supply if supplying consumption leaves extra.

    Args:
        normal_data (array[days,5min_intervals]):
            Energy values to supply with solar power.
        sol (array[days,5min_intervals]):
            Solar energy supply.

    Return:
        sol_test (array[days,5min_intervals]):
            Energy remainder to be supplied by grid.
        excess (array[days,5min_intervals]):
            Excess solar energy remaining after supplying loads.
    """
    sol_test = []
    excess = []

    sol_test_c = []
    excess_c = []
    normal_data = normal_data*12
    for i in range(normal_data.shape[0]):
        for j in range(normal_data.shape[1]):
            if(sol[i,j] > normal_data[i,j]):
                excess_c.append(sol[i,j]-normal_data[i,j])
                sol_test_c.append(0)
            else:
                sol_test_c.append(normal_data[i,j] - sol[i,j])
                excess_c.append(0)

        excess.append(excess_c)
        sol_test.append(sol_test_c)
        excess_c = []
        sol_test_c = []

    excess = np.array(excess)/12
    sol_test = np.array(sol_test)/12

    return sol_test, excess

def get_5min_LL_data():
    '''
    Get Launch Lab energy consumption data in 5min intervals.

    Returns
    -------
    tstamp : list
        Timestamps for LaunchLab data.
    power: list
        Energy consumption for LaunchLab data.
    peaks: list
        Peak value in period.
    '''


    with open("LL loads.csv", newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            tstamp = [] # list for timestamps
            tcollect = []
            power = []
            peaks = []
            pcollect = []
            peak=0
            pVal=0
            for row in reader:
                if(float(row['stot']) > peak):
                    peak = float(row['stot'])

                currDay = dt.datetime.strptime(row['tstamp'], '%d/%m/%Y %H:%M')
                currDay = datetime_from_utc_to_local(currDay)
                # Every Day, store list of times (in hour)
                if(currDay.time() == dt.time(hour=00,minute=00)):      #
                    tstamp.append(tcollect)
                    power.append(pcollect)
                    peaks.append(peak)
                    tcollect = []
                    pcollect = []
                    tcollect.append(currDay)      #
                    pcollect.append(pVal/12) # fill lists and get in kWhrs
                    peak=0

                # Every 5 mins
                else:
                    pVal = float(row['ptot'])
                    #print(dt.datetime.strptime(row['tstamp'], '%d/%m/%Y %H:%M'))
                    tcollect.append(currDay)      #
                    pcollect.append(pVal/12) # fill lists and get in kWhrs


    # Get rid of first day (as it is not full)
    tstamp = tstamp[1:]
    power = power[1:]

    return tstamp, power, peaks

def get_LL_data():
    '''
    Get Launch Lab energy consumption data in hour intervals.

    Returns
    -------
    tstamp : list
        Timestamps for LaunchLab data.
    power: list
        Energy consumption for LaunchLab data.
    peaks: list
        Peak value in period.
    '''

    with open("LL loads.csv", newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            tstamp = [] # list for timestamps
            tcollect = []
            power = []
            peaks = []
            pcollect = []
            peak=0
            pVal=0
            for row in reader:
                if(float(row['stot']) > peak):
                    peak = float(row['stot'])

                currDay = dt.datetime.strptime(row['tstamp'], '%d/%m/%Y %H:%M')
                #sast = sast.replace(tzinfo=from_zone)
                currDay = datetime_from_utc_to_local(currDay)
                # Every Day, store list of times (in hour)
                if(currDay.time() == dt.time(hour=00,minute=00)):
                    tstamp.append(tcollect)
                    power.append(pcollect)
                    peaks.append(peak)
                    tcollect = []
                    pcollect = []
                    peak=0

                # End of every Hour, add entry to list and reset accumulator for power
                if(currDay.minute == 55):
                    pVal += float(row['ptot'])
                    #print(dt.datetime.strptime(row['tstamp'], '%d/%m/%Y %H:%M'))
                    tcollect.append(currDay-dt.timedelta(minutes=55))      #
                    pcollect.append(pVal/12) # fill lists and get in kWhrs
                    pVal=0

                # Accumulate power consumption in that hour
                else:
                    pVal += float(row['ptot'])

    # Get rid of first day (as it is not full)
    tstamp = tstamp[1:]
    power = power[1:]

    return tstamp, power, peaks

def LL_without_PV(time_LL, power_LL, peaks_LL):
    """
    Use Launch Lab energy consumption to get energy consumption financial model
    for standard data.
    """

    f = cf.finModel()

    for i in range(len(power_LL)): # loop through days
        for j in range(len(power_LL[0])): # loop through hours
            day = time_LL[i][j]
            f.RateCollection(day, power_LL[i][j], peaks_LL[i])

            lastDay = cf.last_day_of_month(day)
            if(day == lastDay):
                f.EndOfMonth(day)
    return f, power_LL, time_LL

def LL_with_PV(time_LL, power_LL, peaks_LL):
    sol_month_total = 0
    sol_totals = []

    #Get without PV data
    f_nopv, p, t = LL_without_PV(time_LL, power_LL, peaks_LL)

    # Calculate solar supply (starting from first full day in LL data)
    start = time_LL[1][0]
    end = time_LL[-1][-1]
    solarPow, time_Solar, maxi = CalcSolPow(start, end)
    solarPow = fix_solar(solarPow)

    # Turn in to array (starting from first complete day)
    power_LL = np.array(power_LL) # turn in to array

    #Calculate power values when solar supply is subtracted
    solarPow = solarPow/1000 # divide by 1000 to get in kWh
    newPower = np.zeros_like(solarPow)

    f_total = cf.finModel()
    f_pv = cf.finModel()

    for i in range(len(newPower)): #loop through days
        for j in range(len(newPower[0])): # loop through hours
            day = time_Solar[i][j].to_pydatetime()
            sol_month_total += solarPow[i,j]
            if(solarPow[i,j] > power_LL[i,j]):
                newPower[i,j] = 0
            else:
                newPower[i,j] = power_LL[i,j] - solarPow[i,j]
            f_total.RateCollectionPV(day, newPower[i,j])
            f_pv.RateCollectionPV(day, solarPow[i,j])

            lastDay = cf.last_day_of_month(day)
            if(day == lastDay):
                sol_totals.append(sol_month_total)
                sol_month_total = 0
                f_total.EndOfMonth(day)
                f_pv.EndOfMonth(day)

    return f_total, newPower, sol_totals           # f_total, f_pv, f_nopv, newPower, time_LL

def Change_To_LEDs(time, energy):
    """
    Calculates the change in energy in using LED lights instead of normal lights

    Args:
        time (array[days,hours]):
            Timestamps for energy data in days, hours.
        energy (array[days,hours]):
            Original energy values in days, hours.

    Returns:
        time (array[days,hours]):
            Same as input arg.
        new_energy (array[days,hours]):
            Energy after lights are changed in days, hours.
    """
    STD_DOUBLE_PWR = 43 # W
    STD_SINGLE_PWR = 60 # W
    LED_DOUBLE_PWR = 14 # W
    LED_SINGLE_PWR = 14 # W
    NUMBER_OF_DOUBLES = 60
    NUMBER_OF_SINGLES = 68

    stdPower = (NUMBER_OF_DOUBLES*STD_DOUBLE_PWR + NUMBER_OF_SINGLES*STD_SINGLE_PWR)/1000 # divide by 1000 to get in kWhrs
    LEDLightPower = (NUMBER_OF_DOUBLES*LED_DOUBLE_PWR + NUMBER_OF_SINGLES*LED_SINGLE_PWR)/1000 # divide by 1000 to get in kWhrs

    new_energy = np.zeros_like(energy)

    # Add LED lights
    for i in range(new_energy.shape[0]): # loop through days
        for j in range(new_energy.shape[1]): # loop through hours
            # Add approx power used by LED lights
            new_energy[i,j] = energy[i,j] - stdPower + LEDLightPower

    return time, new_energy

def getFinModel(tStamp, energy):
    """
    Get financial model from energy in form array[days, hours].

    Args:
        tStamp (array[days,hours]):
            Timestamps for energy data in days, hours.
        energy (array[days,hours]):
            Energy values used to calculate cost in days, hours.

    Returns:
        fModel (class instance):
            Can be used to get cost values and slotted energy usage (peak, std,
            off-peak).

    """

    fModel = cf.finModel()

    for i in range(energy.shape[0]): # loop through days
        for j in range(energy.shape[1]): # loop through hours
            day = tStamp[i][j]
            # Add energy for hour
            fModel.RateCollectionPV(day, energy[i,j])

            #Check if last day
            lastDay = cf.last_day_of_month(day)
            if(day == lastDay):
                fModel.EndOfMonth(day)

    return fModel

#--------------------Helper Functions------------------#
def earliestDate(date1, date2):
    if date1[0] > date2[0]:
        return date1[0]
    else:
        return date2[0]

def latestDate(date1, date2):
    if date1[-1]< date2[-1]:
        return date1[-1]
    else:
        return date2[-1]

def GetCSVData(Filename):
    with open(Filename, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        tstamp = [] # list for timestamps
        tcollect = []
        energy = []
        peaks = []
        ecollect = []
        peak=0

        for row in reader:
            try:
                if(float(row['kVA']) > peak):
                    peak = float(row['kVA'])

                # Every Day, store list of times (in hour)
                day = dt.datetime.strptime(row['Date/Time'], '%d/%m/%Y %H:%M')
                if(day.time() == dt.time(hour=00,minute=00)):
                    tcollect.append(day)
                    ecollect.append(float(row['kWh']))
                    tstamp.append(tcollect)
                    energy.append(ecollect)
                    peaks.append(peak)
                    tcollect = []
                    ecollect = []
                    peak=0

                # End of every Hour, add entry to list and reset accumulator for power
                else:
                    tcollect.append(day)      #
                    ecollect.append(float(row['kWh'])) # fill lists and get in kWhrs

            except:
                pass

        return tstamp, energy, peaks

def datetime_from_utc_to_local(utc_datetime):
    now_timestamp = time.time()
    offset = dt.datetime.fromtimestamp(now_timestamp) - dt.datetime.utcfromtimestamp(now_timestamp)
    return utc_datetime + offset

def fix_solar(solar_power):
    soz = np.array(solar_power)
    shifted = np.zeros_like(soz)
    for i in range(soz.shape[0]):
        for j in range(soz.shape[1]):
            if(j<(soz.shape[1]-2)):
                shifted[i,j+2] = soz[i,j]
    return shifted

def SolPow_hr_to_5min(solar_power):
    sol_mins = np.zeros((solar_power.shape[0], 24*12))

    for i in range(solar_power.shape[0]): # days
        for j in range(solar_power.shape[1]): # hours
            curr_val = solar_power[i,j] # kWh value
            for k in range(12): # mins
                min_i = j*12+k
                sol_mins[i,min_i] =  curr_val # Fill with averaged values per 5 min
    return sol_mins

def To_Days_Hrs(tStamp, data):
    t_collect = []
    d_collect = []

    time = []
    new_data = []
    dVal = 0

    # Change from (Days, 5 min interval) to (Days, hrs)
    for i in range(data.shape[0]): # Days
        for j in range(data.shape[1]): # 5 min interval
            if(tStamp[i,j].time() == dt.time(hour=00,minute=00)):
                if(t_collect): # Make sure the list is full
                    time.append(t_collect)
                    new_data.append(d_collect)

                t_collect = []
                d_collect = []
            if(tStamp[i,j].minute == 55):
                dVal += data[i,j]
                t_collect.append(tStamp[i,j] - dt.timedelta(minutes=55))
                d_collect.append(dVal)
                dVal = 0
            else:
                dVal += data[i,j]
    time = np.array(time)
    new_data = np.array(new_data)

    return time, new_data

def To_Days_Hrs_temp(tStamp, temp_data):
    t_collect = []
    d_collect = []

    time = []
    new_data = []
    dVal = 0

    # Change from (Days, 5 min interval) to (Days, hrs)
    for i in range(temp_data.shape[0]): # Days
        for j in range(temp_data.shape[1]): # 5 min interval
            if(tStamp[i,j].time() == dt.time(hour=00,minute=00)):
                if(t_collect):
                    time.append(t_collect)
                    new_data.append(d_collect)

                    t_collect = []
                    d_collect = []
            if(tStamp[i,j].minute == 55):
                dVal += temp_data[i,j]
                t_collect.append(tStamp[i,j] - dt.timedelta(minutes=55))
                d_collect.append(dVal/12) # Average the temp
                dVal = 0
            else:
                dVal += temp_data[i,j]
    time = np.array(time)
    new_data = np.array(new_data)

    return time, new_data

def To_Days_5Mins(tStamp, data):
    t  = []
    d = []
    t_collect = []
    d_collect = []
    dVal = 0

    for i in range(data.shape[0]): # Days
            for j in range(data.shape[1]): # Mins
                if(tStamp[i,j].time() == dt.time(hour=00,minute=00)):
                    if(t_collect):
                        t.append(t_collect)
                        d.append(d_collect)
                        t_collect = []
                        d_collect = []

                if(tStamp[i,j].minute % 5 == 0):
                    dVal += data[i,j]
                    t_collect.append(tStamp[i,j])
                    d_collect.append(dVal)
                    dVal = 0
                else:
                    dVal += data[i,j]
        # ------- Every Day -----------------#

    t = np.array(t)
    d = np.array(d)
    return t,d

def To_Days_5Mins_temp(tStamp, data):
    t  = []
    d = []
    t_collect = []
    d_collect = []
    dVal = 0

    for i in range(data.shape[0]): # Days
            for j in range(data.shape[1]): # Mins
                if(tStamp[i,j].time() == dt.time(hour=00,minute=00)):
                    if(t_collect):
                        t.append(t_collect)
                        d.append(d_collect)
                        t_collect = []
                        d_collect = []

                if(tStamp[i,j].minute % 5 == 0):
                    t_collect.append(tStamp[i,j])
                    d_collect.append(dVal/4)
                    dVal = 0
                else:
                    dVal += data[i,j]
        # ------- Every Day -----------------#

    t = np.array(t)
    d = np.array(d)
    return t,d

def To_Month_From_Hrs(tStamp, data, only_month=False):
    time = []
    data_new = []
    d_collect = []
    t_collect = []

    first_month = tStamp[0,0].date().month
    next_month = tStamp[0,0].replace(day=28) + dt.timedelta(days=4)

    for i in range(data.shape[0]): # Days
        for j in range(data.shape[1]): # Hours
            if(tStamp[i,j] == next_month):
                data_new.append(d_collect)
                if(only_month):
                    time.append(tStamp[i,j].strftime('%B, %Y'))
                else:
                    time.append(d_collect)
                next_month = tStamp[i,j].replace(day=28) + dt.timedelta(days=4)
                d_collect = []
                t_collect = []

            else:
                d_collect.append(data[i,j])
                if(only_month == False):
                    t_collect.append(tStamp[i,j])

    return time, data_new

def Month_Tot(tStamp, data, only_month=False):
    time = []
    data_new = []
    data_tot = 0
    t_collect = []

    first_month = tStamp[0,0].date().month
    next_month = tStamp[0,0].replace(day=28) + dt.timedelta(days=4)

    for i in range(data.shape[0]): # Days
        for j in range(data.shape[1]): # Hours
            if(tStamp[i,j] == next_month):
                data_new.append(data_tot)
                data_tot = 0
                if(only_month):
                    time.append(tStamp[i,j].strftime('%B, %Y'))
                else:
                    time.append(d_collect)
                next_month = tStamp[i,j].replace(day=28) + dt.timedelta(days=4)
                t_collect = []

            else:
                data_tot += data[i,j]
                if(only_month == False):
                    t_collect.append(tStamp[i,j])

    return time, data_new

def Month_Avg(tStamp, data):
    time = []
    data_new = []
    data_tot = 0
    days_in_month = 0
    t_collect = []
    d_collect = []
    prevMonth = tStamp[0,0].month

    for i in range(tStamp.shape[0]): # Days
        for j in range(tStamp.shape[1]): # Hours
            if(tStamp[i,j].month > prevMonth):
                data_new.append(d_collect)
                time.append(t_collect)
                d_collect = []
                t_collect = []
                d_collect.append(data[i,j])
                t_collect.append(tStamp[i,j])

                prevMonth = tStamp[i,j].month
            else:
                d_collect.append(data[i,j])
                t_collect.append(tStamp[i,j])

    return time, data_new

def PVPow(startDay, endDay):
    """
    Determine power from solar radiation per day from one date to another

    Parameters
    ----------
    startDay : datetime object
        Start date for calculation of solar irradiation

    endDay : datetime object
        End date for calculation of solar irradiation

    Returns
    -------
    solarPow : numpy array, shape: (#days between start and end day,
                                     hours in day = 24)
        Calculated power supplied from solar panel per hour per day

    Reference:
    ----------
    https://stackoverflow.com/questions/44952762/pvlib-dc-power-from-irradiation-simple-calculation
    Used as reference for solar panel calculations and use of pvlib
    https://photovoltaic-software.com/PV-solar-energy-calculation.php
    Used for calculation of PV system output energy
    """
    PANEL_EFFICIENCY = 0.1697 # Worst value chosen (pessimistic case)
    PANEL_AREA = 1.960 * 0.992 # m^2
    number_panels = 100
    roof_area = number_panels*PANEL_AREA # m^2
    VOLT_OUTPUT = 5.82 #V
    PERFORMANCE_RATIO = 0.75 # default value for losses (PR calc below)
    MAX_OUTPUT_POWER = 330 # max rated power at 1000W/m^2

    dates = []
    maxi = []
    dayAmount = (endDay-startDay).days
    solarPow = np.zeros((dayAmount+1,24))

    for i in range(dayAmount+1):
        stellies = Location(-33.925146, 18.865785, 'UTC', 136, 'LaunchLab')
        times = pd.date_range(start=startDay+dt.timedelta(days=i),
                            end=startDay+dt.timedelta(days=i, hours=23, minutes=59),
                            freq='60min')
        ephem_data = pvlib.solarposition.spa_python(times, stellies.latitude, stellies.longitude)
        irrad_data = stellies.get_clearsky(times)
        AM = pvlib.atmosphere.relativeairmass(ephem_data['apparent_zenith'])
        total = pvlib.irradiance.total_irrad(40, 180,
                ephem_data['apparent_zenith'], ephem_data['azimuth'],
                dni=irrad_data['dni'], ghi=irrad_data['ghi'],
                dhi=irrad_data['dhi'], airmass=AM,
                surface_type='urban')
        poa = total['poa_global'].values
        Ans=(poa/1000)*330*number_panels
        solarPow[i,:] = Ans
        maxi.append(max(Ans/number_panels))
        dates.append(times)
    return solarPow, dates, maxi

def Run_With_PV(time_LL, power_LL, peaks_LL):
    sol_month_total = 0
    sol_totals = []

    #Get without PV data
    f_nopv, p, t = LL_without_PV(time_LL, power_LL, peaks_LL)

    # Calculate solar supply (starting from first full day in LL data)
    start = time_LL[1][0]
    end = time_LL[-1][-1]
    solarPow, time_Solar, maxi = PVPow(start, end)

    # Turn in to array (starting from first complete day)
    power_LL = np.array(power_LL) # turn in to array

    #Calculate power values when solar supply is subtracted
    solarPow = solarPow/1000 # divide by 1000 to get in kWh
    newPower = np.zeros_like(solarPow)

    f_total = cf.finModel()
    f_pv = cf.finModel()

    for i in range(len(newPower)): #loop through days
        for j in range(len(newPower[0])): # loop through hours
            day = time_Solar[i][j].to_pydatetime()
            sol_month_total += solarPow[i,j]
            if(solarPow[i,j] > power_LL[i,j]):
                newPower[i,j] = 0
            else:
                newPower[i,j] = power_LL[i,j] - solarPow[i,j]
            f_total.RateCollectionPV(day, newPower[i,j])
            f_pv.RateCollectionPV(day, solarPow[i,j])

            lastDay = cf.last_day_of_month(day)
            if(day == lastDay):
                sol_totals.append(sol_month_total)
                sol_month_total = 0
                f_total.EndOfMonth(day)
                f_pv.EndOfMonth(day)

    return f_total, sol_totals, f_nopv, maxi           # f_total, f_pv, f_nopv, newPower, time_LL

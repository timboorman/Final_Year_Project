import math
import datetime

class ewhModel:

    #Physical constants
    rho = 1000    #Denisity of water
    c = 4184      #Specific heat capacity of water [joule/(kg*Kelin)]

    def __init__(self, thermal_resistance, tank_volume):

        self.R = thermal_resistance
        self.GeyserOn = False
        self.TANK_LENGTH = 1
        self.TANK_VOLUME = tank_volume
        self.TANK_RADIUS = math.sqrt((self.TANK_VOLUME/1000)/(math.pi*self.TANK_LENGTH))
        self.TANK_AREA = 2*math.pi*self.TANK_RADIUS*self.TANK_LENGTH + 2*math.pi*self.TANK_RADIUS*self.TANK_RADIUS


        print('len %d, vol %d, area %.3f, radius %.3f, R %.2f'%(self.TANK_LENGTH,
                                                                self.TANK_VOLUME,
                                                                self.TANK_AREA,
                                                                self.TANK_RADIUS,
                                                                self.R))


    # ---------------------------- Physical equations --------------------------------------
    def __waterEnthalpy__(self, water_temperature, ref_temperature, liters_water):
        #print("Enthalpy")
        return self.c * self.rho *(liters_water * 0.001) * (water_temperature - ref_temperature)


    def __deltaTemperature__(self, energy, liters_water):
        #print("Delta_temp")
        return energy/(self.c * self.rho * (liters_water * 0.001))



    def __thermalDecay__(self, time, t_inital, t_ambient, volume, thermal_resistance):
        #print("Decay")
        return t_ambient + (t_inital - t_ambient)*math.exp((-1.0 * time)/(self.c*self.rho*(0.001*volume)*thermal_resistance))
    # -------------------------------------------------------------------------------------------



class ewhModel_one(ewhModel):



    def __init__(self, thermal_resistance, tank_volume, t_initial):  ##kry tipies
        ewhModel.__init__(self, thermal_resistance, tank_volume)
        self.t_inside_rst = t_initial
        self.t_inside = t_initial
        self.model_type = 'one'

    def reset(self):
        self.t_inside = self.t_inside_rst

    # ------------------------ Sim methods ---------------------------------------------
    def stepTime(self, time_sec, added_power_kw):
        #Increase due to power added
        element_energy_added = (added_power_kw*1000)*time_sec  #Convert to Watt and integrate
        self.t_inside += self.__deltaTemperature__(element_energy_added, self.TANK_VOLUME)

        #Decrease due to thermal losses
        self.t_inside = self.__thermalDecay__(time_sec, self.t_inside, self.t_amb, self.TANK_VOLUME, self.R);

    def stepTimeDecay(self, time_sec):
        #Decrease due to thermal losses
        self.t_inside = self.__thermalDecay__(time_sec, self.t_inside, self.t_amb, self.TANK_VOLUME, self.R);

    def stepVolume(self, volume_litres):
        self.t_inside = ((self.TANK_VOLUME - volume_litres)/self.TANK_VOLUME) * (self.t_inside - self.t_inlet) + self.t_inlet
    # ------------------------------------------------------------------------------------

    def setTemp(self, temp):
        self.t_inside = temp
    # ------------------------ State getters and setters --------------------------------
    def getOutletTemp(self):
        return self.t_inside    #The one-node model assumes uniform temperature

    def setInletTemp(self, temp_degC):
        self.t_inlet = temp_degC

    def setAmbTemp(self, temp_degC):
        self.t_amb = temp_degC
    #------------------------------------------------------------------------------------

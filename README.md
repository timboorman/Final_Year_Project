# Final_Year_Project
TM Boorman Final Year Project (Skripsie)

This repository contains the code for a final year dissertation paper that investigated savings one could make in using interventions such as solar panel installation and changing lights to LED. It was done using the LaunchLab (a small business in Stellenbosch, South Africa) as a test case.

Main contributions of the project where:
 - Software models of hot-water-cylinders/water-heaters/geysers based on a mathematical model (single-node).
 - Software model of Stellenbosch tariffs (monthly) for electricity used throughout the year of a small business.
 - Simulation of cost to a company using CSV data for up to a whole year with configuration options to allow comparison with solar power usage and with LED light replacement (this was done externally using a Jupyter Notebook).

File descriptions:
- gModels.py: contains class for geyser creation. This file aims to turn the mathematical model of a hot-water-cylinder in to a software object that can be interacted with and the attributes changed (such as internal temperature and volume of water).
- Geyser_Funcs.py: contains set of functions/methods that use the gModel class to run simulations. This includes: setup/initialisation of geyser, simulated running of the geyser with volume consumption data input ("Simulation" method) and simulations using varied types of geyser - for investigation of energy consumption changes.
- MyModels.py: contains simulation methods for solar panel use (such as available energy during time of use and energy change when introducting solar panels to system), financial simulation, loading and displaying of load profile of building (input of data in CSV format) and various conversion methods for data types and forms.

 Credit:
 - This project made use of an external library to get solar radiation levels used in solar power calculations. 
   (pvlib: https://doi.org/10.21105/joss.00884)
 - Mathematical models for hot-water-cylinders based on paper by P.J.C Nel, M.J. Booysen and B. Van Der Merwe (link: https://ieeexplore.ieee.org/document/7438883)

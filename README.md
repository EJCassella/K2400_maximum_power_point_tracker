# K2400_maximum_power_point_tracker

MPPT for pv cells using set up in EPMM labs at the UoS

---

## Usage:

1. Anaconda should be installed on the C16 computer, so open "Anaconda Prompt"
2. cd into the desktop
3. Type in the following:

```bash
 git clone https://github.com/EJCassella/K2400_maximum_power_point_tracker
```

4. Change directory into the new directory:

```bash
 cd K2400_maximum_power_point_tracker
```

5. Create the conda enviroment from the .yml file by typing:

```bash
conda env create -f MPPenvironment.yml
```

6. Activate the conda environment using:
   `conda activate MPPenvironment`
7. Everything is ready to go! Hook up your device to the 🐊crocodile clips and make sure the lamp is turned on.
8. Run the script using the following (for example, will MPP track for 120 seconds for a device with 0.2 cm^2 active area):

```bash
python K2400_MPP_tracking.py GPIB0::20::INSTR 120 0.2
```

```bash
$ ./python K2400_MPP_tracking.py -h
usage: K2400_MPP_tracking.py [-h] [--shutterOut] [address] [total_tracking_time] [device_area]

Maximum power point tracker with shutter control for devices and minimodules using Keithley 2400

positional arguments:
address GPIB address for Keithley 2400, should be GPIB0::20::INSTR
total_tracking_time Total number of seconds to run for
device_area Device active area in cm^2

options:
-h, --help show this help message and exit
--shutterOut
Digital I/O address for USB6501 object to address the solar simulator shutter. Should be
Testboard/port1/line0

(MPPenv) C:\Users\Elena\Documents\GitHub\K2400_maximum_power_point_tracker>`
```

## Data output:

Note: This code is a work in progress and I will be updating the data output ASAP.

Currently (02-02-2025) the code outputs a log file with three columns, the timestamp in seconds, the device voltage in Volts, and the device current in Amps.

## Future updates:

I plan to update the data output to include the short-circuit current density and record more device metadata. We will also output the efficiency/voltage/current plots.

I'll add a backstop to make sure the perturbed voltage doesn't run away with itself, specifically making sure it doesn't run the device in reverse bias.

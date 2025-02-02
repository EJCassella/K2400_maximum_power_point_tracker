# -*- coding: utf-8 -*-
"""
Maximum Power Point Tracker (MPPT)

This script is designed to track the maximum power point (MPP) of a photovoltaic device
using a Keithley 2400 sourcemeter and the solar simulator setup for the EPMM group at 
the University of Sheffield. Optional shutter control is implemented via a USB6501 object
connected via BNC to the solar simulator.

Created on Fri Jan 31 17:08:40 2025
@author: Elena Cassella
"""

import argparse
import sys
import time
import pyvisa as visa
import numpy as np
import matplotlib.pyplot as plt
from nidaqmx import Task

class MaximumPowerPointTracker:
    """
    A class to manage and control Maximum Power Point Tracking (MPPT) using 
    a Keithley 2400 sourcemeter and an optional shutter system.

    Attributes:
        args (Namespace): Command-line arguments.
        K2400 (object): Keithley 2400 sourcemeter object.
        task (object): Shutter control NIDAQmx task object.
        start_time (float): Start time for tracking.
        v_step (float): Voltage step size.
        Voc (float): Open-circuit voltage.
        Isc (float): Short-circuit current.
        Vmpp (float): Voltage at maximum power point.
        log_file (file object): File for logging tracking data.
        v_data (list): Voltage data for plotting.
        i_data (list): Current data for plotting.
        t_data (list): Time data for plotting.
        efficiencies (list): Efficiency data for plotting.
        pce_line, v_line, i_line (Line2D): Line objects for real-time plotting.
    """


    def __init__(self, args):
      """Initialises the MPPT system, including the Keithley 2400 and shutter control."""
      self.args = args
      self.K2400 = None
      self.task = None
      self.start_time = None
      self.v_step = 0 
      self.Voc = 0
      self.Isc = 0
      self.Vmpp = 0
      self.log_file = open("mpp_tracker_log.txt", "w")    
      self.initialise()

      self.write_to_console(f"{self.args.total_tracking_time / 60:.2f} minutes MPP tracking.")

      # Initialising empty lists ready to update interactive plot
      self.v_data = []
      self.i_data = []
      self.t_data = []
      self.efficiencies = []

      # Initialise plot line objects
      self.pce_line = None
      self.v_line = None
      self.i_line = None


    def write_to_console(self, *args):
      """Prints messages to the console in real time."""
      print(*args, file=sys.stdout, flush=True)


    def write_data_to_file(self, *args):
      """Writes tracking data to a log file."""
      print(*args, file=self.log_file, flush=True)
    

    def initialise(self):
      """ Initialises the Keithley 2400 and the shutter control."""
      self.K2400 = self.initialise_keithley()
      self.task = self.initialise_shutter_control()


    def initialise_keithley(self):
      """
      Initialises and configures the Keithley 2400 sourcemeter.
      
      Returns:
          K2400 (object): Initialised Keithley 2400 sourcemeter object.
      
      Raises:
          SystemExit: If the Keithley 2400 cannot be initialised.
      """
      try:
        rm = visa.ResourceManager()
        K2400 = rm.open_resource(resource_name=self.args.address, timeout=60000, _read_termination= u'\n')
        K2400.write('*RST')
        K2400.write(':trace:clear')
        K2400.write(':system:azero on')
        K2400.write(':sense:function:concurrent on')
        K2400.write(':sense:function "current:dc", "voltage:dc"')
        K2400.write(':format:elements voltage,current,time')

      except:
        self.write_to_console("Unable to connect to Keithley 2400.")
        try:
          K2400.close()
        except:
          pass
        sys.exit(1)
      self.write_to_console("Keithley 2400 successfully initialised.")
      return K2400


    def initialise_shutter_control(self):
      """
      Initialises the USB6501 shutter control using NIDAQmx.
      
      Returns:
          task (object): InitialiSed NIDAQmx task object for shutter control.
      
      Raises:
          None: If the shutter control initialisation fails, it returns None.
      """
      try:
        task = Task()
        task.do_channels.add_do_chan(self.args.shutterOut)
        task.start()
        task.write([False]) # Initialise shutter state OPEN        
        self.write_to_console("DAQ task initialised for automatic shutter control.")
        return task
      except:
          self.write_to_console("Could not initialise shutter control. Manually control shutter.")
          if task:
              task.stop()
              task.close()
          return None
        

    def find_open_circuit(self):
      """
      Measures the open-circuit voltage (Voc) of the device using the Keithley 2400.
      
      Returns:
          None: It updates the Voc attribute directly.
      """
      self.K2400.write(':source:function current')
      self.K2400.write(':source:current:mode fixed')
      self.K2400.write(':source:current:range min')
      self.K2400.write(':source:current 0')
      self.K2400.write('sense:voltage:protection 10')
      self.K2400.write('sense:voltage:range 10')
      self.K2400.write(':sense:voltage:nplcycles 1')
      self.K2400.write(':sense:current:nplcycles 1')
      self.K2400.write(':display:digits 7')
      self.K2400.write(':output on')
      self.write_to_console("Holding device at 0 current for 5 seconds before measuring Voc.")
      time.sleep(5) # Allow device to stabilise before measuring Voc.
      self.write_to_console("Measuring open circuit voltage.")
      Voc, _, _ = self.K2400.query_ascii_values('READ?')
      self.Voc = Voc
      self.write_to_console(f"Device Voc: {np.round(Voc,2)} V.")
      self.K2400.write(':output off')


    def plot_sweep(self, v, i, p, maxIndex):
      """
      Plots the current-voltage and power-voltage sweeps of the device.
      
      Args:
          v (array): Voltage data.
          i (array): Current data.
          p (array): Power data.
          maxIndex (int): Index of the maximum power point in the sweep.
      
      Returns:
          None: Displays a plot of the sweeps.
      """
      fig, ax = plt.subplots()
      ax.set_xlim(0, self.Voc)
      ax.set_ylim(0, abs(self.Isc)*1.1)
      ax.plot(v, abs(i))
      ax.set_xlabel('Voltage (V)')
      ax.set_ylabel('Current (A)')
      ax.scatter(self.Vmpp, abs(i[maxIndex]), color='k')
      ax2 = ax.twinx()
      ax2.plot(v, p)
      ax2.set_ylim(0, max(p)*1.1)
      ax2.set_ylabel('Power (W)')
      ax.axvline(x=self.Vmpp, ymin=0, ymax=abs(self.Isc+1), ls='--', color='k')
      plt.show(block=False)


    def determine_initial_Vmpp(self):
      """
      Determines the initial voltage at maximum power point (Vmpp) by sweeping the 
      voltage from open-circuit voltage (Voc) to 0 and measuring current and power.
      
      Returns:
          None: It updates the Vmpp and Isc attributes directly.
      """
      n_points = 600
      current_compliance = 0.04 
      self.find_open_circuit()
      self.write_to_console("Sweeping from Voc to 0 V to find initial Vmpp.")
      self.K2400.write(':source:function voltage')
      self.K2400.write(':source:voltage:mode sweep')
      self.K2400.write(':source:sweep:spacing linear')
      self.K2400.write(':source:delay 0.05')
      self.K2400.write(f'trigger:count {n_points:d}')
      self.K2400.write(f':source:sweep:points {n_points:d}')
      self.K2400.write(f':source:voltage:start {self.Voc:.4f}')
      self.K2400.write(':source:voltage:stop 0.0000')
      self.v_step = abs(self.K2400.query_ascii_values(':source:voltage:step?')[0])
      self.K2400.write(f':source:voltage:range {self.Voc:.4f}')
      self.K2400.write(':source:sweep:ranging best')
      self.K2400.write(f':sense:current:protection {current_compliance:.6f}')
      self.K2400.write(f':sense:current:range {current_compliance:.6f}')
      self.K2400.write(':sense:voltage:nplcycles 0.5')
      self.K2400.write(':sense:current:nplcycles 0.5')
      self.K2400.write(':display:digits 5')

      self.K2400.write(f':source:voltage {self.Voc:0.4f}')
      self.K2400.write(':output on')

      jv_sweep = self.K2400.query_ascii_values('READ?')
      jv_sweep = np.reshape(jv_sweep, (-1,3))

      v = jv_sweep[:,0]
      i = jv_sweep[:,1]
      self.Isc = i[-1]
      p = abs(v*i)
      mpp_ind = np.argmax(p)
      self.Vmpp = v[mpp_ind]
      self.write_to_console("Initial Mpp found:")
      self.write_to_console(f"{np.round(p[mpp_ind]*1000,2)} mW @ {np.round(self.Vmpp,2)} V")
      self.plot_sweep(v, i , p, mpp_ind)


    def initialise_interactive_plot(self):
      """
      Initialises an interactive plot for tracking efficiency, voltage, and current density.
      
      Returns:
          None: Sets up plots in the figure for real-time updates.
      """
      plt.ion()
      fig, axes = plt.subplots(3, 1, sharex='col')
      
      #  1st row plot of efficiency
      self.pce_line, = axes[0].plot([], [], lw=2)
      axes[0].set_xlim(0, self.args.total_tracking_time) 
      axes[0].set_ylim(0, 23) 
      axes[0].set_ylabel('Power Conversion \nEfficiency (%)')

      # 2nd row plot of voltage
      self.v_line, = axes[1].plot([], [], lw=2)
      axes[1].set_xlim(0, self.args.total_tracking_time) 
      axes[1].set_ylim(0, self.Voc) #V range
      axes[1].set_ylabel('Voltage (V)')

      # 3rd row plot of current density
      self.i_line, = axes[2].plot([], [], lw=2)
      axes[2].set_xlim(0, self.args.total_tracking_time) 
      axes[2].set_ylim(0, abs(self.Isc*1000/self.args.device_area)*1.1) 
      axes[2].set_xlabel('Time (s)')
      axes[2].set_ylabel('Current \nDensity (mA/cm^2)')


    def update_plot(self, v, i, tx):
      """
      Updates the real-time plots for efficiency, voltage, and current density.
      
      Args:
          v (float): Voltage value at the current measurement.
          i (float): Current value at the current measurement.
          tx (float): Current timestamp of the measurement.
      
      Returns:
          None: Updates the interactive plot with new data.
      """
      self.t_data.append(tx-self.start_time)
      self.v_data.append(v)
      self.i_data.append(abs((i*1000)/self.args.device_area)) # Current in mA /cm^2

      # Function to calculate device PCE from Vmpp and Impp data
      def calculate_eff(v, i):
          """
          Calculates the device efficiency from the Vmpp and Impp data.

          Args:
            v (float): Voltage value at the current measurement.
            i (float): Current value at the current measurement.

          Returns:
            efficiency (float): Device efficiency at the current voltage.
          """
          j = i*1000/self.args.device_area
          efficiency = abs(v*j) # efficiency = Pout / Pin = vmpp*jmpp / 100 mW/cm2 which cancels out when you multiply by 100 for %
          return efficiency
      
      self.efficiencies.append(calculate_eff(v, i))
      
      # Update the plots with the new data
      self.pce_line.set_data(self.t_data, self.efficiencies)
      self.v_line.set_data(self.t_data, self.v_data)
      self.i_line.set_data(self.t_data, self.i_data)

      # Redraw the plot 
      plt.draw()
      plt.pause(0.1)


    def check_runtime(self, tx):
      """
      Checks how much time has elapsed; if more than `total_tracking_time`, stops measuring and shuts down.

      Args:
          tx (float): Current timestamp of the measurement.

      Returns:
          None: Ends the tracking if the runtime exceeds the total_tracking_time.
      """
      t_measurement = tx - self.start_time 
      if t_measurement > self.args.total_tracking_time:
        self.shutdown()


    def shutdown(self):
      """
      Shuts down the Keithley 2400, closes resources, and exits the script.
      
      Returns:
          None: Ends the script and releases all resources.
      """
      if self.task:
        self.task.write([True]) #shutterOFF
        self.task.stop()
        self.task.close()
      plt.ioff()
      plt.show(block=False)
      self.log_file.close()
      self.write_to_console("Keithley and USB6501 shutdown completed. Log file closed. Exiting.")
      sys.exit(0)


    def track_maximum_power_point(self):
      """
      Tracks the maximum power point (MPP) by adjusting the voltage at regular intervals (perturb and observe).
      
      Returns:
          None: Continuously tracks and adjusts the voltage to maximise power output unless KeyboardInterrupt.
      """
      self.determine_initial_Vmpp()
      self.write_to_console("Walking back to the initial Vmpp...")
      self.initialise_interactive_plot()
      V_set = 0
      self.K2400.write(':source:voltage:mode fixed')
      self.K2400.write(':trigger:count 1')
      v, i, t = self.K2400.query_ascii_values('READ?')
      self.start_time = t
      
      while V_set < self.Vmpp:
        self.K2400.write(f':source:voltage {V_set}')
        v, i, tx = self.K2400.query_ascii_values('READ?')
        self.update_plot(v, i, tx)
        V_set += self.v_step
        self.check_runtime(tx)
        self.write_data_to_file(f'{tx-self.start_time}, {v}, {i}')

      self.K2400.write(f':source:voltage {self.Vmpp:0.4f}')
      self.write_to_console('Device at Vmpp. Beginning MPP tracking.')
      
      previous_power=abs(v*i)
      direction = 1

      try:
        while True:
          self.K2400.write(f':source:voltage {self.Vmpp:0.4f}')
          v, i, tx = self.K2400.query_ascii_values('READ?')
          power = abs(v*i)
          self.check_runtime(tx)
          self.update_plot(v, i, tx)

          if power > previous_power:
            self.Vmpp += direction * self.v_step
          else:
            direction *= -1
            self.Vmpp += direction * self.v_step 

          previous_power = power
      except KeyboardInterrupt:
        self.shutdown()

          
    @staticmethod
    def parse_arguments():
      """
      Parses command-line arguments for the MPPT script.
      
      Returns:
          args (Namespace): Parsed command-line arguments.
      """
      parser = argparse.ArgumentParser(description='Maximum power point tracker with shutter control for devices and minimodules using Keithley 2400')
      parser.add_argument("address", nargs='?', default=None, type=str, help="GPIB address for Keithley 2400, should be GPIB0::20::INSTR")
      parser.add_argument("total_tracking_time", nargs='?', default=None,  type=int, help="Total number of seconds to run for")
      parser.add_argument("device_area", nargs='?', default=None,  type=float, help="Device active area in cm^2")
      parser.add_argument("--shutterOut", nargs='?', type=str, default='Testboard/port1/line0', help='Digital I/O address for USB6501 object to address the solar simulator shutter. Should be Testboard/port1/line0')
      return parser.parse_args()
      

if __name__ == "__main__":
  args = MaximumPowerPointTracker.parse_arguments() # Parsing command-line arguments.
  mpp_tracker = MaximumPowerPointTracker(args) # Initialising MPPT tracking system.
  mpp_tracker.track_maximum_power_point() # Begin tracking maximum power point.
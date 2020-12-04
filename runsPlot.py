#!/usr/bin/env python3
# This program plots a three dimensional graph representing a runner's
# performance vs time and length of run. Input is an activity file downloaded
# from connect.garmin.com.

from mpl_toolkits import mplot3d
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
#from matplotlib.ticker import LinearLocator, FormatStrFormatter
import argparse
import datetime
from datetime import date

#============================================================================
# Globals

version = 3

#Input file field index values.
TYPE       = 0
TIME_STAMP = 1
DISTANCE   = 4
TIME       = 6

#============================================================================
# Classes

# A class to hold a run event.
class Event:
  def __init__(self, _timeStamp, _distance, _pace):
    self.timeStamp = _timeStamp # date.
    self.day = 0                # Day count from first run.
    self.distance = _distance   # In miles.
    self.pace = _pace           # In minutes per mile.

# A class to hold all the runs.
class Runs:
  def __init__(self):
    self.inputEvents = np.array([], dtype = Event)
    self.day = []
    self.distance = []
    self.pace = []

  def length(self):
    return len(self.inputEvents)

  # For each run in the file at path, load date, distance and pace. Pace is
  # computed from distance and time.
  def load(self, path):
    values = []
    self.__init__()
    with open(path) as inputFile:
      # Skip the header line.
      inputFile.readline()
      for line in inputFile:
        text = self.removeQuotesAndCommas(line)
        values = text.split(',')

        # Load only running events.
        if values[TYPE] == 'Running':
          # From values, get date, distance in miles.
          runDate = date.fromisoformat(values[TIME_STAMP].split()[0])
          runDistance = float(values[DISTANCE])

          # To get run pace, first convert time (hh:mm:ss) to minutes, then
          # compute pace (minutes/mile).
          h, m, s = values[TIME].split(':')
          t = 60.0 * float(h) + float(m) + (float(s) / 60.0)
          runPace = t / runDistance

          # Exclude outliers.
          if runDistance >= 2.0 and runDistance <= 27.0 \
            and runPace > 6.0 and runPace < 20.0:
              self.inputEvents = np.append(self.inputEvents, \
                Event(runDate, runDistance, runPace))

    # Computer the day numbers.
    firstDay = self.inputEvents[len(self.inputEvents) - 1].timeStamp
    for event in self.inputEvents:
      event.day = (event.timeStamp - firstDay).days


  def fitPlane(self):
    # Create the arrays needed for the fit.
    self.day = []
    self.distance = []
    self.pace = []
    for event in self.inputEvents:
      self.day.append(event.day);
      self.distance.append(event.distance);
      self.pace.append(event.pace);

    tmp_A = []
    tmp_b = []
    for i in range(len(self.day)):
      tmp_A.append([self.day[i], self.distance[i], 1])
      tmp_b.append(self.pace[i])
    b = np.matrix(tmp_b).T
    A = np.matrix(tmp_A)
    self.fit = (A.T * A).I * A.T *b
    errors = b - A * self.fit
    residual = np.linalg.norm(errors)
    print("solution:")
    print("  %f x + %f y + %f = z" %(self.fit[0], self.fit[1], self.fit[2]))
    # print("errors:")
    # print("  ", errors)
    print("residual:")
    print("  ", residual)

  def plot(self):
    fig = plt.figure()
    ax = plt.subplot(111, projection = '3d')
    ax.scatter(self.day, self.distance, self.pace, color = 'b')

    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    X, Y = np.meshgrid(np.arange(xlim[0], xlim[1]), \
      np.arange(ylim[0], ylim[1]))
    Z = np.zeros(X.shape)
    for r in range(X.shape[0]):
      for c in range(X.shape[1]):
        Z[r,c] = self.fit[0] * X[r,c] + self.fit[1] * Y[r,c] + self.fit[2]
    ax.plot_wireframe(X, Y, Z, color = 'y')

    ax.set_xlabel('Days since ' + \
      self.inputEvents[len(self.inputEvents)-1].timeStamp.strftime("%m-%d-%Y"))
    ax.set_ylabel('Distance - miles')
    ax.set_zlabel('Pace - min/mile')
    plt.show()

  # Remove commas embedded in quoted strings. Remove quotes from strings.
  # Return the modified string.
  def removeQuotesAndCommas(self, inputText):
    inQuotes = False
    outputText = ''
    for c in inputText:
      if inQuotes:
        if c == '"':
          inQuotes = False
        elif c != ',':
          outputText += c
      else:
        if c == '"':
          inQuotes = True
        else:
          outputText += c
    return outputText

#============================================================================
# Functions

def displayVersion():
  print("runningHistory version " + str(version))
  quit()

#============================================================================
# Main program

parser = argparse.ArgumentParser(description = \
  "Plot pace vs time and length of run")
parser.add_argument('inputFile', type = str, help = 'Input file path')
parser.add_argument('-v', '--version', action = 'store_true', \
  help = 'Display version and quit')

args = parser.parse_args()
if args.version:
  displayVersion()

runs = Runs()
runs.load(args.inputFile)
print("Total number of runs = ", runs.length())
runs.fitPlane()
runs.plot()

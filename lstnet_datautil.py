import numpy as np
import pandas as pd

# Logging
import logging
log = logging.getLogger('LSTNet')

class DataUtil(object):
    #
    # This class contains data specific information.
    # It does the following:
    #  - Read data from file
    #  - Normalise it
    #  - Split it into train, dev (validation) and test
    #  - Create X and Y for each of the 3 sets (train, dev, test) according to the following:
    #    Every sample (x, y) shall be created as follows:
    #     - x --> window number of values
    #     - y --> one value that is at horizon in the future i.e. that is horizon away past the last value of x
    #    This way X and Y will have the following dimensions:
    #     - X [number of samples, window, number of multivariate time series]
    #     - Y [number of samples, number of multivariate time series]
    
    def __init__(self, filename, train, horizon, window, normalise = 2):
        try:

            log.debug("Start reading data")
            self.rawdata   = pd.read_excel(filename, header=None)
			      
            self.rawdata.columns = ['date', 'time', 'demand']

            self.rawdata['datetime'] = pd.to_datetime(self.rawdata['date'].astype(str)+" "+self.rawdata['time'].astype(str), format='%Y-%m-%d %H:%M:%S')
            self.rawdata.drop(['date', 'time'], inplace=True, axis=1)

            self.rawdata = self.rawdata.set_index('datetime')
            print(self.rawdata.head())
            log.debug("End reading data")

            self.w         = window
            self.h         = horizon
            self.data      = np.zeros(self.rawdata.shape)
            self.n, self.m = self.data.shape
            self.normalise = normalise
            self.scale     = np.ones(self.m)
        
            self.normalise_data(normalise)
            self.split_data(train)
        except IOError as err:
            # In case file is not found, all of the above attributes will not have been created
            # Hence, in order to check if this call was successful, you can call hasattr on this object 
            # to check if it has attribute 'data' for example
            log.error("Error opening data file ... %s", err)
        
        
    def normalise_data(self, normalise):
        log.debug("Normalise: %d", normalise)

        if normalise == 0: # do not normalise
            self.data = self.rawdata
        
        if normalise == 1: # same normalisation for all timeseries
            self.data = self.rawdata / np.max(self.rawdata)
        
        if normalise == 2: # normalise each timeseries alone. This is the default mode
            for i in range(self.m):
                self.scale[i] = np.max(np.abs(self.rawdata.iloc[:, i]))
                self.data[:, i] = self.rawdata.iloc[:, i] / self.scale[i]
    
    def split_data(self, traindate):
        train = len(self.rawdata[:traindate]) * 0.8
        valid = len(self.rawdata[:traindate]) * 0.2
        log.info("Splitting data into training set (%.2f), validation set (%.2f) and testing set (%.2f)", train, valid, 1 - (train + valid))
        train_set = range(self.w + self.h - 1, int(train))
        valid_set = range(int(train), int((train + valid)))
        test_set  = range(int((train + valid)), self.n)
        
        self.train = self.get_data(train_set)
        self.valid = self.get_data(valid_set)
        self.test  = self.get_data(test_set)
        
    def get_data(self, rng):
        n = len(rng)
        
        X = np.zeros((n, self.w, self.m))
        Y = np.zeros((n, self.m))
        
        for i in range(n):
            end   = rng[i] - self.h + 1
            start = end - self.w
            
            X[i,:,:] = self.data[start:end, :]
            Y[i,:]   = self.data[rng[i],:]
        
        return [X, Y]

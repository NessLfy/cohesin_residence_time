import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from scipy.optimize import curve_fit
from functools import partial


def opendata(path:str)->pd.DataFrame:
    """
    Open the data from the path and return the dataframe
    """
    df_raw = pd.read_csv(path+'/'+[x for x in os.listdir(path) if 'raw.csv' in x][0])
    df_interp = pd.read_csv(path+'/'+[x for x in os.listdir(path) if 'interp.csv' in x][0])
    df_interp.rename(columns={'Unnamed: 0':'time'},inplace=True)
    df_raw.rename(columns={'Unnamed: 0':'time'},inplace=True)
    df_interp.sort_values(by=['time'],inplace=True)
    df_raw.sort_values(by=['time'],inplace=True)
    return df_interp


def concat_runs(pattern:list, path:str = '/Users/louaness/Documents/cohesin_residence_time/runs/')->pd.DataFrame:
    """
    Concatenate all the runs from the path and return the dataframe

    Args:

    pattern: list
        List of strings to match the files

    path: str
        Path to the runs
    """
    df_wapl_d = []
    list_files = os.listdir(path)
    for l,i in enumerate(list_files):
        counter = 0
        for pat in pattern:
            if pat in i:
                counter +=1 
        if counter >=2:
            path_df = path+i
            try:
                df_interp_wapl = opendata(path_df)
                df_interp_wapl['nucleus'] = df_interp_wapl['nucleus'] + (10*l)
                df_interp_wapl['replicate'] = i
                df_wapl_d.append(df_interp_wapl)
            except:
                print(f'Error, the file {i} could not be opened, might not contain data or is not analized yet.')
                continue

    df_wapl_d = pd.concat(df_wapl_d)
    return df_wapl_d


def normalize_ifrap(df_wapl:pd.DataFrame)->None:
    """
    Normalize the iFRAP values of the dataframe

    Args:
    df_wapl: pd.DataFrame
        Dataframe with the iFRAP values
    !! This function modifies the dataframe inplace
    """
    counter = 0
    for n in df_wapl.nucleus.unique():
        counter +=1
        mean = df_wapl[(df_wapl.nucleus == n)&(df_wapl.time == 5)].interpolated_values_unbleached - df_wapl[(df_wapl.nucleus == n)&(df_wapl.time ==5)].interpolated_values_bleached  
        mean_r = df_wapl[(df_wapl.nucleus == n)&(df_wapl.time == 5)].unfrap_cell - df_wapl[(df_wapl.nucleus == n)&(df_wapl.time ==5)].interpolated_values_background
        C = mean/mean_r
        C = C.values[0]
        ifrap = np.abs((df_wapl[(df_wapl.nucleus == n)].interpolated_values_unbleached - df_wapl[(df_wapl.nucleus == n)].interpolated_values_bleached)/(df_wapl[(df_wapl.nucleus == n)].unfrap_cell - df_wapl[(df_wapl.nucleus == n)].interpolated_values_background))/np.abs(C)
        ifrap = ifrap.values
        df_wapl.loc[df_wapl['nucleus'] == n, 'iFRAP'] = ifrap


def compute_offset(df_wapl:pd.DataFrame)->None:
    """
    Compute the offset of the iFRAP values of the dataframe for the fitting. THe offset is the mean of the first 5 time points (pre-FRAP)

    Args:
    df_wapl: pd.DataFrame
        Dataframe with the iFRAP values
    
    return:
        The mean iFRAP of the first 5 time points
    """
    counter = 0
    for n in df_wapl.nucleus.unique():
        counter +=1
        mean = df_wapl[(df_wapl.nucleus == n)&(df_wapl.time < 5)].interpolated_values_unbleached - df_wapl[(df_wapl.nucleus == n)&(df_wapl.time <5)].interpolated_values_bleached  
        mean_r = df_wapl[(df_wapl.nucleus == n)&(df_wapl.time < 5)].unfrap_cell - df_wapl[(df_wapl.nucleus == n)&(df_wapl.time <5)].interpolated_values_background
        C = mean/mean_r
        C = C.values[0]
        return np.mean(np.abs(C))
    

def double_exp(t,a1,k1,k2,offset):
    return a1*np.exp(-k1*t) + (1-a1)*np.exp(-k2*t)+offset

def fit_df(df,offset) -> tuple:
    """
    Fit the dataframe with the iFRAP values to a double exponential function

    Args:
    df: pd.DataFrame
        Dataframe with the iFRAP values

    return:
    popt: tuple
        Optimal values for the parameters so that the sum of the squared residuals of f(xdata, *popt) - ydata is minimized
    pcov: 2D array
        The estimated covariance of popt. The diagonals provide the variance of the parameter estimate.
    sd: array
        The standard deviation of the parameters
    """
    x = df.time.unique()[5:]
    x = x*0.5
    y = df.iFRAP[5:] 
    partial_double_exp = partial(double_exp,offset=offset)

    popt,pcov = curve_fit(partial_double_exp, x, y,p0=[0.5,0.075,0.01],bounds=([0,0.05,0.001],[1,0.2,0.021]))

    sd = np.sqrt(np.diag(pcov))

    return popt,pcov,sd


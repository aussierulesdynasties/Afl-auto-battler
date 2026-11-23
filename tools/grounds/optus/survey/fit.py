import numpy as np,math,sys
from scipy.ndimage import median_filter
def combine(res,tol=1.0):
    th=2*np.pi*np.arange(res.shape[0])/res.shape[0]
    med=np.nanmedian(res,1)
    # running median over 2 deg for outlier rejection, iterate
    for it in range(3):
        good=~np.isnan(med);ref=np.interp(th,th[good],med[good],period=2*np.pi)
        ref=median_filter(ref,size=9,mode='wrap')
        r2=np.where(np.abs(res-ref[:,None])<tol,res,np.nan);med=np.nanmedian(r2,1)
    return th,med
def design(th,N):
    cols=[np.ones_like(th)]
    for n in range(1,N+1):cols+= [np.cos(n*th),np.sin(n*th)]
    return np.stack(cols,1)
def fit(th,r,N,w=None):
    g=~np.isnan(r);A=design(th[g],N);c,*_=np.linalg.lstsq(A,r[g],rcond=None);return c
def ev(c,th):return design(th,(len(c)-1)//2)@c

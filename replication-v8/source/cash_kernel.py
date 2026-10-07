"""Native acceleration of the identical cash recursion, with Python reference."""
from pathlib import Path
import ctypes,sys
import numpy as np
R=Path(__file__).resolve().parent
LIB=R/('cash.dylib' if sys.platform=='darwin' else 'cash.so')
if LIB.exists():
 library=ctypes.CDLL(str(LIB));function=library.cash_path
 arr=np.ctypeslib.ndpointer(dtype=np.float64,ndim=1,flags='C_CONTIGUOUS')
 function.argtypes=[ctypes.c_int,ctypes.c_int,ctypes.c_double,arr,arr,arr,arr,ctypes.c_double,arr,arr,arr,ctypes.c_double,arr,arr];function.restype=None
else:function=None
def path(initial,initial_grad,growth,years,short_factor,short_position,short_grad,flow,flow_grad,borrow=.005,native=True):
 arrays=[np.ascontiguousarray(x,dtype=np.float64).ravel() for x in [initial_grad,growth,years,short_factor,short_grad,flow,flow_grad]]
 ig,g,dt,sf,sg,f,fg=arrays;n=len(g);k=len(ig);assert len(dt)==n and len(sf)==n and len(f)==n and len(sg)==k and len(fg)==n*k
 cash=np.empty(n);grad=np.empty((n,k))
 if native and function is not None:function(n,k,float(initial),ig,g,dt,sf,float(short_position),sg,f,fg,float(borrow),cash,grad.ravel())
 else:
  cash[0]=initial;grad[0]=ig;ff=fg.reshape(n,k)
  for j in range(1,n):
   grow=g[j]*(1+borrow*dt[j] if cash[j-1]<0 else 1)
   cash[j]=cash[j-1]*grow+short_position*sf[j]+f[j]
   grad[j]=grad[j-1]*grow+sg*sf[j]+ff[j]
 return cash,grad

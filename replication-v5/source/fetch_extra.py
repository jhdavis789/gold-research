from pathlib import Path
import sys
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R.parent));import fetch_snapshot as f
f.DATA=R.parent/'data/v5_costs_20261004';f.SYMBOLS=['USO','FXA','FXC']
if __name__=='__main__':f.main()

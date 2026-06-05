import pandas as pd
from kite_auth import get_kite_session
import os

kite = get_kite_session()
instruments = kite.instruments("NFO")
df = pd.DataFrame(instruments)
df.to_csv("instruments_nfo.csv", index=False)
print("Saved NFO instruments to instruments_nfo.csv")

import streamlit as st
import pandas as pd
import numpy as np

# DataFrame の表示
st.markdown("## DataFrame での20列、50行の数値のランダム生成表示")
st.markdown("- 読み込むごとに数値をランダムに生成")
st.markdown("- 各列でのソートが可能")
df = pd.DataFrame(np.random.randn(50, 20), columns=("col %d" % i for i in range(20)))
st.dataframe(df)

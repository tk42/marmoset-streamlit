import io
import numpy as np
import pandas as pd
import streamlit as st
from numpy.lib.stride_tricks import sliding_window_view

FILE_DATA_INDEX_START = 1
FILE_DATA_INDEX_END = 14
ANALYSIS_DATA_INDEX_HEADER = 15
ANALYSIS_DATA_INDEX_START = 16


def calc_dist(df: pd.DataFrame):
    dx, dy, dz = map(np.diff, [df["Xcm"], df["Ycm"], df["Zcm"]])
    return np.sqrt(dx**2 + dy**2 + dz**2)


def draw_fig_cumsum(df: pd.DataFrame):
    d = calc_dist(df)

    df["cumsum"] = np.insert(d.cumsum(), 0, 0)
    df["datetime"] = pd.to_datetime(df["date time"], format="%Y-%m-%d %H:%M:%S.000")
    df.set_index("datetime", inplace=True)

    fig = df["cumsum"].plot(grid=True)
    return df["cumsum"], fig


def draw_fig_activities(df: pd.DataFrame, bins: int, sec: int):
    d = calc_dist(df)

    summed_within_secs = list(map(sum, sliding_window_view(d, sec)))

    histogram = pd.Series(summed_within_secs, name="Histogram").value_counts(bins=bins)
    fig = histogram.plot.bar(grid=True, tick_label=histogram.index)
    return histogram, fig


def format_header(header: io.BytesIO):
    formatted_header = {}
    for i, line in enumerate(header.getvalue().decode("cp932").split("\r\n")):
        d = line.split(",")
        if i == 9:
            formatted_header[d[0]] = ", ".join(d[1:])
        else:
            formatted_header[d[0]] = "".join(d[1:])
    del formatted_header["***** Analysis Data *****"]
    t = "\n".join([f"|{k}|{v}|" for k, v in formatted_header.items()])
    return f"|Key|Field|\n|:---|:---|\n{t}"


def format_dataframe(buffer: io.BytesIO):
    header = []
    data = []
    for i, line in enumerate(buffer.getvalue().decode("cp932").split("\r\n")):
        if i == 0:
            header = line.split(",")
        else:
            data += [line.split(",")]
    df = pd.DataFrame(
        data=data[:-2],
        columns=header,
    )
    return df.astype(
        {
            "Project No": "int",
            "Session No": "int",
            "date time": "string",
            "Xpx": "float",
            "Ypx": "float",
            "Xcm": "float",
            "Ycm": "float",
            "Zcm": "float",
            "AreaNo": "int",
        }
    )


def load_csv(uploaded_file: io.StringIO):
    header_bytes = io.BytesIO()
    df_bytes = io.BytesIO()
    for i, line in enumerate(uploaded_file):
        if FILE_DATA_INDEX_START <= i and i <= FILE_DATA_INDEX_END:
            header_bytes.write(line)
        elif ANALYSIS_DATA_INDEX_HEADER <= i:
            df_bytes.write(line)
    assert len(header_bytes.getvalue()) > 0, "No header data to parse"
    header = format_header(header_bytes)
    assert len(df_bytes.getvalue()) > 0, "No experiment data to parse"
    df = format_dataframe(df_bytes)
    return header, df


def main():
    st.set_page_config(page_icon="🐒", page_title="Marmoset Streamlit")

    st.image(
        "./marmoset.jpeg",
        width=300,
    )

    st.title("Marmoset Streamlit")

    st.write("This app shows the marmoset's acitivies! The cage size specification is as below.")

    st.markdown(
        """
         - a = 50.0 cm
         - X = 45.40 cm
         - Y = 53.92 cm
         - Z = 50.0 cm
        """
    )

    uploaded_file = st.file_uploader("Pick a CSV file", type=["csv"])

    if uploaded_file is not None:
        file_container = st.expander("Check your uploaded .csv")
        header_data, df = load_csv(uploaded_file)
        uploaded_file.seek(0)
        file_container.write(df)
        st.success("Loaded successful")

    else:
        st.info("👆 Upload a .csv file first.")
        st.stop()

    st.subheader("Experiment info.")
    st.markdown(header_data)

    st.subheader("Cumsumed trajectory")
    df_cumsum, fig = draw_fig_cumsum(df)
    file_container = st.expander("Check the table data")
    file_container.write(df_cumsum)
    st.plotly_chart(fig.figure)

    st.subheader("Activities histogram")
    bins = st.number_input("Pick a cluster number", min_value=2, max_value=50)
    sec = st.number_input("Pick an interval secs", min_value=1, max_value=300)
    df_hist, fig = draw_fig_activities(df, bins, sec)
    file_container = st.expander("Check the table data")
    file_container.write(df_hist)
    st.plotly_chart(fig.figure)


if __name__ == "__main__":
    main()

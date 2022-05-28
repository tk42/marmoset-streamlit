import io
import numpy as np
import streamlit as st
import pandas as pd

FILE_DATA_INDEX_START = 1
FILE_DATA_INDEX_END = 14
ANALYSIS_DATA_INDEX_HEADER = 15
ANALYSIS_DATA_INDEX_START = 16


def draw_fig_cumsum(st: st, df: pd.DataFrame):
    file_container = st.expander("Check the table data")
    dx, dy, dz = map(np.diff, [df["Xcm"], df["Ycm"], df["Zcm"]])
    d = np.sqrt(dx**2 + dy**2 + dz**2)

    df["cumsum"] = np.insert(d.cumsum(), 0, 0)
    df["datetime"] = pd.to_datetime(df["date time"], format="%Y-%m-%d %H:%M:%S.000")
    df.set_index("datetime", inplace=True)

    file_container.write(df["cumsum"])
    fig = df["cumsum"].plot(grid=True)
    st.plotly_chart(fig.figure)


def draw_fig_activities(st: st, df: pd.DataFrame, bins: int):
    file_container = st.expander("Check the table data")
    dx, dy, dz = map(np.diff, [df["Xcm"], df["Ycm"], df["Zcm"]])
    d = np.sqrt(dx**2 + dy**2 + dz**2)

    df["diff"] = np.insert(d, 0, 0)

    file_container.write(df["diff"])
    fig = df["diff"].plot.hist(bins=bins, grid=True)
    st.plotly_chart(fig.figure)


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

    st.write("This app shows your marmoset acitivies! The size specification is as below.")

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
    draw_fig_cumsum(st, df)

    st.subheader("Activities histogram")
    bins = st.slider("Pick a cluster number", 2, 50)
    draw_fig_activities(st, df, bins)


if __name__ == "__main__":
    main()

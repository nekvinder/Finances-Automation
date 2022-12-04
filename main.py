import pandas as pd
import copy
from makestatic import make_static
import datetime
import plotly.express as px  # to create interactive charts
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import dash
from dash import html, dcc, dash_table
from dash.dependencies import Input, Output
import os.path
import time

PERSONAL_EXPENSES_LIMIT = 10000

file = "data.csv"
last_modified_csv = "Last Modified: %s" % time.ctime(os.path.getmtime(file))
# df= pd.read_csv("Expense Record.csv")
df = pd.read_csv(file)
df["DATEP"] = pd.to_datetime(df.Date, format="%d/%m/%Y")
df.sort_values(by=["DATEP"], inplace=True, ascending=False)

# rename and Remap columns
df["Year"] = df.apply(lambda row: datetime.datetime.strptime(str(row.Date), "%d/%m/%Y").year, axis=1)
df["Month Name"] = df.apply(lambda row: datetime.datetime.strptime(str(row.Date), "%d/%m/%Y").strftime("%b"), axis=1)
df["YEAR_MONTH"] = df.apply(lambda row: datetime.datetime.strptime(str(row.Date), "%d/%m/%Y").strftime("01 %m %Y"), axis=1)
df["YEAR_MONTH_DATE"] = pd.to_datetime(df.YEAR_MONTH, format="%d %m %Y")
df["AMOUNT"] = df["Amount"]
df["CATEGORY"] = df["Category-Select"]
# print(df['CATEGORY'].unique())
df.fillna(0)

# Filter Data
df = df[df["Category-Select"] != "Internal Bank Transfer"]
df = df[df["Category-Select"] != "Office Expenses"]


def createMonthlyPersonalExpensesBars(title, data, filterFields=[]):
    dataFrame = copy.deepcopy(data)
    for field in filterFields:
        dataFrame = dataFrame[dataFrame["CATEGORY"] != field]
    monthlyTimeline = pd.pivot_table(dataFrame, values=["AMOUNT"], index=["YEAR_MONTH_DATE", "CATEGORY"], aggfunc=sum).reset_index()
    monthlyTimeline.columns = [x.upper() for x in monthlyTimeline.columns]
    monthlyTimelineChart = px.bar(monthlyTimeline, x="YEAR_MONTH_DATE", y="AMOUNT", title=title, color="CATEGORY", barmode="group")
    monthlyTimelineChart.add_hline(y=PERSONAL_EXPENSES_LIMIT)
    monthlyTimelineChart.add_trace(
        go.Scatter(
            x=[datetime.date.today()], y=[PERSONAL_EXPENSES_LIMIT], mode="markers+text", name="Markers and Text", text=["Personal Expenses limit"], textposition="bottom center"
        )
    )
    monthlyTimelineChart.update_yaxes(title="Expenses (R)", visible=True, showticklabels=True)
    monthlyTimelineChart.update_xaxes(title="Date", visible=True, showticklabels=True)
    return monthlyTimelineChart


def createMonthlyTimeline(dataFrame):
    monthlyTimeline = pd.pivot_table(dataFrame, values=["AMOUNT"], index=["DATEP", "CATEGORY"], aggfunc=sum).reset_index()
    monthlyTimeline.columns = [x.upper() for x in monthlyTimeline.columns]
    monthlyTimelineChart = px.line(monthlyTimeline, x="DATEP", y="AMOUNT", title="Monthly Timeline", color="CATEGORY", markers=True)
    monthlyTimelineChart.update_yaxes(title="Expenses (R)", visible=True, showticklabels=True)
    monthlyTimelineChart.update_xaxes(title="Date", visible=True, showticklabels=True)
    return monthlyTimelineChart


def createNonInvestmentsTimeline(data):
    dataFrame = data[data["Category-Select"] != "Long Term Investments"]
    dataFrame = dataFrame[data["Category-Select"] != "Emergency Fund"]
    monthlyTimeline = pd.pivot_table(dataFrame, values=["AMOUNT"], index=["DATEP", "CATEGORY"], aggfunc=sum).reset_index()
    monthlyTimeline.columns = [x.upper() for x in monthlyTimeline.columns]
    monthlyTimelineChart = px.line(monthlyTimeline, x="DATEP", y="AMOUNT", title="Expenses Timeline", color="CATEGORY", markers=True)
    monthlyTimelineChart.update_yaxes(title="Expenses (R)", visible=True, showticklabels=True)
    monthlyTimelineChart.update_xaxes(title="Date", visible=True, showticklabels=True)
    return monthlyTimelineChart


def createPocketMoneyVSPersonalExpensesPie(data):
    dataFrame = data[(data["Category-Select"] == "Monthly Pocket Money") | (data["Category-Select"] == "Personal Expenses")]
    dataFrame = pd.pivot_table(dataFrame, values=["AMOUNT"], index=["CATEGORY"], aggfunc=sum).reset_index()
    fig = px.pie(
        dataFrame,
        values="AMOUNT",
        names="CATEGORY",
        title="Blind VS Documented Personal Expense - Reduce Monthly Pocket Money",
    )
    fig.update_traces(textinfo="text+value+percent")
    return fig


def createIncomeDistributionPie(data):
    dataFrame = pd.pivot_table(data, values=["AMOUNT"], index=["CATEGORY"], aggfunc=sum).reset_index()
    fig = px.pie(dataFrame, values="AMOUNT", names="CATEGORY", title="Income distribution")
    fig.update_traces(textinfo="text+value+percent")
    return fig


def getDataTable(data):
    newData = copy.deepcopy(data)
    print(newData.columns)
    keepCols = ["Name", "Date", "Category-Select", "Amount"]
    deleteCols = [x for x in newData.columns.tolist() if x not in keepCols]
    for col in deleteCols:
        pass
        newData.drop(col, inplace=True, axis=1)
    values = [newData[k].tolist() for k in newData.columns]
    fig = make_subplots(rows=1, cols=1, shared_xaxes=True, vertical_spacing=0.03, specs=[[{"type": "table"}]])
    fig.add_trace(
        go.Table(
            header=dict(values=["Date", "Category", "Amount"], font=dict(size=10), align="left"),
            cells=dict(values=values, align="left"),
        ),
        row=1,
        col=1,
    )
    return fig


def getHtmlDiv(imgFunction, fullWidth=True):
    if fullWidth:
        style = {"width": "100%", "display": "inline-block"}
    else:
        style = {"padding": 10, "flex": 2}
    return html.Div(
        children=[
            html.Div(
                children=dcc.Graph(
                    id="barscene",
                    figure=imgFunction,
                ),
            ),
        ],
        className="double-graph",
        style=style,
    )


def startDashApp():
    app = dash.Dash(__name__)
    app.layout = html.Div(
        children=[
            html.Div(
                children=[html.H2(children=last_modified_csv, className="header-description", style={"textAlign": "center"})],
                className="header",
                style={"backgroundColor": "#F5F5F5"},
            ),
            html.Div(
                children=[getHtmlDiv(createIncomeDistributionPie(df), False), getHtmlDiv(createPocketMoneyVSPersonalExpensesPie(df), False)],
                style={"display": "flex", "flex-direction": "row"},
            ),
            getHtmlDiv(createMonthlyPersonalExpensesBars("Keep check on the following", df, ["Trips And Lux", "Mom", "Emergency Fund", "Long Term Investments"])),
            getHtmlDiv(createMonthlyPersonalExpensesBars("Income distribution", df)),
            # getHtmlDiv(createNonInvestmentsTimeline(df)),
            # getHtmlDiv(createMonthlyTimeline(df)),
            getHtmlDiv(getDataTable(df)),
        ]
    )
    app.run_server(debug=True, threaded=True)


def emitDashImages():
    imageFunctions = [
        createIncomeDistributionPie,
        createMonthlyTimeline,
        createNonInvestmentsTimeline,
        createPocketMoneyVSPersonalExpensesPie,
    ]
    for imgFn in imageFunctions:
        imgFn(df).write_image("images/" + imgFn.__name__ + ".png")
    pass


if __name__ == "__main__":
    startDashApp()
    # emitDashImages()

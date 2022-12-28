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

ideal_income_distribution = {"Long Term Investments": 0.6, "Emergency Fund": 0.05}
PERSONAL_EXPENSES_LIMIT = 10000


class GetExpenses:
    @staticmethod
    def getData():
        file = "expenses.csv"
        last_modified_csv = "Last Modified: %s" % time.ctime(os.path.getmtime(file))
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
        df.fillna(0)

        # Filter Data
        df = df[df["Category-Select"] != "Internal Bank Transfer"]
        df = df[df["Category-Select"] != "Office Expenses"]
        return last_modified_csv, df


class GenerateDash:
    @staticmethod
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

    @staticmethod
    def createMonthlyTimeline(data):
        dataFrame = copy.deepcopy(data)
        monthlyTimeline = pd.pivot_table(dataFrame, values=["AMOUNT"], index=["DATEP", "CATEGORY"], aggfunc=sum).reset_index()
        monthlyTimeline.columns = [x.upper() for x in monthlyTimeline.columns]
        monthlyTimelineChart = px.line(monthlyTimeline, x="DATEP", y="AMOUNT", title="Monthly Timeline", color="CATEGORY", markers=True)
        monthlyTimelineChart.update_yaxes(title="Expenses (R)", visible=True, showticklabels=True)
        monthlyTimelineChart.update_xaxes(title="Date", visible=True, showticklabels=True)
        return monthlyTimelineChart

    @staticmethod
    def createGuidelinesText(data):
        dataFrame = copy.deepcopy(data)

        dataFrame = pd.pivot_table(dataFrame, values=["AMOUNT"], index=["CATEGORY"], aggfunc=sum).reset_index()
        total_expenses = dataFrame["AMOUNT"].sum()
        dataFrame["amount_percentage"] = dataFrame["AMOUNT"] / total_expenses
        print(dataFrame)
        text = ""
        for category, ideal_currentCategory_percentage in ideal_income_distribution.items():
            ideal_other_percentage = 1 - ideal_currentCategory_percentage
            current_amount = dataFrame[dataFrame["CATEGORY"] == category]["AMOUNT"].values[0]
            current_percentage = float(dataFrame[dataFrame["CATEGORY"] == category]["amount_percentage"].values[0])
            other_amount = total_expenses - current_amount
            falling_percentage = ideal_currentCategory_percentage - current_percentage
            if falling_percentage > 0:
                print("current_percentage", current_percentage)
                print("falling_percentage", falling_percentage)
                print("total_expenses", total_expenses)
                # text += f'{category} should be {percentage * 100}% of your expenses. Currently it is falling by {falling_percentage * 100}%\n'
                rounded_remaining_amount = round(((ideal_currentCategory_percentage * other_amount) / ideal_other_percentage) - current_amount)
                text += f"You should add {rounded_remaining_amount} to { category }\n"

        print(text)

        return text

    @staticmethod
    def getMonthlyPassiveIncome(data):
        dataFrame = copy.deepcopy(data)
        dataFrame = pd.pivot_table(dataFrame, values=["AMOUNT"], index=["CATEGORY"], aggfunc=sum).reset_index()
        invested_amount = dataFrame[dataFrame["CATEGORY"] == "Long Term Investments"]["AMOUNT"].values[0]
        yearly_income = invested_amount * 0.07
        monthly_income = round(yearly_income / 12, -1)
        return f" current monthly income is {monthly_income}\n"

    @staticmethod
    def createNonInvestmentsTimeline(data):
        dataFrame = copy.deepcopy(data)
        dataFrame = dataFrame[dataFrame["Category-Select"] != "Long Term Investments"]
        dataFrame = dataFrame[dataFrame["Category-Select"] != "Emergency Fund"]
        monthlyTimeline = pd.pivot_table(dataFrame, values=["AMOUNT"], index=["DATEP", "CATEGORY"], aggfunc=sum).reset_index()
        monthlyTimeline.columns = [x.upper() for x in monthlyTimeline.columns]
        monthlyTimelineChart = px.line(monthlyTimeline, x="DATEP", y="AMOUNT", title="Expenses Timeline", color="CATEGORY", markers=True)
        monthlyTimelineChart.update_yaxes(title="Expenses (R)", visible=True, showticklabels=True)
        monthlyTimelineChart.update_xaxes(title="Date", visible=True, showticklabels=True)
        return monthlyTimelineChart

    @staticmethod
    def createLTInvestmentsPie(data):
        dataFrame = copy.deepcopy(data)
        dataFrame = dataFrame[(dataFrame["CATEGORY"] == "Long Term Investments")]
        pvtTable = pd.pivot_table(dataFrame, values=["AMOUNT"], index=["Name"], aggfunc=sum).reset_index()
        fig = px.pie(
            pvtTable,
            values="AMOUNT",
            names="Name",
            title="Longterm Investments distribution - " + GenerateDash.getMonthlyPassiveIncome(data),
        )
        fig.update_traces(textinfo="text+value+percent")
        return fig

    @staticmethod
    def createPocketMoneyVSPersonalExpensesPie(data):
        dataFrame = copy.deepcopy(data)
        dataFrame = dataFrame[(dataFrame["Category-Select"] == "Monthly Pocket Money") | (data["Category-Select"] == "Personal Expenses")]
        dataFrame = pd.pivot_table(dataFrame, values=["AMOUNT"], index=["CATEGORY"], aggfunc=sum).reset_index()
        fig = px.pie(
            dataFrame,
            values="AMOUNT",
            names="CATEGORY",
            title="Blind VS Documented Personal Expense - Reduce Monthly Pocket Money",
        )
        fig.update_traces(textinfo="text+value+percent")
        return fig

    @staticmethod
    def createIncomeDistributionPie(data):
        dataFrame = copy.deepcopy(data)
        dataFrame = pd.pivot_table(dataFrame, values=["AMOUNT"], index=["CATEGORY"], aggfunc=sum).reset_index()
        fig = px.pie(dataFrame, values="AMOUNT", names="CATEGORY", title="Income distribution")
        fig.update_traces(textinfo="text+value+percent")
        return fig

    @staticmethod
    def getDataTable(data):
        newData = copy.deepcopy(data)
        print("columns list : " + str(list(newData.columns)))
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

    @staticmethod
    def getHtmlDiv(imgFunction, fullWidth=True):
        if fullWidth:
            style = {"width": "100%", "display": "inline-block"}
        else:
            style = {"padding": 10, "flex": 2}
        return html.Div(  # type: ignore
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

    def startDashApp(self):
        df = self.df
        app = dash.Dash(__name__)  # type: ignore
        guidelines = self.createGuidelinesText(df)
        app.layout = html.Div(
            children=[
                html.Div(
                    children=[html.H2(children=self.last_modified_csv, className="header-description", style={"textAlign": "center"})],
                    className="header",
                    style={"backgroundColor": "#F5F5F5"},
                ),
                html.Div(
                    children=[
                        html.H3(children=f"Pending tasks", className="header-description", style={"textAlign": "center"}),
                        html.P(children=guidelines.split("\n"), className="header-description", style={"textAlign": "center"}),
                    ],
                    className="header",
                    style={"backgroundColor": "#F5F5F5"},
                ),
                html.Div(
                    children=[self.getHtmlDiv(self.createIncomeDistributionPie(df), False), self.getHtmlDiv(self.createPocketMoneyVSPersonalExpensesPie(df), False)],
                    style={"display": "flex", "flex-direction": "row"},
                ),
                self.getHtmlDiv(self.createLTInvestmentsPie(df), False),
                self.getHtmlDiv(self.createMonthlyPersonalExpensesBars("Keep check on the following", df, ["Trips And Lux", "Mom", "Emergency Fund", "Long Term Investments"])),
                self.getHtmlDiv(self.createMonthlyPersonalExpensesBars("Income distribution", df)),
                # getHtmlDiv(createNonInvestmentsTimeline(df)),
                # getHtmlDiv(createMonthlyTimeline(df)),
                self.getHtmlDiv(self.getDataTable(df)),
            ]
        )
        app.run_server(debug=True, threaded=True)

    def emitDashImages(self):
        imageFunctions = [
            self.createIncomeDistributionPie,
            self.createMonthlyTimeline,
            self.createNonInvestmentsTimeline,
            self.createPocketMoneyVSPersonalExpensesPie,
        ]
        for imgFn in imageFunctions:
            imgFn(self.df).write_image("images/" + imgFn.__name__ + ".png")

    def __init__(self):
        self.last_modified_csv, self.df = GetExpenses().getData()


if __name__ == "__main__":
    genDash = GenerateDash()
    genDash.startDashApp()
    # emitDashImages()

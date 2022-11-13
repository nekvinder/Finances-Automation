import pandas as pd
from makestatic import make_static 
import datetime
import plotly.express as px               #to create interactive charts
import plotly.graph_objects as go
import dash
from dash import html,dcc
from dash.dependencies import Input, Output
import os.path, time

file = "data.csv"
last_modified_csv = "Last Modified: %s" % time.ctime(os.path.getmtime(file))
# df= pd.read_csv("Expense Record.csv")
df= pd.read_csv(file)
df["DATEP"] = pd.to_datetime(df.Date,format='%d/%m/%Y')

# rename and Remap columns
df['Year'] = df.apply(lambda row: datetime.datetime.strptime(str(row.Date), "%d/%m/%Y").year , axis = 1)
df['Month Name'] = df.apply(lambda row: datetime.datetime.strptime(str(row.Date), "%d/%m/%Y").strftime("%b") , axis = 1)
df['YEAR_MONTH'] = df.apply(lambda row: datetime.datetime.strptime(str(row.Date), "%d/%m/%Y").strftime("%b %Y") , axis = 1)
df['AMOUNT'] = df['Amount']
df['CATEGORY'] = df['Category-Select']
# print(df['CATEGORY'].unique())
df.fillna(0)

# Filter Data
df= df[df["Category-Select"] != "Internal Bank Transfer"]
df= df[df["Category-Select"] != "Office Expenses"]

def createMonthlyTimeline(dataFrame):
    monthlyTimeline = pd.pivot_table(dataFrame, values = ['AMOUNT'], index = [ 'DATEP','CATEGORY'], aggfunc=sum).reset_index()
    monthlyTimeline.columns = [x.upper() for x in monthlyTimeline.columns]
    monthlyTimelineChart = px.line(monthlyTimeline, x='DATEP', y="AMOUNT", title="Monthly Timeline", color = 'CATEGORY', markers=True)
    monthlyTimelineChart.update_yaxes(title='Expenses (R)', visible=True, showticklabels=True)
    monthlyTimelineChart.update_xaxes(title='Date', visible=True, showticklabels=True)
    return monthlyTimelineChart
    # monthlyTimelineChart.show()

def createNonInvestmentsTimeline(data):
    dataFrame = data[data["Category-Select"] != "Long Term Investments"]
    dataFrame = dataFrame[data["Category-Select"] != "Emergency Fund"]
    monthlyTimeline = pd.pivot_table(dataFrame, values = ['AMOUNT'], index = [ 'DATEP','CATEGORY'], aggfunc=sum).reset_index()
    monthlyTimeline.columns = [x.upper() for x in monthlyTimeline.columns]
    monthlyTimelineChart = px.line(monthlyTimeline, x='DATEP', y="AMOUNT", title="Expenses Timeline", color = 'CATEGORY', markers=True)
    monthlyTimelineChart.update_yaxes(title='Expenses (R)', visible=True, showticklabels=True)
    monthlyTimelineChart.update_xaxes(title='Date', visible=True, showticklabels=True)
    return monthlyTimelineChart

def createPocketMoneyVSPersonalExpensesPie(data):
    dataFrame = data[(data["Category-Select"] == "Monthly Pocket Money") | (data["Category-Select"] == "Personal Expenses")]
    dataFrame = pd.pivot_table(dataFrame, values = ['AMOUNT'], index = ['CATEGORY'], aggfunc=sum).reset_index()
    fig = px.pie(dataFrame, values='AMOUNT', names='CATEGORY', title='Blind VS Documented Personal Expense - Reduce Monthly Pocket Money')
    fig.update_traces(textinfo = "text+value+percent")
    return fig

def createIncomeDistributionPie(data):
    dataFrame = pd.pivot_table(data, values = ['AMOUNT'], index = ['CATEGORY'], aggfunc=sum).reset_index()
    fig = px.pie(dataFrame, values='AMOUNT', names='CATEGORY', title='Income distribution')
    fig.update_traces(textinfo = "text+value+percent")
    return fig

def startDashApp():
    app = dash.Dash(__name__)
    app.layout = html.Div(
        children=[
            html.Div(
                children=[
                    html.H1(
                        children="Expenses distribution",style={'textAlign': 'center'}, className="header-title" 
                    ), #Header title
                    html.H2(
                        children=last_modified_csv,
                        className="header-description", style={'textAlign': 'center'},
                    ),
                ],
                className="header",style={'backgroundColor':'#F5F5F5'},
            ), #Description below the header
            # html.Div(
            #     children=[
            #         html.Div(children = 'Year', style={'fontSize': "24px"},className = 'menu-title'),
            #         dcc.Dropdown(
            #             id = 'year-filter',
            #             options = [
            #                 {'label': Year, 'value':Year}
            #                 for Year in offence_district.Year.unique()
            #             ], #'Year' is the filter
            #             value ='2010',
            #             clearable = False,
            #             searchable = False,
            #             className = 'dropdown', style={'fontSize': "24px",'textAlign': 'center'},
            #         ),
            #     ],
            #     className = 'menu',
            # ), #the dropdown function
            
            html.Div(
                children=[
                    html.Div(
                        children=[
                            html.Div(
                            children = dcc.Graph(
                                id = 'barscene',
                                figure = createIncomeDistributionPie(df),
                                #config={"displayModeBar": False},
                            ),
                            style={'width': '100%', 'display': 'inline-block'},
                            ),
                        ],
                    className = 'double-graph',
                    style={'padding': 10, 'flex': 2}
                    ), 
                    html.Div(
                        children=[
                            html.Div(
                            children = dcc.Graph(
                                id = 'barscene',
                                figure = createPocketMoneyVSPersonalExpensesPie(df),
                                #config={"displayModeBar": False},
                            ),
                            style={'width': '100%', 'display': 'inline-block'},
                            ),
                        ],
                    className = 'double-graph',
                    style={'padding': 10, 'flex': 2}
                    ),
                ],style={'display': 'flex', 'flex-direction': 'row'}
            ),
            html.Div(
                children=[
                    html.Div(
                    children = dcc.Graph(
                        id = 'barscene',
                        figure = createNonInvestmentsTimeline(df),
                        #config={"displayModeBar": False},
                    ),
                    style={'width': '100%', 'display': 'inline-block'},
                    ),
                ],
            className = 'double-graph',
            ), 
            html.Div(
                children=[
                    html.Div(
                    children = dcc.Graph(
                        id = 'barscene',
                        figure = createMonthlyTimeline(df),
                        #config={"displayModeBar": False},
                    ),
                    style={'width': '100%', 'display': 'inline-block'},
                ),
            ],
            className = 'double-graph',
            ), 
        ]
    )
    app.run_server(debug=True, threaded=True)

def emitDashImages():
    imageFunctions = [createIncomeDistributionPie,createMonthlyTimeline,createNonInvestmentsTimeline,createPocketMoneyVSPersonalExpensesPie]
    for imgFn in imageFunctions:
        imgFn(df).write_image('images/' + imgFn.__name__ + '.png')
    pass

if __name__ == '__main__':
    # startDashApp()
    emitDashImages()

import dash
from dash import dcc, html
import plotly.graph_objs as go
import pandas as pd
from datetime import datetime
from pymongo import MongoClient
import dash_bootstrap_components as dbc
import dash_auth

# MongoDB connection details
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["smartdustbin"]
collection = db["sensor_data"]

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Define the username and password pairs
VALID_USERNAME_PASSWORD_PAIRS = {
    'your_username': 'your_password',
    'friend_username': 'friend_password'
}

# Add authentication to the app
auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS
)

def get_data():
    cursor = collection.find().sort([("timestamp", -1)])
    data = list(cursor)
    return data

def prepare_daily_waste_data(data):
    try:
        # Convert data to pandas DataFrame
        df = pd.DataFrame(data)
        
        # Convert timestamp strings to datetime objects
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Filter for January 2025
        df = df[
            (df['timestamp'].dt.year == 2025) & 
            (df['timestamp'].dt.month == 1)
        ]
        
        # Extract date from timestamp
        df['date'] = df['timestamp'].dt.date
        
        # Count daily occurrences of each waste type
        daily_counts = df.groupby(['date', 'waste_type']).size().unstack(fill_value=0)
        
        # Ensure both waste types are present
        if 'Wet Waste' not in daily_counts.columns:
            daily_counts['Wet Waste'] = 0
        if 'Dry Waste' not in daily_counts.columns:
            daily_counts['Dry Waste'] = 0
        
    
        return daily_counts
    except Exception as e:
        print(f"Error in prepare_daily_waste_data: {str(e)}")  # Debugging print
        return pd.DataFrame()

app.layout = html.Div([
    dbc.Container([
        # Header
        html.H1("Smart Dustbin Dashboard", className="text-center my-4"),

        # Display the most recent data entry
        html.Div(id="latest-data", style={"marginBottom": "20px"}),

        # Status boxes for dry bin, wet bin, and water level
        dbc.Row([
            dbc.Col(html.Div(id="dry-bin-status", className="status-box"), width=4),
            dbc.Col(html.Div(id="wet-bin-status", className="status-box"), width=4),
            dbc.Col(html.Div(id="water-level-status", className="status-box"), width=4)
        ], className="text-center"),

        # Daily Waste Frequency Chart
        html.Div([
            html.H3("January 2025 Waste Collection Frequency", className="text-center my-4"),
            dcc.Graph(id='daily-waste-chart')
        ], style={"marginTop": "30px"}),

        # Recent Data Table
        html.Div([
            html.H3("Recent Data", className="text-center my-4"),
            html.Div(id="data-table")
        ], style={"marginTop": "30px"})
    ])
])

@app.callback(
    [dash.dependencies.Output("latest-data", "children"),
     dash.dependencies.Output("dry-bin-status", "children"),
     dash.dependencies.Output("dry-bin-status", "style"),
     dash.dependencies.Output("wet-bin-status", "children"),
     dash.dependencies.Output("wet-bin-status", "style"),
     dash.dependencies.Output("water-level-status", "children"),
     dash.dependencies.Output("water-level-status", "style"),
     dash.dependencies.Output("data-table", "children"),
     dash.dependencies.Output("daily-waste-chart", "figure")],
    [dash.dependencies.Input("interval-component", "n_intervals")]
)
def update_dashboard(n):
    try:
        data = get_data()
        #print(f"Number of records retrieved: {len(data)}")  # Debugging print
        
        # Extract the latest data point
        latest_data = data[0] if data else {}
        
        # Display the latest data entry
        if latest_data:
            latest_data_text = f"Timestamp: {latest_data.get('timestamp', 'N/A')} - Waste Type: {latest_data.get('waste_type', 'N/A')} - Waste Level: {latest_data.get('waste_level', 'N/A')} - Water Level: {latest_data.get('water_level', 'N/A')}"
        else:
            latest_data_text = "No data available."

        # Initialize status variables
        dry_bin_status = "N/A"
        wet_bin_status = "N/A"
        water_level_status = "N/A"

        # Find the most recent status for each bin type
        for entry in data:
            if entry.get('waste_type') == "Dry Waste" and dry_bin_status == "N/A":
                dry_bin_status = entry.get('waste_level', 'N/A')
            elif entry.get('waste_type') == "Wet Waste":
                if wet_bin_status == "N/A":
                    wet_bin_status = entry.get('waste_level', 'N/A')
                if water_level_status == "N/A":
                    water_level_status = entry.get('water_level', 'N/A')
            
            if dry_bin_status != "N/A" and wet_bin_status != "N/A" and water_level_status != "N/A":
                break

        # Set colors based on status
        dry_bin_color = "red" if dry_bin_status == "Full" else "green" if dry_bin_status != "N/A" else "gray"
        wet_bin_color = "red" if wet_bin_status == "Full" else "green" if wet_bin_status != "N/A" else "gray"
        water_level_color = "red" if water_level_status == "Full" else "green" if water_level_status != "N/A" else "gray"

        # Create status box styles
        status_box_style = lambda color: {
            "backgroundColor": color,
            "color": "white",
            "padding": "10px",
            "margin": "5px"
        }

        # Create table
        if data:
            table = dbc.Table(
                [
                    html.Thead(
                        html.Tr([
                            html.Th("Timestamp"),
                            html.Th("Waste Type"),
                            html.Th("Waste Level"),
                            html.Th("Water Level")
                        ])
                    ),
                    html.Tbody([
                        html.Tr([
                            html.Td(entry['timestamp']),
                            html.Td(entry['waste_type']),
                            html.Td(entry['waste_level']),
                            html.Td(entry.get('water_level', 'N/A'))
                        ]) for entry in data[:10]
                    ])
                ],
                bordered=True,
                hover=True,
                striped=True
            )
        else:
            table = html.Div("No data available", className="text-center mt-3")

        # Prepare data for the bar chart
        daily_counts = prepare_daily_waste_data(data)
        
        # Create bar chart
        bar_chart = {
            'data': [
                go.Bar(
                    name='Dry Waste',
                    x=daily_counts.index.astype(str),
                    y=daily_counts['Dry Waste'],
                    marker_color='#f1c232'
                ),
                go.Bar(
                    name='Wet Waste',
                    x=daily_counts.index.astype(str),
                    y=daily_counts['Wet Waste'],
                    marker_color='#e69138'
                )
            ],
            'layout': go.Layout(
                barmode='group',
                title='Daily Waste Collection Frequency - January 2025',
                xaxis={
                    'title': 'Date',
                    'tickformat': '%Y-%m-%d'
                },
                yaxis={
                    'title': 'Number of Collections',
                    'dtick': 5,  # Set interval to 5
                    'range': [0, max(max(daily_counts['Dry Waste']), max(daily_counts['Wet Waste'])) + 5]  # Adjust range to next multiple of 5
                },
                legend={'orientation': 'h', 'y': -0.2},
                height=400,
                margin={'t': 40, 'b': 40, 'l': 40, 'r': 40}
            )
        }

        return (
            latest_data_text,
            f"Dry Bin [{dry_bin_status}]",
            status_box_style(dry_bin_color),
            f"Wet Bin [{wet_bin_status}]",
            status_box_style(wet_bin_color),
            f"Waste Bin Water Level [{water_level_status}]",
            status_box_style(water_level_color),
            table,
            bar_chart
        )
    except Exception as e:
        print(f"Error in update_dashboard: {str(e)}")  # Debugging print
        raise

# Add interval component for real-time updates
app.layout.children.append(dcc.Interval(
    id='interval-component',
    interval=10*1000,  # updates every 10 seconds
    n_intervals=0
))


app.run_server(debug=True, host='127.0.1', port=8050)

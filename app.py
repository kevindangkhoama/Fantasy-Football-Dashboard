# %%
# Import Libraries
from espn_api.basketball import League
import pandas as pd
import dash
from dash import dcc, html, dash_table, State
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px

# %%
def refresh():
    # These variables are required for private leagues
    # If league is public, these parameters are not required
    espn_s2 = f"AEBxlh0p0NHPbu6WIY0O0TNX6B7oQkhT1bCnR12c5SvsUf5Dnap49bkneUfyt9h1Y5m1MBalds2N47X5i%2FE6YhYUJDbxumf3HrW1iFK%2BPWOGnTpl%2F0wbLLy7C19hr50jNoma59zfYY5iOKxOvK6yT9cn689C4OoQ%2BTiVm%2FG7TjfaGLFIKIJ8OkuSJBye7xYCgnLh%2BvD5Fbbwgz8pLX6htmu%2BEyilZCOrqQ81zDXUrRQgWhIOOXEx1Uy5d1SOQOPkdfqV%2F6Nsr2jUTvgr2T%2FS9yxs"
    swid = "{5C675DD8-073A-4E00-AD7A-B926A3F2800B}"

    # Create a league object
    league = League(league_id=1267411756, year=2024, espn_s2=espn_s2, swid=swid)
    
    # Select a team to analyze
    team_id = 2

    # Create a list to store the data
    data = []
    lineup_points_breakdown = []
    id = 1

    # Iterate over weeks 1 to 20
    for week in range(1, 21):
        # Assign the box_score variable
        box_scores = league.box_scores(matchup_period=week)
        
        # Iterate through the box_scores list
        for box in box_scores:
            # If the team you are analyizing is the home team, record information regarding team score, name and lineup
            if box.home_team.team_id == team_id:
                team_score = box.home_score
                lineup = box.home_lineup
                team_name = box.home_team.team_name
                # Append the team's weekly data to the list
                data.append({
                    'Week': week,
                    'Team Name': team_name,
                    'Team Score': team_score,
                    'Lineup': lineup,
                })

                # Extracting points breakdown for each player in the lineup
                for player in lineup:
                    player_name = player.name
                    player_id = player.playerId
                    player_points_breakdown = player.points_breakdown
                    lineup_points_breakdown.append({
                        'Unique ID': id,
                        'Week': week,
                        'Player': player_name,
                        'Player ID': player_id,
                        'Points Breakdown': player_points_breakdown
                    })
                    id += 1
                    
            # If the team you are analyzing is the away team, record information regarding team score, name and lineup
            elif box.away_team.team_id == team_id:
                team_score = box.away_score
                lineup = box.away_lineup
                team_name = box.away_team.team_name
                
                # Append the team's weekly data to the list
                data.append({
                    'Week': week,
                    'Team Name': team_name,
                    'Team Score': team_score,
                    'Lineup': lineup,
                })
            
                # Extracting points breakdown for each player in the lineup
                for player in lineup:
                    player_name = player.name
                    playr_id = player.playerId
                    player_points_breakdown = player.points_breakdown
                    lineup_points_breakdown.append({
                        'Unique ID': id,
                        'Week': week,
                        'Player': player_name,
                        'Player ID': playr_id,
                        'Points Breakdown': player_points_breakdown
                    })
                    id += 1
            
        # Print the scores for the specified team to ensure that you are analyzing the correct team and are accessing the correct data
        # print(f"Week {week}: {team_name} scored {team_score} points with lineup {lineup}")

    # Create a pandas dataframe from the data list
    df_player = pd.DataFrame(data)
    points_breakdown = pd.DataFrame(lineup_points_breakdown)

    # We use the explode function to separate the lineup column into individual rows by the comma to split the players
    df_player = df_player.explode('Lineup')

    # Add an ID column to the dataframe
    df_player['Unique ID'] = range(1, len(df_player) + 1)

    # Convert the lineup column to a string to split the column into two columns
    df_player['Lineup'] = df_player['Lineup'].astype(str)

    # Split the lineup column into two columns: Player and Points
    df_player[['Player', 'Fantasy Points']] = df_player['Lineup'].str.split(', ', expand=True)

    # Remove the 'Player(' and ')' from the Player column
    df_player['Player'] = df_player['Player'].str.replace(r'Player\(', '', regex=True).astype(str)

    # Remove the 'points(' and ')' from the Points column
    df_player['Fantasy Points'] = df_player['Fantasy Points'].str.replace(r'.*points:([\d.]+)\)', r'\1', regex=True).astype(float)

    # Create a new column for the weekly contribution percentage
    df_player['Weekly Contribution Percentage'] = round(df_player['Fantasy Points'] / df_player['Team Score'] * 100, 2)

    # Drop the original Lineup, Team Name and Team Score columns
    df_player.drop(columns=['Lineup', 'Team Name', 'Team Score'], inplace=True)
                
    # Work for Second DF
    # Define a function to extract each key's value from the dictionary
    def extract_stat(stat_dict, stat):
        return stat_dict.get(stat, 0)  # If the stat is not present, default to 0

    # Extracting all unique stats
    unique_stats = set(stat for stat_dict in points_breakdown['Points Breakdown'] for stat in stat_dict.keys())

    # Creating new columns for each stat
    for stat in unique_stats:
        points_breakdown[stat] = points_breakdown['Points Breakdown'].apply(lambda x: extract_stat(x, stat))
        
    # Drop the 'points_breakdown' column
    points_breakdown.drop(columns=['Points Breakdown'], inplace=True)
    
    # Merge two dataframes based on ID
    cleaned_df = points_breakdown.merge(df_player, how='left', on='Unique ID')

    # Drop the Week_y and Player_y columns
    cleaned_df.drop(columns=['Week_y', 'Player_y'], inplace=True)
    cleaned_df.rename(columns={'Week_x': 'Week', 'Player_x': 'Player'}, inplace=True)

    # Change the data types of the columns to category
    cleaned_df['Week'] = cleaned_df['Week'].astype('str')
    cleaned_df['Player'] = cleaned_df['Player'].astype('category')

    # Check to see if merge was successful
    # print(cleaned_df.shape)
    
    team_name = f"{team_name}"
    return cleaned_df, team_name

# %%
# Call function to get api data and team name
cleaned_df, team_name = refresh()

# %%
# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SANDSTONE])
server = app.server
# Define app layout
app.layout = html.Div([
    dbc.NavbarSimple(
        children=[
            # nav bar redirect and refresh button
            dbc.NavItem(dbc.NavLink("About", href="/About")),
            dbc.NavItem(dbc.NavLink("View Table", href="/table")),
            dbc.Button("Refresh Data", id="refresh-button", color="primary", className="mr-2")
        ],
        brand="Fantasy Basketball Dashboard",
        brand_href="/",
        # set color
        color="primary",
        dark=True
    ),
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content', children=[
        html.Label("Select Weeks to Display:"),
        # slider for barplot
        dcc.RangeSlider(
            id='week-slider',
            min=0,
            max=len(cleaned_df['Week'].unique()) - 1,
            marks={i: f'Week{week}' for i, week in enumerate(cleaned_df['Week'].unique())},
            value=[len(cleaned_df['Week'].unique()) - 5, len(cleaned_df['Week'].unique()) - 1], # last 5 weeks
        ),
        # player dropdown
        dcc.Dropdown(
            id='player-dropdown',
            options=[{'label': player, 'value': player} for player in cleaned_df['Player'].unique()],
            value=list(cleaned_df['Player'].unique()),  # Select all players by default
            multi=True  # Allow multiple selections
        ),
        dcc.Graph(id='fantasy-points-bar-chart')
    ]),
    # pop up to signify when refresh is complete
    # may take a bit since api call is slow
    dbc.Modal(
        [
            dbc.ModalHeader("Data Refreshed"),
            dbc.ModalBody("The data has been successfully refreshed."),
            dbc.ModalFooter(),
        ],
        id="modal",
        centered=True,
    ),
])

# Define callback to update page content based on URL
@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
# path names for redirects
def display_page(pathname):
    if pathname == '/table':
        return generate_table_view()
    if pathname == '/About':
        return html.H1("About Page")
    else:
        return generate_home_view()

# Function to generate table view
def generate_table_view():
    return html.Div([
        html.H2(f"{team_name}'s Player Data Table"),
        dash_table.DataTable(
            id='table',
            columns=[{"name": i, "id": i} for i in cleaned_df.columns],
            page_size= 20, # select page size
            data=cleaned_df.to_dict('records'),
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},  # Apply style to odd rows
                    'backgroundColor': 'rgb(240, 240, 240)'  # Alternate row color
                }
            ]
        )
    ])

# Function to generate home view
def generate_home_view():
    return html.Div([
        html.Label("Select Weeks to Display:"),
        # year slider again
        dcc.RangeSlider(
            id='week-slider',
            min=0,
            max=len(cleaned_df['Week'].unique()) - 1,
            marks={i: f'Week{week}' for i, week in enumerate(cleaned_df['Week'].unique())},
            value=[len(cleaned_df['Week'].unique()) - 5, len(cleaned_df['Week'].unique()) - 1],
            allowCross=False,  # Prevent crossing over
            step=1,  # Allow only integer steps
        ),
        # player drop down again
        html.Label("Select Players:"),
        dcc.Dropdown(
            id='player-dropdown',
            options=[{'label': player, 'value': player} for player in cleaned_df['Player'].unique()],
            value=list(cleaned_df['Player'].unique()),  # Select all players by default
            multi=True  # Allow multiple selections
        ),
        dcc.Graph(id='fantasy-points-bar-chart')
    ])

# Define callback to update the graph
@app.callback(
    Output('fantasy-points-bar-chart', 'figure'),
    [Input('week-slider', 'value'),
     Input('player-dropdown', 'value')],
)
def update_bar_chart(selected_weeks_index, selected_players):
    # Get the selected weeks based on their index
    selected_weeks = cleaned_df['Week'].unique()[selected_weeks_index[0]:selected_weeks_index[1] + 1]

    # Filter data for the selected weeks and players
    selected_data = cleaned_df[(cleaned_df['Week'].isin(selected_weeks)) & (cleaned_df['Player'].isin(selected_players))]

    # Plotly Express bar chart
    fig = px.bar(selected_data,
                 x='Player', y='Fantasy Points', color="Week",
                 title='Fantasy Points Bar Chart for Selected Players and Weeks', # title
                 barmode='group', # Set barmode to 'group' for grouped bars
                 height=800, # custom height
                 color_discrete_sequence=list(reversed(px.colors.sequential.Blues)))  # set colors

    
    fig.update_layout(
        xaxis_tickangle=45, # rotate 45 degrees
        plot_bgcolor='white',  # Set plot background color to white
        xaxis=dict(showgrid=False),  # Turn off horizontal grid lines
        yaxis=dict(showgrid=True, gridcolor='lightgrey'),  # Show only vertical grid lines
    )
    
    return fig
# callback for popup
@app.callback(
    Output("modal", "is_open"),
    [Input("refresh-button", "n_clicks")],
    [State("modal", "is_open")],
)
def toggle_modal(n_clicks, is_open): # check when button is clicked if so...
    if n_clicks:
        refresh() # refresh api
        return not is_open
    return is_open

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)




from plotly.offline import plot
import dash
import pandas as pd
from pathlib import Path
#from dash import html, dash_table, Input, Output, callback
from django_plotly_dash import DjangoDash
import os
from django.conf import settings

SITE_URL = 'http://localhost:5000/'

def generate_layout(servername):
    '''In goes server asset subdir, our goes page layout'''
    #server_name=dir.split("/")[len(dir.split("/"))-1]

    dict_section_figs = dict(
        # Early stage - Width
        section_width=[
            'figure_Daily Messages.html',
            'figure_N of unique users participated.html',
            'figure_N of First Time Participants.html'
        ],
        # Early stage - Depth
        section_depth=[
            'figure_N of users spending substantial time on the server.html',
            'figure_% of Meaningful Participants out of All Participants.html'
        ],
        # Early stage - Red Flag
        section_redflag=[
            'figure_User Uniformity Index.html',
            'figure_Time Uniformity Index.html'
        ],
        # Retention
        section_retention=[
            'figure_N of users still active after being active once.html',
            'figure_% of users still active after being active once.html'
        ],
        # Moderators
        section_moderators=[
            'figure_Mods: Daily messages across all mods.html',
            'figure_Mods: Daily messages.html',
            'figure_Mods: interactions per new user.html',
            'figure_Mods: unique users interacted with.html',
            'figure_Mods: % of new users interacted with.html',
            'figure_Mods: average words per message.html'
        ],
        # Comparison (optional graphs)
        section_comparison=[
            'figure_Comparison A (last month average).html',
            'figure_Comparison B (last month average).html',
            'figure_Comparison C (last month average).html',
            'figure_Comparison: % of users still active after being active once.html'
        ]
    )

    def Iframe(servername, fig):
        '''
        Returns an Iframe object for a given file
        Expects dir: pathlib.Path, fig:str
        '''
        iframe_path = SITE_URL + 'static/assets/%s/%s' % (servername, fig)
        return dash.html.Iframe(src=iframe_path, width=840, height=440, style={"border": "0px"})

    def figure_exists(servername, fig):
        fig_path = os.path.join(settings.BASE_DIR, "Reddit_app/static/assets/", servername, fig)
        return os.path.exists(fig_path)

    dict_section_iframes = {}
    for section, figs in dict_section_figs.items():
        # important to get rid of leading / in asset url
        dict_section_iframes[section] = [Iframe(servername, fig) for fig in figs if figure_exists(servername, fig)]

    # Load weekly user table
    csv_path = os.path.join(settings.BASE_DIR, "Reddit_app/static/assets/Zilliqa", 'dataframe_df_weekly_active_users_categorized.csv')
    df_daily_active_users_categorized = pd.read_csv(csv_path)
    df_daily_active_users_categorized['user_id'] = df_daily_active_users_categorized.user_id.astype(str)

    columns = [
        dict(id='week_first_day', name='Week'),
        dict(id='user_category', name='Activity Level'),
        dict(id='user_id', name='User ID'),
        dict(id='username', name='Username'),
    ]

    style_dict = {
        'border': '1px solid #23272A',
        'backgroundColor': '#23272A',
        'color': '#ABABAB'
    }

    user_datatable = dash.html.Div([
        dash.dash_table.DataTable(
            id='datatable-users',
            columns=columns,
            data=df_daily_active_users_categorized.to_dict('records'),
            filter_action="native",
            sort_action="native",
            page_action='native',
            page_size=100,
            style_table={'overflowY': 'auto', 'height': '600px'},
            style_cell=style_dict,
            style_data_conditional=[{
                'if': {'state': 'selected'},
                'backgroundColor': '#262626',
                'border': '1px solid #415D80',
                'color': 'white'
            }],
            style_cell_conditional=[{
                'if': {'column_id': 'username'},
                'textAlign': 'left'
            }]
        )], style={'width': '800px', 'height': '600px'}
    )

    title = f'{dir} Discord Server Stats'

    if dict_section_iframes['section_comparison']:
        section_comparison = [
            dash.html.Br(),
            dash.html.H2('Comparison Against Reference Server'),
            dash.html.Br(),
            *dict_section_iframes['section_comparison']
        ]
    else:
        section_comparison = []

    layout = dash.html.Div([
        dash.html.H1(title),
        dash.html.Br(),
        dash.html.H2('Early stage - Width'),
        dash.html.Br(),
        *dict_section_iframes['section_width'],
        dash.html.Br(),
        dash.html.H2('Early stage - Depth'),
        dash.html.Br(),
        *dict_section_iframes['section_depth'],
        dash.html.Br(),
        dash.html.H2('Early stage - Red Flag'),
        dash.html.Br(),
        *dict_section_iframes['section_redflag'],
        dash.html.Br(),
        dash.html.H2('Retention'),
        dash.html.Br(),
        *dict_section_iframes['section_retention'],
        dash.html.Br(),
        dash.html.H2('Moderators'),
        dash.html.Br(),
        *dict_section_iframes['section_moderators'],
        *section_comparison,  # optional
        dash.html.H2('Weekly Active Users'),
        dash.html.Br(),
        user_datatable
    ], style={'padding': 30})

    return layout


# main app
# external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = DjangoDash("dash_container")

app.layout = dash.html.Div([
    dash.dcc.Location(id='url', refresh=False),
    dash.html.Div(id='page-content', style={'padding': 30}),
])
def update_layout(servername):
    layout = generate_layout(servername)
    app.layout = dash.html.Div([
        dash.dcc.Location(id='url', refresh=False),
        dash.html.Div(id='page-content', style={'padding': 30}),
        layout
    ])


def generate_directory():
    FILE_DIR = Path(__file__).with_name('assets')
    SUB_DIRS = {subdir.name.replace(' ', ''): subdir for subdir in FILE_DIR.iterdir() if subdir.is_dir()}

    '''Returns list of links to all server stats'''
    children = [dash.html.H3('Servers dashboards:')]
    for dir in SUB_DIRS:
        # discard initial '/' for title
        children.append(dash.dcc.Link(title=dir, href=f'/{dir}'))
        children.append(dash.html.Br())

    return children

@dash.callback(dash.Output('page-content', 'children'),
          dash.Input('url', 'pathname'))
def display_page(path):
    FILE_DIR = Path(__file__).with_name('assets')
    SUB_DIRS = {subdir.name.replace(' ', ''): subdir for subdir in FILE_DIR.iterdir() if subdir.is_dir()}

    path_name = path[1:]  # Drop '/'
    if path_name == 'dir':
        return generate_directory()
    elif path_name in SUB_DIRS:
        return generate_layout(SUB_DIRS[path_name])
    else:
        return '404'


#server = app.server
#if __name__ == '__main__':
#    app.run_server(host='localhost', debug=True, port=8060)



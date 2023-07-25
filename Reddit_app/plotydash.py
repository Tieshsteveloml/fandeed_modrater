
from plotly.offline import plot
import plotly.graph_objs as go
import pandas as pd
from pathlib import Path
from dash import html, dash_table, Input, Output, callback

DICT_SECTION_FIGS = (
    # Early stage - Width
    ('Early Stage - Width', (
        'Daily Messages',
        '# of unique users participated',
        '# of First Time Participants')
     ),
    # Early stage - Depth
    ('Early Stage - Depth', (
        '# of users spending substantial time on the server',
        '% of Meaningful Participants out of All Participants',)
     ),

    # Early stage - Red Flag
    ('Early Stage - Red Flag', (
        'User Uniformity Index',
        'Time Uniformity Index'
    )),
    # Retention
    ('Retention', (
        '# of users still active after being active once',
        '% of users still active after being active once'
    )),
    # Moderators
    ('Mods', (
        'Mods: Daily messages across all mods',
        'Mods: Daily messages',
        'Mods: interactions per new user',
        'Mods: unique users interacted with',
        'Mods: % of new users interacted with',
        'Mods: average words per message'
    )),
    # Comparison (optional graphs)
    ('Comparison', (
        'Comparison A (last month average)',
        'Comparison B (last month average)',
        'Comparison C (last month average)',
        'Comparison: % of users still active after being active once'
    ))
)

def generate_layout(dir, master_chart):
    #dir='Reddit_app/assets/Zilliqa'
    server_name=dir.split("/")[len(dir.split("/"))-1]
    title=server_name+" Discord Server Stats "
    master_file='<h1 style="color:white;">'+title+"<br><br></h1>"

    #writing it into a html page
    for i in range(0, len(DICT_SECTION_FIGS)):
        section_name=DICT_SECTION_FIGS[i][0]
        master_file = master_file + "<h2>" + section_name + "</h2>"
        for j in range(0, len(DICT_SECTION_FIGS[i][1])):
            fig_name=DICT_SECTION_FIGS[i][1][j]
            fig=[x[1] for x in master_chart if x[0]==fig_name]
            if len(fig)>0: #we can find the chart
                chart_html="<h3>"+fig[0].to_html(full_html=False, include_plotlyjs='cdn')+"<br></h3>"
                master_file=master_file+chart_html
            else:
                print ("not able to find this chart: ", fig_name)
    with open(dir + "/master.html", 'w') as f:
        f.write(master_file)


def generate_layout_old(dir):
    '''In goes server asset subdir, our goes page layout'''
    server_name=dir.split("/")[len(dir.split("/"))-1]
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


    def Iframe(dir, fig):
        '''
        Returns an Iframe object for a given file
        Expects dir: pathlib.Path, fig:str
        '''
        return html.Iframe(src=dir+'/'+fig, width=840, height=440, style={"border": "0px"})


    def figure_exists(dir, fig):
        return Path(dir+'/'+fig).exists()

    dict_section_iframes = {}
    for section, figs in dict_section_figs.items():
        # important to get rid of leading / in asset url
        dict_section_iframes[section] = [Iframe(dir, fig) for fig in figs if figure_exists(dir, fig)]

    # Load weekly user table
    df_daily_active_users_categorized = pd.read_csv(dir+'/dataframe_df_weekly_active_users_categorized.csv')
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

    user_datatable = html.Div([
        dash_table.DataTable(
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

    title = f'{server_name} Discord Server Stats'


    if dict_section_iframes['section_comparison']:
        section_comparison = [
            html.Br(),
            html.H2('Comparison Against Reference Server'),
            html.Br(),
            *dict_section_iframes['section_comparison']
        ]
    else:
        section_comparison = []

    layout = html.Div([
        html.H1(title),
        html.Br(),
        html.H2('Early stage - Width'),
        html.Br(),
        *dict_section_iframes['section_width'],
        html.Br(),
        html.H2('Early stage - Depth'),
        html.Br(),
        *dict_section_iframes['section_depth'],
        html.Br(),
        html.H2('Early stage - Red Flag'),
        html.Br(),
        *dict_section_iframes['section_redflag'],
        html.Br(),
        html.H2('Retention'),
        html.Br(),
        *dict_section_iframes['section_retention'],
        html.Br(),
        html.H2('Moderators'),
        html.Br(),
        *dict_section_iframes['section_moderators'],
        *section_comparison,  # optional
        html.H2('Weekly Active Users'),
        html.Br(),
        user_datatable
    ], style={'padding': 30})

    return layout


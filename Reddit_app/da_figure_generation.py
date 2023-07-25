#! /usr/bin/env python
import sys
import pathlib
import functools
from time import time
from datetime import date
import os
import toml
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from Reddit_app.message_count import remove_stopwords, count_emoji, count_unique_users, reply_count, mention_list, clean_user_list

# Some changeable parameters
ma_window = 14  # moving average window length
active_user_min_messages = 5

# Figure styling
palette = px.colors.qualitative.Plotly
palette[0] = '#7FB2EB'
px.bar = functools.partial(px.bar, color_discrete_sequence=palette)
px.line = functools.partial(px.line, color_discrete_sequence=palette)
px.area = functools.partial(px.area, color_discrete_sequence=palette)
px.scatter = functools.partial(px.scatter, color_discrete_sequence=palette)


def style_daily_bar(fig):
    return fig.update_traces(width=86_400 * 1000 * 1.1, marker=dict(line=dict(width=0)))

def add_moving_avg(fig, df, y, x=None, avg=None, ma_window=ma_window):
    '''Adds moving average trace to figures'''

    # Ignore supplied ones for now
    avg = None

    if avg is None:
        # Calculate moving average
        y_ma = df[y].rolling(window=ma_window, center=True).mean()
    else:
        # or use supplied df column name
        y_ma = df[avg]

    if x is None:
        fig.add_traces(go.Scatter(x=df.index, y=y_ma, mode='lines', name='Average'))
    else:
        fig.add_traces(go.Scatter(x=df[x], y=y_ma, mode='lines', name='Average'))
    return fig

def daily_bar_avg(df, y, x=None, avg=None):
    '''Quick bar + rolling avg graph creation'''
    fig = style_daily_bar(px.bar(df, x=x, y=y))
    return add_moving_avg(fig, df, y, x, avg)


def save_figure(fig, title, server_name):
    fig_dir='./Reddit_app/assets/'+server_name
    fig_dir='./static/assets/'+server_name
    print ("fig directory is ", fig_dir)
    new_title = title.replace('#', 'N')  # Plotly being plotly
    path = f'{fig_dir}/figure_{new_title}.html'
    fig.write_html(path)
    print('Saved:', path)

def style_fig(fig, title=None, xtitle=None, ytitle=None, save=True, server_name=None):
    '''Styles and saves plotly figure'''

    bg_color = '#23272A'
    grid_color = '#393939'
    fig.update_layout(
        paper_bgcolor=bg_color,
        plot_bgcolor=bg_color,
        font_color='#ABABAB',
        template='plotly_dark',
        xaxis=dict(gridcolor=grid_color, zerolinecolor=grid_color),
        yaxis=dict(gridcolor=grid_color, zerolinecolor=grid_color),
    )

    if title is not None:
        fig.update_layout(title=title)
    if xtitle is not None:
        fig.update_xaxes(title=xtitle)
    if ytitle is not None:
        fig.update_yaxes(title=ytitle)
    fig.update_layout(width=800, height=400, template='plotly_white')
    # Saving in global figures for now
    if save:
        save_figure(fig, title, server_name)
    return fig

def generating_chart(server_name):
    master_chart=[]

    asset_dir = './static/assets'
    fig_dir = asset_dir+"/"+server_name
    os.makedirs(fig_dir, exist_ok=True)

    config = toml.load('./Reddit_app/datasets/'+server_name+'.toml')
    mods = config['mods']

    # Data wrangling / Figure building script
    time_start = time()

    # reading and cleaning dataset
    print('Loading data...')

    df_data = pd.read_json('./Reddit_app/datasets/'+server_name+'.json')  # btw, sample data is not in chronological order

    """
    {'id': '853466029175078932', 'type': 0, 'content': 'Will the book be available in MALAYSIA 🇲🇾?', 
    'channel_id': '852767377933598770', 
    'author': {'id': '760494176998654013', 'username': 'a-yxi.  -_-', 'avatar': '079c616f21df9f7a7f70a7a7307c6ba3', 'discriminator': '8538', 'public_flags': 0}, 
    'attachments': [], 'embeds': [], 'mentions': [], 'mention_roles': [], 
    'pinned': False, 'mention_everyone': False, 'tts': False, 'timestamp': '2021-06-13T02:49:17.987000+00:00', 
    'edited_timestamp': None, 'flags': 0, 'components': [], 'hit': True},
    """

    # ###############
    # to flatten author-data structural

    df_author = pd.DataFrame.from_records(df_data.author.values.flatten())
    # present columns: ['author_id', 'username', 'avatar', 'discriminator', 'public_flags', 'bot']
    df_author.rename(columns={'id': 'author_id'}, inplace=True)
    df_master_data = pd.concat([df_data, df_author], axis=1)

    df_master_data['datetime_time'] = pd.to_datetime(df_master_data.timestamp)
    df_master_data['datetime_day'] = df_master_data.datetime_time.apply(lambda x: x.date())

    # Discard bot messages
    if 'bot' in df_master_data.columns:
        df_master_data = df_master_data[~df_master_data.bot.fillna(False)]

    df_master_data = df_master_data.sort_values('datetime_time').reset_index(drop=True)

    """
    columns are
    ['id', 'type', 'content', 'channel_id', 'author', 'attachments',
           'embeds', 'mentions', 'mention_roles', 'pinned', 'mention_everyone',
           'tts', 'timestamp', 'edited_timestamp', 'flags', 'components', 'hit',
           'message_reference', 'sticker_items', 'activity', 'thread', 'stickers',
           'application_id', 'interaction', 'webhook_id', 'author_id', 'username',
           'avatar', 'discriminator', 'public_flags']
    """
    # id:username map
    dict_author_id_names = {}
    for author_id, username in zip(df_master_data.author_id.values, df_master_data.username.values):
        if author_id not in dict_author_id_names:
            dict_author_id_names[author_id] = username

    """
    #adding overall server performance
    """
    # getting number of new messages in a day
    df_daily = df_master_data.groupby([df_master_data['datetime_time'].dt.date]).count()
    df_daily['rolling_avg'] = df_daily['content'].rolling(window=ma_window).mean()

    dict_daily_stats = {}
    dict_daily_stats['Message_Sent'] = df_daily['content'].iloc[-1]
    dict_daily_stats['Message_Sent_Rolling_7D_AVG'] = df_daily['rolling_avg'].iloc[-1]
    dict_daily_stats['Message_Sent_Z_Score'] = (df_daily['content'].iloc[-1] - df_daily['content'].iloc[-15:-1].mean()) / \
                                               df_daily['content'].iloc[-15:-1].std()

    fig = daily_bar_avg(df_daily, y='content', avg='rolling_avg')
    fig=style_fig(fig, 'New Messages', '', '', server_name=server_name)
    master_chart.append(('New Messages', fig))
    """
    getting number of total words sent
    """
    df_master_data['total_words_count'] = [len(x.split(" ")) for x in df_master_data['content']]
    df_master_data['total_meaningful_count'] = [len(remove_stopwords(x).split(" ")) for x in df_master_data['content']]

    df_daily_content = df_master_data.groupby([df_master_data['datetime_time'].dt.date]).sum()
    df_daily_content['rolling_avg_words'] = df_daily_content['total_words_count'].rolling(window=ma_window).mean()
    df_daily_content['rolling_avg_meaning_words'] = df_daily_content['total_meaningful_count'].rolling(
        window=ma_window).mean()
    df_daily_content['meaningful_iteractions'] = df_daily_content['rolling_avg_meaning_words'] / df_daily_content[
        'rolling_avg_words']

    dict_daily_stats['total_words_count'] = df_daily_content['total_words_count'].iloc[-1]
    dict_daily_stats['total_words_count_Z_Score'] = (df_daily_content['total_words_count'].iloc[-1] - df_daily_content[
                                                                                                          'total_words_count'].iloc[
                                                                                                      -15:-1].mean()) / \
                                                    df_daily_content['total_words_count'].iloc[-15:-1].std()

    dict_daily_stats['total_meaningful_count'] = df_daily_content['total_meaningful_count'].iloc[-1]
    dict_daily_stats['total_meaningful_count_Z_Score'] = (df_daily_content['total_meaningful_count'].iloc[-1] -
                                                          df_daily_content['total_meaningful_count'].iloc[-15:-1].mean()) / \
                                                         df_daily_content['total_meaningful_count'].iloc[-15:-1].std()

    dict_daily_stats['meaningful_word_ratio'] = df_daily_content['meaningful_iteractions'].iloc[-1]
    dict_daily_stats['meaningful_word_ratio_Z_Score'] = (df_daily_content['meaningful_iteractions'].iloc[-1] -
                                                         df_daily_content['meaningful_iteractions'].iloc[-15:-1].mean()) / \
                                                        df_daily_content['meaningful_iteractions'].iloc[-15:-1].std()

    fig = daily_bar_avg(df_daily_content, y='total_words_count', avg='rolling_avg_words')
    style_fig(fig, 'Daily New Words', '', '', server_name=server_name)
    master_chart.append(('Daily New Words', fig))

    fig = daily_bar_avg(df_daily_content, y='total_meaningful_count', avg='rolling_avg_meaning_words')
    style_fig(fig, 'Daily New Meaningful Words', '', '',server_name=server_name)
    master_chart.append(('Daily New Meaningful Words', fig))

    fig = px.line(df_daily_content, y='meaningful_iteractions')
    add_moving_avg(fig, df_daily_content, y='meaningful_iteractions')
    style_fig(fig, 'Daily Meaning Words Ratio', '', '', server_name=server_name)
    master_chart.append(('Daily Meaning Words Rati', fig))

    """
    getting number of embeds and media
    """
    df_master_data['embeds_count'] = [len(x) for x in df_master_data['embeds']]
    df_master_data['attachments_count'] = [len(x) for x in df_master_data['attachments']]
    df_master_data['embeds_count'] = df_master_data['embeds_count'] + df_master_data['attachments_count']

    df_master_data['emote_count'] = [count_emoji(x) for x in df_master_data['content']]
    df_master_data['media_count'] = df_master_data['embeds_count'] + df_master_data[
        'emote_count']  # emote actually dont work very well
    df_master_data['message_count'] = [1] * len(df_master_data)  # emote actually dont work very well

    # to do list could be look at where usually users are linking to.. to further gague user interests

    df_daily_media = df_master_data.groupby([df_master_data['datetime_time'].dt.date]).sum()
    df_daily_media['rolling_avg'] = df_daily_media['media_count'].rolling(window=ma_window).mean()

    fig = daily_bar_avg(df_daily_media, y='media_count', avg='rolling_avg')
    style_fig(fig, 'Daily Emote + Embed Count', '', '',server_name=server_name)
    master_chart.append(('Daily Emote + Embed Count', fig))

    dict_daily_stats['Media_Sent'] = df_daily_media['media_count'].iloc[-1]
    dict_daily_stats['Media_Sent_Rolling_7D_AVG'] = df_daily_media['rolling_avg'].iloc[-1]
    dict_daily_stats['Media_Sent_Z_Score'] = (df_daily_media['media_count'].iloc[-1] - df_daily_media['media_count'].iloc[
                                                                                       -15:-1].mean()) / df_daily_media[
                                                                                                             'media_count'].iloc[
                                                                                                         -15:-1].std()

    df_daily_media['perc_embed_over_words'] = 100 * df_daily_media['media_count'] / df_daily_media['total_words_count']
    df_daily_media['rolling_avg_embed_ratio'] = df_daily_media['perc_embed_over_words'].rolling(window=ma_window).mean()

    """
    looking over embed ratios
    """
    df_daily_media['perc_embed_over_words'] = 100 * df_daily_media['media_count'] / df_daily_media['total_words_count']
    df_daily_media['rolling_avg_embed_ratio'] = df_daily_media['perc_embed_over_words'].rolling(window=ma_window).mean()

    fig = daily_bar_avg(df_daily_media, y='perc_embed_over_words', avg='rolling_avg_embed_ratio')
    style_fig(fig, 'Daily Emote + Embed Count % of Total Words', '', '', server_name=server_name)
    master_chart.append(('Daily Emote + Embed Count % of Total Words', fig))

    """
    # of users that are active (1 message or more) as a % of total users
    #@todo: figure out how many users in a guilde
    """
    df_daily_users = df_master_data.groupby([df_master_data['datetime_time'].dt.date])['author_id'].unique()
    df_daily_users = df_daily_users.to_frame()
    df_daily_users['unique_users'] = df_daily_users['author_id'].apply(count_unique_users)
    df_daily_users['rolling_avg_unique_users'] = df_daily_users['unique_users'].rolling(window=ma_window).mean()

    fig = daily_bar_avg(df_daily_users, y='unique_users', avg='rolling_avg_unique_users')
    style_fig(fig, '# of unique users participated', '', '',server_name=server_name)
    master_chart.append(('# of unique users participated', fig))

    """
    # of users that are active for the first time:
    #@todo %of total users
    """
    cumulative_author_list = []
    first_time_user_list = []
    first_time_user_count = []

    for author_id in df_daily_users.author_id.values:
        unique_list = list(set(list(author_id)))
        new_users_list = [x for x in unique_list if x not in cumulative_author_list]
        first_time_user_list.append(new_users_list)
        first_time_user_count.append(len(new_users_list))
        cumulative_author_list = list(set(cumulative_author_list + unique_list))

    df_daily_users['first_time_user_list'] = first_time_user_list
    df_daily_users['first_time_user_count'] = first_time_user_count
    df_daily_users['rolling_avg_first_time_users'] = df_daily_users['first_time_user_count'].rolling(
        window=ma_window).mean()
    # df_daily_users=df_daily_users.reset_index()

    fig = daily_bar_avg(df_daily_users, y='first_time_user_count', avg='rolling_avg_first_time_users')
    style_fig(fig, '# of First Time Participants', '', '', server_name=server_name)
    master_chart.append(('# of First Time Participants', fig))

    """
    % of users who sent over 5 messages a day
    #@todo: out of all active participants and out of all users
    """
    df_user_daily_combo = df_master_data.groupby(
        [df_master_data['datetime_time'].dt.date, df_master_data['author_id']]).count()
    df_user_daily_combo.index.names = ['index_datetime_time', 'index_author_id']
    df_user_daily_combo = df_user_daily_combo.reset_index()

    df_5msg = df_user_daily_combo.groupby('index_datetime_time')['content'].apply(lambda x: (x > 4).sum()).reset_index(
        name='users_with_5msg')
    df_5msg['rolling_avg_5msg_users'] = df_5msg['users_with_5msg'].rolling(window=ma_window).mean()
    df_5msg = df_5msg.merge(df_daily_users.reset_index()[['datetime_time', 'unique_users']], how='left',
                            left_on='index_datetime_time', right_on='datetime_time')

    # figure_# of Participants sent out more than 5 messages
    fig = daily_bar_avg(df_5msg, y='users_with_5msg', avg='rolling_avg_5msg_users', x='datetime_time')
    style_fig(fig, '# of users spending substantial time on the server', '', '', server_name=server_name)
    master_chart.append(('# of users spending substantial time on the server', fig))

    df_5msg['real_active_users'] = df_5msg['users_with_5msg'] / df_5msg['unique_users']
    df_5msg['rolling_avg_real_active_users'] = df_5msg['real_active_users'].rolling(window=ma_window).mean()

    fig = daily_bar_avg(df_5msg, y='real_active_users', avg='rolling_avg_real_active_users', x='datetime_time')
    style_fig(fig, '% of Meaningful Participants out of All Participants', '', '', server_name=server_name)
    master_chart.append(('% of Meaningful Participants out of All Participants', fig))

    """
    % of users who cumulatively send over 100 messages and daily increase
    #@todo: out of all active participants and out of all users
    """
    df_daily_user_combo = df_master_data.groupby(
        [df_master_data['author_id'], df_master_data['datetime_time'].dt.date]).count()
    df_daily_user_combo.index.names = ['index_author_id', 'index_datetime_time']
    df_daily_user_combo = df_daily_user_combo.reset_index()

    df_daily_user_combo = df_daily_user_combo[['index_author_id', 'index_datetime_time', 'content']]

    df_user_cum_msg_count = df_daily_user_combo.groupby(['index_author_id', 'index_datetime_time']).sum().groupby(
        level=0).cumsum().reset_index()
    df_user_100_club = df_user_cum_msg_count[df_user_cum_msg_count['content'] > 100]
    df_user_100_club = df_user_100_club.groupby('index_author_id').first()  # list of top 100 active users
    df_user_100_club = df_user_100_club.sort_values(by='index_datetime_time', ascending=True)
    df_user_100_club = df_user_100_club.reset_index()
    df_user_100_club_cum = df_user_100_club.groupby('index_datetime_time').count()
    df_user_100_club_cum['cum_member'] = df_user_100_club_cum['content'].cumsum()
    df_user_100_club_cum = df_user_100_club_cum.reset_index()

    df_cum_user_summary = pd.DataFrame(columns=['index_datetime_time'])
    df_cum_user_summary['index_datetime_time'] = df_daily_content.index

    df_cum_user_summary = df_cum_user_summary.merge(df_user_100_club_cum[['index_datetime_time', 'cum_member']],
                                                    on='index_datetime_time', how='left')
    df_cum_user_summary.loc[0, 'cum_member'] = 0
    df_cum_user_summary = df_cum_user_summary.fillna(method='ffill')

    df_cum_user_summary['daily_increase'] = df_cum_user_summary['cum_member'].diff()

    fig = style_daily_bar(px.bar(df_cum_user_summary, x='index_datetime_time', y='cum_member'))
    style_fig(fig, '# of Participants sent out more than 100 messages cumulatively', '', '', server_name=server_name)
    master_chart.append(('# of Participants sent out more than 100 messages cumulatively', fig))


    fig = style_daily_bar(px.bar(df_cum_user_summary, x='index_datetime_time', y='daily_increase'))
    fig = add_moving_avg(fig, df_cum_user_summary, x='index_datetime_time', y='daily_increase')
    style_fig(fig, 'Daily new increase of Participants sent out more than 100 messages cumulatively', '', '', server_name=server_name)
    master_chart.append(('Daily new increase of Participants sent out more than 100 messages cumulatively', fig))

    """
    # of replies in a day
    """
    df_master_data['replies_counts'] = [reply_count(x) for x in df_master_data['message_reference']]
    df_replies = df_master_data.groupby([df_master_data['datetime_time'].dt.date]).sum()
    df_replies['rolling_avg'] = df_replies['replies_counts'].rolling(window=ma_window).mean()

    df_replies['replies_counts_ratio'] = df_replies['replies_counts'] / df_replies['message_count']
    df_replies['rolling_avg_reply_ratio'] = df_replies['replies_counts_ratio'].rolling(window=ma_window).mean()

    fig = daily_bar_avg(df_replies, y='replies_counts', avg='rolling_avg')
    style_fig(fig, 'Daily Replied Messages', '', '',server_name=server_name)
    master_chart.append(('Daily Replied Messages', fig))

    fig = daily_bar_avg(df_replies, y='replies_counts_ratio', avg='rolling_avg_reply_ratio')
    style_fig(fig, 'Daily Replied Messages % of Total Messages', '', '', server_name=server_name)
    master_chart.append(('Daily Replied Messages % of Total Messages', fig))

    df_master_data['datetime_hour'] = df_master_data.datetime_time.round('H')
    df_master_data['year_week'] = df_master_data.datetime_day.apply(
        lambda x: f'{pd.Timestamp.isocalendar(x)[0]}_{pd.Timestamp.isocalendar(x)[1]:02d}')


    def first_day_of_week(x):
        year, week, day = pd.Timestamp.isocalendar(x)
        day = 1
        return date.fromisocalendar(year, week, day)


    df_master_data['date_week_first_day'] = df_master_data.datetime_day.apply(first_day_of_week)

    # df_daily_user_messages, columns: author_id, datetime_day, message_count, content (list of strings).
    df_daily_user_messages = df_master_data.groupby(['author_id', 'datetime_day']).agg(
        {'author_id': 'count', 'content': lambda x: list(x)})
    df_daily_user_messages = df_daily_user_messages.rename(columns={'author_id': 'message_count'}).sort_values(
        ['datetime_day', 'author_id']).reset_index()

    df_weekly_user_messages = df_master_data.groupby(['year_week', 'date_week_first_day', 'author_id']).agg(
        {'author_id': 'count', 'content': lambda x: list(x)})

    df_weekly_user_messages = df_weekly_user_messages.rename(columns={'author_id': 'message_count'}).sort_values(
        ['year_week', 'author_id']).reset_index()
    df_weekly_user_messages['ismoderator'] = df_weekly_user_messages.author_id.apply(lambda x: x in mods)


    # GINI index for time and users: df_daily_gini, columns: day, gini_users, gini_time, users, messages
    # 0: uniform, 1:not at all


    # columns: author_id, datetime_day, count
    # df_daily_user_messages = df_master_data.groupby(['author_id', 'datetime_day']).author_id.agg('count').to_frame('message_count').reset_index()

    daily_gini = dict(day=[], gini_users=[], gini_time=[], users=[], messages=[])
    for day in df_daily_user_messages.datetime_day.unique():
        # GINI users

        # Get user_messages of day and sort by message_count
        day_user_messages = df_daily_user_messages[df_daily_user_messages.datetime_day == day].sort_values(
            'message_count').reset_index(drop=True)
        # User message proportion
        day_total_messages = day_user_messages.message_count.sum()
        day_total_users = day_user_messages.shape[0]

        # Gini calculation
        lorenz_curve = (day_user_messages.message_count / day_total_messages).cumsum().values
        uniform_distribution_curve = np.arange(1,
                                               1 + day_total_users) * day_user_messages.message_count.mean() / day_total_messages

        # Area between curve and ideal curve / area of triangle
        day_gini_users = (uniform_distribution_curve - lorenz_curve).sum() / uniform_distribution_curve.sum()

        # GINI time

        # Getting messages per hour for current day

        day_data = df_master_data[df_master_data.datetime_day == day].copy()
        # day_messages_per_hour columns: datetime_hour, message_count
        day_messages_per_hour = day_data.groupby('datetime_hour').author_id.agg('count').to_frame('message_count')
        # Fill missing hours with 0
        hours_in_day = pd.date_range(day, periods=24, freq="h", tz='UTC')
        day_messages_per_hour = day_messages_per_hour.reindex(hours_in_day, fill_value=0).sort_values('message_count')

        # Gini time calculation
        lorenz_curve = (day_messages_per_hour.message_count / day_total_messages).cumsum().values
        uniform_distribution_curve = np.arange(1, 24 + 1) * day_messages_per_hour.message_count.mean() / day_total_messages

        # Area between curve and ideal curve / area of triangle
        with np.errstate(divide='ignore', invalid='ignore'):
            day_gini_time = (uniform_distribution_curve - lorenz_curve).sum() / uniform_distribution_curve.sum()

        daily_gini['day'].append(day)
        daily_gini['gini_users'].append(day_gini_users)
        daily_gini['gini_time'].append(day_gini_time)
        # Might as well pick these up
        daily_gini['users'].append(day_total_users)
        daily_gini['messages'].append(day_total_messages)

    df_daily_gini = pd.DataFrame.from_dict(daily_gini).sort_values('day').reset_index(drop=True)

    fig = px.scatter(df_daily_gini, x='day', y='users')
    fig = add_moving_avg(fig, df_daily_gini, x='day', y='users')
    style_fig(fig, 'Daily Users', '', '',server_name=server_name)
    master_chart.append(('Daily Users', fig))

    fig = px.scatter(df_daily_gini, x='day', y='messages')
    fig = add_moving_avg(fig, df_daily_gini, x='day', y='messages')
    style_fig(fig, 'Daily Messages', '', '', server_name=server_name)
    master_chart.append(('Daily Messages', fig))


    fig = px.scatter(df_daily_gini, x='day', y='gini_users')
    fig = add_moving_avg(fig, df_daily_gini, x='day', y='gini_users')
    style_fig(fig, 'User Uniformity Index', 'Date', 'Index (Less is more uniform)', server_name=server_name)
    master_chart.append(('User Uniformity Index', fig))

    fig = px.scatter(df_daily_gini, x='day', y='gini_time')
    fig = add_moving_avg(fig, df_daily_gini, x='day', y='gini_time')
    style_fig(fig, 'Time Uniformity Index', 'Day', 'Index (Less is more uniform)', server_name=server_name)
    master_chart.append(('Time Uniformity Index', fig))

    df_daily_user_messages['ismoderator'] = df_daily_user_messages.author_id.apply(lambda author_id: author_id in mods)

    df_daily_active_user_messages = df_daily_user_messages.query(
        f'message_count >= {active_user_min_messages} and not ismoderator')
    df_daily_active_user_messages = df_daily_active_user_messages.sort_values(['author_id', 'datetime_day']).reset_index(
        drop=True)
    # df_daily_user_messages columns: author_id, datetime_day, count, content,  ismoderator


    # % of active users after 1/2/4 weeks
    active_users = df_daily_active_user_messages.author_id.unique()

    # dict with key=author_id, value={first, last}
    users_first_last_active = dict()
    for item in df_daily_active_user_messages.iloc:
        if item.author_id not in users_first_last_active:
            users_first_last_active[item.author_id] = dict(first=item.datetime_day, last=item.datetime_day)
        else:
            users_first_last_active[item.author_id]['last'] = item.datetime_day

    for author_id in users_first_last_active:
        users_first_last_active[author_id]['active_after'] = users_first_last_active[author_id]['last'] - \
                                                             users_first_last_active[author_id]['first']

    df_users_active_span = pd.DataFrame.from_dict(users_first_last_active, orient='index')

    df_users_active_after = df_users_active_span.groupby('active_after')['active_after'].count().to_frame()
    df_users_active_after = df_users_active_after.rename(columns={'active_after': 'users_active_span'}).reset_index()
    df_users_active_after.rename(columns={'active_after': 'active_span'}, inplace=True)
    df_users_active_after['active_span'] = df_users_active_after.active_span.dt.days
    df_users_active_after['still_active_after'] = df_users_active_after.iloc[::-1].users_active_span.cumsum().values[::-1]

    df_users_active_after[
        'percent_still_active_after'] = df_users_active_after.still_active_after / df_users_active_after.still_active_after.sum()

    fig = px.area(df_users_active_after, x='active_span', y='percent_still_active_after', range_x=[0, 30])
    style_fig(fig, '% of users still active after being active once', 'Days', 'Users (%)', server_name=server_name)
    master_chart.append(('% of users still active after being active once', fig))

    fig = px.area(df_users_active_after, x='active_span', y='still_active_after', range_x=[0, 30])
    style_fig(fig, '# of users still active after being active once', 'Days', 'Users', server_name=server_name)
    master_chart.append(('# of users still active after being active once', fig))

    fig = px.area(df_users_active_after, x='active_span', y='users_active_span')
    style_fig(fig, '# of users that stay active for a given time span', 'Days', 'Users', server_name=server_name)
    master_chart.append(('# of users that stay active for a given time span', fig))

    # as unintuitive as this may seem, summing a list of lists gets us a flattened list
    df_daily_active_user_content = df_daily_active_user_messages.groupby('datetime_day').agg(
        {'content': 'sum'}).reset_index()

    # Lists of user content
    all_active_user_content = df_daily_active_user_content.content.sum()
    all_content = df_master_data.content.values


    # Weekly user segmentation (medium, high)

    # For super active users I think an absolute value could work best, at low user count it's easy to skew things
    # or perhaps just set an additional constraint like minimum message per time period
    def is_medium_user(pct, lower_bound=0.4, upper_bound=0.6):
        return lower_bound <= pct <= upper_bound


    def is_high_user(pct, lower_bound=0.9, upper_bound=0.95):
        return lower_bound <= pct <= upper_bound


    def is_top_user(pct, lower_bound=0.95, upper_bound=1):
        return lower_bound <= pct <= upper_bound


    # Weekly user segmentation, searchable table
    # columns: week_first_day:date, user_id:str, username:str
    weekly_active_users_categorized = dict(week_first_day=[], user_id=[], user_category=[])

    for day in df_weekly_user_messages.date_week_first_day.unique():
        day_user_messages = df_weekly_user_messages[df_weekly_user_messages.date_week_first_day == day].copy()
        day_user_messages['pct_rank'] = day_user_messages.message_count.rank(pct=True)

        medium = day_user_messages[day_user_messages.pct_rank.apply(is_medium_user)].author_id.to_list()
        weekly_active_users_categorized['user_id'].extend(medium)
        weekly_active_users_categorized['week_first_day'].extend([day] * len(medium))
        weekly_active_users_categorized['user_category'].extend(['medium'] * len(medium))

        high = day_user_messages[day_user_messages.pct_rank.apply(is_high_user)].author_id.to_list()
        weekly_active_users_categorized['user_id'].extend(high)
        weekly_active_users_categorized['week_first_day'].extend([day] * len(high))
        weekly_active_users_categorized['user_category'].extend(['high'] * len(high))

        top = day_user_messages[day_user_messages.pct_rank.apply(is_top_user)].author_id.to_list()
        weekly_active_users_categorized['user_id'].extend(top)
        weekly_active_users_categorized['week_first_day'].extend([day] * len(top))
        weekly_active_users_categorized['user_category'].extend(['top'] * len(top))

    df_weekly_active_users_categorized = pd.DataFrame.from_dict(weekly_active_users_categorized)
    df_weekly_active_users_categorized['username'] = df_weekly_active_users_categorized.user_id.map(dict_author_id_names)
    df_weekly_active_users_categorized.to_csv(f'{fig_dir}/dataframe_df_weekly_active_users_categorized.csv', index=None)
    print(f'Saved: {fig_dir}/dataframe_df_weekly_active_users_categorized.csv')

    # % of users who have only talked once in 4 weeks

    weeks = df_weekly_user_messages.year_week.unique()
    year_week_sliding_window = [list(weeks[:1]), list(weeks[:2]), list(weeks[:3])]
    year_week_sliding_window.extend(np.lib.stride_tricks.sliding_window_view(weeks, 4).tolist())

    # Users active only once per last 4 weeks

    # l4w: last four weeks
    l4w_users_once = dict(year_week=[], count=[], pct=[], author_ids=[])

    for four_week_group in year_week_sliding_window:
        l4w_messages = df_weekly_user_messages.query(f'year_week in {four_week_group}')
        l4w_messages = l4w_messages.groupby('author_id').agg({'message_count': 'sum'}).reset_index()
        l4w_total_users = len(l4w_messages.author_id.unique())

        l4w_messages_once = l4w_messages[l4w_messages.message_count == 1]
        l4w_total_users_once = len(l4w_messages_once.author_id)

        l4w_users_once['year_week'].append(four_week_group[-1])
        l4w_users_once['count'].append(l4w_total_users_once)
        l4w_users_once['pct'].append(l4w_total_users_once / l4w_total_users)
        l4w_users_once['author_ids'].append(l4w_messages_once.author_id.tolist())

    # columns: year_week, count, pct, author_ids
    df_l4w_users_once = pd.DataFrame.from_dict(l4w_users_once)

    # MODS

    df_daily_mod_messages = df_daily_user_messages[df_daily_user_messages.ismoderator]

    # taken from below
    df_master_data['replies_counts'] = [reply_count(x) for x in df_master_data['message_reference']]

    mod_stats = dict(user_id=[], username=[], avg_words=[], total_replies=[])  # , total_emotes=[], avg_emotes=[])

    for mod in mods:
        mod_messages = df_daily_mod_messages[df_daily_mod_messages.author_id == mod].content.sum()
        if not mod_messages:
            print(f'Mod:{mod} has no messages. Check author_id.')
            continue

        avg_words = np.mean([len(msg.split()) for msg in mod_messages])
        total_replies = df_master_data[df_master_data.author_id == mod].replies_counts.sum()

        mod_stats['user_id'].append(mod)
        mod_stats['username'].append(dict_author_id_names[mod])
        mod_stats['avg_words'].append(avg_words)
        mod_stats['total_replies'].append(total_replies)

        # Emotes removed for now
        # total_emotes = df_master_data[df_master_data.author_id == mod].emote_count.sum()
        # avg_emotes = total_emotes / len(mod_messages)
        # mod_stats['total_emotes'].append(total_emotes)
        # mod_stats['avg_emotes'].append(avg_emotes)

    # key:author_id, value:avg_words, total_replies
    df_mod_stats = pd.DataFrame.from_dict(mod_stats)


    # 'Mod message stats'
    fig = px.bar(df_mod_stats, x='username', y='avg_words', barmode='group')
    style_fig(fig, 'Mods: average words per message', '', '', server_name=server_name)
    master_chart.append(('Mods: average words per message', fig))
    users = df_daily_user_messages.author_id.unique()

    # dict with key=author_id, value={first, last}
    users_first_last_active = dict()
    for item in df_daily_user_messages.iloc:
        if item.author_id not in users_first_last_active:
            users_first_last_active[item.author_id] = dict(first=item.datetime_day, last=item.datetime_day)
        else:
            users_first_last_active[item.author_id]['last'] = item.datetime_day

    for author_id in users_first_last_active:
        users_first_last_active[author_id]['active_after'] = users_first_last_active[author_id]['last'] - \
                                                             users_first_last_active[author_id]['first']

    df_users_span = pd.DataFrame.from_dict(users_first_last_active, orient='index')

    # Daily, who intercats with whom?  df_user_interactions
    # columns: datetime_day, author_id, (all) interactions, interacted_with (unique ids, without own author_id)

    n_previous_interacted = 2
    server_channel_ids = df_master_data.channel_id.unique()

    channel_interactions_dfs = []
    for channel_id in server_channel_ids:
        df_channel_data = df_master_data[df_master_data.channel_id == channel_id].sort_values(
            'datetime_time').reset_index(drop=True)
        if df_channel_data.shape[0] < n_previous_interacted:
            continue

        interactions = [df_channel_data.author_id[range(0, i)].tolist() for i in range(0, n_previous_interacted)]
        interactions.extend(
            np.lib.stride_tricks.sliding_window_view(df_channel_data.author_id.values, n_previous_interacted).tolist())
        df_channel_data['interactions'] = interactions[:-1]

        # columns: datetime_day, author_id, interactions (list of repeatable author_ids)
        df_channel_interactions = df_channel_data.groupby(['datetime_day', 'author_id']).agg(
            {'interactions': 'sum'}).reset_index()
        channel_interactions_dfs.append(df_channel_interactions)

    df_user_interactions = pd.concat(channel_interactions_dfs)

    interacted_with = df_user_interactions.interactions.apply(lambda x: np.unique(x).tolist()).tolist()
    for i, author_id in enumerate(df_user_interactions.author_id):
        if author_id in interacted_with[i]:
            interacted_with[i].remove(author_id)

    df_user_interactions['interacted_with'] = interacted_with
    df_user_interactions = df_user_interactions.groupby(['datetime_day', 'author_id']).agg(
        {'interactions': 'sum', 'interacted_with': 'sum'}).reset_index()
    # Drop empty interactions
    df_user_interactions['n_interacted_with'] = df_user_interactions.interacted_with.apply(lambda x: len(x))
    df_user_interactions = df_user_interactions[df_user_interactions.n_interacted_with.apply(lambda x: x > 0)]

    df_user_interactions['username'] = df_user_interactions.author_id.apply(lambda x: dict_author_id_names[x])
    df_user_interactions['ismoderator'] = df_user_interactions.author_id.apply(lambda author_id: author_id in mods)
    # A directed (undirected also ofc) graph view of users and their interactions should be possible at this point

    n_interacted_with_new_user = []
    n_interacted_per_new_user = []
    n_interactions_with_new_user = []
    n_interactions_per_new_user = []
    for item in df_user_interactions.iloc:

        _n_interacted_with_new_user = 0
        _n_interactions_with_new_user = 0
        for user_id in item.interacted_with:
            # Date comparisons can be slow
            if item.datetime_day == df_users_span.loc[user_id]['first']:
                _n_interacted_with_new_user += 1
                _n_interactions_with_new_user += item.interactions.count(user_id)
        # unique new users interacted with
        n_interacted_with_new_user.append(_n_interacted_with_new_user)
        with np.errstate(divide='ignore', invalid='ignore'):
            n_interacted_per_new_user.append(
                _n_interacted_with_new_user / df_daily_users.loc[item.datetime_day].first_time_user_count)
        # interactions with new users
        n_interactions_with_new_user.append(_n_interactions_with_new_user)
        with np.errstate(divide='ignore', invalid='ignore'):
            n_interactions_per_new_user.append(
                _n_interactions_with_new_user / df_daily_users.loc[item.datetime_day].first_time_user_count)

    df_user_interactions['n_interacted_with_new'] = n_interacted_with_new_user
    df_user_interactions['n_interacted_per_new'] = n_interacted_per_new_user
    df_user_interactions['n_interactions_with_new'] = n_interactions_with_new_user
    df_user_interactions['n_interactions_per_new'] = n_interactions_per_new_user

    df_mod_interactions = df_user_interactions[df_user_interactions.ismoderator]

    fig = style_daily_bar(px.bar(df_mod_interactions, x='datetime_day', y='n_interacted_with', color='username'))
    style_fig(fig, 'Unique users interacted with', '', 'unique users', server_name=server_name)
    master_chart.append(('Unique users interacted with', fig))

    fig = style_daily_bar(px.bar(df_mod_interactions, x='datetime_day', y='n_interacted_per_new', color='username'))
    style_fig(fig, 'Mods: % of new users interacted with', '', 'new users (%)', server_name=server_name)
    master_chart.append(('Mods: % of new users interacted with', fig))

    fig = style_daily_bar(px.bar(df_mod_interactions, x='datetime_day', y='n_interactions_per_new', color='username'))
    style_fig(fig, 'Mods: interactions per new user', '', 'interactions per new user', server_name=server_name)
    master_chart.append(('Mods: interactions per new user', fig))

    df_mod_daily_interactions = df_mod_interactions.groupby(['datetime_day', 'author_id']).agg(
        dict(interactions=sum, username=lambda x: x))
    df_mod_daily_interactions['n_interactions'] = [len(interactions) for interactions in
                                                   df_mod_daily_interactions.interactions.values]
    df_mod_daily_interactions = df_mod_daily_interactions.reset_index().set_index('datetime_day')

    fig = style_daily_bar(px.bar(df_mod_daily_interactions, y='n_interactions', color='username'))
    style_fig(fig, 'Mods: Daily messages', '', 'messages', server_name=server_name)
    master_chart.append(('Mods: Daily messages', fig))

    df_allmods_daily_interactions = df_mod_interactions.groupby(['datetime_day']).agg(dict(interactions=sum))
    df_allmods_daily_interactions['n_interactions'] = [len(interactions) for interactions in
                                                       df_allmods_daily_interactions.interactions.values]
    df_allmods_daily_interactions = df_allmods_daily_interactions.reset_index().set_index('datetime_day')

    fig = daily_bar_avg(df_allmods_daily_interactions, y='n_interactions')
    style_fig(fig, 'Mods: Daily messages across all mods', '', 'messages', server_name=server_name)
    master_chart.append(('Mods: Daily messages across all mods', fig))


    # End of figure generation
    print(f'Time elapsed: {time() - time_start:.01f} s.')
    return master_chart

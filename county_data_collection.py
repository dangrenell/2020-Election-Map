# Use islands conda env
import re
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import geopandas as gpd
from datetime import datetime


def logger(func_name, message):
    now = datetime.now()
    with open('log.txt', 'a') as file:
        log_message = f'{now}: "{message}" from "{func_name}\n".'
        file.write(log_message)


def error_logging(function):
    def wrapper(*arg, **kargs):
        try:
            return function(*arg, **kargs)

        except Exception as e:
            logger(function, e)

    return wrapper


def shape_df_maker():
    STATEFP_dict = dict([['31', 'Nebraska'],
                         ['53', 'Washington'],
                         ['35', 'New Mexico'],
                         ['46', 'South Dakota'],
                         ['48', 'Texas'],
                         ['06', 'California'],
                         ['21', 'Kentucky'],
                         ['39', 'Ohio'],
                         ['01', 'Alabama'],
                         ['13', 'Georgia'],
                         ['55', 'Wisconsin'],
                         ['41', 'Oregon'],
                         ['42', 'Pennsylvania'],
                         ['28', 'Mississippi'],
                         ['29', 'Missouri'],
                         ['37', 'North Carolina'],
                         ['40', 'Oklahoma'],
                         ['54', 'West Virginia'],
                         ['36', 'New York'],
                         ['18', 'Indiana'],
                         ['20', 'Kansas'],
                         ['16', 'Idaho'],
                         ['32', 'Nevada'],
                         ['50', 'Vermont'],
                         ['30', 'Montana'],
                         ['27', 'Minnesota'],
                         ['38', 'North Dakota'],
                         ['15', 'Hawaii'],
                         ['04', 'Arizona'],
                         ['10', 'Delaware'],
                         ['44', 'Rhode Island'],
                         ['08', 'Colorado'],
                         ['49', 'Utah'],
                         ['51', 'Virginia'],
                         ['56', 'Wyoming'],
                         ['22', 'Louisiana'],
                         ['26', 'Michigan'],
                         ['25', 'Massachusetts'],
                         ['12', 'Florida'],
                         ['78', 'United States Virgin Islands'],
                         ['09', 'Connecticut'],
                         ['34', 'New Jersey'],
                         ['24', 'Maryland'],
                         ['45', 'South Carolina'],
                         ['23', 'Maine'],
                         ['33', 'New Hampshire'],
                         ['11', 'District of Columbia'],
                         ['66', 'Guam'],
                         ['69', 'Commonwealth of the Northern Mariana Islands'],
                         ['60', 'American Samoa'],
                         ['19', 'Iowa'],
                         ['72', 'Puerto Rico'],
                         ['05', 'Arkansas'],
                         ['47', 'Tennessee'],
                         ['17', 'Illinois'],
                         ['02', 'Alaska']])

    shape_df = gpd.read_file('data/cb_2018_us_county_5m.shp')
    shape_df['State'] = shape_df.apply(
        lambda x: STATEFP_dict[x['STATEFP']], axis=1)
    shape_df = shape_df.drop(['STATEFP', 'COUNTYFP', 'COUNTYNS',
                              'AFFGEOID', 'GEOID', 'LSAD', 'ALAND', 'AWATER'], axis=1)
    shape_df.columns = ['County', 'geometry', 'State']

    return shape_df


def county_df_maker(results):
    table = []
    header = ['County', 'Candidate', 'Margin', '2016 margin',
              'Est. votes reported', 'Total votes', 'Absentee']
    result_list = results[1].find_all('tr')
    result_list = result_list[1:-1]
    for rslt in result_list:
        if 'Biden' in rslt.text:
            index = rslt.text.find('Biden')
            county_name = [rslt.text[:index].strip()]
            county_name.extend(rslt.text[index:].split())
            table.append(county_name)
        elif 'Trump' in rslt.text:
            index = rslt.text.find('Trump')
            county_name = [rslt.text[:index].strip()]
            county_name.extend(rslt.text[index:].split())
            table.append(county_name)
    state_df = pd.DataFrame(table, columns=header)
    state_df = state_df.drop(
        ['2016 margin', 'Absentee', 'Est. votes reported'], axis=1)
    state_df.Margin = state_df.Margin.str[1:].astype('float')
    state_df.Margin = state_df.Margin/100
    state_df['Total votes'] = state_df['Total votes'].str.replace(
        ',', '').astype('int')
    state_df['Biden vote approx'] = state_df.apply(lambda x: x['Total votes'] * (
        0.5 + x['Margin']/2) if x['Candidate'] == 'Biden' else x['Total votes'] * (0.5 - x['Margin']/2), axis=1)
    state_df['Trump vote approx'] = state_df.apply(lambda x: x['Total votes'] * (
        0.5 + x['Margin']/2) if x['Candidate'] == 'Trump' else x['Total votes'] * (0.5 - x['Margin']/2), axis=1)
    state_df['Biden Share'] = state_df['Biden vote approx'] / \
        state_df['Total votes']
    state_df['Trump Share'] = state_df['Trump vote approx'] / \
        state_df['Total votes']
    return state_df


# @error_logging
def df_list_maker():
    state_names = ["Alabama", "Arkansas", "Arizona", "California", "Colorado", "Delaware", "Florida", "Georgia", "Hawaii", "Iowa", "Idaho", "Indiana", "Kansas", "Kentucky", "Louisiana", "Maryland", "Michigan", "Minnesota", "Missouri", "Montana", "North Carolina",
                   "North Dakota", "Nebraska", "New Jersey", "New Mexico", "Nevada", "New York", "Ohio", "Oklahoma", "Oregon", "Pennsylvania", "South Carolina", "South Dakota", "Tennessee", "Texas", "Utah", "Virginia", "Washington", "Wisconsin", "West Virginia", "Wyoming"]
    state_names = [state.lower() for state in state_names]
    state_names = [state.replace(' ', '-') for state in state_names]
    # non_county_states = ["Alaska", "Connecticut", "Illinois", "Massachusetts", "Maine", "Mississippi", "New Hampshire", "Rhode Island", "Vermont"]

    df_list = []

    for state_with_dash in state_names:
        URL = f'https://www.nytimes.com/interactive/2020/11/03/us/elections/results-{state_with_dash}.html?action=click&pgtype=Article&state=default&module=styln-elections-2020&region=TOP_BANNER&context=election_recirc'
        headers = {'User-Agent':
                   'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15'}
        page = requests.get(URL, headers=headers)
        soup = BeautifulSoup(page.content, 'html.parser')
        results = soup.find_all('table')
        print("Success:", state_with_dash)
        df_list.append((state_with_dash.replace(
            '-', ' ').title(), county_df_maker(results)))

    return df_list


@error_logging
def ak_maker():
    state_with_dash = "alaska"
    URL = f'https://www.nytimes.com/interactive/2020/11/03/us/elections/results-{state_with_dash}.html?action=click&pgtype=Article&state=default&module=styln-elections-2020&region=TOP_BANNER&context=election_recirc'
    headers = {'User-Agent':
               'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15'}
    page = requests.get(URL, headers=headers)
    soup = BeautifulSoup(page.content, 'html.parser')
    results = soup.find_all('table')
    print("Success:", state_with_dash)
    table = []
    header = ['County', 'Candidate', 'Margin',
              'Est. votes reported', 'Total votes', 'Absentee']
    result_list = results[1].find_all('tr')
    result_list = result_list[1:-1]
    for rslt in result_list:
        if 'Biden' in rslt.text:
            index = rslt.text.find('Biden')
        elif 'Trump' in rslt.text:
            index = rslt.text.find('Trump')
        county_name = [rslt.text[:index].strip()]
        county_name.extend(rslt.text[index:].split())
        table.append(county_name)
    state_df = pd.DataFrame(table, columns=header)
    state_df = state_df.drop(['Absentee', 'Est. votes reported'], axis=1)
    state_df.Margin = state_df.Margin.str[1:].astype('float')
    state_df.Margin = state_df.Margin/100
    state_df['Total votes'] = state_df['Total votes'].str.replace(
        ',', '').astype('int')
    state_df['Biden vote approx'] = state_df.apply(lambda x: x['Total votes'] * (
        0.5 + x['Margin']/2) if x['Candidate'] == 'Biden' else x['Total votes'] * (0.5 - x['Margin']/2), axis=1)
    state_df['Trump vote approx'] = state_df.apply(lambda x: x['Total votes'] * (
        0.5 + x['Margin']/2) if x['Candidate'] == 'Trump' else x['Total votes'] * (0.5 - x['Margin']/2), axis=1)
    state_df['Biden Share'] = state_df['Biden vote approx'] / \
        state_df['Total votes']
    state_df['Trump Share'] = state_df['Trump vote approx'] / \
        state_df['Total votes']
    state_df['State'] = state_with_dash.title()

    return state_df


@error_logging
def ct_maker():
    state_with_dash = "connecticut"
    URL = f'https://www.nytimes.com/interactive/2020/11/03/us/elections/results-{state_with_dash}.html?action=click&pgtype=Article&state=default&module=styln-elections-2020&region=TOP_BANNER&context=election_recirc'
    headers = {'User-Agent':
               'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15'}
    page = requests.get(URL, headers=headers)
    soup = BeautifulSoup(page.content, 'html.parser')
    results = soup.find_all('table')
    print("Success:", state_with_dash)
    table = []
    header = ['County', 'Candidate', 'Margin',
              'Est. votes reported', 'Total votes', 'Absentee']
    result_list = results[1].find_all('tr')
    result_list = result_list[1:-1]
    for rslt in result_list:
        if 'Biden' in rslt.text:
            index = rslt.text.find('Biden')
        elif 'Trump' in rslt.text:
            index = rslt.text.find('Trump')
        county_name = [rslt.text[:index].strip()]
        county_name.extend(rslt.text[index:].split())
        table.append(county_name)
    state_df = pd.DataFrame(table, columns=header)
    state_df = state_df.drop(['Absentee', 'Est. votes reported'], axis=1)
    state_df.Margin = state_df.Margin.str[1:].astype('float')
    state_df.Margin = state_df.Margin/100
    state_df['Total votes'] = state_df['Total votes'].str.replace(
        ',', '').astype('int')
    state_df['Biden vote approx'] = state_df.apply(lambda x: x['Total votes'] * (
        0.5 + x['Margin']/2) if x['Candidate'] == 'Biden' else x['Total votes'] * (0.5 - x['Margin']/2), axis=1)
    state_df['Trump vote approx'] = state_df.apply(lambda x: x['Total votes'] * (
        0.5 + x['Margin']/2) if x['Candidate'] == 'Trump' else x['Total votes'] * (0.5 - x['Margin']/2), axis=1)
    state_df['Biden Share'] = state_df['Biden vote approx'] / \
        state_df['Total votes']
    state_df['Trump Share'] = state_df['Trump vote approx'] / \
        state_df['Total votes']
    state_df['State'] = state_with_dash.title()

    return state_df


@error_logging
def il_maker():
    state_with_dash = "illinois"
    URL = f'https://www.nytimes.com/interactive/2020/11/03/us/elections/results-{state_with_dash}.html?action=click&pgtype=Article&state=default&module=styln-elections-2020&region=TOP_BANNER&context=election_recirc'
    headers = {'User-Agent':
               'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15'}
    page = requests.get(URL, headers=headers)
    soup = BeautifulSoup(page.content, 'html.parser')
    results = soup.find_all('table')
    print("Success:", state_with_dash)
    table = []
    header = ['County', 'Candidate', 'Margin', '2016 margin',
              'Est. votes reported', 'Total votes', 'Absentee']
    result_list = results[1].find_all('tr')
    result_list = result_list[1:-1]
    for rslt in result_list:
        if 'Biden' in rslt.text:
            index = rslt.text.find('Biden')
        elif 'Trump' in rslt.text:
            index = rslt.text.find('Trump')
        county_name = [rslt.text[:index].strip()]
        county_name.extend(rslt.text[index:].split())
        table.append(county_name)
    state_df = pd.DataFrame(table, columns=header)
    state_df = state_df.drop(
        ['2016 margin', 'Absentee', 'Est. votes reported'], axis=1)
    state_df.Margin = state_df.Margin.str[1:].astype('float')
    state_df.Margin = state_df.Margin/100
    state_df['Total votes'] = state_df['Total votes'].str.replace(
        '—', '0')  # add this to main function and process il normally
    state_df['Total votes'] = state_df['Total votes'].str.replace(
        ',', '').astype('int')
    state_df['Biden vote approx'] = state_df.apply(lambda x: x['Total votes'] * (
        0.5 + x['Margin']/2) if x['Candidate'] == 'Biden' else x['Total votes'] * (0.5 - x['Margin']/2), axis=1)
    state_df['Trump vote approx'] = state_df.apply(lambda x: x['Total votes'] * (
        0.5 + x['Margin']/2) if x['Candidate'] == 'Trump' else x['Total votes'] * (0.5 - x['Margin']/2), axis=1)
    state_df['Biden Share'] = state_df['Biden vote approx'] / \
        state_df['Total votes']
    state_df['Trump Share'] = state_df['Trump vote approx'] / \
        state_df['Total votes']
    state_df['State'] = state_with_dash.title()

    return state_df


@error_logging
def ma_maker():
    state_with_dash = "massachusetts"
    URL = f'https://www.nytimes.com/interactive/2020/11/03/us/elections/results-{state_with_dash}.html?action=click&pgtype=Article&state=default&module=styln-elections-2020&region=TOP_BANNER&context=election_recirc'
    headers = {'User-Agent':
               'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15'}
    page = requests.get(URL, headers=headers)
    soup = BeautifulSoup(page.content, 'html.parser')
    results = soup.find_all('table')
    print("Success:", state_with_dash)
    table = []
    header = ['County', 'Candidate', 'Margin',
              'Est. votes reported', 'Total votes', 'Absentee']
    result_list = results[1].find_all('tr')
    result_list = result_list[1:-1]
    for rslt in result_list:
        if 'Biden' in rslt.text:
            index = rslt.text.find('Biden')
        elif 'Trump' in rslt.text:
            index = rslt.text.find('Trump')
        county_name = [rslt.text[:index].strip()]
        county_name.extend(rslt.text[index:].split())
        table.append(county_name)
    state_df = pd.DataFrame(table, columns=header)
    state_df = state_df.drop(['Absentee', 'Est. votes reported'], axis=1)
    state_df['Margin'] = state_df['Margin'].str.replace('—', '+0')
    state_df.Margin = state_df.Margin.str[1:].astype('float')
    state_df.Margin = state_df.Margin/100
    state_df['Total votes'] = state_df['Total votes'].str.replace(',', '')
    state_df['Total votes'] = state_df['Total votes'].fillna(0).astype('int')
    state_df['Biden vote approx'] = state_df.apply(lambda x: x['Total votes'] * (
        0.5 + x['Margin']/2) if x['Candidate'] == 'Biden' else x['Total votes'] * (0.5 - x['Margin']/2), axis=1)
    state_df['Trump vote approx'] = state_df.apply(lambda x: x['Total votes'] * (
        0.5 + x['Margin']/2) if x['Candidate'] == 'Trump' else x['Total votes'] * (0.5 - x['Margin']/2), axis=1)
    state_df['Biden Share'] = state_df['Biden vote approx'] / \
        state_df['Total votes']
    state_df['Trump Share'] = state_df['Trump vote approx'] / \
        state_df['Total votes']
    state_df['State'] = state_with_dash.title()

    return state_df


@error_logging
def me_maker():
    state_with_dash = "maine"
    URL = f'https://www.nytimes.com/interactive/2020/11/03/us/elections/results-{state_with_dash}.html?action=click&pgtype=Article&state=default&module=styln-elections-2020&region=TOP_BANNER&context=election_recirc'
    headers = {'User-Agent':
               'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15'}
    page = requests.get(URL, headers=headers)
    soup = BeautifulSoup(page.content, 'html.parser')
    results = soup.find_all('table')
    print("Success:", state_with_dash)

    maine_URL = 'https://en.wikipedia.org/wiki/List_of_towns_in_Maine'
    maine_page = requests.get(maine_URL, headers=headers)
    maine_soup = BeautifulSoup(maine_page.content, 'html.parser')
    maine_table = maine_soup.find_all('table')[0]
    trs = maine_table.find_all('tr')
    df_table = []  # ['Town', 'County']
    for tr in trs[1:]:
        tds = tr.find_all('td')
        df_table.append([td.text.strip() for td in tds][:2])
    maine_county_dict = dict(df_table)

    table = []
    header = ['Town', 'Candidate', 'Margin', 'Est. votes reported',
              'Total votes', 'Absentee']  # Using town name for join
    result_list = results[1].find_all('tr')
    result_list = result_list[1:-1]
    # This fix can be applied to the main function (same for MS below)
    for rslt in result_list:
        if 'Biden' in rslt.text:
            index = rslt.text.find('Biden')
            county_name = [rslt.text[:index].strip()]
            county_name.extend(rslt.text[index:].split())
            table.append(county_name)
        elif 'Trump' in rslt.text:
            index = rslt.text.find('Trump')
            county_name = [rslt.text[:index].strip()]
            county_name.extend(rslt.text[index:].split())
            table.append(county_name)
    state_df = pd.DataFrame(table, columns=header)
    state_df = state_df.drop(['Absentee', 'Est. votes reported'], axis=1)
    state_df['Margin'] = state_df['Margin'].str.replace('—', '+0')
    state_df.Margin = state_df.Margin.str[1:].astype('float')
    state_df.Margin = state_df.Margin/100
    state_df['Total votes'] = state_df['Total votes'].str.replace(',', '')
    state_df['Total votes'] = state_df['Total votes'].fillna(0).astype('int')

    state_df['Town'] = state_df.apply(
        lambda x: maine_county_dict[x['Town']] if x['Town'] in maine_county_dict else x['Town'], axis=1)
    state_df.rename(columns={'Town': 'County'}, inplace=True)

    state_df['Biden vote approx'] = state_df.apply(lambda x: x['Total votes'] * (
        0.5 + x['Margin']/2) if x['Candidate'] == 'Biden' else x['Total votes'] * (0.5 - x['Margin']/2), axis=1)
    state_df['Trump vote approx'] = state_df.apply(lambda x: x['Total votes'] * (
        0.5 + x['Margin']/2) if x['Candidate'] == 'Trump' else x['Total votes'] * (0.5 - x['Margin']/2), axis=1)

    state_df = state_df.drop('Candidate', axis=1).groupby(['County']).agg({'Margin': 'mean',
                                                                           'Total votes': 'sum',
                                                                           'Biden vote approx': 'sum',
                                                                           'Trump vote approx': 'sum'})

    state_df['County'] = state_df.index
    state_df['Candidate'] = pd.Series(["Filler" for _ in range(len(state_df))])

    state_df['Biden Share'] = state_df['Biden vote approx'] / \
        state_df['Total votes']
    state_df['Trump Share'] = state_df['Trump vote approx'] / \
        state_df['Total votes']
    state_df['State'] = state_with_dash.title()

    state_df = state_df[['County', 'Candidate', 'Margin', 'Total votes', 'Biden vote approx',
                         'Trump vote approx', 'Biden Share', 'Trump Share', 'State']]

    state_df = state_df.reset_index(drop=True)

    return state_df


@error_logging
def ms_maker():
    state_with_dash = "mississippi"
    URL = f'https://www.nytimes.com/interactive/2020/11/03/us/elections/results-{state_with_dash}.html?action=click&pgtype=Article&state=default&module=styln-elections-2020&region=TOP_BANNER&context=election_recirc'
    headers = {'User-Agent':
               'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15'}
    page = requests.get(URL, headers=headers)
    soup = BeautifulSoup(page.content, 'html.parser')
    results = soup.find_all('table')
    print("Success:", state_with_dash)
    table = []
    header = ['County', 'Candidate', 'Margin', '2016 margin',
              'Est. votes reported', 'Total votes', 'Absentee']
    result_list = results[1].find_all('tr')
    result_list = result_list[1:-1]
    for rslt in result_list:
        if 'Biden' in rslt.text:
            index = rslt.text.find('Biden')
            county_name = [rslt.text[:index].strip()]
            county_name.extend(rslt.text[index:].split())
            table.append(county_name)
        elif 'Trump' in rslt.text:
            index = rslt.text.find('Trump')
            county_name = [rslt.text[:index].strip()]
            county_name.extend(rslt.text[index:].split())
            table.append(county_name)
    state_df = pd.DataFrame(table, columns=header)
    state_df = state_df.drop(
        ['2016 margin', 'Absentee', 'Est. votes reported'], axis=1)
    state_df['Margin'] = state_df['Margin'].str.replace('—', '+0')
    state_df.Margin = state_df.Margin.str[1:].astype('float')
    state_df.Margin = state_df.Margin/100
    state_df['Total votes'] = state_df['Total votes'].str.replace(',', '')
    state_df['Total votes'] = state_df['Total votes'].fillna(0).astype('int')
    state_df['Biden vote approx'] = state_df.apply(lambda x: x['Total votes'] * (
        0.5 + x['Margin']/2) if x['Candidate'] == 'Biden' else x['Total votes'] * (0.5 - x['Margin']/2), axis=1)
    state_df['Trump vote approx'] = state_df.apply(lambda x: x['Total votes'] * (
        0.5 + x['Margin']/2) if x['Candidate'] == 'Trump' else x['Total votes'] * (0.5 - x['Margin']/2), axis=1)
    state_df['Biden Share'] = state_df['Biden vote approx'] / \
        state_df['Total votes']
    state_df['Trump Share'] = state_df['Trump vote approx'] / \
        state_df['Total votes']
    state_df['State'] = state_with_dash.title()

    return state_df


@error_logging
def nh_maker():
    state_with_dash = "new-hampshire"
    URL = f'https://www.nytimes.com/interactive/2020/11/03/us/elections/results-{state_with_dash}.html?action=click&pgtype=Article&state=default&module=styln-elections-2020&region=TOP_BANNER&context=election_recirc'
    headers = {'User-Agent':
               'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15'}
    page = requests.get(URL, headers=headers)
    soup = BeautifulSoup(page.content, 'html.parser')
    results = soup.find_all('table')
    print("Success:", state_with_dash)

    n_hampshire_URL = 'https://en.wikipedia.org/wiki/List_of_cities_and_towns_in_New_Hampshire'
    n_hampshire_page = requests.get(n_hampshire_URL, headers=headers)
    n_hampshire_soup = BeautifulSoup(n_hampshire_page.content, 'html.parser')
    n_hampshire_table = n_hampshire_soup.find_all('table')[0]
    trs = n_hampshire_table.find_all('tr')
    df_table = []  # ['Town', 'County']
    for tr in trs[1:]:
        tds = tr.find_all('td')
        df_table.append([td.text.strip() for td in tds][:2])
    n_hampshire_county_dict = dict(df_table)

    table = []
    header = ['Town', 'Candidate', 'Margin', 'Est. votes reported',
              'Total votes', 'Absentee']  # Using town for join
    result_list = results[1].find_all('tr')
    result_list = result_list[1:-1]
    for rslt in result_list:
        if 'Biden' in rslt.text:
            index = rslt.text.find('Biden')
        elif 'Trump' in rslt.text:
            index = rslt.text.find('Trump')
        county_name = [rslt.text[:index].strip()]
        county_name.extend(rslt.text[index:].split())
        table.append(county_name)
    state_df = pd.DataFrame(table, columns=header)
    state_df = state_df.drop(['Absentee', 'Est. votes reported'], axis=1)
    state_df['Margin'] = state_df['Margin'].str.replace('Tied', '+0')
    state_df['Margin'] = state_df['Margin'].str.replace('—', '+0')
    state_df.Margin = state_df.Margin.str[1:].astype('float')
    state_df.Margin = state_df.Margin/100
    state_df['Total votes'] = state_df['Total votes'].str.replace(',', '')
    state_df['Total votes'] = state_df['Total votes'].fillna(0).astype('int')

    state_df['Town'] = state_df.apply(lambda x: n_hampshire_county_dict[x['Town']]
                                      if x['Town'] in n_hampshire_county_dict else x['Town'], axis=1)
    state_df.rename(columns={'Town': 'County'}, inplace=True)

    state_df['Biden vote approx'] = state_df.apply(lambda x: x['Total votes'] * (
        0.5 + x['Margin']/2) if x['Candidate'] == 'Biden' else x['Total votes'] * (0.5 - x['Margin']/2), axis=1)
    state_df['Trump vote approx'] = state_df.apply(lambda x: x['Total votes'] * (
        0.5 + x['Margin']/2) if x['Candidate'] == 'Trump' else x['Total votes'] * (0.5 - x['Margin']/2), axis=1)

    state_df = state_df.drop('Candidate', axis=1).groupby(['County']).agg({'Margin': 'mean',
                                                                           'Total votes': 'sum',
                                                                           'Biden vote approx': 'sum',
                                                                           'Trump vote approx': 'sum'})

    state_df['County'] = state_df.index
    state_df['Candidate'] = pd.Series(["Filler" for _ in range(len(state_df))])

    state_df['Biden Share'] = state_df['Biden vote approx'] / \
        state_df['Total votes']
    state_df['Trump Share'] = state_df['Trump vote approx'] / \
        state_df['Total votes']
    state_df['State'] = state_with_dash.replace('-', ' ').title()

    state_df = state_df[['County', 'Candidate', 'Margin', 'Total votes', 'Biden vote approx',
                         'Trump vote approx', 'Biden Share', 'Trump Share', 'State']]

    state_df = state_df.reset_index(drop=True)

    return state_df


@error_logging
def ri_maker():
    state_with_dash = "rhode-island"
    URL = f'https://www.nytimes.com/interactive/2020/11/03/us/elections/results-{state_with_dash}.html?action=click&pgtype=Article&state=default&module=styln-elections-2020&region=TOP_BANNER&context=election_recirc'
    headers = {'User-Agent':
               'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15'}
    page = requests.get(URL, headers=headers)
    soup = BeautifulSoup(page.content, 'html.parser')
    results = soup.find_all('table')
    print("Success:", state_with_dash)
    table = []
    header = ['County', 'Candidate', 'Margin',
              'Est. votes reported', 'Total votes', 'Absentee']
    result_list = results[1].find_all('tr')
    result_list = result_list[1:-1]
    for rslt in result_list:
        if 'Biden' in rslt.text:
            index = rslt.text.find('Biden')
        elif 'Trump' in rslt.text:
            index = rslt.text.find('Trump')
        county_name = [rslt.text[:index].strip()]
        county_name.extend(rslt.text[index:].split())
        table.append(county_name)
    state_df = pd.DataFrame(table, columns=header)
    state_df = state_df.drop(['Absentee', 'Est. votes reported'], axis=1)
    state_df['Margin'] = state_df['Margin'].str.replace('Tied', '+0')
    state_df['Margin'] = state_df['Margin'].str.replace('—', '+0')
    state_df['Margin'] = state_df['Margin'].str.replace('>', '')
    state_df['Margin'] = state_df['Margin'].str.replace('%', '')
    state_df.Margin = state_df.Margin.str[1:].astype('float')
    state_df.Margin = state_df.Margin/100
    state_df['Total votes'] = state_df['Total votes'].str.replace(',', '')
    state_df['Total votes'] = state_df['Total votes'].str.replace('—', '0')
    state_df['Total votes'] = state_df['Total votes'].fillna(0).astype('int')
    state_df['Biden vote approx'] = state_df.apply(lambda x: x['Total votes'] * (
        0.5 + x['Margin']/2) if x['Candidate'] == 'Biden' else x['Total votes'] * (0.5 - x['Margin']/2), axis=1)
    state_df['Trump vote approx'] = state_df.apply(lambda x: x['Total votes'] * (
        0.5 + x['Margin']/2) if x['Candidate'] == 'Trump' else x['Total votes'] * (0.5 - x['Margin']/2), axis=1)
    state_df['Biden Share'] = state_df['Biden vote approx'] / \
        state_df['Total votes']
    state_df['Trump Share'] = state_df['Trump vote approx'] / \
        state_df['Total votes']
    state_df['State'] = state_with_dash.replace('-', ' ').title()

    return state_df


@error_logging
def vt_maker():
    state_with_dash = "vermont"
    URL = f'https://www.nytimes.com/interactive/2020/11/03/us/elections/results-{state_with_dash}.html?action=click&pgtype=Article&state=default&module=styln-elections-2020&region=TOP_BANNER&context=election_recirc'
    headers = {'User-Agent':
               'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15'}
    page = requests.get(URL, headers=headers)
    soup = BeautifulSoup(page.content, 'html.parser')
    results = soup.find_all('table')
    print("Success:", state_with_dash)

    vermont_URL = 'https://en.wikipedia.org/wiki/List_of_towns_in_Vermont'
    vermont_page = requests.get(vermont_URL, headers=headers)
    vermont_soup = BeautifulSoup(vermont_page.content, 'html.parser')
    vermont_table = vermont_soup.find_all('table')[0]
    trs = vermont_table.find_all('tr')
    df_table = []  # ['Town', 'County']
    for tr in trs[1:]:
        tds = tr.find_all('td')
        df_table.append([td.text.strip() for td in tds][1:3])
    vermont_county_dict = dict(df_table)

    table = []
    header = ['Town', 'Candidate', 'Margin', 'Est. votes reported',
              'Total votes', 'Absentee']  # Using town for join
    result_list = results[1].find_all('tr')
    result_list = result_list[1:-1]
    for rslt in result_list:
        if 'Biden' in rslt.text:
            index = rslt.text.find('Biden')
            county_name = [rslt.text[:index].strip()]
            county_name.extend(rslt.text[index:].split())
            table.append(county_name)
        elif 'Trump' in rslt.text:
            index = rslt.text.find('Trump')
            county_name = [rslt.text[:index].strip()]
            county_name.extend(rslt.text[index:].split())
            table.append(county_name)
    state_df = pd.DataFrame(table, columns=header)
    state_df = state_df.drop(['Absentee', 'Est. votes reported'], axis=1)
    state_df['Margin'] = state_df['Margin'].str.replace('—', '+0')
    state_df.Margin = state_df.Margin.str[1:].astype('float')
    state_df.Margin = state_df.Margin/100
    state_df['Total votes'] = state_df['Total votes'].str.replace(',', '')
    state_df['Total votes'] = state_df['Total votes'].fillna(0).astype('int')

    state_df['Town'] = state_df.apply(
        lambda x: vermont_county_dict[x['Town']] if x['Town'] in vermont_county_dict else x['Town'], axis=1)
    state_df.rename(columns={'Town': 'County'}, inplace=True)

    state_df['Biden vote approx'] = state_df.apply(lambda x: x['Total votes'] * (
        0.5 + x['Margin']/2) if x['Candidate'] == 'Biden' else x['Total votes'] * (0.5 - x['Margin']/2), axis=1)
    state_df['Trump vote approx'] = state_df.apply(lambda x: x['Total votes'] * (
        0.5 + x['Margin']/2) if x['Candidate'] == 'Trump' else x['Total votes'] * (0.5 - x['Margin']/2), axis=1)

    state_df = state_df.drop('Candidate', axis=1).groupby(['County']).agg({'Margin': 'mean',
                                                                           'Total votes': 'sum',
                                                                           'Biden vote approx': 'sum',
                                                                           'Trump vote approx': 'sum'})

    state_df['County'] = state_df.index
    state_df['Candidate'] = pd.Series(["Filler" for _ in range(len(state_df))])

    state_df['Biden Share'] = state_df['Biden vote approx'] / \
        state_df['Total votes']
    state_df['Trump Share'] = state_df['Trump vote approx'] / \
        state_df['Total votes']
    state_df['State'] = state_with_dash.replace('-', ' ').title()

    state_df = state_df[['County', 'Candidate', 'Margin', 'Total votes', 'Biden vote approx',
                         'Trump vote approx', 'Biden Share', 'Trump Share', 'State']]

    state_df = state_df.reset_index(drop=True)

    state_df['State'] = state_with_dash.title()

    return state_df


def main():
    # shape_df = shape_df_maker()
    df_list = df_list_maker()
    ak_df = ak_maker()
    ct_df = ct_maker()
    il_df = il_maker()
    ma_df = ma_maker()
    me_df = me_maker()
    ms_df = ms_maker()
    nh_df = nh_maker()
    ri_df = ri_maker()
    vt_df = vt_maker()

    fixed_states = [ak_df, ct_df, il_df, ma_df,
                    me_df, ms_df, nh_df, ri_df, vt_df]

    for tpl in df_list:
        tpl[1]['State'] = tpl[0].title()

    full_df_list = [tpl[1] for tpl in df_list] + fixed_states

    all_state_df = pd.concat(full_df_list)
    upper_fence = np.quantile(all_state_df['Total votes'], .75) + 1.5*(np.quantile(
        all_state_df['Total votes'], .75) - np.quantile(all_state_df['Total votes'], .25))
    all_state_df['Relative Vote Total'] = all_state_df['Total votes']/upper_fence
    all_state_df['Relative Vote Total'] = all_state_df['Relative Vote Total'].apply(
        lambda x: min(1, x))
    all_state_df['b'] = all_state_df.apply(lambda x: x['Biden Share'], axis=1)
    all_state_df['r'] = all_state_df.apply(lambda x: x['Trump Share'], axis=1)
    all_state_df['g'] = all_state_df.apply(
        lambda x: min(x['b'], x['r']), axis=1)
    all_state_df['rgb'] = all_state_df.apply(
        lambda x: (x['r'], x['g'], x['b']), axis=1)
    all_state_df['rgb'] = all_state_df.apply(lambda x: (
        x['r'], x['g'], x['b'], x['Relative Vote Total']), axis=1)

    county_correction_dict = {('New York', 'Brooklyn'): 'Kings',
                              ('New York', 'Staten Island'): 'Richmond',
                              ('New York', 'Manhattan'): 'New York'}

    all_state_df['County'] = all_state_df.apply(lambda x: county_correction_dict[(
        x['State'], x['County'])] if (x['State'], x['County']) in county_correction_dict else x, axis=1)

    all_state_df = all_state_df.dropna(
        subset=['Biden Share', 'Trump Share', 'b', 'r', 'g', 'rgb'])

    all_state_df.to_csv('County level data.csv')

    # one_df = shape_df.merge(all_state_df)
    # # hi_df = one_df[one_df['State'] == 'Hawaii']
    # one_df = one_df[one_df['State'] != 'Hawaii']

    # one_df.to_csv('County level data.csv')


if __name__ == '__main__':
    main()

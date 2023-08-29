import requests
import datetime
from bs4 import BeautifulSoup
from loguru import logger
from collections import Counter
import pandas as pd
import json
import streamlit as st

def main():
    st.write("# Sitemap Analyzer")
    with st.form(key='my_form'):
        sitemap_url = st.text_input(label='Enter the Sitemap URL')
        submit_button = st.form_submit_button(label='Submit')

    if submit_button:
        if not sitemap_url:
            st.error("Sitemap Url is blank.")
            st.stop()
        with st.spinner("Scrapping ..."):
            response = requests.get(sitemap_url)

            soup = BeautifulSoup(response.content, 'xml')
            sitemaps = soup.find_all('sitemap')
            data = {}
            flag = True
            for sitemap in sitemaps:
                flag = False
                sub_sitemap_url = sitemap.find('loc').text
                sub_response = requests.get(sub_sitemap_url)
                sub_soup = BeautifulSoup(sub_response.content, 'xml')
                urls = sub_soup.find_all('url')
                for url in urls:
                    loc = url.find('loc').text
                    lastmod = None
                    if url.find('lastmod') is not None:
                        lastmod = url.find('lastmod').text
                    data[loc] = lastmod
            if flag: 
                urls = soup.find_all('url')
                for url in urls:
                    loc = url.find('loc').text
                    lastmod = None
                    if url.find('lastmod') is not None:
                        lastmod = url.find('lastmod').text
                    data[loc] = lastmod

            # Convert the dates to datetime and count the number of posts per day
            post_dates = None
            try:
                post_dates = [datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%S+00:00") for date in data.values() if date is not None]
            except Exception as ex:
                logger.error(ex)
            if not post_dates:
                post_dates = [datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%S%z") for date in data.values() if date is not None]
            post_counts = Counter([date.date() for date in post_dates])

            # Prepare data for the table
            dates = sorted(post_counts.keys(), reverse=True)
            counts = [post_counts[date] for date in dates]

            # Create a DataFrame with dates and counts
            table_data = {'Dates': dates, 'Counts': counts}
            df = pd.DataFrame(table_data)
            df['Dates'] = pd.to_datetime(df['Dates'])
            # Group by month and plot a bar chart for each month
            df['Month'] = df['Dates'].dt.to_period('M')
            # Sort DataFrame in reverse order
            df['Dates'] = df['Dates'].astype('str')
            df = df.sort_values(by='Dates', ascending=False)
            for month, group in df.groupby('Month', sort=False):
                group = group.drop(columns=['Month'])
                st.title(month.strftime("%B, %Y"))
                st.bar_chart(group.set_index('Dates'))
                # Calculate and display the highest and lowest post counts for the month
                highest_post_count = group['Counts'].max()
                lowest_post_count = group['Counts'].min()
                average_post_count = round(group['Counts'].mean())
                total_by_month_post_count = group['Counts'].sum()
                c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
                c1.write(f'Highest: {highest_post_count}')
                c2.write(f'Lowest: {lowest_post_count}')
                c3.write(f'Avg: {average_post_count}')
                c4.write(f'Total: {total_by_month_post_count}')

if __name__ == '__main__':
    main()
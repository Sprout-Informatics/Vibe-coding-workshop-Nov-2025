!pip install yfinance

import yfinance as yf
import pandas as pd
import altair as alt
from datetime import datetime, timedelta

aapl_data = yf.download('AAPL', period='10y', interval='1mo')

# Handle the MultiIndex columns by dropping the top level
aapl_data.columns = aapl_data.columns.droplevel(1)
aapl_data = aapl_data.reset_index()

aapl_data.columns = ['date', 'close', 'high', 'low', 'open', 'volume']

aapl_data['MA50'] = aapl_data['close'].rolling(window=20).mean()
aapl_data['MA100'] = aapl_data['close'].rolling(window=40).mean()
aapl_data['MA50_std'] = aapl_data['close'].rolling(window=20).std()
aapl_data['MA100_std'] = aapl_data['close'].rolling(window=40).std()
aapl_data['MA50_upper'] = aapl_data['MA50'] + aapl_data['MA50_std']
aapl_data['MA50_lower'] = aapl_data['MA50'] - aapl_data['MA50_std']
aapl_data['MA100_upper'] = aapl_data['MA100'] + aapl_data['MA100_std']
aapl_data['MA100_lower'] = aapl_data['MA100'] - aapl_data['MA100_std']

# Filter out rows with NaN values in moving average columns
aapl_data_filtered = aapl_data.dropna(subset=['MA50', 'MA100', 'MA50_upper', 'MA50_lower', 'MA100_upper', 'MA100_lower'])

# Calculate the date 5 years ago from the most recent date in the data
end_date = aapl_data_filtered['date'].max()
start_date = end_date - timedelta(days=5*365) # Approximate 5 years

base = alt.Chart(aapl_data_filtered).encode(
    x=alt.X('date:T', axis=alt.Axis(format='%Y-%m', title='Date'), scale=alt.Scale(domain=[start_date, end_date])) # Set x-axis limits
)

# Modify colors and stroke widths for garish effect
rule = base.mark_rule().encode(
    y=alt.Y('low', title='Price'),
    y2='high',
    color=alt.condition("datum.open < datum.close", alt.value("lime"), alt.value("fuchsia"), legend=alt.Legend(title="Price Change")) # More vibrant colors
)

bar = base.mark_bar().encode(
    y='open',
    y2='close',
    color=alt.condition("datum.open < datum.close", alt.value("lime"), alt.value("fuchsia")), # Matching vibrant colors
    opacity=alt.value(0.9) # Increase opacity
)

ma50_line = base.mark_line(color='yellow', strokeWidth=5).encode( # Thick yellow line
    y='MA50',
    tooltip=['date:T', 'MA50']
)

ma100_line = base.mark_line(color='aqua', strokeWidth=5).encode( # Thick aqua line
    y='MA100',
    tooltip=['date:T', 'MA100']
)

ma50_band = base.mark_area(opacity=0.6, color='red').encode( # More opaque red band
    y='MA50_lower',
    y2='MA50_upper',
    tooltip=['date:T', 'MA50_lower', 'MA50_upper']
)

ma100_band = base.mark_area(opacity=0.6, color='blue').encode( # More opaque blue band
    y='MA100_lower',
    y2='MA100_upper',
    tooltip=['date:T', 'MA100_lower', 'MA100_upper']
)

candlestick_chart = rule + bar
combined_chart = candlestick_chart + ma50_line + ma100_line + ma50_band + ma100_band

# Add a garish title and interactivity
combined_chart = combined_chart.properties(
    title='AAPL Garish Stock Performance (Last 5 Years)'
).interactive()

combined_chart

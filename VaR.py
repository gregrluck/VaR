# from https://towardsdatascience.com/learn-to-calculate-your-portfolios-value-at-risk-e1e2c5c68456
import scipy
import scipy.stats
from tiingo import TiingoClient
import pandas as pd, datetime, numpy as np
import matplotlib.pyplot as plt
import warnings

warnings.filterwarnings('ignore')  # Tiingo API is returning a warning due to an upcoming pandas update

# #User Set Up
data = {'Stocks': ['GOOGL', 'TSLA', 'AAPL'], 'Quantity': [100, 50, 300]}  # Define your holdings
ScenariosNo = 500  # Define the number of scenarios you want to run
Percentile = 99  # Define your confidence interval
VarDaysHorizon = 1  # Define your time period

# Logging
info = 1  # 1 if you want more info returned by the script

# Create a DataFrame of holdings
df = pd.DataFrame(data)
print('[INFO] Calculating the max amount of money the portfolio will lose within', VarDaysHorizon, 'days', Percentile,
      'percent of the time.')
today = datetime.date.today() - datetime.timedelta(days=1)


def is_business_day(date):
    return bool(len(pd.bdate_range(date, date)))


def dateforNoOfScenarios(date):
    i = 0
    w = 0
    while i < ScenariosNo:
        if (is_business_day(today - datetime.timedelta(days=w)) == True):
            i = i + 1
            w = w + 1
        else:
            w = w + 1
            continue
    # print('gotta go back these many business days',i)
    # print('gotta go back these many days',w)
    # remember to add an extra day (days +1 = scenario numbers)
    return (today - datetime.timedelta(
        days=w * 1.04 + 1))  # 4% is an arbitrary number i've calculated the holidays to be in 500days.


def SourceHistoricPrices():
    if info == 1: print('[INFO] Fetching stock prices for portfolio holdings')

    # Set Up for Tiingo
    config = {}
    config['session'] = True
    config['api_key'] = '<insert API Key from Tiingo>'
    client = TiingoClient(config)
    # Create a list of tickers for the API call
    Tickers = []
    i = 0
    for ticker in data:
        while i <= len(data):
            Tickers.append(data[ticker][i])
            i = i + 1
    if info == 1: print('[INFO] Portfolio Holdings determined as', Tickers)
    if info == 1: print('[INFO] Portfolio Weights determined as', data['Quantity'])

    # Call the API and store the data
    global HistData
    startDate = dateforNoOfScenarios(today)
    endDate = today
    HistData = client.get_dataframe(Tickers, startDate, endDate, metric_name='close')
    print(HistData.size)
    if info == 1: print('[INFO] Fetching stock prices completed.', len(HistData), 'days.')
    return (HistData)


def ValuePortfolio():
    HistData['PortValue'] = 0
    i = 0
    if info == 1: print('[INFO] Calculating the portfolio value for each day')
    while i <= len(data):
        stock = data['Stocks'][i]
        quantity = data['Quantity'][i]
        HistData['PortValue'] = HistData[stock] * quantity + HistData['PortValue']
        i = i + 1


def CalculateVaR():
    if info == 1: print('[INFO] Calculating Daily % Changes')

    # calculating percentage change
    HistData['Perc_Change'] = HistData['PortValue'].pct_change()
    # calculate money change based on current valuation
    HistData['DollarChange'] = HistData.loc[HistData.index.max()]['PortValue'] * HistData['Perc_Change']
    if info == 1: print('[INFO] Picking', round(HistData.loc[HistData.index.max()]['PortValue'], 2), ' value from ',
                        HistData.index.max().strftime('%Y-%m-%d'),
                        ' as the latest valuation to base the monetary returns')
    ValueLocForPercentile = round(len(HistData) * (1 - (Percentile / 100)))
    if info == 1: print('[INFO] Picking the', ValueLocForPercentile, 'th highest value')
    global SortedHistData
    SortedHistData = HistData.sort_values(by=['DollarChange'])
    if info == 1: print('[INFO] Sorting the results by highest max loss')
    VaR_Result = SortedHistData.iloc[ValueLocForPercentile + 1, len(SortedHistData.columns) - 1] * np.sqrt(
        VarDaysHorizon)
    print('The portfolio\'s VaR is:', round(VaR_Result, 2))

def CalculateES():
    ValueLocForPercentile = round(len(HistData) * (1 - (Percentile / 100)))
    ES_Result = round(SortedHistData['DollarChange'].head(ValueLocForPercentile).mean(axis=0), 2) * np.sqrt(
        VarDaysHorizon)
    print('The portfolios\'s Expected Shortfall is', ES_Result)

def plotme():
    data1 = HistData['Perc_Change']
    num_bins = 50

    # the histogram of the data
    n, bins, patches = plt.hist(data1, num_bins, normed=1, facecolor='green', alpha=0.5)

    # add a 'best fit' line
    sigma = HistData['Perc_Change'].std()
    data2 = scipy.stats.norm.pdf(bins, 0, sigma)
    plt.plot(bins, data2, 'r--')
    plt.xlabel('Percentage Change')
    plt.ylabel('Probability/Frequency')

    # Tweak spacing to prevent clipping of ylabel
    plt.subplots_adjust(left=0.15)
    plt.show()


# Run the program
SourceHistoricPrices()
ValuePortfolio()
CalculateVaR()
CalculateES()
plotme()

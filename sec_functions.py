import pandas as pd
import requests
from headers import headers

headers = {"User-Agent": "trial.keshav@gmail.com"}

def cik_matching_ticker (ticker, headers=headers):
    ticker = ticker.upper().replace(".", "-")
    ticker_json = requests.get("https://www.sec.gov/files/company_tickers.json", headers=headers).json()

    for company in ticker_json.values():
        if company["ticker"] == ticker:
            cik = str(company["cik_str"]).zfill(10)
            return cik
    raise ValueError(f"Ticker {ticker} not found in SEC database")

def get_submission_data(ticker, headers=headers, only_filings_df=False):
    cik = sf.cik_matching_ticker(ticker)
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    company_json=requests.get(url, headers=headers).json()
    if only_filings_df:
        return pd.DataFrame(company_json['filings']['recent'])
    return company_json

def get_filtered_filings(ticker, ten_k=True, just_acession_numbers=False, headers=headers):
    company_filings_df = get_submission_data(ticker, only_filings_df=True, headers=headers)
    if ten_k:
        df = company_filings_df[company_filings_df['form'] == "10-K"]
    else:
        df = company_filings_df[company_filings_df['form'] == "10-Q"]
    if just_acession_numbers:
        df = df.set_index['reportDate']
        accession_df = df['accessionNumber']
        return accession_df
    else:
        return df
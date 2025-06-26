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
    
def get_facts(ticker, headers=headers):
    cik = sf.cik_matching_ticker(ticker)
    url = f"http://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    company_facts = requests.get(url, headers=headers).json()
    return company_facts

def facts_DF(ticker, headers=headers):
    facts = get_facts(ticker, headers)
    us_gaap_data = facts["facts"]["us-gaap"]            #this is not just one year or one filing, this is all the data and there are two categories under facts - dei and us-gaap. You can check the relevant tags on edgar
    df_data = []

    for fact, details in us_gaap_data.items():
        for unit in details["units"]:
            for item in details["units"][unit]:
                row = item.copy()
                row["fact"] = fact
                df_data.append(row)

    df = pd.DataFrame(df_data)
    df["end"] = pd.to_datetime(df["end"])
    df["start"] = pd.to_datetime(df["start"])
    df = df.drop_duplicates(subset=["fact", "end", "val"])    #to remove any duplicates from mutliple forms like 8K etc.
    df.set_index("end", inplace=True)
    labels_dict = {fact: details["label"] for fact, details in us_gaap_data.items()}
    return df, labels_dict

def annual_facts(ticker, headers=headers):
    accession_nums = sf.get_filtered_filings(ticker, ten_k=True, just_acession_numbers=True)
    df, label_dict = facts_DF(ticker, headers)
    ten_k = df[df["accn"].isin(accession_nums)]
    ten_k = ten_k[ten_k.index.isin(accession_nums.index)]
    pivot = ten_k.pivot_table(values="val", columns="fact", index="end")
    pivot.rename(columns=label_dict, inplace=True)
    return pivot.T
import pandas as pd


def clean_nipa_data(_save: bool = False) -> pd.DataFrame:
    """
    Cleans the NIPA data used in Aizcorbe's example 2.1

    Parameters
    ----------
    _save: bool, defaults to 'False'
        whether to save the output to the silver folder

    Returns
    -------
    pd.DataFrame
        Dataframe of cleaned data akin to what is used for PriceIndexCalc
    """
    # import the expenditure and prices data
    try:
        df_expenditures = pd.read_csv("data/bronze/2000-2010 US NIPA data - nominal spending.csv")
        df_price_indices = pd.read_csv("data/bronze/2000-2010 US NIPA data - price indexes.csv")
    except Exception as e:
        raise FileNotFoundError("Could not find the data in the path: {}".format(e))

    # clean and massage these datasets
    df_expenditure_new = df_expenditures.melt(id_vars=['Years'], var_name='product_name', value_name='spending')
    df_price_new = df_price_indices.melt(id_vars=['Years'], var_name='product_name', value_name='index')
    
    # merge the two together
    df_merged = pd.merge(df_expenditure_new, df_price_new, on=['product_name','Years'], how='inner')#.drop('Years_y', axis='columns')
    df_merged.rename(columns={"spending":"quantity", "index":"price", "product_name":"id"}, inplace=True)

    # save if needed
    if _save == True:
        df_merged.to_csv("data/silver/NIPA_ard.csv")

    # return the dataframe
    return df_merged



if __name__ == "__main__":
    df = clean_nipa_data(True)
    print(df.head())
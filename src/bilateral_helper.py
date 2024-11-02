from typing import Sequence, Optional, Union, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import seaborn as sns

from PriceIndexCalc.pandas_modules.bilateral import *

def bilateral_methods(
    df: pd.DataFrame,
    price_col: str = 'price',
    quantity_col: str = 'quantity',
    product_id_col: str='id',
    date_col: str='month',
    # groups: Optional[Sequence[str]] = None,
    method: str = 'tornqvist',
    base_month: Union[int, str] = 1,
    reference_month: Union[int, str] = 1,
    plot: bool = False,
) -> pd.DataFrame:
    """
    Calculate all the bilateral indices.

    Parameters
    ----------
    df: pandas DataFrame
        Contains price and quantity columns, a time series column, and a product
        ID column as a minimum. A characteristics column should also be present
        for hedonic methods.
    price_col: str, defaults to 'price'
        User-defined name for the price column.
    quantity_col: str, defaults to 'quantity'
        User-defined name for the quantity column.
    product_id_col: str, defaults to 'id'
        User-defined name for the product ID column.
    date_col: str, defaults to 'month'
        User-defined name for the date column.
    # groups: list of str, defaults to None
    #     The names of the groups columns.
    method: str, defaults to 'tornqvist'
        Options: {'carli', 'jevons', 'dutot', 'laspeyres', 'paasche',
        'geom_laspeyres', 'geom_paasche', 'drobish', 'marshall_edgeworth',
        'palgrave', 'fisher', 'tornqvist', 'walsh', 'sato_vartia', 'lowe',
        'geary_khamis_b', 'tpd', 'rothwell'}

        The bilateral method to use.
    base_month: int or str, defaults to 1
        Integer or string specifying the base month. An integer specifies the
        position while a string species the month in the format 'YYYY-MM'.
    reference_month: int or str, defaults to 1
        Integer or string specifying the reference month for rebasing if
        different from the base month. An integer specifies the position while a
        string species the month in the format 'YYYY-MM'.
    plot: bool, defaults to False
        Boolean parameter on whether to plot the resulting timeseries for price
        indices.

    Returns
    -------
    pd.DataFrame
        Dataframe containing the timeseries and index values.
    """
    method = method.lower()

    valid_bilateral_methods = {
        'carli', 'jevons', 'dutot', 'laspeyres', 'lowe',
        'paasche', 'geom_laspeyres', 'geom_paasche', 'drobish',
        'marshall_edgeworth', 'palgrave', 'fisher', 'tornqvist',
        'walsh', 'sato_vartia', 'geary_khamis_b', 'tpd', 'rothwell'
    }

    if method not in valid_bilateral_methods:
        raise ValueError("Invalid option, please select a valid bilateral method.")

    args = (price_col, quantity_col, product_id_col, date_col)

    periods = sorted(df[date_col].unique())
    no_of_periods = len(periods)

    if isinstance(base_month, str):
        base_month = periods.index(base_month) + 1

    if isinstance(reference_month, str):
        reference_month = periods.index(reference_month) + 1

    # Obtain the base period in the dataframe.
    base_period = periods[base_month-1]

    # Determine product IDs present in the base period.
    df_base_master = df.loc[df[date_col] == base_period]
    keep_ids = df_base_master.loc[:, product_id_col].unique()

    # Filter df to remove product IDs not present in the base period.
    df = df[df[product_id_col].isin(keep_ids)].reset_index(drop=True)

    # if groups:
    #     return (
    #         df
    #         .groupby(groups)
    #         .apply(
    #                 lambda df_group: bilateral_methods(
    #                     df_group,
    #                     *args,
    #                     method=method,
    #                     base_month=base_month,
    #                     reference_month=reference_month,
    #                     plot=plot,
    #                 )
    #         )
    #         .reset_index()
    #         .rename({'level_1': 'month'}, axis=1)
    #     )

    index_vals = np.zeros(no_of_periods)

    df_by_period = {
        period: df.loc[df[date_col] == period] 
        for period in periods
    }

    return df_by_period

    # with ThreadPoolExecutor(no_of_periods) as executor:
    #     futures = [
    #         executor.submit(
    #             compute_bilateral, 
    #             df_by_period, 
    #             periods, 
    #             base_month-1, 
    #             j, 
    #             method, 
    #             *args
    #         )
    #         for j in range(no_of_periods)
    #     ]
    #     for future in as_completed(futures):
    #         i, j, result  = future.result()
    #         index_vals[j] = result

    # output_df = (
    #     pd.DataFrame(
    #         index_vals,
    #         index=periods
    #     )
    #     .rename({0: 'index_value'}, axis=1)
    # )
    # output_df.sort_index(inplace=True)
    # if base_month != reference_month:
    #     # Rebase the index values to the reference month.
    #     output_df = output_df / output_df.iloc[reference_month-1]
    # if plot:
    #     sns.set(rc={'figure.figsize':(11, 4)})
    #     (output_df * 100).plot(linewidth=2)
    # return output_df


def compute_bilateral(
        df_by_period: Dict,
        periods: Sequence,
        i: int,
        j: int,
        bilateral_method: str,
        price_col: str = 'price',
        quantity_col : str = 'quantity',
        product_id_col: str = 'id',
        date_col: str = 'month'
) -> Tuple:
    """
    Compute bilateral indices for a given pair of periods.

    Parameters
    ----------
    df_by_period : Dict
        Dictionary of dataframes by period.
    periods : Sequence
        Sequence of periods.
    i : int
        Index of first period.
    j : int
        Index of second period.
    bilateral_method : str
        Name of the bilateral method.
    price_col : str, optional
        Name of the column containing the price information.
    quantity_col : str, optional
        Name of the column containing the quantity information.
    product_id_col : str, optional
        Name of the column containing the product id information.
    """
    df_base = df_by_period[periods[i]]
    df_curr = df_by_period[periods[j]]

    common_products = (
        set(df_base[product_id_col])
        .intersection(set(df_curr[product_id_col]))
    )

    df_base = df_base[df_base[product_id_col].isin(common_products)]
    df_curr = df_curr[df_curr[product_id_col].isin(common_products)]

    if bilateral_method == 'tpd':
        df_matched = pd.concat([df_base, df_curr]).drop_duplicates()
        df_matched = _weights_calc(df_matched)
        return i, j, time_dummy(df_matched)[-1]
    else:
        bilateral_func = globals()[bilateral_method]
        p_base = df_base[price_col].values
        p_curr = df_curr[price_col].values
        data = (p_base, p_curr)

        if bilateral_method in {
            'laspeyres', 
            'paasche', 
            'geom_laspeyres', 
            'geom_paasche', 
            'tornqvist', 
            'fisher', 
            'lowe'
        }:
            q_base = df_base[quantity_col].values
            data += (q_base,)

        if bilateral_method in {
            'paasche', 
            'geom_paasche', 
            'drobish', 
            'marshall_edgeworth', 
            'tornqvist', 
            'fisher', 
        }:
            q_curr = df_curr[quantity_col].values
            data += (q_curr,)

        return i, j, bilateral_func(*data)


if __name__ == "__main__":
    df = pd.read_csv("./data/silver/NIPA_ard_targeted.csv")
    print(df.head())

    df_output = bilateral_methods(
        df, 
        price_col='price',
        quantity_col='quantity',
        product_id_col='id',
        date_col='Years',
        method='laspeyres',
        plot=True
    )
    print(df_output)
    df_output[0]
    df_output[1]
from tzlocal import get_localzone
import pandas as pd

from communications.constants import COMMUNICATIONS_FILE_NAME


def get_data() -> pd.DataFrame:

    df = pd.read_csv(f'downloads/{COMMUNICATIONS_FILE_NAME}.csv')

    df.fillna('-', inplace=True)

    local_tz = get_localzone()
    df['Data Atualização'] = pd.to_datetime(df['Data Atualização']).dt.tz_localize(local_tz).dt.tz_convert('America/Sao_Paulo')

    return df

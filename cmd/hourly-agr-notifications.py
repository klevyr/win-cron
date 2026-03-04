#!/usr/bin/env python
# Copyright (c) 2015-2020 Klever Ramon <klever at kircmedia.com>
# License: AGPLv3
from radagast import Radagast
from datetime import date
import pandas as pd

transfer_columns = ['Fecha', 'MesID', 'DiaID', 'uid', 'Hora', 'Cola',
                    'Response','StatusContact','TipoId','Envios']

def getTextQueueType(col):
    if col == 'COLPUSHJOU':
        return 'PUSH_SMS'
    elif col == 'COLPUSHSMS':
        return 'PUSH'
    return 'SMS'

if __name__ == '__main__':
    rad = Radagast()
    rad.set_logger(__file__ + ".log")
    rad.log.info("***** NEW *****")
    today_dtformat = date.today().strftime("%Y-%m-%d")
    today_asformat = date.today().strftime("%Y%m%d")
    rad.log.info("* config transfers")
    rad.log.info(f" >> now `{today_asformat}`")
    # init transfers
    rad.load_config()
    rad.log.info("* init transfer config")
    rad.acsbundle_init()
    # prepare transfers
    rad.set_config_transfer(
        filetransfer="EMAIL_AGR_NOTIF.dtfx",
        configsection="SQL",
        configkey="Where",
        configvalue=f"E1Z141Q2 = '{today_asformat}'"
    )
    rad.acsbundle_download()
    rad.set_config_transfer(
        filetransfer="SMS_AGR_NOTIF.dtfx",
        configsection="SQL",
        configkey="Where",
        configvalue=f"S1Z141Q2 = '{today_asformat}'"
    )
    rad.acsbundle_download()
    ## Otros Payclub, cna
    rad.set_current_transfer_filename("CNAPUAP_DAILY.dtfx").acsbundle_download()
    rad.set_current_transfer_filename("CNACLIP_DAILY.dtfx").acsbundle_download()
    # init uploads
    # SMS
    rad.log.info("* init DTL")
    df = pd.read_csv(f"{rad.defaultOutputData}/sms_agr_notifications.csv",
                     encoding="ISO-8859-1",
                     names=transfer_columns,
                     dtype=str
                     )
    df['TipoCola'] = df['Cola'].map(getTextQueueType)
    rad.runSqlQuery(f"DELETE FROM `mon_notif_sms` WHERE Fecha = '{today_dtformat}'")
    df.to_sql(name='mon_notif_sms', con=rad.getMSqlEngine(), if_exists='append', index=False)
    rad.log.info("> SMS, done.")
    # EMAIL
    df = pd.read_csv(f"{rad.defaultOutputData}/mail_agr_notifications.csv",
                     encoding="ISO-8859-1",
                     names=transfer_columns,
                     dtype=str
                     )
    df['TipoCola'] = 'POSTFIX'
    rad.runSqlQuery(f"DELETE FROM `mon_notif_email` WHERE Fecha = '{today_dtformat}'")
    df.to_sql(name='mon_notif_email', con=rad.getMSqlEngine(), if_exists='append', index=False)
    rad.log.info("> EMAIL, done.")
    # CNACLIP
    df = pd.read_csv(f"{rad.defaultOutputData}/cnaclip-daily.csv",
                     encoding="ISO-8859-1",
                     names=['cldocu','cltipp','cltise','clfevc','clusbi'],
                     dtype=str
                     )
    rad.runSqlQuery(f"TRUNCATE TABLE `cna_cnaclip`")
    df.to_sql(name='cna_cnaclip', con=rad.getMSqlEngine(), if_exists='append', index=False)
    rad.log.info("> CNACLIP, done.")
    # CNAPUAP
    df = pd.read_csv(f"{rad.defaultOutputData}/cnapuap-daily.csv",
                     encoding="ISO-8859-1",
                     names=['ruc','tipp','cedsoc','usname','email','celnum','profile','passwd',
                            'usbitmp','sendate','sendtime','usbidef','defsendate','defsendtime'],
                     dtype=str
                     )
    rad.runSqlQuery(f"TRUNCATE TABLE `cna_cnapuap`")
    df.to_sql(name='cna_cnapuap', con=rad.getMSqlEngine(), if_exists='append', index=False)
    rad.log.info("> CNAPUAP, done.")

    rad.log.info("*** end sync")
    files_remove = [
        f"{rad.defaultOutputData}/sms_agr_notifications.csv",
        f"{rad.defaultOutputData}/mail_agr_notifications.csv",
        f"{rad.defaultOutputData}/cnapuap-daily.csv",
        f"{rad.defaultOutputData}/cnaclip-daily.csv",
    ]
    rad.clean_transfer_data(files_remove)
    rad.log.info("done!")

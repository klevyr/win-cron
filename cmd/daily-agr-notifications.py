#!/usr/bin/env python
# Copyright (c) 2015-2018 Klever Ramon <klever at kircmedia.com>
# License: AGPLv3
from radagast import Radagast
from datetime import datetime
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
    # init transfers
    rad.load_config()
    rad.log.info("* init transfer config")
    rad.acsbundle_init()
    # EMAIL NOTIFICATIONS
    lastUpdate = rad.runSqlQuery("""
                                 SELECT IFNULL(MAX(Fecha), CAST(DATE_FORMAT(NOW(),'%Y-%m-01') AS DATETIME)) maximo 
                                 FROM mon_notif_email_sms
                                 WHERE Fecha < DATE_FORMAT(NOW(), '%Y-%m-%d')
                                 AND Origen = 'LOG_EMAIL'
                                 """)
    inidt, enddt = rad.getIncrementalDateRangebyDate(lastUpdate.maximo) # type: ignore
    inidate = inidt.strftime("%Y%m%d")
    enddate = enddt.strftime("%Y%m%d")
    sms_start, sms_end = inidate, enddate
    rad.log.info("* config EMAIL transfers")
    rad.log.info(f" > range `{inidate}` @ `{enddate}`")
    rad.set_config_transfer(
        filetransfer="EMAIL_AGR_NOTIF.dtfx",
        configsection="SQL",
        configkey="Where",
        configvalue=f"TM45A IN ('T','E') AND E1Z141Q2 >= '{inidate}' AND E1Z141Q2 <= '{enddate}'"
    )
    rad.acsbundle_download()
    # SMS NOTIFICATIONS
    lastUpdate = rad.runSqlQuery("""SELECT IFNULL(MAX(Fecha), CAST(DATE_FORMAT(NOW(),'%Y-%m-01') AS DATETIME)) maximo 
                                 FROM mon_notif_email_sms
                                 WHERE Fecha < DATE_FORMAT(NOW(), '%Y-%m-%d')
                                 AND Origen = 'LOG_SMS'
                                 """)
    inidt, enddt = rad.getIncrementalDateRangebyDate(lastUpdate.maximo) # type: ignore
    inidate = inidt.strftime("%Y%m%d")
    enddate = enddt.strftime("%Y%m%d")
    mail_start, mail_end = inidate, enddate
    rad.log.info("* config SMS transfers")
    rad.log.info(f" > range `{inidate}` @ `{enddate}`")
    rad.set_config_transfer(
        filetransfer="SMS_AGR_NOTIF.dtfx",
        configsection="SQL",
        configkey="Where",
        configvalue=f"TRIM(S1XX84W) NOT IN ('0','0000000000') AND S1Z141Q2 >= '{inidate}' AND S1Z141Q2 <= '{enddate}'"
    )
    rad.acsbundle_download()
    # init uploads
    # SMS
    rad.log.info("* init DTL")
    df = pd.read_csv(f"{rad.defaultOutputData}/sms_agr_notifications.csv",
                     encoding="ISO-8859-1",
                     names=transfer_columns,
                     dtype=str
                     )
    df['TipoCola'] = df['Cola'].map(getTextQueueType)
    src_transfer = "LOG_SMS"
    df['Origen'] = src_transfer
    rad.runSqlQuery(f"DELETE FROM `mon_notif_email_sms` WHERE Fecha BETWEEN '{sms_start}' AND '{sms_end}' AND Origen = '{src_transfer}'")
    df.to_sql(name='mon_notif_email_sms', con=rad.getMSqlEngine(), if_exists='append', index=False)
    rad.log.info(f"> SMS, {df.shape} done.")
    # EMAIL
    df = pd.read_csv(f"{rad.defaultOutputData}/mail_agr_notifications.csv",
                     encoding="ISO-8859-1",
                     names=transfer_columns,
                     dtype=str
                     )
    df['TipoCola'] = 'EMAIL'
    src_transfer = "LOG_EMAIL"
    df['Origen'] = src_transfer
    rad.runSqlQuery(f"DELETE FROM `mon_notif_email_sms` WHERE Fecha BETWEEN '{mail_start}' AND '{mail_end}' AND Origen = '{src_transfer}'")
    df.to_sql(name='mon_notif_email_sms', con=rad.getMSqlEngine(), if_exists='append', index=False)
    rad.log.info(f"> EMAIL, {df.shape} done.")

    files_remove = [
        f"{rad.defaultOutputData}/sms_agr_notifications.csv",
        f"{rad.defaultOutputData}/mail_agr_notifications.csv",
    ]
    rad.clean_transfer_data(files_remove)
    rad.log.info("*** end")

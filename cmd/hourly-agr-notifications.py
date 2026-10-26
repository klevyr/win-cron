#!/usr/bin/env python
# Copyright (c) 2015-2020 Klever Ramon <klever at kircmedia.com>
# License: AGPLv3
from radagast import Radagast
from datetime import date
import pandas as pd

transfer_columns = [
    "Fecha",
    "MesID",
    "DiaID",
    "uid",
    "Hora",
    "Cola",
    "Response",
    "StatusContact",
    "TipoId",
    "Envios",
]


def getTextQueueType(col):
    """Devuelve el tipo de cola asociado"""
    if col == "COLPUSHJOU":
        return "PUSH_SMS"
    elif col == "COLPUSHSMS":
        return "PUSH"
    return "SMS"


if __name__ == "__main__":
    rad = Radagast()
    rad.set_logger(__file__ + ".log")
    rad.log.info("====== NEW ======")
    today_dtformat = date.today().strftime("%Y-%m-%d")
    today_asformat = date.today().strftime("%Y%m%d")
    rad.log.info("> init transfer config")
    rad.log.info(f" >> now `{today_asformat}`")
    # init transfers
    rad.load_config()
    rad.log.info("* init transfer config")
    rad.acsbundle_init()
    # prepare transfers
    rad.log.info("> config EMAIL transfers")
    # EMAIL
    rad.set_config_transfer(
        filetransfer="EMAIL_AGR_NOTIF.dtfx",
        configsection="SQL",
        configkey="Where",
        configvalue=f"TM45A IN ('T','E') AND E1Z141Q2 = '{today_asformat}'",
    )
    rad.acsbundle_download()
    rad.log.info("> Finish download")
    # SMS
    rad.log.info("> config SMS transfers")
    rad.set_config_transfer(
        filetransfer="SMS_AGR_NOTIF.dtfx",
        configsection="SQL",
        configkey="Where",
        configvalue=f"TRIM(S1XX84W) NOT IN ('0','0000000000') AND S1Z141Q2 = '{today_asformat}'",
    )
    rad.acsbundle_download()
    rad.log.info("> Finish download")
    # init uploads
    rad.log.info("> init upload db")
    # SMS
    df = pd.read_csv(
        f"{rad.defaultOutputData}/sms_agr_notifications.csv",
        encoding="UTF-8",
        names=transfer_columns,
        dtype=str,
    )
    df["TipoCola"] = df["Cola"].map(getTextQueueType)
    src_transfer = "LOG_SMS"
    df["Origen"] = src_transfer
    rad.log.info("> clean data")
    rad.runSqlQuery(
        f"DELETE FROM `mon_notif_email_sms` WHERE Fecha = '{today_dtformat}'"
    )
    rad.log.info("> uploading")
    df.to_sql(
        name="mon_notif_email_sms",
        con=rad.getMSqlEngine(),
        if_exists="append",
        index=False,
    )
    rad.log.info(f"> SMS, %s done.", df.shape[0])
    # EMAIL
    df = pd.read_csv(
        f"{rad.defaultOutputData}/mail_agr_notifications.csv",
        encoding="UTF-8",
        names=transfer_columns,
        dtype=str,
    )
    df["TipoCola"] = "EMAIL"
    src_transfer = "LOG_EMAIL"
    df["Origen"] = src_transfer
    rad.log.info("> uploading")
    df.to_sql(
        name="mon_notif_email_sms",
        con=rad.getMSqlEngine(),
        if_exists="append",
        index=False,
    )
    rad.log.info(f"> EMAIL, %s done.", df.shape[0])

    files_remove = [
        f"{rad.defaultOutputData}/sms_agr_notifications.csv",
        f"{rad.defaultOutputData}/mail_agr_notifications.csv",
    ]
    rad.clean_transfer_data(files_remove)
    rad.log.info("===> end")

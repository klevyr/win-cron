#!/usr/bin/env python
# Copyright (c) 2015-2020 Klever Ramon <klever at kircmedia.com>
# License: AGPLv3
from radagast import Radagast
from datetime import date

if __name__ == '__main__':
    rad = Radagast()
    rad.set_logger(__file__ + ".log")
    rad.log.info("***** NEW *****")
    dt = date.today().strftime("%Y%m%d")
    rad.log.info("* config transfers")
    rad.log.info(f" >> now `{dt}`")
    # init transfers
    rad.load_config()
    rad.log.info("* init transfer config")
    rad.acsbundle_init()
    # prepare transfers
    rad.set_config_transfer(
        filetransfer="EMAIL_AGR_NOTIF.dtfx",
        configsection="SQL",
        configkey="Where",
        configvalue=f"E1Z141Q2 = '{dt}'"
    )
    rad.acsbundle_download()
    rad.set_config_transfer(
        filetransfer="SMS_AGR_NOTIF.dtfx",
        configsection="SQL",
        configkey="Where",
        configvalue=f"S1Z141Q2 = '{dt}'"
    )
    rad.acsbundle_download()
    ## Otros Payclub, cna
    #rad.transfer_data("CNAPUAP_DAILY")
    #rad.transfer_data("CNACLIP_DAILY")
    rad.log.info("* init SQL")
    #rad.run_mysql("hourly_notifications.sql")
    #rad.run_mysql("hourly_othersdb.sql")
    rad.log.info("*** end sync")
    files_remove = [
        "D:/com/share/sms_notifications.csv",
        "D:/com/share/mail_notifications.csv",
        "D:/com/share/bop_trans.csv",
        "D:/com/share/cnapuap-daily.csv",
        "D:/com/share/cnaclip-daily.csv",
    ]
    #rad.clean_transfer_data(files_remove)
    rad.log.info("done!")

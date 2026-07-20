#!/usr/bin/env python
# Copyright (c) 2015-2018 Klever Ramon <klever at kircmedia.com>
# License: AGPLv3
from radagast import Radagast
from datetime import datetime

if __name__ == '__main__':
    rad = Radagast()
    rad.set_logger(__file__ + ".log")
    rad.log.info("***** NEW *****")
    rad.load_config()
    # EMAIL NOTIFICATIONS
    lastUpdate = rad.runSqlQuery("SELECT IFNULL(MAX(dtlog), CAST(DATE_FORMAT(NOW(),'%Y-%m-01') AS DATETIME)) maximo FROM mail_messages")
    inidt, enddt = rad.getIncrementalDateRangebyDate(lastUpdate.maximo)
    inidate = inidt.strftime("%Y%m%d")
    enddate = enddt.strftime("%Y%m%d")
    rad.log.info("* prepare EMAIL transfers")
    rad.log.info(f"  ini[{inidate}]")
    rad.log.info(f"  end[{enddate}]")
    rad.set_config_transfer(
        filetransfer="EMAIL_NOTIF",
        configsection="SQL",
        configkey="Where",
        configvalue=f"TM45A != 'R' AND E1Z141Q2 >= '{inidate}' AND E1Z141Q2 <= '{enddate}'"
    )
    # SMS NOTIFICATIONS
    lastUpdate = rad.runSqlQuery("SELECT IFNULL(MAX(dtlog), CAST(DATE_FORMAT(NOW(),'%Y-%m-01') AS DATETIME)) maximo FROM sms_messages")
    inidt, enddt = rad.getIncrementalDateRangebyDate(lastUpdate.maximo)
    inidate = inidt.strftime("%Y%m%d")
    enddate = enddt.strftime("%Y%m%d")
    rad.log.info("* prepare SMS transfers")
    rad.log.info(f"  ini[{inidate}]")
    rad.log.info(f"  end[{enddate}]")
    rad.set_config_transfer(
        filetransfer="SMS_NOTIF",
        configsection="SQL",
        configkey="Where",
        configvalue=f"S1Z141Q2 >= '{inidate}' AND S1Z141Q2 <= '{enddate}'"
    )
    rad.set_config_transfer(
        filetransfer="PUSH_NOTIF",
        configsection="SQL",
        configkey="Where",
        configvalue=f"P1Z141Q2 >= '{inidate}' AND P1Z141Q2 <= '{enddate}'"
    )
    # init transfers
    rad.log.info("* init transfer")
    ## Notifications
    rad.transfer_data("SMS_NOTIF")
    rad.transfer_data("PUSH_NOTIF")
    rad.transfer_data("EMAIL_NOTIF")
    rad.log.info("* init SQL")
    rad.run_mysql("daily_notifications.sql")
    files_remove = [
        "D:/com/share/sms_notifications.csv",
        "D:/com/share/mail_notifications.csv",
    ]
    rad.clean_transfer_data(files_remove)
    rad.log.info("*** end")

#!/usr/bin/env python
# Copyright (c) 2015-2020 Klever Ramon <klever at kircmedia.com>
# License: AGPLv3
from radagast import Radagast
from datetime import date
import pandas as pd

if __name__ == "__main__":
    rad = Radagast()
    rad.set_logger(__file__)
    rad.log.info("====== NEW ======")
    rad.log.info("> init transfer config")
    # init transfers
    rad.load_config()
    rad.acsbundle_init()
    # prepare transfers
    rad.set_current_transfer_filename("CNAPUAP_DAILY.dtfx").acsbundle_download()
    rad.set_current_transfer_filename("CNACLIP_DAILY.dtfx").acsbundle_download()
    rad.log.info("> Finish download")
    # init uploads
    rad.log.info("> init upload db")
    # CNACLIP
    df = pd.read_csv(
        f"{rad.defaultOutputData}/cnaclip-daily.csv",
        encoding="ISO-8859-1",
        names=["cldocu", "cltipp", "cltise", "clfevc", "clusbi"],
        dtype=str,
    )
    rad.runSqlQuery(f"TRUNCATE TABLE `cna_cnaclip`")
    df.to_sql(
        name="cna_cnaclip", con=rad.getMSqlEngine(), if_exists="append", index=False
    )
    rad.log.info(f"> CNACLIP, % done.", df.shape[0])
    # CNAPUAP
    df = pd.read_csv(
        f"{rad.defaultOutputData}/cnapuap-daily.csv",
        encoding="ISO-8859-1",
        names=[
            "ruc",
            "tipp",
            "cedsoc",
            "usname",
            "email",
            "celnum",
            "profile",
            "passwd",
            "usbitmp",
            "sendate",
            "sendtime",
            "usbidef",
            "defsendate",
            "defsendtime",
        ],
        dtype=str,
    )
    rad.runSqlQuery(f"TRUNCATE TABLE `cna_cnapuap`")
    df.to_sql(
        name="cna_cnapuap", con=rad.getMSqlEngine(), if_exists="append", index=False
    )
    rad.log.info(f"> CNAPUAP, %s done.", df.shape[0])

    files_remove = [
        f"{rad.defaultOutputData}/cnapuap-daily.csv",
        f"{rad.defaultOutputData}/cnaclip-daily.csv",
    ]
    rad.clean_transfer_data(files_remove)
    rad.log.info("===> end")

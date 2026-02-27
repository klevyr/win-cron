#!/usr/bin/env python
# Copyright (c) 2015-2020 Klever Ramon <klever at kircmedia.com>
# License: AGPLv3
import atexit, configparser, logging
import os, sys, smtplib
import sqlalchemy as sqa
from datetime import date, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from subprocess import Popen, PIPE


class Radagast:
    """
    Class Radagast

    Orquestador de procesos de sincronizacion de informacion entre
    Gestor y la Base de datos local.
    """

    def __init__(self):
        root = ""
        if sys.platform == 'win32':
            root = str(__file__)[:2]
        self.maindir = f"{root}/bin/cron"
        self.us_transfer = ""
        self.pw_transfer = ""
        self.pw_windows = ""
        self.mysql_user = ""
        self.mysql_passwd = ""
        self.mysql_host = ""
        self.mysql_db = ""
        self.exchangeServer = ""
        self.senderAccount = ""
        self.log = logging.getLogger()
        self.lockfile = ""
        self.transferfolder = f"{self.maindir}/cmd/transfer/"
        self.configfil = f"{self.maindir}/config.ini"
        self.logpath = f"{self.maindir}/cmd/logs/"
        atexit.register(self.cleanup)

    def getDateRange_LastMonth(self):
        """
        Obtiene la informacion de rango de fechas del mes
        anterior en base a la fecha actual:

        >>> today() # 20220103
        >>> getDateRange_LastMonth() # return (20211201, 20211231)
        """
        # calcula el rango de fechas del mes anterior
        # fd -> first day
        # ld -> last day
        fd_currmonth = date.today().replace(day=1)
        ld_prevmonth = fd_currmonth - timedelta(days=1)
        fd_prevmonth = ld_prevmonth.replace(day=1)
        return fd_prevmonth, ld_prevmonth

    def getDateRange_CurrentMonth(self):
        """
        Obtiene la informacion de rango de fechas del periodo actual
        sin contar el dia actual, es decir del 1ro hasta el dia caido
        """
        # fd -> first day
        # yt -> yesterday
        fd_currmonth = date.today().replace(day=1)
        yt_currmonth = date.today() - timedelta(days=1)
        return fd_currmonth, yt_currmonth

    def getIncrementalDateRangebySubstract(self, sub_days, range_days=1):
        """
        Devuelve el rango de fechas para base incrementales:
        >>> getIncrementalDateRange(2)
        today=20220331
        ld_ = 20220329
        fd_ = 20220328
        >>> getIncrementalDateRange(4, 2)
        today=20220331
        ld_ = 20220327
        fd_ = 20220325
        """
        # fd -> date sub_days
        # ld -> date + range_days
        ld_incremental = date.today() - timedelta(days=sub_days)
        fd_incremental = ld_incremental - timedelta(days=range_days)
        return fd_incremental, ld_incremental

    def getIncrementalDateRangebyDate(self, max_date):
        """
        Devuelve el rango de fechas para base incrementales:
        >>> getIncrementalDateRange(max_date=20226603)
        today=20220605
        ld_ = max_date+1 => 20226604
        fd_ = today-1    => 20226604
        """
        ld_incremental = date.today() - timedelta(days=1)
        fd_incremental = max_date     + timedelta(days=1)
        return fd_incremental, ld_incremental

    def set_logger(self, filelog):
        """
        Obtiene el apuntador para el archivo de log y salida
        en pantalla en caso de ejecutarlo via linea de comandos
        y genera un archivo lock para controlar procesos duplicados.
        """
        scriptname = os.path.splitext(os.path.basename(filelog))[0]
        self.lockfile = self.logpath + scriptname + ".lock"
        # Custom
        self.log = logging.getLogger(scriptname)
        self.log.setLevel(logging.INFO)
        # Console Handler
        c_handler = logging.StreamHandler(stream=sys.stdout)
        c_format = logging.Formatter('%(asctime)s %(message)s',
                                     datefmt='%Y-%m-%d %H:%M:%S')
        c_handler.setLevel(logging.INFO)
        c_handler.setFormatter(c_format)
        # FileHandler
        c_logfile = self.logpath + scriptname + '.log'
        if not os.path.exists(c_logfile):
            with open(c_logfile, 'w'): pass
        f_handler = logging.FileHandler(c_logfile)
        f_format = logging.Formatter(
            '%(asctime)s %(levelname)-8s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S')
        f_handler.setLevel(logging.INFO)
        f_handler.setFormatter(f_format)
        # Logger
        self.log.addHandler(f_handler)
        self.log.addHandler(c_handler)
        # set lockfile
        self.lock()

    def lock(self):
        """
        Controlar la existencia del archivo .lock, en caso de:
        - ya existir, se cancela la ejecucion del proceso actual
        - no existir, continuar la ejecucion y coloa el PID en el archivo
        """
        try:
            with open(self.lockfile, 'x') as lockfile:
                # create lock file by prevent many process running
                lockfile.write(str(os.getpid()))
                self.log.info("init script with PID {}".format(os.getpid()))
        except IOError:
            # file already exists
            processid = ""
            try:
                with open(self.lockfile, 'r') as lckfil:
                    processid = lckfil.read()
            except IOError:
                pass
            self.log.warning(
                "already running by PID {}...  Pass!".format(processid)
            )
            exit()
    
    def cleanup(self):
        """
        Elimina el archivo .lock cuando haya finalizado el proceso
        """
        self.log.info("Cleanup lock file...")
        try:
            os.remove(self.lockfile)
            self.log.info("clean ok.")
        except PermissionError:
            self.log.error("Permission denied")
        except :
            self.log.error("File can not be removed")
        self.log.info("*** END ***")


    def load_config(self):
        """
        Lectura del archivo de configuracion INI de acceso a la base de datos,
        con el acceso se obtiene los parametros dinamicos en `capp_cfg`
        """
        # Configuracion Basica DB
        config = configparser.ConfigParser()
        config.read(self.configfil)
        self.mysql_user = config["mysql"]["user"]
        self.mysql_passwd = config["mysql"]["passwd"]
        self.mysql_host = config["mysql"]["host"]
        self.mysql_db = config["mysql"]["database"]
        # Configuracion DB
        engine = self.getMSqlEngine()
        with engine.connect() as conn:
            rs = conn.execute(sqa.text("""SELECT param, txtvalue FROM `capp_cfg`
                WHERE param IN ('transfers_pw','transfers_us','ldap_pw',
                'mail_server','mail_sendername')""")).fetchall()
        config_dict = {}
        for param, value in rs:
            config_dict[param] = value
        self.us_transfer = config_dict["transfers_us"]
        self.pw_transfer = config_dict["transfers_pw"]
        self.pw_windows  = config_dict["ldap_pw"]
        self.exchangeServer = config_dict["mail_server"]
        self.senderAcount = config_dict["mail_sendername"]

    def set_config_transfer(self, filetransfer, configsection,
                            configkey, configvalue):
        """
        Lee los archivos de transferencis AS400 y modifica los
        parametros especificados
        """
        config = configparser.ConfigParser()
        # config.optionxform = str
        tfile = self.transferfolder + filetransfer
        config.read(tfile)
        cfgfile = open(tfile, 'w')
        self.log.info("Update trans. file '%s'" % tfile)
        config.set(configsection, configkey, configvalue)
        config.write(cfgfile, False)
        self.log.info("Change section %s[%s]:%s" %
                      (configsection, configkey, configvalue)
                      )
        cfgfile.close()

    def transfer_data(self, filename):
        """
        Utiliza el programa `RXFERPCB` para realizar las tranferencias del
        gestor
        
        1. Ir al directorio donde se encuentra JAVA  (acsbundle.jar) (C:/Users/Public/IBM/ClientSolutions)
        2.  Logueo al AS400 
        `java -jar acsbundle.jar /plugin=logon /system=AS400F35 /userid=usuario_AS /password=clave_AS /gui=0`
        # Descarga de Transferencia 
        3. java -jar acsbundle.jar /plugin=download /system=AS400F35 ruta/nombre_del_icono.dtfx
        # borrar cache que pida no solicite contraseña por cuestiones de seguridad 
        java -jar acsbundle.jar /plugin=logon /system=AS400F35 /c /gui=0
 
        """
        self.log.info("* Transfering " + filename + "...")
        p = Popen([
            "rxferpcb",
            self.transferfolder + filename + ".dtf",
            self.us_transfer,
            self.pw_transfer],
            stdin=PIPE,
            stdout=PIPE,
            stderr=PIPE
        )
        output, err = p.communicate()
        if err:
            self.log.error(err)
        transfer_keywords = ["TIEMPO", "FILAS "]
        lines = 0
        for line in output.decode('ISO8859-1').split('\r\n'):
            lines += 1
            if line.strip()[:6].upper() in transfer_keywords:
                self.log.info(line.strip())
        # self.log.info(output.decode('ISO8859-1'))

    def acsbundle_init(self):
        """
        Inicializa la nueva version de transferencia utilizando el programa `acsbundle.jar`
        para realizar las tranferencias del gestor.
        """
        proc = Popen(["java", "-jar", "acsbundle.jar", "/plugin=logon", "/system=AS400F35",
                      f"/userid={self.us_transfer}", f"/password={self.pw_transfer}",
                      "/gui=0"], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        output, err = proc.communicate()
        if err:
            self.log.error(err)
        for line in output.decode('ISO8859-1').split('\r\n'):
            self.log.info(line)

    def acsbundle_upload(self):
        """
        Realiza la carga de archivos al as400.
        """
        proc = Popen(["java", "-jar", "acsbundle.jar", "/plugin=upload",
                      "SMSBAT.dttx", f"/userid={self.us_transfer}"],
                      stdin=PIPE, stdout=PIPE, stderr=PIPE)
        output, err = proc.communicate()
        if err:
            self.log.error(err)
        for line in output.decode('ISO8859-1').split('\n'):
            if line.strip()[:6].upper() == "FILAS ":
                print("")
                rows = line.strip().replace("      ", " ")
                print("    " + rows)
                input("    Presione ENTER para finalizar.")
                self.log.info(rows)
                #self.meta.append(rows.split(':')[1].strip())

    def acsbundle_download(self):
        """
        Realiza la descarga de archivos del as400.
        """
        proc = Popen(["java", "-jar", "acsbundle.jar", "/plugin=download",
                      "/system=AS400F35", "", f"/userid={self.us_transfer}"],
                      stdin=PIPE, stdout=PIPE, stderr=PIPE)
        output, err = proc.communicate()
        if err:
            self.log.error(err)
        for line in output.decode('ISO8859-1').split('\n'):
            if line.strip()[:6].upper() == "FILAS ":
                print("")
                rows = line.strip().replace("      ", " ")
                print("    " + rows)
                input("    Presione ENTER para finalizar.")
                self.log.info(rows)
                #self.meta.append(rows.split(':')[1].strip())
    


    def clean_transfer_data(self, filelist, clean_mode='truncate'):
        """
        Elimina la informacion transferida una vez cargado al gestor 
        de base de datos, bajo dos metodos:

         - `truncate` sobreescribe el archivo dejando en blanco (defecto)
         - `unlink` elimina el archivo, puede ser recuperable.
        """
        self.log.info("* Cleanup transfers filelist ...")
        if type(filelist) is list:
            for fl in filelist:
                self.log.info(f"- {fl}")
                if clean_mode == 'unlink':
                    os.unlink(fl)
                elif clean_mode == 'truncate':
                    with open(fl, 'w') as filwriter:
                        filwriter.write("")

        else:
            self.log.warning("filelist is not list.")


    def readSqlTemplate(self, sqltemplate):
        """
        Lectura de un archivo SQLTEMPLATE y devuelve el buffer
        """
        dir_path = os.path.dirname(os.path.realpath(__file__))
        sqltemplatefile = os.path.join(dir_path, "scripts", sqltemplate)
        sqlbuffer = ""
        with open(sqltemplatefile, 'r', encoding="utf-8") as reader:
            sqlbuffer = reader.read()
        return sqlbuffer


    def saveParsedSqlTemplate(self, sqlparsedtemplate, sqlfilename):
        """
        Guarda un buffer reformateado basado en una plantilla SQL
        """
        dir_path = os.path.dirname(os.path.realpath(__file__))
        newsqlfile = os.path.join(dir_path, "scripts", sqlfilename)
        with open(newsqlfile, 'w', encoding="utf-8") as writer:
            writer.write(sqlparsedtemplate)


    def run_mysql(self, sqlfilename):
        """
        Ejecutar un scrip SQL a travez de linea de comandos `mysql`
        """
        dir_path = os.path.dirname(os.path.realpath(__file__))
        sqlfile = os.path.join(dir_path, "scripts", sqlfilename)
        mysql_cmd_line = (
            "mysql -v -v -u{} -p{} {} < {}".format(
                self.mysql_user,
                self.mysql_passwd,
                self.mysql_db,
                sqlfile
            )
        )
        self.log.info("processing file %s." % sqlfile)
        process = Popen(
            mysql_cmd_line,
            stdout=PIPE,
            stdin=PIPE,
            stderr=PIPE,
            shell=True
        )
        output, err = process.communicate()
        sql_keywords = [
            "ALTER T", "CREATE ", "INSERT ",
            "LOAD DA", "PREPARE", "QUERY O",
            "SELECT ", "TRUNCAT", "UPDATE ",
            "DROP TA", "EXECUTE", "DROP PR",
            "SET @SQ"
        ]
        if err:
            self.log.error(err)
        lines = 0
        for line in output.decode('ISO8859-1').split('\r\n'):
            lines += 1
            if line[:7].upper() in sql_keywords:
                self.log.info(line.strip())

    def sendEmailMessage(self, rcpts, subject, htmlbody):
        """
        Enviar una notificacion via email sobre un proceso especifico
        """
        msg = MIMEMultipart()
        # Header
        msg['From'] = self.senderAccount
        msg['To'] = ','.join(rcpts)
        msg['Subject'] = subject
        # Body
        msg.attach(MIMEText(htmlbody, 'html'))
        # Send Email
        server = smtplib.SMTP(self.exchangeServer)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(self.us_transfer, self.pw_windows)
        server.sendmail(self.senderAccount, rcpts, msg.as_string())
        server.quit()

    def getMSqlEngine(self):
        """
        ___future___
        Devuelve una conexion a MYSQL
        """
        url = f"mysql+pymysql://{self.mysql_user}:{self.mysql_passwd}@{self.mysql_host}/{self.mysql_db}"
        return sqa.create_engine(url)

    def runSqlQuery(self, sqlscript):
        """
        ___future___
        Ejecuta una sentencia SQL via conexion
        """
        engine = self.getMSqlEngine()
        dat = ""
        with engine.connect() as conn:
            if "SELECT " in sqlscript:
                dat = conn.execute(sqa.text(sqlscript)).mappings().one()
            else:
                dat = conn.execute(sqa.text(sqlscript))
        return dat

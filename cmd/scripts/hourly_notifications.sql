-- BASES SMS TODAY
-- SMS MESSAGES
TRUNCATE `sms_messages_today`;
LOAD DATA CONCURRENT INFILE 'D:/com/share/sms_notifications.csv' 
IGNORE INTO TABLE `sms_messages_today` FIELDS TERMINATED BY ',' 
ENCLOSED BY '"' ESCAPED BY '\\' LINES TERMINATED BY '\r\n';
-- PUSH MESSAGES
LOAD DATA CONCURRENT INFILE 'D:/com/share/push_notifications.csv' 
IGNORE INTO TABLE `sms_messages_today` FIELDS TERMINATED BY ',' 
ENCLOSED BY '"' ESCAPED BY '\\' LINES TERMINATED BY '\r\n';
-- EMAIL TODAY
TRUNCATE `mail_messages_today`;
LOAD DATA CONCURRENT INFILE 'D:/com/share/mail_notifications.csv' 
IGNORE INTO TABLE `mail_messages_today` CHARACTER SET latin1 FIELDS TERMINATED BY ',' 
ENCLOSED BY '"' ESCAPED BY '\\' LINES TERMINATED BY '\r\n';
/** Monitoreo Tiempos SMS *
DELETE FROM digital_db.mon_times_sms_current WHERE dtlog = date_format(now(), '%Y-%m-%d');
INSERT INTO digital_db.mon_times_sms_current 
SELECT 
    EXTRACT(YEAR_MONTH FROM dtlog) MesID,
  dtlog, campain, a.marc, LEFT(tini, 2) hh, marca, descrip,
  CONCAT(campain, ' - ', descrip) Cod_Descrip, enlace, tipo, grupo, 
    time_to_sec( DATE_FORMAT(
		TIMEDIFF(
		str_to_date(concat(dtlog,'-',tfin), '%Y-%m-%d-%H.%i.%s.%f'),
		str_to_date(concat(dtlog,'-',tini), '%Y-%m-%d-%H.%i.%s.%f')
		), '%H:%i:%s.%f'
	) ) dif_secs,
    case when length(confid) = 16 then 'Enviado' else 'Cola' end estado,
    count(*)
FROM sms_messages_today a
LEFT JOIN sms_details b ON a.ent=b.ent AND a.marc=b.marc AND a.campain=b.cod
WHERE LEFT(celnum,4) = '5939' 
GROUP BY 
  MesID, dtlog, campain, a.marc, hh, marca, descrip,
  Cod_Descrip, enlace, tipo, grupo, dif_secs,
  estado;
*/
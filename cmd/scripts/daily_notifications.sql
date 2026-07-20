/** 
 * BASES NOTIFICACIONES INFORMES
 *
 * Genera la informacion de las librerias de notificaciones
 * TMSMT13U (SMS) y TMSMT34U (EMAIL)
 */ 

/** SMS */
-- carga a la base mes actual
LOAD DATA CONCURRENT INFILE 'D:/com/share/sms_notifications.csv' 
IGNORE INTO TABLE `sms_messages` FIELDS TERMINATED BY ',' 
ENCLOSED BY '"' ESCAPED BY '\\' LINES TERMINATED BY '\r\n';
LOAD DATA CONCURRENT INFILE 'D:/com/share/push_notifications.csv' 
IGNORE INTO TABLE `sms_messages` FIELDS TERMINATED BY ',' 
ENCLOSED BY '"' ESCAPED BY '\\' LINES TERMINATED BY '\r\n';

/** EMAIL */
LOAD DATA CONCURRENT INFILE 'D:/com/share/mail_notifications.csv' 
IGNORE INTO TABLE `mail_messages` CHARACTER SET latin1 FIELDS TERMINATED BY ',' 
ENCLOSED BY '"' ESCAPED BY '\\' LINES TERMINATED BY '\r\n';

/** Monitoreo Tiempos SMS *
-- TRUNCATE mon_times_sms_current;
DELETE FROM digital_db.mon_times_sms_current 
    WHERE dtlog = date_format(date_sub(now(), INTERVAL 1 DAY), '%Y-%m-%d');
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
/** actualiza informacion ultimo envio con la fecha actual *
-- SMS
UPDATE digital_db.notificacion_ultimoenvio_periodo nup 
INNER JOIN (
  select concat(ent, marc, campain) uid, ent, marc, campain, extract(YEAR_MONTH FROM max(dtlog)) Fecha_UltimoEnvio, count(*) Cant
  from capp_db.sms_messages_today sm 
  GROUP BY uid, ent, marc, campain ) lst ON nup.uid=lst.uid
SET 
  nup.Fecha_UltimoEnvio = lst.Fecha_UltimoEnvio
WHERE TRUE ;
-- EMAIL
UPDATE digital_db.notificacion_ultimoenvio_periodo nup 
INNER JOIN (
  select concat(ent, marc, campain) uid, ent, marc, campain, extract(YEAR_MONTH FROM max(dtlog)) Fecha_UltimoEnvio, count(*) Cant
  from capp_db.mail_messages_today sm 
  GROUP BY uid, ent, marc, campain ) lst ON nup.uid=lst.uid
SET 
  nup.Fecha_UltimoEnvio = lst.Fecha_UltimoEnvio
WHERE TRUE ;
*/
/**
 * Elimina la informacion de dia en curso
 *
TRUNCATE TABLE sms_messages_today;
TRUNCATE TABLE mail_messages_today;
*/
-- Informacion comercios
TRUNCATE `sms_cnapuap`;
LOAD DATA CONCURRENT INFILE 'D:/com/share/cnapuap-daily.csv' INTO TABLE `sms_cnapuap` CHARACTER SET latin1
FIELDS TERMINATED BY ',' ENCLOSED BY '"' ESCAPED BY '/' LINES TERMINATED BY '\r\n';
-- Informacion canal alternativo
TRUNCATE `sms_cnaclipdaily`;
LOAD DATA CONCURRENT INFILE 'D:/com/share/cnaclip-daily.csv' INTO TABLE `sms_cnaclipdaily` CHARACTER SET latin1
FIELDS TERMINATED BY ',' ENCLOSED BY '"' ESCAPED BY '/' LINES TERMINATED BY '\r\n';

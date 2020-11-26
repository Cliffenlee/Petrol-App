drop schema if exists promotions;
Create schema promotions;
use promotions;

DROP TABLE IF EXISTS `promotions`;
CREATE TABLE `promotions` (
  `code` varchar(12) NOT NULL,
  `discount` int(11) NOT NULL,
  `name` varchar(50) NOT NULL,
  `redemptions` int(11) DEFAULT NULL,
  `start_date` date NOT NULL,
  `end_date` date NOT NULL,
  `message` varchar(300) NOT NULL,
  PRIMARY KEY (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



DROP TABLE IF EXISTS `applicability`;
CREATE TABLE `applicability` (
  `code` varchar(12) NOT NULL,
  `tier` int NOT NULL,
  PRIMARY KEY (`code`,`tier`),
  CONSTRAINT `applicability_fk1` FOREIGN KEY (`code`) REFERENCES `promotions` (`code`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

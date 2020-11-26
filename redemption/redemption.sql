drop schema if exists redemption;
Create schema redemption;
use redemption;

DROP TABLE IF EXISTS `redemptions`;
CREATE TABLE `redemptions` (
  `code` varchar(12) NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`code`, `user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

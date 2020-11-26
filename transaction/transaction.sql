SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
START TRANSACTION;
SET time_zone = "+00:00";

--
-- Database: `transaction`
--
CREATE DATABASE IF NOT EXISTS `transaction` DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;
USE `transaction`;

-- --------------------------------------------------------

--
-- Table structure for table `transaction`
--

DROP TABLE IF EXISTS `payment`;
CREATE TABLE IF NOT EXISTS `payment` (
  `payment_id` VARCHAR(40),
  `discount` float,
  `percentage` int,
  `net_amount` float NOT NULL,
  `executed` int DEFAULT 0,
  PRIMARY KEY (`payment_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Dumping data for table `payment`
--

INSERT INTO `payment` VALUES
("PAYID-LZ3AYJI91559578UA6958621", 5.0, 10, 32.00, 1),
("PAYID-LZY5GRQ1US35391KS9931231", NULL, NULL, 35.00, 0);

-- --------------------------------------------------------

DROP TABLE IF EXISTS `userPayment`;
CREATE TABLE IF NOT EXISTS `userPayment` (
  `user_id` int NOT NULL,
  `payment_id` VARCHAR(40) NOT NULL,
  PRIMARY KEY (`payment_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Dumping data for table `userPayment`
--

INSERT INTO userPayment(user_id,payment_id) VALUES
(1,"PAYID-LZ3AYJI91559578UA6958621"),
(2,"PAYID-LZY5GRQ1US35391KS9931231");
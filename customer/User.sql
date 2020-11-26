SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
START TRANSACTION;
SET time_zone = "+00:00";

--
-- Database: `Customer`
--
CREATE DATABASE IF NOT EXISTS `customer` DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;
USE `customer`;

-- --------------------------------------------------------

--
-- Table structure for table `reward`
--

DROP TABLE IF EXISTS `user`;
CREATE TABLE IF NOT EXISTS `user` (
  `userID` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(32) NOT NULL,
  `email` VARCHAR(64) NOT NULL,
  `telehandle` VARCHAR(32) NOT NULL,
  `teleID` INT,
  `point` INT NOT NULL,
  `exp` INT NOT NULL,

  UNIQUE(`email`),
  PRIMARY KEY (`userID`)
);

--
-- Dumping data for table `user`
--

INSERT INTO `user` VALUES
(NULL,'Apple TAN',"apple@gmail.com",'apple_tan',NULL,4000,5000),
(NULL,'Glen See','glen.see.2018@smu.edu.sg',"glen_see",NULL,1000,2000);

-- --------------------------------------------------------
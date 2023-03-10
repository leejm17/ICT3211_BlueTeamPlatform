-- MySQL dump 10.13  Distrib 8.0.32, for Linux (x86_64)
--
-- Host: localhost    Database: scfami_spider
-- ------------------------------------------------------
-- Server version	8.0.32-0ubuntu0.22.04.2

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `spiderjobs`
--

DROP TABLE IF EXISTS `spiderjobs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `spiderjobs` (
  `project` varchar(255) DEFAULT NULL,
  `spider` varchar(255) DEFAULT NULL,
  `jobid` varchar(255) NOT NULL,
  `url` varchar(2083) DEFAULT NULL,
  `depth` int DEFAULT NULL,
  `status` char(20) DEFAULT NULL,
  `datetime` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`jobid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `spiderjobs`
--

LOCK TABLES `spiderjobs` WRITE;
/*!40000 ALTER TABLE `spiderjobs` DISABLE KEYS */;
INSERT INTO `spiderjobs` VALUES ('yara_scrapy','generic','00f9263cbda111ed87dc0242ac110002','https://googsle.com',1,'finished','2023-03-08 19:04:32'),('yara_scrapy','generic','0512e6b8bda111ed87dc0242ac110002','https://googsle.com',1,'finished','2023-03-08 19:04:39'),('yara_scrapy','generic','0994b630bda111ed87dc0242ac110002','https://googsle.com',1,'finished','2023-03-08 19:04:46'),('yara_scrapy','bazaar','2072728ebda111ed87dc0242ac110002','semi',0,'finished','2023-03-08 19:05:25'),('yara_scrapy','github','2c92780ebe5811ed97fd0242ac110002','https://github.com/Yara-Rules/rules',1,'finished','2023-03-09 16:55:43'),('yara_scrapy','github','3adf8856bd9111ed87dc0242ac110002','https://github.com/abcdf',0,'finished','2023-03-08 17:11:37'),('yara_scrapy','github','623a3ae2bd9e11ed87dc0242ac110002','https://github.com/Yara-Rules/rules',1,'finished','2023-03-08 18:45:46'),('yara_scrapy','bazaar','7e7cbc2cbda111ed87dc0242ac110002','asd',0,'finished','2023-03-08 19:08:02'),('yara_scrapy','bazaar','82c60212bda011ed87dc0242ac110002','https://google.com',1,'finished','2023-03-08 19:01:00'),('yara_scrapy','generic','88423094bda011ed87dc0242ac110002','https://google.com',1,'finished','2023-03-08 19:01:09'),('yara_scrapy','github','a173cf9ebda211ed87dc0242ac110002','https://github.com/Yara-Rules/rules',0,'finished','2023-03-08 19:16:10'),('yara_scrapy','bazaar','a40eb822bda211ed87dc0242ac110002','https://github.com/Yara-Rules/rules',0,'finished','2023-03-08 19:16:15'),('yara_scrapy','bazaar','a5edec8cbd9611ed87dc0242ac110002','https://github.com/abcdf',0,'finished','2023-03-08 17:50:24'),('yara_scrapy','bazaar','afff096cbda111ed87dc0242ac110002','https://github.com/abc123df',0,'finished','2023-03-08 19:09:25'),('yara_scrapy','github','bacc76ecbd9011ed87dc0242ac110002','https://github.com/abcdf',0,'finished','2023-03-08 17:08:02'),('yara_scrapy','github','bc1a7ee6bd9e11ed87dc0242ac110002','https://github.com/Yara-Rules/rules',1,'finished','2023-03-08 18:48:17'),('yara_scrapy','github','d752e0b2bd9011ed87dc0242ac110002','https://github.com/abcdf',0,'finished','2023-03-08 17:08:50'),('yara_scrapy','bazaar','db419e9ebd9911ed87dc0242ac110002','https://github.com/abcdf',0,'finished','2023-03-08 18:13:22'),('yara_scrapy','bazaar','e8adcb70bd9911ed87dc0242ac110002','https://github.com/abcdf',0,'finished','2023-03-08 18:13:45'),('yara_scrapy','github','edb42f14bd9011ed87dc0242ac110002','https://github.com/abcdf',0,'finished','2023-03-08 17:09:27'),('yara_scrapy','github','fbd1d5d4bd9911ed87dc0242ac110002','https://github.com/abcdf',0,'finished','2023-03-08 18:14:17');
/*!40000 ALTER TABLE `spiderjobs` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2023-03-09 17:21:23

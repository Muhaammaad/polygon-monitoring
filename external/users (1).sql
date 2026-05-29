-- phpMyAdmin SQL Dump
-- version 5.2.1deb3
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Erstellungszeit: 23. Dez 2025 um 10:35
-- Server-Version: 8.0.44-0ubuntu0.24.04.1
-- PHP-Version: 8.3.6

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Datenbank: `data_hive_test_2`
--

-- --------------------------------------------------------

--
-- Tabellenstruktur für Tabelle `users`
--

CREATE TABLE `users` (
  `id` int NOT NULL,
  `user_id` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT NULL,
  `user_name` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci,
  `first_name` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci,
  `last_name` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci,
  `company_name` varchar(100) DEFAULT NULL,
  `phone` varchar(255) DEFAULT NULL,
  `prefix` varchar(10) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT NULL,
  `gender` int DEFAULT NULL,
  `email` varchar(255) DEFAULT NULL,
  `uber_email` varchar(255) DEFAULT NULL,
  `uber_prefix` varchar(5) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT NULL,
  `uber_phone` varchar(255) DEFAULT NULL,
  `uuid_id` varchar(255) DEFAULT NULL,
  `planday_id` int DEFAULT NULL,
  `navision_id` int DEFAULT NULL,
  `telegram_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT NULL,
  `bringoz_id` varchar(255) DEFAULT NULL,
  `tookan_id` int DEFAULT NULL,
  `STATUS` varchar(255) DEFAULT 'ACTIVE',
  `fleet` int DEFAULT NULL,
  `salutation` int DEFAULT NULL,
  `typ` int DEFAULT NULL,
  `role` int DEFAULT NULL,
  `application_date` date DEFAULT NULL,
  `vehicle` varchar(50) DEFAULT NULL,
  `approval` int DEFAULT NULL,
  `address` varchar(100) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT NULL,
  `postal_code` int DEFAULT NULL,
  `location` varchar(50) DEFAULT NULL,
  `country` varchar(50) DEFAULT NULL,
  `ahv_number` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT NULL,
  `birth_date` date DEFAULT NULL,
  `language` varchar(50) DEFAULT NULL,
  `nationality` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT NULL,
  `first_conversation` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT NULL,
  `first_work_day` date DEFAULT NULL,
  `last_work_day` date DEFAULT NULL,
  `entry_date_contract_on_duty_ag` date DEFAULT NULL,
  `approval_until` date DEFAULT NULL,
  `civil_status` int DEFAULT NULL,
  `other_jobs` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT NULL,
  `number_of_children` int DEFAULT NULL,
  `entry_date_old_contract` date DEFAULT NULL,
  `entry_date_onduty_ag` date DEFAULT NULL,
  `marriage_date` date DEFAULT NULL,
  `divorce_date` date DEFAULT NULL,
  `partner_name` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT NULL,
  `partner_surname` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT NULL,
  `partner_ahv_number` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT NULL,
  `partner_nationality` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT NULL,
  `partner_address` varchar(100) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT NULL,
  `partner_job` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT NULL,
  `iban` varchar(34) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT NULL,
  `missing_documents` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT NULL,
  `termination_date` date DEFAULT NULL,
  `termination_final_date` date DEFAULT NULL,
  `termination_reason` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT NULL,
  `out_of_system` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT NULL,
  `note` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci,
  `status_application` int DEFAULT NULL,
  `vehicle_model` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT NULL,
  `able_to_drive` tinyint(1) DEFAULT NULL,
  `application_from_where` varchar(100) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT NULL,
  `region` int DEFAULT NULL,
  `status_work` int DEFAULT NULL,
  `introduction_with` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT NULL,
  `introduction_date` date DEFAULT NULL,
  `start_short_operation` date DEFAULT NULL,
  `private_mail` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT NULL,
  `password` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT NULL,
  `admin` int NOT NULL DEFAULT '0',
  `navision` tinyint(1) DEFAULT NULL,
  `current_state` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT NULL,
  `b_opunit` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT NULL,
  `b_status` int DEFAULT NULL,
  `family_member` int NOT NULL DEFAULT '0',
  `child_allowances` int NOT NULL DEFAULT '0',
  `deleted` int NOT NULL DEFAULT '0',
  `doc_url` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci,
  `telegram_language` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

--
-- Daten für Tabelle `users`
--

INSERT INTO `users` (`id`, `user_id`, `user_name`, `first_name`, `last_name`, `company_name`, `phone`, `prefix`, `gender`, `email`, `uber_email`, `uber_prefix`, `uber_phone`, `uuid_id`, `planday_id`, `navision_id`, `telegram_id`, `bringoz_id`, `tookan_id`, `STATUS`, `fleet`, `salutation`, `typ`, `role`, `application_date`, `vehicle`, `approval`, `address`, `postal_code`, `location`, `country`, `ahv_number`, `birth_date`, `language`, `nationality`, `first_conversation`, `first_work_day`, `last_work_day`, `entry_date_contract_on_duty_ag`, `approval_until`, `civil_status`, `other_jobs`, `number_of_children`, `entry_date_old_contract`, `entry_date_onduty_ag`, `marriage_date`, `divorce_date`, `partner_name`, `partner_surname`, `partner_ahv_number`, `partner_nationality`, `partner_address`, `partner_job`, `iban`, `missing_documents`, `termination_date`, `termination_final_date`, `termination_reason`, `out_of_system`, `note`, `status_application`, `vehicle_model`, `able_to_drive`, `application_from_where`, `region`, `status_work`, `introduction_with`, `introduction_date`, `start_short_operation`, `private_mail`, `password`, `admin`, `navision`, `current_state`, `b_opunit`, `b_status`, `family_member`, `child_allowances`, `deleted`, `doc_url`, `telegram_language`) VALUES
(30978183, '1028', 'Janakan Selvathas', 'Janakan', 'Selvathas', NULL, '799912323', '+41', 1, 'test@gmail.com', NULL, NULL, NULL, '247cf780-cd02-437e-9bdf-879d1e897db1', 1157085, 100006, '1234', '180e240eb8f4c6ffe3f09b85803', 1979335, 'ACTIVE', 1, 2, 5, NULL, '2021-08-31', 'Auto', 1, 'Schönaustrasse 58, 4058 Basel', 4058, 'Basel', 'Switzerland', '782.1234.9213.123', '2002-01-01', 'Deutsch', 'Switzerland', 'Andere', '2024-05-24', '2024-09-13', NULL, '2199-12-30', 1, NULL, 0, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'CH02392034023952029', NULL, NULL, NULL, NULL, NULL, NULL, 10, 'Toyota corolla e11 asds', 1, 'Indeed', 36, 6, 'Hakan', '2021-09-10', NULL, 'test@gmail.com', '$2y$10$GTUDVLuSQfaklidwWkSq2eeFVeHCXE9BKXUTzizeYwzD34wvyrGeG', 0, NULL, NULL, '1558658', 0, 0, 0, 0, 'https://drive.google.com/drive/folders/1SFTYwSrfVOf6b4GY5ilvRB8ZUd6Hzf0T', 'Deutsch');

--
-- Indizes der exportierten Tabellen
--

--
-- Indizes für die Tabelle `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_approval` (`approval`),
  ADD KEY `fk_civil_status` (`civil_status`),
  ADD KEY `fk_fleet` (`fleet`),
  ADD KEY `fk_region` (`region`),
  ADD KEY `fk_status_application` (`status_application`),
  ADD KEY `fk_typ` (`typ`),
  ADD KEY `fk_status_work` (`status_work`),
  ADD KEY `fk_salutation` (`salutation`),
  ADD KEY `idx_users_ids` (`user_id`,`tookan_id`,`planday_id`);

--
-- AUTO_INCREMENT für exportierte Tabellen
--

--
-- AUTO_INCREMENT für Tabelle `users`
--
ALTER TABLE `users`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=30984734;

--
-- Constraints der exportierten Tabellen
--

--
-- Constraints der Tabelle `users`
--
ALTER TABLE `users`
  ADD CONSTRAINT `fk_approval` FOREIGN KEY (`approval`) REFERENCES `users_approval` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_civil_status` FOREIGN KEY (`civil_status`) REFERENCES `users_civil_status` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_fleet` FOREIGN KEY (`fleet`) REFERENCES `users_fleet` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_region` FOREIGN KEY (`region`) REFERENCES `users_region` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_salutation` FOREIGN KEY (`salutation`) REFERENCES `users_salution` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_status_application` FOREIGN KEY (`status_application`) REFERENCES `users_status_application` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  ADD CONSTRAINT `fk_status_work` FOREIGN KEY (`status_work`) REFERENCES `users_status_work` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;

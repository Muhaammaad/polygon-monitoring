-- phpMyAdmin SQL Dump
-- version 5.2.1deb3
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Erstellungszeit: 23. Dez 2025 um 10:25
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
-- Tabellenstruktur für Tabelle `uber_warnings`
--

CREATE TABLE `uber_warnings` (
  `id` int NOT NULL,
  `driver_id` varchar(255) DEFAULT NULL,
  `note` varchar(255) DEFAULT NULL,
  `counter` int DEFAULT NULL,
  `ts` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

--
-- Daten für Tabelle `uber_warnings`
--

INSERT INTO `uber_warnings` (`id`, `driver_id`, `note`, `counter`, `ts`) VALUES
(142505, '3baee4a0-4ec1-4d4c-9b60-38392195e47d', 'pause', 1, '2025-10-01 19:50:02'),
(142506, '1bd69d71-5d7a-43bb-83f3-171321736eae', 'out_of_town', 1, '2025-10-01 20:00:03'),
(142507, '7c293b2d-a9f2-468a-9e56-46673f238bc5', 'login_outside_zone', 1, '2025-10-01 20:50:02'),
(142508, '7c293b2d-a9f2-468a-9e56-46673f238bc5', 'login_inside_zone', 1, '2025-10-01 21:40:02');

--
-- Indizes der exportierten Tabellen
--

--
-- Indizes für die Tabelle `uber_warnings`
--
ALTER TABLE `uber_warnings`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT für exportierte Tabellen
--

--
-- AUTO_INCREMENT für Tabelle `uber_warnings`
--
ALTER TABLE `uber_warnings`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=142509;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;

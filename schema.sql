-- phpMyAdmin SQL Dump
-- version 5.2.1deb2
-- https://www.phpmyadmin.net/
--
-- Hôte : localhost:3306
-- Généré le : lun. 27 nov. 2023 à 15:38
-- Version du serveur : 8.0.35-1
-- Version de PHP : 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de données : `db_SAE32`
--

-- --------------------------------------------------------

--
-- Structure de la table `colis`
--

CREATE TABLE `colis` (
  `id` int NOT NULL,
  `poids` int DEFAULT NULL,
  `hauteur` int DEFAULT NULL,
  `largeur` int DEFAULT NULL,
  `longueur` int DEFAULT NULL,
  `etat` varchar(20) DEFAULT NULL,
  `dateEmballage` date DEFAULT NULL,
  `dateArriveDepot` date DEFAULT NULL,
  `dateDepartDepot` date DEFAULT NULL,
  `dateLivraison` date DEFAULT NULL,
  `dateReception` date DEFAULT NULL,
  `expediteur_id` int DEFAULT NULL,
  `transporteur_id` int DEFAULT NULL,
  `destinataire_id` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Déchargement des données de la table `colis`
--

INSERT INTO `colis` (`id`, `poids`, `hauteur`, `largeur`, `longueur`, `etat`, `dateEmballage`, `dateArriveDepot`, `dateDepartDepot`, `dateLivraison`, `dateReception`, `expediteur_id`, `transporteur_id`, `destinataire_id`) VALUES
(1, 102, 800, 800, 600, 'En attente', '2023-11-27', NULL, NULL, NULL, NULL, 2, 1, 4),
(2, 300, 300, 500, 500, 'En attente', '2023-11-27', NULL, NULL, NULL, NULL, 2, 1, 4);

-- --------------------------------------------------------

--
-- Structure de la table `utilisateur`
--

CREATE TABLE `utilisateur` (
  `id` int NOT NULL,
  `nom` text NOT NULL,
  `email` text NOT NULL,
  `mot_de_passe` text NOT NULL,
  `role` varchar(50) DEFAULT NULL,
  `adresse` text,
  `codePostal` text,
  `ville` text,
  `tel` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Déchargement des données de la table `utilisateur`
--

INSERT INTO `utilisateur` (`id`, `nom`, `email`, `mot_de_passe`, `role`, `adresse`, `codePostal`, `ville`, `tel`) VALUES
(1, 'MUXART', 'lilian.catalan@orange.fr', 'scrypt:32768:8:1$tIZz6LbSLjkHFkYe$ca2f783a2d11fe55541b9b31188c945ff27cd6bfddb9b9c989a32fb8816d9189e705b0fa0e5b4e2786f04a2ac05dbabd5305b132ca6a55530bb4712a336c29e3', 'transporteur', NULL, NULL, NULL, NULL),
(2, 'admin', 'admin@admin.fr', 'scrypt:32768:8:1$cPeu5DBgrq5va8EU$bf55ac48993ae2d163c9e14964e0dc482062c57e51e2d28d5bee7477d08e345191f8c1cd4baa7eaaefab9a194a206bd356e219a136d944bc3df92b455739b81f', 'admin', 'test', 'test', 'test', 'test'),
(4, 'Lemaitre Nathan', 'nathan.lemaitre34560@gmail.com', 'scrypt:32768:8:1$Dza3vPnLw9l6Wfc2$4ccd38925ffbbe804f73d3859e219eecd181262c613f6d4dfd6c3ad3111c54ad95e1f1e6b28bce79064f713a06a994098834a739dae5ed515faea80d66e97b73', 'user', '280 chemin du pontil', '34560', 'Villeveyrac', '0639692112');

--
-- Index pour les tables déchargées
--

--
-- Index pour la table `colis`
--
ALTER TABLE `colis`
  ADD PRIMARY KEY (`id`),
  ADD KEY `expediteur_id` (`expediteur_id`),
  ADD KEY `transporteur_id` (`transporteur_id`),
  ADD KEY `destinataire_id` (`destinataire_id`);

--
-- Index pour la table `utilisateur`
--
ALTER TABLE `utilisateur`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`(255));

--
-- AUTO_INCREMENT pour les tables déchargées
--

--
-- AUTO_INCREMENT pour la table `colis`
--
ALTER TABLE `colis`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT pour la table `utilisateur`
--
ALTER TABLE `utilisateur`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- Contraintes pour les tables déchargées
--

--
-- Contraintes pour la table `colis`
--
ALTER TABLE `colis`
  ADD CONSTRAINT `Colis_ibfk_1` FOREIGN KEY (`expediteur_id`) REFERENCES `utilisateur` (`id`),
  ADD CONSTRAINT `Colis_ibfk_2` FOREIGN KEY (`transporteur_id`) REFERENCES `utilisateur` (`id`),
  ADD CONSTRAINT `Colis_ibfk_3` FOREIGN KEY (`destinataire_id`) REFERENCES `utilisateur` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
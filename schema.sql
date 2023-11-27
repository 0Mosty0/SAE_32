-- Fichier schema.sql

-- Supprime la table si elle existe déjà
DROP TABLE IF EXISTS utilisateurs;

-- Crée une nouvelle table utilisateurs
CREATE TABLE utilisateurs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nom TEXT NOT NULL,
    email TEXT NOT NULL,
    mot_de_passe TEXT NOT NULL,
    role VARCHAR(50) DEFAULT 'user' -- 'user' par défaut
);



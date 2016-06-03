DROP TABLE IF EXISTS UserCredentials;
DROP EXTENSION IF EXISTS citext CASCADE;
CREATE EXTENSION citext;
CREATE TABLE UserCredentials(
	first_name text,
	last_name text,
	email citext NOT NULL,
	password text NOT NULL,
	salt text NOT NULL,
	dob	date NOT NULL,
	PRIMARY KEY(email)
);

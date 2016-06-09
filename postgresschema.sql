DROP TABLE IF EXISTS UserCredentials;
DROP TABLE IF EXISTS LoggedInUser;
DROP EXTENSION IF EXISTS citext CASCADE;
CREATE EXTENSION citext;
CREATE TABLE IF NOT EXISTS UserCredentials(
	first_name text,
	last_name text,
	email citext NOT NULL,
	password text NOT NULL,
	salt text NOT NULL,
	dob	date NOT NULL,
	PRIMARY KEY(email)
);

CREATE TABLE IF NOT EXISTS LoggedInUser(
    email citext references UserCredentials(email),
    lastloggedin timestamp,
    loggedin boolean,
    PRIMARY KEY(email)
);

CREATE OR REPLACE FUNCTION insert_user_logged() RETURNS TRIGGER as $_$
	BEGIN
		INSERT INTO LoggedInUser VALUES (new.email,now(),True);
		RETURN NEW;
	END;
$_$ LANGUAGE plpgsql;

CREATE TRIGGER user_loggedin AFTER INSERT ON UserCredentials
	FOR EACH ROW
	EXECUTE PROCEDURE insert_user_logged();
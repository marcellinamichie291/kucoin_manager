-- upgrade --
CREATE TABLE IF NOT EXISTS "dummymodel" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "name" VARCHAR(200) NOT NULL
) /* Model for demo purpose. */;
CREATE TABLE IF NOT EXISTS "accountmodel" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "name" VARCHAR(200) NOT NULL,
    "api_key" VARCHAR(200) NOT NULL,
    "api_secret" VARCHAR(200) NOT NULL,
    "api_passphrase" VARCHAR(200) NOT NULL
) /* Model for demo purpose. */;
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSON NOT NULL
);

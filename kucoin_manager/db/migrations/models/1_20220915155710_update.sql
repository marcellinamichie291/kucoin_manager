-- upgrade --
ALTER TABLE "account" ADD "api_type" VARCHAR(20) NOT NULL  DEFAULT 'future';
-- downgrade --
ALTER TABLE "account" DROP COLUMN "api_type";

-- upgrade --
ALTER TABLE "orders" ADD "message" VARCHAR(255) NOT NULL  DEFAULT 'success';
-- downgrade --
ALTER TABLE "orders" DROP COLUMN "message";

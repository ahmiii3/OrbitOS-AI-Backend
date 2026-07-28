from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "users" (
    "id" UUID NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL,
    "name" VARCHAR(255) NOT NULL,
    "email" VARCHAR(255) NOT NULL UNIQUE,
    "hashed_password" VARCHAR(255) NOT NULL,
    "role" VARCHAR(50) NOT NULL,
    "is_active" BOOL NOT NULL,
    "email_verified" BOOL NOT NULL
);
CREATE INDEX IF NOT EXISTS "idx_users_email_133a6f" ON "users" ("email");
COMMENT ON TABLE "users" IS 'User entity model in PostgreSQL (Tortoise ORM).';
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "eJztmF1v2jAUhv9KlCsqdail0FbTNAlapjIV0kHYpk6TZRIDVhM7jZ1S1PHfZ5uYkJBQqN"
    "quTL0B8vocx3ne+OPwYPrURR4r9xkKzY/Gg0mgj8SPlL5vmDAIElUKHA48FRiJCKXAAeMh"
    "dLgQh9BjSEguYk6IA44pkaGyMwMRjvnUUD0ZmBhXlPFRiHrfLo2STUNOMUOG1W3vlWWnLn"
    "VEr5iMnpgfEXwbIcDpCPGxesRfv4WMiYvuEdOXwQ0YYuS5KQLYlR0oHfBpoLR+v3X+RUXK"
    "sQ2AQ73IJ0l0MOVjShbhUYTdssyRbSNEUAg5cpcAkcjzYpBamo9YCDyM0GKobiK4aAgjT2"
    "I2Pw0j4ki6hrqT/Kh+joe2FAZAx7JBr2kDYK64IoeQAR1LDiXSUUy4BPUwm/ebAFGqKW9w"
    "dlHvlo6O9xSCuR9M4zJnKhFyOE9V0BPKTogkEwD5Ku1z0cKxj/KJpzMz5N04tax/PMUBLS"
    "QWJC+2hqvxvQBwUzygaxFvGnu/xgC71W727Hr7St7OZ+zWU/zqdlO2VJQ6zailuV9UzNn5"
    "TF50Yvxo2ReGvDSurU4z6+oizr425ZhgxCkgdAKgu/SaalVTE5GJ61HgPtH1dOa762/Fdc"
    "1oyfZ49Inr6nvF77MxDPO91vEZlwWtXfTVh/fAQ2TEx+KyUqutMfZ7vauWVBGVcasTN1Xm"
    "bbMUX+RD7G0DeJHwPIQf37F2m+8YsrFYegLI2ISGOceDYtI5qe9v9WbUQ+pttWro+Nfjq8"
    "7AL3XsShOuHWwAuHZQyFc2pfFiBsShHd/lMG5QgRKSggPvcl6G9UAkvhRsvaa87gm3YVmX"
    "qV220bIzjPvtRrNbOlToRRDmSm517LxVGtyhEIsb5Swia6mvJr8i+oWyU+xlgTe8WSo+pD"
    "CAzs0Ehi5YaaEVWhS72uRX/KwCCRwpfvI55VPFlXRdeOaMzZwaO27ZX1dlwyTmsTK7GPkz"
    "F8MtwreohYXR2fcynspv90gxkkP4UDmsnlRPj46rpyJEDXOhnKx5bfXML659xTRmckhbbG"
    "5LKe/nh83OD3JSbUE4Dv8P6R4ebHJ4EFGFdFVbmq64I0ckp4z/2rM6BX/cJCnZ+h073Phj"
    "eJitrBU7QHsNXAkjtYVppqV2/WcW99ml1chW37KDxr/ezGZ/ARvSEZc="
)

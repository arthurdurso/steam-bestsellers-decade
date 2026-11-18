-- =============================================================
-- Estrutura do projeto no Unity Catalog
-- Executar uma vez no SQL Editor do Databricks.
-- É idempotente: pode ser executado de novo sem erro nem duplicação.
-- =============================================================

-- Catalog do projeto: isola tudo do Steam Promo Impact.
CREATE CATALOG IF NOT EXISTS steam
COMMENT 'Steam Promo Impact: as promoções na Steam compensam para as publishers?';

-- Camadas da arquitetura medallion.
CREATE SCHEMA IF NOT EXISTS steam.bronze
COMMENT 'Dados crus: JSON das APIs (volume raw) e tabelas carregadas pelo Auto Loader';

CREATE SCHEMA IF NOT EXISTS steam.silver
COMMENT 'Dados tratados: modelos staging e intermediate do dbt';

CREATE SCHEMA IF NOT EXISTS steam.gold
COMMENT 'Dados de negócio: dimensões, fatos e marts do dbt';

CREATE SCHEMA IF NOT EXISTS steam.ci
COMMENT 'Execuções do dbt no CI (GitHub Actions), isoladas dos dados reais';

-- Área de pouso dos coletores: /Volumes/steam/bronze/raw/<fonte>/dt=YYYY-MM-DD/...
CREATE VOLUME IF NOT EXISTS steam.bronze.raw
COMMENT 'JSON cru gravado pelos coletores, particionado por fonte e data';

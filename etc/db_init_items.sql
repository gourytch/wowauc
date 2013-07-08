BEGIN;

CREATE SCHEMA info;

  
CREATE TABLE info.item_data (
  id				BIGINT PRIMARY KEY,
  icon				VARCHAR(64),
  displayInfoId 		INTEGER,
  
  equipable			BOOLEAN NOT NULL DEFAULT FALSE,
  stackable			BOOLEAN NOT NULL DEFAULT FALSE,
  
  itemClass			INTEGER NOT NULL DEFAULT 0,
  itemSubClass			INTEGER NOT NULL DEFAULT 0,
  itemLevel			INTEGER NOT NULL DEFAULT 0,
  quality			INTEGER NOT NULL DEFAULT 0,
  disenchantingSkillRank	INTEGER NOT NULL DEFAULT 0,
  itemSourceId			INTEGER,
  itemSourceType		VARCHAR(16),

  maxCount			INTEGER NOT NULL DEFAULT 1,
  containerSlots		INTEGER NOT NULL DEFAULT 0,

  buyPrice			INTEGER,
  sellPrice			INTEGER
);



CREATE TABLE info.item_names (
  id			BIGINT NOT NULL,
  locale		CHARACTER(5),
  name			VARCHAR(100),
  description		VARCHAR(512),
  PRIMARY KEY (id, locale)
 );


COMMIT;


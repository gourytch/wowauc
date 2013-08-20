BEGIN;

CREATE SCHEMA auc;

CREATE TABLE auc.realms (
    id          SERIAL PRIMARY KEY,
    region      VARCHAR(2) NOT NULL,
    name        VARCHAR(64) NOT NULL,
    slug        VARCHAR(64) NOT NULL,
    locale      VARCHAR(8) NOT NULL DEFAULT 'en_US'
);


CREATE UNIQUE INDEX uix_auc_realms ON auc.realms (region, name);
CREATE UNIQUE INDEX ix_auc_realms_slug ON auc.realms (region, slug);


CREATE TABLE auc.houses (
    id          SERIAL PRIMARY KEY,
    realm_id    INTEGER REFERENCES auc.realms(id),
    fraction    CHAR(1) NOT NULL DEFAULT 'N'
);


CREATE UNIQUE INDEX uix_auc_houses ON auc.houses (realm_id, fraction);


CREATE TABLE auc.lots (
    id          BIGSERIAL PRIMARY KEY,
    t_open      TIMESTAMP NOT NULL,
    t_mod       TIMESTAMP NOT NULL,
    house_id    INTEGER REFERENCES auc.houses(id),
    wowauc_id   BIGINT NOT NULL,
    item_id     INTEGER NOT NULL,
    owner       VARCHAR(64) NOT NULL,
    startbid    BIGINT NOT NULL,
    lastbid     BIGINT NOT NULL,
    buyout      BIGINT NOT NULL DEFAULT 0,
    quantity    INTEGER NOT NULL DEFAULT 1,
    rand        INTEGER NOT NULL DEFAULT 0,
    seed        INTEGER NOT NULL DEFAULT 0,
);


CREATE UNIQUE INDEX uix_auc_wowauc_id ON auc.lots (house_id, wowauc_id);


CREATE TABLE auc.open_lots (
    tcode       CHAR(1) NOT NULL, -- V|L|M|S|x
    t_deadline  TIMESTAMP NOT NULL,
) INHERITS (auc.lots);

CREATE TABLE auc.closed_lots (
    t_close     TIMESTAMP NOT NULL,
    success     BOOLEAN NOT NULL
) INHERITS (auc.lots);


CREATE TABLE auc.push_sessions (
    id          BIGSERIAL PRIMARY KEY,
    house_id    INTEGER NOT NULL UNIQUE,
    wow_time    TIMESTAMP NOT NULL
);


CREATE TABLE auc.push_results (
    push_id     BIGINT PRIMARY KEY,
    house_id    INTEGER NOT NULL,
    wow_time    TIMESTAMP NOT NULL,
    num_open    INTEGER,
    num_closed  INTEGER,
    num_success INTEGER
);

-----------------------------------------------------------------------------


CREATE FUNCTION auc.guess_ktime_min (
    _time       TIMESTAMP,
    _code       TEXT)
RETURNS TIMESTAMP
STRICT LANGUAGE plpgsql AS $$

BEGIN

    CASE _code

        WHEN 'V', 'VERY_LONG' THEN
            RETURN _time + '12 HOURS'::INTERVAL;

        WHEN 'L', 'LONG' THEN
            RETURN _time + '2 HOURS'::INTERVAL;

        WHEN 'M', 'MEDIUM' THEN
            RETURN _time + '30 MINUTES'::INTERVAL;

        WHEN 'S', 'SHORT' THEN
            RETURN _time;

        ELSE
            RETURN NULL;

    END CASE;

END;
$$;


CREATE FUNCTION auc.guess_ktime_max (
    _time       TIMESTAMP,
    _code       TEXT)
RETURNS TIMESTAMP
STRICT LANGUAGE plpgsql AS $$

BEGIN

    CASE _code

        WHEN 'V', 'VERY_LONG' THEN
            RETURN _time + '48 HOURS'::INTERVAL;

        WHEN 'L', 'LONG' THEN
            RETURN _time + '12 HOURS'::INTERVAL;

        WHEN 'M', 'MEDIUM' THEN
            RETURN _time + '2 HOURS'::INTERVAL;

        WHEN 'S', 'SHORT' THEN
            RETURN _time + '30 MINUTES'::INTERVAL;

        ELSE
            RETURN NULL;

    END CASE;

END;
$$;


CREATE FUNCTION auc.add_realm (
    _region  TEXT,
    _name    TEXT,
    _slug    TEXT,
    _locale  TEXT)
RETURNS INTEGER
STRICT VOLATILE LANGUAGE plpgsql AS $$

DECLARE

    _realm_id   INTEGER;

BEGIN

    INSERT INTO auc.realms (region, name, slug, locale)
        VALUES (_region, _name, _slug, _locale);

    SELECT id INTO _realm_id FROM auc.realms
        WHERE region = _region AND name = _name;

    INSERT INTO auc.houses (realm_id, fraction)
        VALUES (_realm_id, 'A'), (_realm_id, 'H'), (_realm_id, 'N');

    RETURN _realm_id;

END;
$$;


CREATE FUNCTION auc.check_realm (
    _region  TEXT,
    _name    TEXT,
    _slug    TEXT,
    _locale  TEXT)
RETURNS INTEGER
STRICT VOLATILE LANGUAGE plpgsql AS $$

DECLARE

    _realm_id   INTEGER;

BEGIN

    SELECT id INTO _realm_id FROM auc.realms
        WHERE region = _region AND name = _name;

    IF NOT FOUND THEN

        _realm_id := auc.add_realm(_region, _name, _slug, _locale);

    END IF;

    RETURN _realm_id;

END;
$$;


CREATE FUNCTION auc.get_house_id (
    _region  TEXT,
    _name    TEXT,
    _house   CHARACTER(1))
RETURNS INTEGER
STRICT VOLATILE LANGUAGE plpgsql AS $$

DECLARE

    _house_id   INTEGER;

BEGIN

    SELECT H.id INTO _house_id 
        FROM auc.houses H, auc.realms R
        WHERE H.realm_id = R.id
        AND R.region = _region
        AND R.name = _name
        AND H.fraction = _house;

    RETURN _house_id;

END;
$$;


CREATE FUNCTION auc.push_start (
    _region     TEXT,
    _name       TEXT,
    _house      CHARACTER(1), -- A|H|N
    _wowtime    TIMESTAMP)
RETURNS BIGINT
STRICT VOLATILE LANGUAGE plpgsql AS $$

DECLARE

    _house_id   INTEGER;
    _push_id    BIGINT;

BEGIN

    _house_id := auc.get_house_id(_region, _name, _house);

    IF _house_id IS NULL THEN
        RETURN NULL;
    END IF;

    SELECT id INTO _push_id FROM auc.push_sessions
        WHERE house_id = _house_id;

    IF NOT FOUND THEN

        INSERT INTO auc.push_sessions (house_id, wow_time)
            VALUES (_house_id, _wowtime);

        SELECT id INTO _push_id FROM auc.push_sessions
            WHERE house_id = _house_id;

    END IF;

    RETURN _push_id;
END;
$$;



CREATE FUNCTION auc.push_lot (
    _push_id    INTEGER,
    _wowid      BIGINT,
    _item_id    INTEGER,
    _owner      TEXT,
    _bid        BIGINT,
    _buyout     BIGINT,
    _quantity   INTEGER,
    _timeleft   TEXT)
RETURNS BOOLEAN
STRICT VOLATILE LANGUAGE plpgsql AS $$

DECLARE

    _house_id   INTEGER;
    _wowtime    TIMESTAMP;
    _tcode      CHARACTER(1);
    _ktime      TIMESTAMP;
    _rec        auc.lots%ROWTYPE;

BEGIN

    SELECT house_id, wow_time
        INTO _house_id, _wowtime
        FROM auc.push_sessions
        WHERE id = _push_id;

    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;

    _tcode := left(_timeleft, 1);

    SELECT *
        INTO _rec
        FROM auc.lots
        WHERE house_id=_house_id
        AND wowauc_id=_wowid;

    IF NOT FOUND THEN

        _ktime := auc.guess_ktime_max(_wowtime, _tcode);

        INSERT INTO auc.lots (
            t_open, t_mod, t_deadline,
            house_id,
            wowauc_id, item_id, owner,
            startbid, lastbid, buyout,
            quantity, tcode,
            finished, success)
            VALUES (
                _wowtime, _wowtime, _ktime,
                _house_id,
                _wowid, _item_id, _owner,
                _bid, _bid, _buyout,
                _quantity, _tcode,
                FALSE, NULL);

        RETURN TRUE;

    ELSE -- IF FOUND

        IF _rec.finished THEN

            RAISE NOTICE 'LOT %:% ALREADY CLOSED',
                _rec.house_id, _rec.wowauc_id;

            RETURN FALSE;

        END IF;

        IF _rec.tcode <> _tcode THEN -- time duration was changed

            _ktime := auc.guess_ktime_max(_wowtime, _tcode);

--            RAISE NOTICE 'LOT %:% TCODE WAS CHANGED FROM % TO %, KTIME CHANGED FROM % TO %',
--                _rec.house_id, _rec.wowauc_id, _rec.tcode, _tcode, _rec.t_deadline, _ktime;

            _rec.lastbid    := _bid;
            _rec.tcode      := _tcode;
            _rec.t_deadline := _ktime;
        END IF;

        IF _rec.lastbid <> _bid THEN
--            RAISE NOTICE 'LOT %:% BID WAS CHANGED FROM % TO %',
--                _rec.house_id, _rec.wowauc_id, _rec.lastbid, _bid;
            _rec.lastbid    := _bid;
        END IF;

        IF _rec.buyout <> _buyout THEN
--            RAISE NOTICE 'LOT %:% BUYOUT WAS CHANGED FROM % TO %',
--                _rec.house_id, _rec.wowauc_id, _rec.buyout, _buyout;
            _rec.buyout     := _buyout;
        END IF;

        IF _rec.quantity <> _quantity THEN
--            RAISE NOTICE 'LOT %:% QUANTITY WAS CHANGED FROM % TO %',
--                _rec.house_id, _rec.wowauc_id, _rec.quantity, _quantity;
            _rec.quantity = _quantity;
        END IF;

        _rec.t_mod := _wowtime;

        UPDATE auc.lots
            SET t_mod       = _rec.t_mod,
                t_deadline  = _rec.t_deadline,
                lastbid     = _rec.lastbid,
                buyout      = _rec.buyout,
                quantity    = _rec.quantity,
                tcode       = _rec.tcode
            WHERE id = _rec.id;

        RETURN TRUE;

    END IF;

END;
$$;


CREATE FUNCTION auc.push_finish (_push_id BIGINT)
RETURNS BOOLEAN
STRICT VOLATILE LANGUAGE plpgsql AS $$

DECLARE

    _house_id   INTEGER;
    _wowtime    TIMESTAMP;
    _c          NO SCROLL CURSOR (hid INTEGER, wt TIMESTAMP)
                    FOR SELECT *
                    FROM auc.lots
                    WHERE NOT finished
                    AND house_id = hid
                    AND t_mod < wt;
    _r          auc.lots%ROWTYPE;
    _success    BOOLEAN;

    _num_open       INTEGER;
    _num_closed     INTEGER;
    _num_success    INTEGER;

BEGIN

    SELECT house_id, wow_time
        INTO _house_id, _wowtime
        FROM auc.push_sessions
        WHERE id=_push_id;

    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;

    _num_closed := 0;
    _num_success := 0;

    OPEN _c(_house_id, _wowtime);

    FETCH _c INTO _r;

    WHILE FOUND LOOP

        CASE
            WHEN _r.startbid < _r.lastbid THEN
                _success := TRUE;
            WHEN _wowtime < _r.t_deadline THEN
                _success := TRUE;
            ELSE
                _success := FALSE;
        END CASE;

        UPDATE auc.lots
            SET finished = TRUE,
                success = _success,
                t_close = _wowtime
            WHERE CURRENT OF _c;

        _num_closed := _num_closed + 1;

        IF _success THEN
            _num_success := _num_success + 1;
        END IF;

        FETCH _c INTO _r;

    END LOOP;

    CLOSE _c;

    SELECT count(*)
        INTO _num_open
        FROM auc.lots
        WHERE NOT finished
        AND house_id = _house_id;

--    UPDATE auc.lots
--        SET finished = TRUE, success = TRUE, t_close = _wowtime
--        WHERE house_id = _house_id
--        AND NOT finished
--        AND (startbid < lastbid);
--
--    UPDATE auc.lots
--        SET finished = TRUE, success = TRUE, t_close = _wowtime
--        WHERE house_id = _house_id
--        AND NOT finished
--        AND t_mod < _wowtime
--        AND t_deadline > _wowtime;
--
--    UPDATE auc.lots
--        SET finished = TRUE, success = FALSE, t_close = _wowtime
--        WHERE house_id = _house_id
--        AND NOT finished
--        AND t_mod < _wowtime;

    INSERT
        INTO auc.push_results (
            push_id, house_id, wow_time,
            num_open, num_closed, num_success)
        VALUES (
            _push_id, _house_id, _wowtime,
            _num_open, _num_closed, _num_success);

    DELETE FROM auc.push_sessions
        WHERE id=_push_id;

    RETURN TRUE;

END;
$$;


CREATE FUNCTION auc.push_need (
    _region     TEXT,
    _name       TEXT,
    _house      CHARACTER(1), -- A|H|N
    _wowtime    TIMESTAMP)
RETURNS BOOLEAN
STRICT VOLATILE LANGUAGE plpgsql AS $$
DECLARE

    _house_id   INTEGER;
    _max_time   TIMESTAMP;
BEGIN

    _house_id := auc.get_house_id(_region, _name, _house);

    IF _house_id IS NULL THEN
        RETURN NULL;
    END IF;

    SELECT max(wow_time)
        INTO _max_time
        FROM auc.push_results
        WHERE house_id = _house_id;

    IF NOT FOUND OR _max_time IS NULL THEN
        RETURN TRUE;
    END IF;

    RETURN (_max_time < _wowtime);
END;
$$;

-----------------------------------------------------------------------------

-- SELECT auc.add_realm ('eu', 'Fordragon', 'fordragon', 'ru_RU');

COMMIT;


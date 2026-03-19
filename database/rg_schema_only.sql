--
-- PostgreSQL database dump
--

\restrict fNoxRykVjUf5JE8pHYYXbTm7Wq3JLgImhyAyI1JuGWZcV5FSFcTaP2CMUiBUXuL

-- Dumped from database version 14.22 (Ubuntu 14.22-0ubuntu0.22.04.1)
-- Dumped by pg_dump version 14.22 (Ubuntu 14.22-0ubuntu0.22.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: cpe_metrics; Type: TABLE; Schema: public; Owner: rg
--

CREATE TABLE public.cpe_metrics (
    id integer NOT NULL,
    ts timestamp without time zone DEFAULT now() NOT NULL,
    device_id text,
    cpu_pct double precision,
    mem_pct double precision,
    temp_c double precision,
    rx_mbps double precision,
    tx_mbps double precision,
    latency_ms double precision,
    wifi_clients integer,
    wifi_clients_per_band text,
    run_id integer
);


ALTER TABLE public.cpe_metrics OWNER TO rg;

--
-- Name: cpe_metrics_id_seq; Type: SEQUENCE; Schema: public; Owner: rg
--

CREATE SEQUENCE public.cpe_metrics_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.cpe_metrics_id_seq OWNER TO rg;

--
-- Name: cpe_metrics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: rg
--

ALTER SEQUENCE public.cpe_metrics_id_seq OWNED BY public.cpe_metrics.id;


--
-- Name: cpe_status; Type: TABLE; Schema: public; Owner: rg
--

CREATE TABLE public.cpe_status (
    id integer NOT NULL,
    ts timestamp without time zone DEFAULT now() NOT NULL,
    device_id text,
    internet_ok boolean,
    cloud_ok boolean,
    ipv4 text,
    mac text,
    serial text,
    model text,
    fw text,
    probe_ms integer,
    error text
);


ALTER TABLE public.cpe_status OWNER TO rg;

--
-- Name: cpe_status_id_seq; Type: SEQUENCE; Schema: public; Owner: rg
--

CREATE SEQUENCE public.cpe_status_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.cpe_status_id_seq OWNER TO rg;

--
-- Name: cpe_status_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: rg
--

ALTER SEQUENCE public.cpe_status_id_seq OWNED BY public.cpe_status.id;


--
-- Name: event_log; Type: TABLE; Schema: public; Owner: rg
--

CREATE TABLE public.event_log (
    id integer NOT NULL,
    ts timestamp without time zone DEFAULT now() NOT NULL,
    level character varying(16) NOT NULL,
    message text NOT NULL
);


ALTER TABLE public.event_log OWNER TO rg;

--
-- Name: event_log_id_seq; Type: SEQUENCE; Schema: public; Owner: rg
--

CREATE SEQUENCE public.event_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.event_log_id_seq OWNER TO rg;

--
-- Name: event_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: rg
--

ALTER SEQUENCE public.event_log_id_seq OWNED BY public.event_log.id;


--
-- Name: run_log; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.run_log (
    id integer NOT NULL,
    run_id integer NOT NULL,
    log text
);


ALTER TABLE public.run_log OWNER TO postgres;

--
-- Name: run_log_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.run_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.run_log_id_seq OWNER TO postgres;

--
-- Name: run_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.run_log_id_seq OWNED BY public.run_log.id;


--
-- Name: runs; Type: TABLE; Schema: public; Owner: rg
--

CREATE TABLE public.runs (
    id integer NOT NULL,
    script_id integer,
    status text NOT NULL,
    started_at timestamp without time zone DEFAULT now() NOT NULL,
    finished_at timestamp without time zone,
    exit_code integer,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    log text
);


ALTER TABLE public.runs OWNER TO rg;

--
-- Name: runs_id_seq; Type: SEQUENCE; Schema: public; Owner: rg
--

CREATE SEQUENCE public.runs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.runs_id_seq OWNER TO rg;

--
-- Name: runs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: rg
--

ALTER SEQUENCE public.runs_id_seq OWNED BY public.runs.id;


--
-- Name: scripts; Type: TABLE; Schema: public; Owner: rg
--

CREATE TABLE public.scripts (
    id integer NOT NULL,
    name text NOT NULL,
    suite text NOT NULL,
    entrypoint text,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone,
    zip_path text
);


ALTER TABLE public.scripts OWNER TO rg;

--
-- Name: scripts_id_seq; Type: SEQUENCE; Schema: public; Owner: rg
--

CREATE SEQUENCE public.scripts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.scripts_id_seq OWNER TO rg;

--
-- Name: scripts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: rg
--

ALTER SEQUENCE public.scripts_id_seq OWNED BY public.scripts.id;


--
-- Name: telemetry; Type: TABLE; Schema: public; Owner: rg
--

CREATE TABLE public.telemetry (
    id integer NOT NULL,
    ts timestamp without time zone DEFAULT now() NOT NULL,
    label character varying(64) NOT NULL,
    metric character varying(32) NOT NULL,
    value double precision NOT NULL
);


ALTER TABLE public.telemetry OWNER TO rg;

--
-- Name: telemetry_id_seq; Type: SEQUENCE; Schema: public; Owner: rg
--

CREATE SEQUENCE public.telemetry_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.telemetry_id_seq OWNER TO rg;

--
-- Name: telemetry_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: rg
--

ALTER SEQUENCE public.telemetry_id_seq OWNED BY public.telemetry.id;


--
-- Name: wifi_radio_state; Type: TABLE; Schema: public; Owner: rg
--

CREATE TABLE public.wifi_radio_state (
    ts timestamp with time zone DEFAULT now() NOT NULL,
    if_name text,
    channel text,
    ht_mode text,
    tx_power text,
    country text
);


ALTER TABLE public.wifi_radio_state OWNER TO rg;

--
-- Name: cpe_metrics id; Type: DEFAULT; Schema: public; Owner: rg
--

ALTER TABLE ONLY public.cpe_metrics ALTER COLUMN id SET DEFAULT nextval('public.cpe_metrics_id_seq'::regclass);


--
-- Name: cpe_status id; Type: DEFAULT; Schema: public; Owner: rg
--

ALTER TABLE ONLY public.cpe_status ALTER COLUMN id SET DEFAULT nextval('public.cpe_status_id_seq'::regclass);


--
-- Name: event_log id; Type: DEFAULT; Schema: public; Owner: rg
--

ALTER TABLE ONLY public.event_log ALTER COLUMN id SET DEFAULT nextval('public.event_log_id_seq'::regclass);


--
-- Name: run_log id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.run_log ALTER COLUMN id SET DEFAULT nextval('public.run_log_id_seq'::regclass);


--
-- Name: runs id; Type: DEFAULT; Schema: public; Owner: rg
--

ALTER TABLE ONLY public.runs ALTER COLUMN id SET DEFAULT nextval('public.runs_id_seq'::regclass);


--
-- Name: scripts id; Type: DEFAULT; Schema: public; Owner: rg
--

ALTER TABLE ONLY public.scripts ALTER COLUMN id SET DEFAULT nextval('public.scripts_id_seq'::regclass);


--
-- Name: telemetry id; Type: DEFAULT; Schema: public; Owner: rg
--

ALTER TABLE ONLY public.telemetry ALTER COLUMN id SET DEFAULT nextval('public.telemetry_id_seq'::regclass);


--
-- Name: cpe_metrics cpe_metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: rg
--

ALTER TABLE ONLY public.cpe_metrics
    ADD CONSTRAINT cpe_metrics_pkey PRIMARY KEY (id);


--
-- Name: cpe_status cpe_status_pkey; Type: CONSTRAINT; Schema: public; Owner: rg
--

ALTER TABLE ONLY public.cpe_status
    ADD CONSTRAINT cpe_status_pkey PRIMARY KEY (id);


--
-- Name: event_log event_log_pkey; Type: CONSTRAINT; Schema: public; Owner: rg
--

ALTER TABLE ONLY public.event_log
    ADD CONSTRAINT event_log_pkey PRIMARY KEY (id);


--
-- Name: run_log run_log_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.run_log
    ADD CONSTRAINT run_log_pkey PRIMARY KEY (id);


--
-- Name: runs runs_pkey; Type: CONSTRAINT; Schema: public; Owner: rg
--

ALTER TABLE ONLY public.runs
    ADD CONSTRAINT runs_pkey PRIMARY KEY (id);


--
-- Name: scripts scripts_pkey; Type: CONSTRAINT; Schema: public; Owner: rg
--

ALTER TABLE ONLY public.scripts
    ADD CONSTRAINT scripts_pkey PRIMARY KEY (id);


--
-- Name: telemetry telemetry_pkey; Type: CONSTRAINT; Schema: public; Owner: rg
--

ALTER TABLE ONLY public.telemetry
    ADD CONSTRAINT telemetry_pkey PRIMARY KEY (id);


--
-- Name: idx_cpe_metrics_ts; Type: INDEX; Schema: public; Owner: rg
--

CREATE INDEX idx_cpe_metrics_ts ON public.cpe_metrics USING btree (ts);


--
-- Name: idx_wifi_radio_state_ts; Type: INDEX; Schema: public; Owner: rg
--

CREATE INDEX idx_wifi_radio_state_ts ON public.wifi_radio_state USING btree (ts);


--
-- Name: ix_tel_metric_ts; Type: INDEX; Schema: public; Owner: rg
--

CREATE INDEX ix_tel_metric_ts ON public.telemetry USING btree (metric, ts);


--
-- Name: TABLE run_log; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.run_log TO rg;


--
-- Name: SEQUENCE run_log_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.run_log_id_seq TO rg;


--
-- PostgreSQL database dump complete
--

\unrestrict fNoxRykVjUf5JE8pHYYXbTm7Wq3JLgImhyAyI1JuGWZcV5FSFcTaP2CMUiBUXuL


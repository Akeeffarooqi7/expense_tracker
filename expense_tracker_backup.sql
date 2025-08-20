--
-- PostgreSQL database dump
--

-- Dumped from database version 17.5
-- Dumped by pg_dump version 17.5

-- Started on 2025-08-20 22:23:48

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
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
-- TOC entry 222 (class 1259 OID 16593)
-- Name: expenses; Type: TABLE; Schema: public; Owner: expense_user
--

CREATE TABLE public.expenses (
    id integer NOT NULL,
    user_id integer,
    amount numeric(12,2),
    category character varying(100),
    currency character varying(10),
    country character varying(100),
    description text,
    date date,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.expenses OWNER TO expense_user;

--
-- TOC entry 221 (class 1259 OID 16592)
-- Name: expenses_id_seq; Type: SEQUENCE; Schema: public; Owner: expense_user
--

CREATE SEQUENCE public.expenses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.expenses_id_seq OWNER TO expense_user;

--
-- TOC entry 4923 (class 0 OID 0)
-- Dependencies: 221
-- Name: expenses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: expense_user
--

ALTER SEQUENCE public.expenses_id_seq OWNED BY public.expenses.id;


--
-- TOC entry 220 (class 1259 OID 16585)
-- Name: otp_verification; Type: TABLE; Schema: public; Owner: expense_user
--

CREATE TABLE public.otp_verification (
    id integer NOT NULL,
    email character varying(255),
    otp character varying(10),
    expires_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.otp_verification OWNER TO expense_user;

--
-- TOC entry 219 (class 1259 OID 16584)
-- Name: otp_verification_id_seq; Type: SEQUENCE; Schema: public; Owner: expense_user
--

CREATE SEQUENCE public.otp_verification_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.otp_verification_id_seq OWNER TO expense_user;

--
-- TOC entry 4924 (class 0 OID 0)
-- Dependencies: 219
-- Name: otp_verification_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: expense_user
--

ALTER SEQUENCE public.otp_verification_id_seq OWNED BY public.otp_verification.id;


--
-- TOC entry 218 (class 1259 OID 16573)
-- Name: users; Type: TABLE; Schema: public; Owner: expense_user
--

CREATE TABLE public.users (
    id integer NOT NULL,
    email character varying(255) NOT NULL,
    password_hash character varying(255) NOT NULL,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.users OWNER TO expense_user;

--
-- TOC entry 217 (class 1259 OID 16572)
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: expense_user
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO expense_user;

--
-- TOC entry 4925 (class 0 OID 0)
-- Dependencies: 217
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: expense_user
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- TOC entry 4756 (class 2604 OID 16596)
-- Name: expenses id; Type: DEFAULT; Schema: public; Owner: expense_user
--

ALTER TABLE ONLY public.expenses ALTER COLUMN id SET DEFAULT nextval('public.expenses_id_seq'::regclass);


--
-- TOC entry 4754 (class 2604 OID 16588)
-- Name: otp_verification id; Type: DEFAULT; Schema: public; Owner: expense_user
--

ALTER TABLE ONLY public.otp_verification ALTER COLUMN id SET DEFAULT nextval('public.otp_verification_id_seq'::regclass);


--
-- TOC entry 4752 (class 2604 OID 16576)
-- Name: users id; Type: DEFAULT; Schema: public; Owner: expense_user
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- TOC entry 4917 (class 0 OID 16593)
-- Dependencies: 222
-- Data for Name: expenses; Type: TABLE DATA; Schema: public; Owner: expense_user
--

COPY public.expenses (id, user_id, amount, category, currency, country, description, date, created_at) FROM stdin;
1	1	50.00	food	Aud	Aus		2025-08-20	2025-08-20 15:25:36.407917
4	1	50.00	Transport	INR	India		2025-08-20	2025-08-20 18:24:55.087642
\.


--
-- TOC entry 4915 (class 0 OID 16585)
-- Dependencies: 220
-- Data for Name: otp_verification; Type: TABLE DATA; Schema: public; Owner: expense_user
--

COPY public.otp_verification (id, email, otp, expires_at, created_at) FROM stdin;
\.


--
-- TOC entry 4913 (class 0 OID 16573)
-- Dependencies: 218
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: expense_user
--

COPY public.users (id, email, password_hash, created_at) FROM stdin;
1	akeef.farooqi@gmail.com	scrypt:32768:8:1$rPe4cAyJhpskqX6e$155c3a02d6f1de248213a16710ccc76c6c53275c942fcf0d750cea6b1e3c0a6bffce7a22f6557719ae4d57a02535f1a27b00aa92a204c8b4cc3ed01cc1c2a553	2025-08-20 15:24:29.403277
\.


--
-- TOC entry 4926 (class 0 OID 0)
-- Dependencies: 221
-- Name: expenses_id_seq; Type: SEQUENCE SET; Schema: public; Owner: expense_user
--

SELECT pg_catalog.setval('public.expenses_id_seq', 4, true);


--
-- TOC entry 4927 (class 0 OID 0)
-- Dependencies: 219
-- Name: otp_verification_id_seq; Type: SEQUENCE SET; Schema: public; Owner: expense_user
--

SELECT pg_catalog.setval('public.otp_verification_id_seq', 1, true);


--
-- TOC entry 4928 (class 0 OID 0)
-- Dependencies: 217
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: expense_user
--

SELECT pg_catalog.setval('public.users_id_seq', 1, true);


--
-- TOC entry 4765 (class 2606 OID 16601)
-- Name: expenses expenses_pkey; Type: CONSTRAINT; Schema: public; Owner: expense_user
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT expenses_pkey PRIMARY KEY (id);


--
-- TOC entry 4763 (class 2606 OID 16591)
-- Name: otp_verification otp_verification_pkey; Type: CONSTRAINT; Schema: public; Owner: expense_user
--

ALTER TABLE ONLY public.otp_verification
    ADD CONSTRAINT otp_verification_pkey PRIMARY KEY (id);


--
-- TOC entry 4759 (class 2606 OID 16583)
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: expense_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- TOC entry 4761 (class 2606 OID 16581)
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: expense_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- TOC entry 4766 (class 2606 OID 16602)
-- Name: expenses expenses_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: expense_user
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT expenses_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


-- Completed on 2025-08-20 22:23:49

--
-- PostgreSQL database dump complete
--


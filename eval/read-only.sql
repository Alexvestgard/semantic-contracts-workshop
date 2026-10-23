-- Give the eval access to the museum tables already loaded by workshop startup.
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'eval_reader') THEN
        CREATE ROLE eval_reader LOGIN PASSWORD 'eval_reader'
            NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
    END IF;
END
$$;
ALTER ROLE eval_reader SET default_transaction_read_only = on;
ALTER ROLE eval_reader SET statement_timeout = '2s';
GRANT CONNECT ON DATABASE postgres TO eval_reader;
GRANT USAGE ON SCHEMA public TO eval_reader;
GRANT SELECT ON object, object_history, object_physical_properties,
    object_gallery_info, object_tags, object_images, object_copyright,
    object_api_metadata TO eval_reader;

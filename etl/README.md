# ETL

The ETL layer is structured around four phases:

1. Extract source files or API payloads.
2. Normalize raw records into a common procurement transparency schema.
3. Enrich records with entity resolution and indicator inputs.
4. Publish batches into PostgreSQL/PostGIS.

The current skeleton includes one California procurement connector and shared interfaces so additional sources can be added without changing the API layer.

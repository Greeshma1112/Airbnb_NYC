
-- Create transformed geometries and index them:

ALTER TABLE nyc_neighborhoods ADD COLUMN geom_4326 geometry(MultiPolygon, 4326);
UPDATE nyc_neighborhoods SET geom_4326 = ST_Transform(geom, 4326);
CREATE INDEX ON nyc_neighborhoods USING GIST(geom_4326);

ALTER TABLE nyc_homicides ADD COLUMN geom_4326 geometry(Point, 4326);
UPDATE nyc_homicides SET geom_4326 = ST_Transform(geom, 4326);
CREATE INDEX ON nyc_homicides USING GIST(geom_4326);


SELECT 
    l.id,
    l.host_name,
    l.price,
    n.name AS neighborhood,
    COUNT(h.*) AS homicide_count
FROM nyc_listings_bnb l
JOIN nyc_neighborhoods n 
  ON ST_Contains(n.geom_4326, l.listing_geom)
LEFT JOIN nyc_homicides h 
  ON ST_Contains(n.geom_4326, h.geom_4326)
GROUP BY l.id, l.host_name, l.price, n.name
ORDER BY homicide_count DESC;

# create a new table
CREATE MATERIALIZED VIEW safe_airbnb_listings AS
SELECT 
    l.id,l.name,
    l.host_name,
    l.price::numeric,
    l.room_type,
    n.name AS neighborhood,
    ST_X(l.listing_geom) AS lon,
    ST_Y(l.listing_geom) AS lat,
    COUNT(h.*) AS homicide_count
FROM nyc_listings_bnb l
JOIN nyc_neighborhoods n ON ST_Contains(n.geom_4326, l.listing_geom)
LEFT JOIN nyc_homicides h ON ST_Contains(n.geom_4326, h.geom_4326)
GROUP BY l.id,l.name, l.host_name, l.price, l.room_type, n.name, l.listing_geom;

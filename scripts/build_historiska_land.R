# Smålands små land och Upplands folkland för kartans gränslager (web/src/lib/historiska_land.json →
# web/public/geo/land.geojson).
#
#     .venv/bin/python scripts/fetch_harader.py && .venv/bin/python scripts/assign_historiska_land.py
#     Rscript --vanilla scripts/build_historiska_land.R
#
# Gränserna är ungefärliga: varje socken (Wikidata, data/geo/socknar_land.csv) får området närmast sin punkt
# (Voronoi), socknarnas områden slås ihop land för land och klipps mot Sveriges gräns (OpenStreetMap, län) och Natural
# Earths land. Sockenpunkterna är oftast kyrkans läge; socknarna är 1900-talets.
suppressPackageStartupMessages({ library(sf); library(jsonlite) })

root <- normalizePath(file.path(dirname(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE))), ".."))
defs <- fromJSON(file.path(root, "web", "src", "lib", "historiska_land.json"), simplifyVector = FALSE)
out <- file.path(root, "web", "public", "geo", "land.geojson")
crs <- 3006
sf_use_s2(FALSE)

s <- read.csv(file.path(root, "data", "geo", "socknar_land.csv"), stringsAsFactors = FALSE, na.strings = "")
pts <- st_transform(st_as_sf(s, coords = c("lon", "lat"), crs = 4326), crs)
pts <- pts[!duplicated(st_coordinates(pts)), ]

admin <- st_make_valid(st_transform(read_sf(file.path(root, "data", "cache", "osm", "admin.geojson")), crs))
sverige <- st_union(st_make_valid(st_geometry(admin[admin$admin_level == "4", ])))
land <- st_make_valid(st_transform(read_sf(file.path(root, "data", "cache", "r", "naturalearth", "land", "ne_10m_land.shp")), 4326))
land <- st_transform(suppressWarnings(st_crop(land, c(xmin = 10, ymin = 55, xmax = 25, ymax = 69.5))), crs)
mask <- st_intersection(sverige, st_union(st_geometry(land)))

env <- st_as_sfc(st_bbox(st_buffer(st_union(pts), 50000)))
cells <- st_collection_extract(st_voronoi(st_union(pts), env), "POLYGON")
cells <- st_sf(geometry = cells)
idx <- st_intersects(cells, pts)
cells$land <- vapply(idx, function(i) if (length(i)) pts$land[i[1]] else NA_character_, "")
cells <- cells[!is.na(cells$land), ]

features <- list()
for (r in defs$epoch$regions) {
  g <- st_union(st_geometry(cells[cells$land == r$id, ]))
  if (length(g) == 0 || st_is_empty(g)) stop("Inga socknar för ", r$id)
  g <- st_make_valid(st_intersection(g, mask))
  g <- st_simplify(st_buffer(st_buffer(g, 60), -60), preserveTopology = TRUE, dTolerance = 300)
  parts <- st_cast(st_make_valid(g), "POLYGON")
  parts <- parts[as.numeric(st_area(parts)) > 2e6]
  parts <- st_sfc(lapply(parts, function(p) st_polygon(list(p[[1]]))), crs = crs)
  g <- st_union(parts)
  at <- st_coordinates(st_transform(st_point_on_surface(parts[which.max(st_area(parts))]), 4326))
  features[[length(features) + 1]] <- st_sf(
    epoch = defs$epoch$key, id = r$id, realm = r$realm, certainty = r$certainty, label = r$label,
    label_lat = round(at[2], 3), label_lon = round(at[1], 3), geometry = st_transform(g, 4326))
}
fc <- do.call(rbind, features)
if (file.exists(out)) file.remove(out)
st_write(fc, out, driver = "GeoJSON", layer_options = c("COORDINATE_PRECISION=3", "RFC7946=YES"), quiet = TRUE)
message(sprintf("%d land, %.0f kB → %s", nrow(fc), file.size(out) / 1024, out))

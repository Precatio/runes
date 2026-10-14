# Rikenas ungefärliga gränser för kartans gränslager (web/src/lib/realms.json → web/public/geo/riken.geojson).
#
#     Rscript --vanilla scripts/build_realms.R
#
# Varje område i realms.json är en sammanslagning av byggstenar: dagens svenska landskap, Danmark, Bornholm, Slesvig
# och Norge. Landskapen kommer ur OpenStreetMap (© OpenStreetMap-bidragsgivare, ODbL): de flesta är inlagda som
# historiska gränser; Dalarna, Värmland, Skåne, Halland, Blekinge och Gotland tas ur länen (Värmland också ur Örebro
# län), Jämtland ur Jämtlands län utan Härjedalens kommun och Öland ur Borgholms och Mörbylånga kommuner, i varje fall
# utan de andra landskapen. Sveriges utdrag (data/cache/osm/sweden-latest.osm.pbf, se scripts/fetch_place_names.py)
# läses med GDAL (ogr2ogr). Danmark, Norge och Slesvig kommer ur Natural Earth (1:10 milj., allmän egendom), som hämtas
# till data/cache/r/naturalearth/; Norge slutar där Sverige börjar enligt OSM, så att de två källornas riksgränser inte
# överlappar. Slesvigs sydgräns är dragen ungefärligt vid Ejdern och Möre som en ruta i sydöstra Småland. Allt klipps
# mot Natural Earths land, så att länens gränser ute i havet inte syns.
suppressPackageStartupMessages({ library(sf); library(jsonlite) })

root <- normalizePath(file.path(dirname(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE))), ".."))
osm_dir <- file.path(root, "data", "cache", "osm")
ne_dir <- file.path(root, "data", "cache", "r", "naturalearth")
defs <- fromJSON(file.path(root, "web", "src", "lib", "realms.json"), simplifyVector = FALSE)
out <- file.path(root, "web", "public", "geo", "riken.geojson")
crs <- 3006  # SWEREF 99 TM: metres, so that the simplification tolerance is a distance

osm_layer <- function(name, where) {
  path <- file.path(osm_dir, paste0(name, ".geojson"))
  pbf <- file.path(osm_dir, "sweden-latest.osm.pbf")
  if (!file.exists(path)) {
    if (!file.exists(pbf)) stop("Sveriges OSM-utdrag saknas: kör scripts/fetch_place_names.py först.")
    message("Läser ", name, " ur OSM-utdraget (några minuter) …")
    status <- system2("ogr2ogr", c("-f", "GeoJSON", shQuote(path), shQuote(pbf), "multipolygons",
                                   "-where", shQuote(where), "-select", "name,admin_level"))
    if (status != 0) stop("ogr2ogr misslyckades")
  }
  st_make_valid(st_transform(read_sf(path), crs))
}

ne_layer <- function(name, group) {
  dir <- file.path(ne_dir, name)
  shp <- file.path(dir, paste0("ne_10m_", name, ".shp"))
  if (!file.exists(shp)) {
    dir.create(dir, recursive = TRUE, showWarnings = FALSE)
    zip <- tempfile(fileext = ".zip")
    download.file(sprintf("https://naciscdn.org/naturalearth/10m/%s/ne_10m_%s.zip", group, name), zip, quiet = TRUE)
    unzip(zip, exdir = dir)
  }
  # The Nordic countries only: the whole world does not project to SWEREF 99 TM
  x <- suppressWarnings(st_crop(st_make_valid(read_sf(shp)), c(xmin = 4, ymin = 53.5, xmax = 32, ymax = 72)))
  st_make_valid(st_transform(x[!st_is_empty(x), ], crs))
}

sf_use_s2(FALSE)  # planar operations, also in longitude and latitude
one <-function(x) st_union(st_make_valid(st_geometry(x)))
box <- function(lon1, lat1, lon2, lat2) {
  st_transform(st_sfc(st_polygon(list(rbind(c(lon1, lat1), c(lon2, lat1), c(lon2, lat2), c(lon1, lat2), c(lon1, lat1)))),
                      crs = 4326), crs)
}

landskap <- osm_layer("landskap", "boundary = 'historic'")
admin <- osm_layer("admin", "boundary = 'administrative' AND admin_level IN ('4','7')")
countries <- ne_layer("admin_0_countries", "cultural")
regions <- ne_layer("admin_1_states_provinces", "cultural")
land <- one(ne_layer("land", "physical"))

by_name <- function(layer, name) {
  x <- layer[!is.na(layer$name) & layer$name %in% name, ]
  if (!nrow(x)) stop("Hittar inte ", paste(name, collapse = ", "))
  one(x)
}
ls <- function(name) by_name(landskap, c(name, paste("Landskapet", name)))

blocks <- list(
  uppland = ls("Uppland"), sodermanland = ls("Södermanland"), vastmanland = ls("Västmanland"), narke = ls("Närke"),
  gastrikland = ls("Gästrikland"), halsingland = ls("Hälsingland"), medelpad = ls("Medelpad"),
  angermanland = ls("Ångermanland"), vastergotland = ls("Västergötland"), ostergotland = ls("Östergötland"),
  dalsland = ls("Dalsland"), smaland = ls("Småland"), bohuslan = ls("Bohuslän"),
  oland = by_name(admin, c("Borgholms kommun", "Mörbylånga kommun")),
  harjedalen = by_name(admin, "Härjedalens kommun"),
  gotland = by_name(admin, "Gotlands län")
)
# The provinces taken from counties, without the parts of the provinces already found
taken <- function() st_union(do.call(c, unname(blocks)))
# (Karlskoga and Degerfors belong to Värmland but to Örebro county)
for (x in list(list("dalarna", "Dalarnas län"), list("varmland", c("Värmlands län", "Örebro län")),
               list("skane", "Skåne län"), list("halland", "Hallands län"), list("blekinge", "Blekinge län"))) {
  blocks[[x[[1]]]] <- st_difference(by_name(admin, x[[2]]), taken())
}
blocks$smaland <- st_difference(blocks$smaland, blocks$oland)
blocks$harjedalen <- st_difference(blocks$harjedalen, blocks$halsingland)  # Ytterhogdal belongs to Hälsingland
blocks$jamtland <- st_difference(by_name(admin, "Jämtlands län"), taken())
# Möre: the coast of south-eastern Småland, from Blekinge to north of Kalmar (approximate)
blocks$more <- st_intersection(blocks$smaland, box(15.75, 56.15, 16.75, 56.92))

dk <- one(countries[countries$ADMIN == "Denmark", ])
blocks$danmark <- st_intersection(dk, box(7, 54.4, 13.2, 58))
blocks$bornholm <- st_intersection(dk, box(14.4, 54.9, 15.4, 55.4))
# Schleswig: Schleswig-Holstein north of the Eider and the Levensau, without Fehmarn
eider <- st_transform(st_sfc(st_polygon(list(rbind(
  c(7.8, 54.28), c(8.85, 54.28), c(9.09, 54.37), c(9.40, 54.30), c(9.66, 54.30), c(9.90, 54.33), c(10.08, 54.37),
  c(10.16, 54.37), c(10.22, 54.46), c(10.90, 54.46), c(10.90, 55.2), c(7.8, 55.2), c(7.8, 54.28)))), crs = 4326), crs)
blocks$slesvig <- st_difference(st_intersection(by_name(regions, "Schleswig-Holstein"), eider), dk)
# Norway without Finnmark (Sámi land) and without the islands far out; Østfold on its own (Viken east of the Oslofjord)
no <- regions[regions$admin == "Norway" & !regions$name %in% c("Finnmark", "Svalbard", "Bouvet Island", "Jan Mayen"), ]
# Natural Earth's border and OpenStreetMap's differ by a few hundred metres: Norway is widened by 3 km and ends where
# Sweden begins, so that they neither overlap nor leave a gap
sverige <- one(admin[admin$admin_level == "4", ])
norway <- st_intersection(st_difference(st_buffer(one(no), 3000), sverige), box(4, 57.5, 32, 70.5))
rest <- one(no[no$name != "Østfold", ])
blocks$ostfold <- st_difference(st_intersection(norway, st_buffer(by_name(no, "Østfold"), 3000)), rest)
blocks$norge <- st_difference(norway, blocks$ostfold)

frame <- st_intersection(land, box(4, 53.8, 32, 71.5))
blocks <- lapply(blocks, function(g) st_union(st_intersection(st_make_valid(g), frame)))

features <- list()
for (ep in defs$epochs) {
  for (r in ep$regions) {
    missing <- setdiff(unlist(r$blocks), names(blocks))
    if (length(missing)) stop("Okända byggstenar i ", r$id, ": ", paste(missing, collapse = ", "))
    g <- st_union(do.call(c, unname(blocks[unlist(r$blocks)])))
    # Close the slivers between neighbouring blocks, then simplify (300 m: invisible at the map's usual zoom)
    g <- st_simplify(st_buffer(st_buffer(g, 60), -60), preserveTopology = TRUE, dTolerance = 300)
    g <- st_make_valid(g)
    parts <- st_cast(g, "POLYGON")
    parts <- parts[as.numeric(st_area(parts)) > 2e6]  # skerries under 2 km² are left out
    # No region has an enclave: holes are lakes on a border or gaps between the sources
    parts <- st_sfc(lapply(parts, function(p) st_polygon(list(p[[1]]))), crs = crs)
    g <- st_union(parts)
    at <- st_coordinates(st_transform(st_point_on_surface(parts[which.max(st_area(parts))]), 4326))
    features[[length(features) + 1]] <- st_sf(
      epoch = ep$key, id = r$id, realm = r$realm, certainty = r$certainty, label = r$label,
      label_lat = round(at[2], 3), label_lon = round(at[1], 3), geometry = st_transform(g, 4326))
  }
}
fc <- do.call(rbind, features)
dir.create(dirname(out), recursive = TRUE, showWarnings = FALSE)
if (file.exists(out)) file.remove(out)
st_write(fc, out, driver = "GeoJSON", layer_options = c("COORDINATE_PRECISION=3", "RFC7946=YES"), quiet = TRUE)
message(sprintf("%d områden, %.0f kB → %s", nrow(fc), file.size(out) / 1024, out))

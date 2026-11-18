# Beskrivande (inget prov): landskap, diameter och avstånd till dagens hav (SGU issjohav_1, kod 1) för varje fristående
# hög; skriver /Volumes/2TB/Antigrvity/Runes/downloads/hogar/hogar_kust.csv (används av build_hogar.py).
#   Rscript utdata/hogar/kust.R
suppressPackageStartupMessages({library(sf); library(jsonlite)})
sf_use_s2(FALSE); SW <- "EPSG:3006"
H <- read.csv("/Volumes/2TB/Antigrvity/Runes/downloads/hogar/hogar.csv", fileEncoding = "UTF-8")
txt <- gsub("\\s+", " ", ifelse(is.na(H$beskrivning), "", H$beskrivning))
m <- regmatches(txt, regexec("(\\d+(?:[.,]\\d+)?)\\s*m\\s*(?:i\\s*)?diam", txt, ignore.case = TRUE, perl = TRUE))
H$d <- suppressWarnings(as.numeric(sub(",", ".", sapply(m, function(v) if (length(v) > 1) v[2] else NA))))
prov <- fromJSON("/Volumes/2TB/Antigrvity/Runes/geografi_kallor/isof/provinces.json")
par <- fromJSON("/Volumes/2TB/Antigrvity/Runes/geografi_kallor/isof/parishes.json"); par <- par[!is.na(par$latitude), ]
pxy <- st_coordinates(st_transform(st_as_sf(par, coords = c("longitude", "latitude"), crs = 4326), SW))
P <- st_transform(st_as_sf(H, coords = c("lon", "lat"), crs = 4326), SW); xy <- st_coordinates(P)
nn <- sapply(seq_len(nrow(xy)), function(i) which.min((pxy[,1]-xy[i,1])^2 + (pxy[,2]-xy[i,2])^2))
H$land <- prov$name[match(par$province_id[nn], prov$id)]
# distance to today's sea, tiled
H$sea <- NA_real_; tile <- paste(floor(xy[,1]/50000), floor(xy[,2]/50000))
for (tl in unique(tile)) {
  i <- which(tile == tl)
  bb <- c(xmin=min(xy[i,1])-30000, ymin=min(xy[i,2])-30000, xmax=max(xy[i,1])+30000, ymax=max(xy[i,2])+30000)
  w <- st_read("/Volumes/2TB/cache/strand/sgu/strandforskjutning_1_900.gpkg", "issjohav_1", wkt_filter=st_as_text(st_as_sfc(st_bbox(bb, crs=st_crs(SW)))), quiet=TRUE)
  w <- w[w$code == 1, ]; if (!nrow(w)) { H$sea[i] <- 30000; next }
  st_crs(w) <- SW
  dm <- st_distance(P[i, ], st_geometry(w)); H$sea[i] <- pmin(apply(matrix(as.numeric(dm), nrow=length(i)), 1, min), 30000)
}
H$big <- !is.na(H$d) & H$d >= 20
t <- aggregate(cbind(n=1, big=H$big, sized=!is.na(H$d)) ~ land, H, sum)
t$andel_stora <- round(100*t$big/t$sized); t <- t[order(-t$big), ]; print(head(t, 12), row.names=FALSE)
cat("andel av alla stora högar i Skåne+Halland:", round(100*sum(H$big & H$land %in% c("Skåne","Halland"))/sum(H$big)), "%\n")
for (L in c("Skåne", "Halland")) { s <- H[H$land == L, ]
  cat(L, ": stora inom 3 km från havet", round(100*mean(s$sea[s$big] <= 3000)), "% ; övriga", round(100*mean(s$sea[!s$big & !is.na(s$d)] <= 3000)), "% ; median km stora", round(median(s$sea[s$big])/1000,1), "övriga", round(median(s$sea[!s$big & !is.na(s$d)])/1000,1), "\n") }
sh <- H[H$land %in% c("Skåne","Halland"), ]
cat("Skåne+Halland stora: inom 3 km", round(100*mean(sh$sea[sh$big] <= 3000)), "% n", sum(sh$big), "; inom 5 km", round(100*mean(sh$sea[sh$big] <= 5000)), "%\n")
cat("median diameter Skåne", median(H$d[H$land=="Skåne"], na.rm=TRUE), "Uppland", median(H$d[H$land=="Uppland"], na.rm=TRUE), "\n")
write.csv(H[, c("raa_nummer","land","d","sea","big")], "/Volumes/2TB/Antigrvity/Runes/downloads/hogar/hogar_kust.csv", row.names=FALSE)

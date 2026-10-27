# Installerar R-paketen som statistikdelen använder: Rscript r/install.R
# sf kräver GDAL, GEOS, PROJ och udunits (macOS: brew install gdal geos proj udunits).
pk <- c("jsonlite", "dplyr", "tidyr", "stringr", "ggplot2", "ragg", "sf", "leaflet", "htmlwidgets",
        "tidytext", "cluster", "FactoMineR", "factoextra", "tidymodels", "ranger",
        "ca", "stringdist", "igraph", "tidygraph", "ggraph", "terra", "gdistance", "raster", "png", "mgcv",
        "spdep", "smerc",
        # 2026-10-27: model checks and plain-words effects (DHARMa, with mgcViz for mgcv models; marginaleffects), shape analysis of runes and groove
        # profiles (geomorph: landmarks and curves; Momocs is archived on CRAN and not available for R 4.6), stylometry
        # (stylo), point patterns and spatial models (spatstat, spaMM, glmmTMB)
        "marginaleffects", "DHARMa", "mgcViz", "geomorph", "stylo", "spatstat", "spaMM", "glmmTMB")
miss <- pk[!vapply(pk, requireNamespace, logical(1), quietly = TRUE)]
if (length(miss)) {
  message("Installerar: ", paste(miss, collapse = ", "))
  install.packages(miss, repos = "https://cloud.r-project.org", Ncpus = 2)  # two at a time: compiling glmmTMB and friends takes a lot of memory (16 GB machine)
}
still <- pk[!vapply(pk, requireNamespace, logical(1), quietly = TRUE)]
if (length(still)) stop("Kunde inte installera: ", paste(still, collapse = ", "))
message("Alla paket finns: ", paste(pk, collapse = ", "))

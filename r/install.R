# Installerar R-paketen som statistikdelen använder: Rscript r/install.R
# sf kräver GDAL, GEOS, PROJ och udunits (macOS: brew install gdal geos proj udunits).
pk <- c("jsonlite", "dplyr", "tidyr", "stringr", "ggplot2", "ragg", "sf", "leaflet", "htmlwidgets",
        "tidytext", "cluster", "FactoMineR", "factoextra", "tidymodels", "ranger",
        "ca", "stringdist", "igraph", "tidygraph", "ggraph", "terra", "gdistance", "raster", "png")
miss <- pk[!vapply(pk, requireNamespace, logical(1), quietly = TRUE)]
if (length(miss)) {
  message("Installerar: ", paste(miss, collapse = ", "))
  install.packages(miss, repos = "https://cloud.r-project.org", Ncpus = max(1, parallel::detectCores() - 1))
}
still <- pk[!vapply(pk, requireNamespace, logical(1), quietly = TRUE)]
if (length(still)) stop("Kunde inte installera: ", paste(still, collapse = ", "))
message("Alla paket finns: ", paste(pk, collapse = ", "))

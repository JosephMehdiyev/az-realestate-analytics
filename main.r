library(tidyverse)
library(DBI)
library(RPostgres)
library(scales)
library(knitr)
library(DiagrammeR)
library(corrr)
library(ggcorrplot)

con <- dbConnect(RPostgres:Postgres(), "bina.az")
con <- dbConnect(
  RPostgres::Postgres(),
  dbname   = "bina-az",
  host     = "localhost",
  port     = 5432,
  user     = "main",
  password = ""
)

# DANGER! This loads entire table into the memory!
estates <- dbReadTable(con, "estates")

# Distribution of renting prices
target_buildings <- c("Yeni tikili", "Həyət evi/Bağ evi", "Köhnə tikili")

estates_rent <- estates %>% 
  filter(
    selling_type == "Kirayə",
    rent_type == "/ay",
    building_type %in% target_buildings,
    price <= 50000
  ) 

# total 4495 rows of renting listings
nrow(estates_rent)


estates_rent %>%
  ggplot(aes(x = price)) +
  geom_density() +
  scale_x_log10() +
  theme_minimal()

estates_rent %>%
  mutate(room_group = if_else(total_room >= 5, "5+", as.character(total_room))) %>%
  ggplot(aes(x = azn_area, color = room_group, fill = room_group)) +
  geom_density(alpha = 0.1) + # alpha adds a light fill under the lines
  scale_x_log10() +
  labs(
    title = "Density of price by number of rooms",
    x = "AZN price per 1 meter square area",
    color = "Rooms",
    fill = "Rooms"
  ) +
  theme_minimal()

# QQplot of log of price
estates_rent %>%
  ggplot(aes(sample = log(price)))+
  stat_qq()+
  stat_qq_line(color = "blue") +
  theme_minimal() 

tidy_cors <- estates_rent %>%
  select(where(is.numeric)) %>%  # Safety first: only numeric columns
  correlate() %>%                # Creates the correlation tibble
  shave()                        # Removes the redundant upper triangle

print(tidy_cors)

cor(log(estates_rent$price), estates_rent$total_room, method = "pearson", use = "complete.obs")

summary(estates_rent)


summary(estates)






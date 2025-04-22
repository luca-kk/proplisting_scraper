# Domain.com.au Scraper

A command-line Python tool for parsing multi-page **Domain.com.au** listing information to CSV format.

---

## Features

- Scrapes data from **Domain.com.au** using `requests` and `BeautifulSoup`
- Parses:
    - Property type
    - Size
    - Price
    - Beds, baths, parking
    - Sale method
    - Sold dates
    - Listing links
- Handles pagination with configurable random delays (anti-bot)
- Optional rent yield estimation based on matching property types (beta feature)
- Auto-generates rental statistics by property configuration

---

## Files Included

*Script Files
- `main.py` – Main script
- `suburb_data.csv` - Contains Suburb, Zip and State for all Australian suburbs

*Project Files
- `README.md` – This file
- `pyproject.toml` – Poetry project configuration
- `poetry.lock` – Exact dependency versions
- `.gitignore` - Git ignore file

---

## Requirements

- Python 3.10+
- [Poetry](https://python-poetry.org/docs/#installation)

---

## Quick Start Guide

### 1. Clone or Download the Repository

*Option A: Using Git

```bash
git clone https://github.com/your-username/realestate_scraper.git
cd realestate_scraper
```

*Option B: Manual Download

- Download the Zip from GitHub repo
- Extract it
- Open a terminal inside the extracted folder

### 2. Install Dependencies with Poetry and Run

Located inside the downloaded repository, run:

```bash
poetry install
poetry run python realestate_scraper.py
```

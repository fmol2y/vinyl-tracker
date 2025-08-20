import logging
from sites import mascom

def main():
    logging.basicConfig(level=logging.INFO)
    logging.info("Starting scraper...")
    records = mascom.scrape()
    logging.info(f"Scraped {len(records)} records.")

    for record in records:
        logging.info(f"Record: {record}")

if __name__ == "__main__":
  main()

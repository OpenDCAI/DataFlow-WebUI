import logging, sys

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

if __name__ == "__main__":
    setup_logging()
    logger = logging.getLogger("example_logger")
    logger.info("Logging is set up and ready to go!")
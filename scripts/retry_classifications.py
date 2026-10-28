#!/usr/bin/env python3
"""Retry image classifications that failed during an earlier crawl."""

from crawl import retry_pending_classifications


if __name__ == "__main__":
    retry_pending_classifications()

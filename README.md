# Assignment 1 – Market Data Toolkit
Este proyecto extrae, estandariza y analiza datos financieros de series temporales.
A continuacion se describen las funciones de cada documento .py

## Extractor (extractor.py)
Connects to APIs (like yfinance) and downloads data.
Framework extensible de extractores + implementación para Yahoo Finance (yfinance).

Características:
- Registry/adapters: añade nuevos extractores con @register_extractor("nombre").
- GenericCallableExtractor para envolver cualquier función HTTP/SDK.
- download_price_series admite data_type: 'prices' (por defecto), 'dividends',
  'splits', 'info', 'financials', 'balance_sheet', 'cashflow', 'earnings',
  'sustainability', 'recommendations', 'holders', etc.
- Estandariza DataFrames de precios a columnas: ['open','high','low','close','adj_close','volume'] y guarda metadatos en df.attrs.
- Soporta descarga paralela.

## Data Models	(dataclasses.py)	
Defines standard objects for Prices, Assets, and Portfolio.

## Portfolio Logic	(portfolio.py)
Combines assets into a portfolio; runs statistics and Monte Carlo.

## Reports	(reports.py)	
Generates Markdown reports and visual plots.

## Main App	(main.ipynb)	
The central notebook where you run everything

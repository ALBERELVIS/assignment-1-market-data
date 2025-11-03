extractor.py
-------------
Framework extensible de extractores + implementación para Yahoo Finance (yfinance).

Características:
- Registry/adapters: añade nuevos extractores con @register_extractor("nombre").
- GenericCallableExtractor para envolver cualquier función HTTP/SDK.
- download_price_series admite data_type: 'prices' (por defecto), 'dividends',
  'splits', 'info', 'financials', 'balance_sheet', 'cashflow', 'earnings',
  'sustainability', 'recommendations', 'holders', etc.
- Estandariza DataFrames de precios a columnas: ['open','high','low','close','adj_close','volume'] y guarda metadatos en df.attrs.
- Soporta descarga paralela.

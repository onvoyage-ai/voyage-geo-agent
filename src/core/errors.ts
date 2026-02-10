export class GeoError extends Error {
  public readonly code: string;

  constructor(message: string, code: string) {
    super(message);
    this.name = 'GeoError';
    this.code = code;
  }
}

export class GeoProviderError extends GeoError {
  public readonly provider: string;
  public readonly statusCode?: number;

  constructor(message: string, provider: string, statusCode?: number) {
    super(message, 'PROVIDER_ERROR');
    this.name = 'GeoProviderError';
    this.provider = provider;
    this.statusCode = statusCode;
  }
}

export class GeoPipelineError extends GeoError {
  public readonly stage: string;

  constructor(message: string, stage: string) {
    super(message, 'PIPELINE_ERROR');
    this.name = 'GeoPipelineError';
    this.stage = stage;
  }
}

export class GeoRateLimitError extends GeoProviderError {
  public readonly retryAfterMs?: number;

  constructor(message: string, provider: string, retryAfterMs?: number) {
    super(message, provider, 429);
    this.name = 'GeoRateLimitError';
    (this as { code: string }).code = 'RATE_LIMIT_ERROR';
    this.retryAfterMs = retryAfterMs;
  }
}

export class GeoTimeoutError extends GeoProviderError {
  public readonly timeoutMs: number;

  constructor(message: string, provider: string, timeoutMs: number) {
    super(message, provider);
    this.name = 'GeoTimeoutError';
    (this as { code: string }).code = 'TIMEOUT_ERROR';
    this.timeoutMs = timeoutMs;
  }
}

export class GeoConfigError extends GeoError {
  constructor(message: string) {
    super(message, 'CONFIG_ERROR');
    this.name = 'GeoConfigError';
  }
}

export class GeoStorageError extends GeoError {
  constructor(message: string) {
    super(message, 'STORAGE_ERROR');
    this.name = 'GeoStorageError';
  }
}

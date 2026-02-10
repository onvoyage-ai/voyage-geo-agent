import { readFileSync, existsSync } from 'node:fs';
import { resolve } from 'node:path';
import { voyageGeoConfigSchema, type VoyageGeoConfig } from './schema.js';
import { DEFAULT_CONFIG } from './defaults.js';

interface LoadConfigOptions {
  configFile?: string;
  cliOverrides?: Partial<VoyageGeoConfig>;
}

export function loadConfig(options: LoadConfigOptions = {}): VoyageGeoConfig {
  const layers: Partial<VoyageGeoConfig>[] = [DEFAULT_CONFIG];

  // Layer 2: Config file
  const fileConfig = loadFileConfig(options.configFile);
  if (fileConfig) {
    layers.push(fileConfig);
  }

  // Layer 3: Environment variables
  const envConfig = loadEnvConfig();
  layers.push(envConfig);

  // Layer 4: CLI overrides
  if (options.cliOverrides) {
    layers.push(options.cliOverrides);
  }

  const merged = deepMerge(...layers);
  return voyageGeoConfigSchema.parse(merged);
}

function loadFileConfig(configFile?: string): Partial<VoyageGeoConfig> | null {
  const paths = configFile
    ? [resolve(configFile)]
    : [
        resolve('voyage-geo.config.json'),
        resolve('.voyage-geo.json'),
      ];

  for (const filePath of paths) {
    if (existsSync(filePath)) {
      const content = readFileSync(filePath, 'utf-8');
      return JSON.parse(content) as Partial<VoyageGeoConfig>;
    }
  }
  return null;
}

function loadEnvConfig(): Partial<VoyageGeoConfig> {
  const config: Partial<VoyageGeoConfig> = {};
  const providers: VoyageGeoConfig['providers'] = {};

  if (process.env.OPENAI_API_KEY) {
    providers.openai = {
      ...DEFAULT_CONFIG.providers.openai,
      apiKey: process.env.OPENAI_API_KEY,
    };
  }

  if (process.env.ANTHROPIC_API_KEY) {
    providers.anthropic = {
      ...DEFAULT_CONFIG.providers.anthropic,
      apiKey: process.env.ANTHROPIC_API_KEY,
    };
  }

  if (process.env.GOOGLE_API_KEY) {
    providers.google = {
      ...DEFAULT_CONFIG.providers.google,
      apiKey: process.env.GOOGLE_API_KEY,
    };
  }

  if (process.env.PERPLEXITY_API_KEY) {
    providers.perplexity = {
      ...DEFAULT_CONFIG.providers.perplexity,
      apiKey: process.env.PERPLEXITY_API_KEY,
    };
  }

  if (Object.keys(providers).length > 0) {
    config.providers = providers;
  }

  if (process.env.LOG_LEVEL) {
    config.logLevel = process.env.LOG_LEVEL as VoyageGeoConfig['logLevel'];
  }

  if (process.env.VOYAGE_GEO_OUTPUT_DIR) {
    config.outputDir = process.env.VOYAGE_GEO_OUTPUT_DIR;
  }

  if (process.env.VOYAGE_GEO_CONCURRENCY) {
    config.execution = {
      ...DEFAULT_CONFIG.execution,
      concurrency: parseInt(process.env.VOYAGE_GEO_CONCURRENCY, 10),
    };
  }

  return config;
}

function deepMerge(...objects: Partial<VoyageGeoConfig>[]): Partial<VoyageGeoConfig> {
  const result: Record<string, unknown> = {};

  for (const obj of objects) {
    for (const [key, value] of Object.entries(obj)) {
      if (value === undefined) continue;

      if (isPlainObject(value) && isPlainObject(result[key])) {
        result[key] = deepMerge(
          result[key] as Partial<VoyageGeoConfig>,
          value as Partial<VoyageGeoConfig>,
        );
      } else {
        result[key] = value;
      }
    }
  }

  return result as Partial<VoyageGeoConfig>;
}

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

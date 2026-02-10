import type { ProviderConfig } from '../config/schema.js';
import type { AIProvider } from './types.js';
import { OpenAIProvider } from './openai/provider.js';
import { AnthropicProvider } from './anthropic/provider.js';
import { GoogleProvider } from './google/provider.js';
import { PerplexityProvider } from './perplexity/provider.js';
import { GeoConfigError } from '../core/errors.js';

type ProviderFactory = (config: ProviderConfig) => AIProvider;

const BUILT_IN_FACTORIES: Record<string, ProviderFactory> = {
  openai: (config) => new OpenAIProvider(config),
  anthropic: (config) => new AnthropicProvider(config),
  google: (config) => new GoogleProvider(config),
  perplexity: (config) => new PerplexityProvider(config),
};

export class ProviderRegistry {
  private providers = new Map<string, AIProvider>();
  private factories = new Map<string, ProviderFactory>(Object.entries(BUILT_IN_FACTORIES));

  register(name: string, config: ProviderConfig): void {
    const factory = this.factories.get(name);
    if (!factory) {
      throw new GeoConfigError(`Unknown provider: ${name}. Available: ${this.availableProviders().join(', ')}`);
    }
    this.providers.set(name, factory(config));
  }

  registerFactory(name: string, factory: ProviderFactory): void {
    this.factories.set(name, factory);
  }

  get(name: string): AIProvider {
    const provider = this.providers.get(name);
    if (!provider) {
      throw new GeoConfigError(`Provider not registered: ${name}`);
    }
    return provider;
  }

  getAll(): AIProvider[] {
    return Array.from(this.providers.values());
  }

  getEnabled(): AIProvider[] {
    return this.getAll().filter((p) => p.isConfigured());
  }

  has(name: string): boolean {
    return this.providers.has(name);
  }

  names(): string[] {
    return Array.from(this.providers.keys());
  }

  availableProviders(): string[] {
    return Array.from(this.factories.keys());
  }
}

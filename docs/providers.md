# Adding a New Provider

Voyage GEO uses a plugin system for AI providers. Follow these steps to add a new one.

## 1. Create the Provider File

Create `src/providers/<name>/provider.ts`:

```typescript
import type { ProviderConfig } from '../../config/schema.js';
import { BaseProvider } from '../base.js';
import type { ProviderResponse } from '../types.js';

export class MyProvider extends BaseProvider {
  readonly name = 'myprovider';
  readonly displayName = 'My Provider';

  constructor(config: ProviderConfig) {
    super(config);
    // Initialize your SDK client here
  }

  async query(prompt: string): Promise<ProviderResponse> {
    const start = Date.now();
    const model = this.config.model || 'default-model';

    try {
      // Call your AI API here
      const response = await this.withTimeout(
        yourClient.chat(prompt),
        30000,
      );

      return {
        text: response.text,
        model,
        provider: this.name,
        latencyMs: Date.now() - start,
        tokenUsage: {
          promptTokens: response.usage.input,
          completionTokens: response.usage.output,
          totalTokens: response.usage.total,
        },
      };
    } catch (err) {
      throw this.wrapError(err);
    }
  }
}
```

## 2. Register the Provider

In `src/providers/registry.ts`, add your provider to `BUILT_IN_FACTORIES`:

```typescript
import { MyProvider } from './myprovider/provider.js';

const BUILT_IN_FACTORIES: Record<string, ProviderFactory> = {
  // ... existing providers
  myprovider: (config) => new MyProvider(config),
};
```

## 3. Add Default Config

In `src/config/defaults.ts`, add default configuration:

```typescript
myprovider: {
  name: 'myprovider',
  enabled: true,
  model: 'default-model',
  maxTokens: 2048,
  temperature: 0.7,
  rateLimit: { requestsPerMinute: 60, tokensPerMinute: 100000 },
},
```

## 4. Add Environment Variable

In `.env.example`:

```
MYPROVIDER_API_KEY=...
```

In `src/config/loader.ts`, add env variable loading:

```typescript
if (process.env.MYPROVIDER_API_KEY) {
  providers.myprovider = {
    ...DEFAULT_CONFIG.providers.myprovider,
    apiKey: process.env.MYPROVIDER_API_KEY,
  };
}
```

## Key Interfaces

- `AIProvider` — the interface your provider must implement
- `BaseProvider` — abstract class with `withTimeout()` and `wrapError()` helpers
- `ProviderResponse` — what `query()` must return
- `ProviderHealthCheck` — what `healthCheck()` returns (inherited from BaseProvider)

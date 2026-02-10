import type { Command } from 'commander';
import { loadConfig } from '../config/loader.js';
import { ProviderRegistry } from '../providers/registry.js';
import { setLogLevel } from '../utils/logger.js';
import { errorMessage, createSpinner } from '../utils/progress.js';
import chalk from 'chalk';

export function registerProvidersCommand(program: Command): void {
  program
    .command('providers')
    .description('List and test AI providers')
    .option('--test', 'Health check all configured providers')
    .option('--list', 'List available providers')
    .option('-c, --config <path>', 'Config file path')
    .option('--log-level <level>', 'Log level', 'info')
    .action(async (opts) => {
      try {
        setLogLevel(opts.logLevel);
        const config = loadConfig({ configFile: opts.config });

        if (opts.test) {
          await testProviders(config);
        } else {
          listProviders(config);
        }
      } catch (err) {
        errorMessage(`Provider error: ${err instanceof Error ? err.message : String(err)}`);
        process.exit(1);
      }
    });
}

function listProviders(config: ReturnType<typeof loadConfig>): void {
  const registry = new ProviderRegistry();
  const available = registry.availableProviders();

  process.stdout.write(chalk.bold('\nAvailable Providers:\n\n'));

  for (const name of available) {
    const providerConfig = config.providers[name];
    const hasKey = !!providerConfig?.apiKey;
    const enabled = providerConfig?.enabled ?? false;

    const status = hasKey
      ? chalk.green('configured')
      : chalk.yellow('no API key');

    const enabledLabel = enabled
      ? chalk.green('enabled')
      : chalk.gray('disabled');

    const model = providerConfig?.model || 'default';

    process.stdout.write(`  ${chalk.bold(name.padEnd(15))} ${status.padEnd(30)} ${enabledLabel.padEnd(20)} model: ${model}\n`);
  }

  process.stdout.write('\n');
}

async function testProviders(config: ReturnType<typeof loadConfig>): Promise<void> {
  const registry = new ProviderRegistry();

  for (const [name, providerConfig] of Object.entries(config.providers)) {
    if (providerConfig.enabled && providerConfig.apiKey) {
      registry.register(name, providerConfig);
    }
  }

  const providers = registry.getEnabled();

  if (providers.length === 0) {
    errorMessage('No providers configured. Set API keys in .env or run `voyage-geo config --init`');
    return;
  }

  process.stdout.write(chalk.bold('\nTesting providers...\n\n'));

  for (const provider of providers) {
    const spinner = createSpinner(`Testing ${provider.displayName}...`);
    spinner.start();

    const result = await provider.healthCheck();

    if (result.healthy) {
      spinner.succeed(`${provider.displayName}: ${chalk.green('healthy')} (${result.latencyMs}ms, model: ${result.model})`);
    } else {
      spinner.fail(`${provider.displayName}: ${chalk.red('failed')} — ${result.error}`);
    }
  }

  process.stdout.write('\n');
}

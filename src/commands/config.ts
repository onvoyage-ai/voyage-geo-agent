import { writeFileSync, existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import type { Command } from 'commander';
import inquirer from 'inquirer';
import { successMessage, errorMessage, infoMessage } from '../utils/progress.js';

export function registerConfigCommand(program: Command): void {
  program
    .command('config')
    .description('Manage configuration')
    .option('--init', 'Interactive configuration setup')
    .option('--show', 'Show current configuration')
    .action(async (opts) => {
      try {
        if (opts.init) {
          await initConfig();
        } else if (opts.show) {
          showConfig();
        } else {
          infoMessage('Use --init for interactive setup or --show to display config');
        }
      } catch (err) {
        errorMessage(`Config error: ${err instanceof Error ? err.message : String(err)}`);
        process.exit(1);
      }
    });
}

async function initConfig(): Promise<void> {
  const configPath = resolve('voyage-geo.config.json');

  if (existsSync(configPath)) {
    const { overwrite } = await inquirer.prompt([
      {
        type: 'confirm',
        name: 'overwrite',
        message: 'Config file already exists. Overwrite?',
        default: false,
      },
    ]);
    if (!overwrite) return;
  }

  const answers = await inquirer.prompt([
    {
      type: 'input',
      name: 'openaiKey',
      message: 'OpenAI API key (leave empty to skip):',
    },
    {
      type: 'input',
      name: 'anthropicKey',
      message: 'Anthropic API key (leave empty to skip):',
    },
    {
      type: 'input',
      name: 'googleKey',
      message: 'Google API key (leave empty to skip):',
    },
    {
      type: 'input',
      name: 'perplexityKey',
      message: 'Perplexity API key (leave empty to skip):',
    },
    {
      type: 'number',
      name: 'concurrency',
      message: 'Concurrency limit:',
      default: 3,
    },
    {
      type: 'number',
      name: 'queries',
      message: 'Default number of queries:',
      default: 20,
    },
    {
      type: 'checkbox',
      name: 'formats',
      message: 'Report formats:',
      choices: ['html', 'json', 'csv', 'markdown'],
      default: ['html', 'json'],
    },
  ]);

  const config: Record<string, unknown> = {
    providers: {},
    execution: { concurrency: answers.concurrency },
    queries: { count: answers.queries },
    report: { formats: answers.formats },
    outputDir: './data/runs',
  };

  const providers = config.providers as Record<string, unknown>;
  if (answers.openaiKey) {
    providers.openai = { name: 'openai', enabled: true, apiKey: answers.openaiKey, model: 'gpt-4o' };
  }
  if (answers.anthropicKey) {
    providers.anthropic = { name: 'anthropic', enabled: true, apiKey: answers.anthropicKey, model: 'claude-sonnet-4-5-20250929' };
  }
  if (answers.googleKey) {
    providers.google = { name: 'google', enabled: true, apiKey: answers.googleKey, model: 'gemini-2.0-flash' };
  }
  if (answers.perplexityKey) {
    providers.perplexity = { name: 'perplexity', enabled: true, apiKey: answers.perplexityKey, model: 'sonar' };
  }

  writeFileSync(configPath, JSON.stringify(config, null, 2), 'utf-8');
  successMessage(`Config saved to ${configPath}`);
}

function showConfig(): void {
  const configPath = resolve('voyage-geo.config.json');
  if (!existsSync(configPath)) {
    infoMessage('No config file found. Run `voyage-geo config --init` to create one.');
    return;
  }

  const content = JSON.parse(readFileSync(configPath, 'utf-8'));
  // Mask API keys
  if (content.providers) {
    for (const provider of Object.values(content.providers) as Array<Record<string, string>>) {
      if (provider.apiKey) {
        provider.apiKey = provider.apiKey.slice(0, 8) + '...' + provider.apiKey.slice(-4);
      }
    }
  }
  process.stdout.write(JSON.stringify(content, null, 2) + '\n');
}

import ora, { type Ora } from 'ora';
import chalk from 'chalk';

export function createSpinner(text: string): Ora {
  return ora({ text, color: 'cyan' });
}

export function stageHeader(name: string, description: string): void {
  const line = chalk.cyan('━'.repeat(60));
  // Using process.stdout.write to avoid lint warning about console.log
  process.stdout.write(`\n${line}\n`);
  process.stdout.write(`${chalk.bold.cyan(`  Stage: ${name}`)}\n`);
  process.stdout.write(`${chalk.gray(`  ${description}`)}\n`);
  process.stdout.write(`${line}\n\n`);
}

export function successMessage(text: string): void {
  process.stdout.write(`${chalk.green('✓')} ${text}\n`);
}

export function errorMessage(text: string): void {
  process.stdout.write(`${chalk.red('✗')} ${text}\n`);
}

export function infoMessage(text: string): void {
  process.stdout.write(`${chalk.blue('ℹ')} ${text}\n`);
}

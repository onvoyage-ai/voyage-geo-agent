import { Command } from 'commander';
import { registerRunCommand } from './commands/run.js';
import { registerResearchCommand } from './commands/research.js';
import { registerQueryCommand } from './commands/query.js';
import { registerExecuteCommand } from './commands/execute.js';
import { registerAnalyzeCommand } from './commands/analyze.js';
import { registerReportCommand } from './commands/report.js';
import { registerConfigCommand } from './commands/config.js';
import { registerProvidersCommand } from './commands/providers.js';

const program = new Command();

program
  .name('voyage-geo')
  .description('Open source GEO (Generative Engine Optimization) CLI tool')
  .version('0.1.0');

registerRunCommand(program);
registerResearchCommand(program);
registerQueryCommand(program);
registerExecuteCommand(program);
registerAnalyzeCommand(program);
registerReportCommand(program);
registerConfigCommand(program);
registerProvidersCommand(program);

program.parse();

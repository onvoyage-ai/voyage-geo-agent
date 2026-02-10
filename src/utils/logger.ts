import pino from 'pino';

let globalLevel: pino.Level = 'info';

export function setLogLevel(level: string): void {
  globalLevel = level as pino.Level;
}

export function createLogger(name: string): pino.Logger {
  return pino({
    name,
    level: globalLevel,
    transport: {
      target: 'pino-pretty',
      options: {
        colorize: true,
        ignore: 'pid,hostname',
        translateTime: 'SYS:HH:MM:ss',
      },
    },
  });
}

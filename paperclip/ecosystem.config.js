export default {
  apps: [
    {
      name: 'vanguard-paperclip',
      script: './src/index.js',
      interpreter: 'node',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        NODE_ENV: 'production',
        PAPERCLIP_PORT: 3100,
        FRIDAY_URL: 'http://localhost:3000',
        LOG_LEVEL: 'info',
      },
      env_development: {
        NODE_ENV: 'development',
        PAPERCLIP_PORT: 3100,
        FRIDAY_URL: 'http://localhost:3000',
        LOG_LEVEL: 'debug',
      },
    },
  ],
};

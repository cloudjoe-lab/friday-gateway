module.exports = {
  apps: [
    {
      name: 'vanguard-paperclip',
      script: './src/index.js',
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        NODE_ENV: 'production',
        VANGUARD_PORT: 3009,
        PAPERCLIP_PORT: 3100,
        FRIDAY_URL: 'http://localhost:3000',
        LOG_LEVEL: 'info',
      },
    },
  ],
};

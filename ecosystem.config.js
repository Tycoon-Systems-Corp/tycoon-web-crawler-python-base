module.exports = {
  apps: [{
    name: 'tycoon-crawler',
    script: 'run_scraper.sh', // A shell script to execute the necessary commands
    interpreter: '/bin/bash', // Specify the interpreter for the shell script
    env: {
      NODE_ENV: 'production'
    },
    watch: true, // Optional: Set to true if you want PM2 to watch for changes and automatically restart the app
    ignore_watch: ['node_modules', 'logs'] // Optional: Directories/files to ignore when watching for changes
  }],
  deploy: {
    production: {
      host: '3.22.158.110',
      repo: 'https://github.com/Tycoon-Systems-Corp/tycoon-web-crawler-python-base',
      path: '/home/ubuntu/tycoon-web-crawler-python-base',
      ref: 'origin/main'
    }
  }
};


module.exports = {
    apps: [
        {
            name: "flask-app",
            script: "start-flask.sh", // Command to run Flask
            exec_mode: "fork", // Fork mode is sufficient for Flask
            autorestart: true, // Restart if the app crashes
            watch: false, // Disable watching for Flask
        },
        {
            name: "rq-worker",
            script: "start-rq.sh",
            instances: "max", // Run 2 instances of RQ worker
            exec_mode: "fork",
            autorestart: true, // Restart if the worker crashes
            watch: false, // Disable watching for RQ worker
        }
    ]
};

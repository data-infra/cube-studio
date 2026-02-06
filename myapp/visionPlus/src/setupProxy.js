const { createProxyMiddleware } = require('http-proxy-middleware');

// https://create-react-app.dev/docs/proxying-api-requests-in-development/
module.exports = function (app) {
    app.use(
        ['**/api/**', '/myapp','/login', '/idex', '/users', '/roles','/static/assets','/static/appbuilder'],
        createProxyMiddleware({
            target: 'http://localhost',
            changeOrigin: true,
        })
    );
};

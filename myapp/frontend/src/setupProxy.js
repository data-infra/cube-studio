const { createProxyMiddleware } = require('http-proxy-middleware');

// https://create-react-app.dev/docs/proxying-api-requests-in-development/
module.exports = function (app) {
    // 重定向 /frontend 到 /frontend/
    app.use((req, res, next) => {
        if (req.path === '/frontend' && !req.path.endsWith('/')) {
            return res.redirect(301, '/frontend/');
        }
        next();
    });

    app.use(
        ['/workflow_modelview'],
        createProxyMiddleware({
            target: 'http://localhost',
            changeOrigin: true,
        })
    );

    app.use(
        ['**/api/**', '/myapp', '/login', '/idex', '/users', '/roles','/static/assets','/static/appbuilder', '/pipeline_modelview', '/project_modelview'],  //本地调试pipeline和首页的时候，不要添加/static/appbuilder代理
        createProxyMiddleware({
            target: 'http://localhost',
            changeOrigin: true,
        })
    );
};
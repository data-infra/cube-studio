/* eslint-disable @typescript-eslint/no-var-requires */
const MonacoWebpackPlugin = require('monaco-editor-webpack-plugin');
const BundleAnalyzerPlugin = require('webpack-bundle-analyzer').BundleAnalyzerPlugin;
const path = require('path');
const paths = require('react-scripts/config/paths');
const { override, fixBabelImports, addLessLoader } = require('customize-cra');
// 合并项目，修改打包输出的路径
paths.appBuild = path.join(path.dirname(paths.appBuild), '../static/appbuilder/visonPlus');

function webpack(config) {
  config.devtool = false;
  // alias
  config.resolve.alias = {
    ...config.resolve.alias,
    '@src': path.resolve(__dirname, 'src'),
  };

  // plugin
  // languages：MonacoWebpackPlugin 会按此列表只打包对应语言；
  // data_analysis 算子的 PythonField 需要 python 语法高亮，必须把 python 加进来
  config.plugins.push(
    new MonacoWebpackPlugin({
      languages: ['json', 'css', 'mysql', 'sql', 'python'],
    }),
  );

  // if (process.env.NODE_ENV !== 'production') {
  //   config.plugins.push(
  //     new BundleAnalyzerPlugin()
  //   )
  // }

  return config;
}
module.exports = {
  webpack: config => {
    config.devtool = false;
    // alias
    config.resolve.alias = {
      ...config.resolve.alias,
      '@src': path.resolve(__dirname, 'src'),
    };

    // plugin
    // 同上：把 python 加入打包语言，否则 PythonField 在生产环境无语法高亮
    config.plugins.push(
      new MonacoWebpackPlugin({
        languages: ['json', 'mysql', 'css', 'sql', 'python'],
      }),
    );

    // if (process.env.NODE_ENV !== 'production') {
    //   config.plugins.push(
    //     new BundleAnalyzerPlugin()
    //   )
    // }

    return config;
  },
};

// module.exports = override(
//   fixBabelImports('import', {
//     libraryName: 'antd',
//     libraryDirectory: 'es',
//     style: true,
//   }),
//   addLessLoader({
//     javascriptEnabled: true,
//     modifyVars: { '@primary-color': '#1DA57A' },
//   }),
// );

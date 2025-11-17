const path = require('path');
const fs = require('fs');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const CopyWebpackPlugin = require('copy-webpack-plugin');

const isDevelopment = process.env.NODE_ENV !== 'production';

// Use Office Add-in dev certs if available
const getHttpsOptions = () => {
  const certPath = path.join(process.env.HOME || process.env.USERPROFILE, '.office-addin-dev-certs');
  const certFile = path.join(certPath, 'localhost.crt');
  const keyFile = path.join(certPath, 'localhost.key');

  if (fs.existsSync(certFile) && fs.existsSync(keyFile)) {
    return {
      type: 'https',
      options: {
        cert: fs.readFileSync(certFile),
        key: fs.readFileSync(keyFile),
      },
    };
  }
  return { type: 'https' };
};

module.exports = {
  entry: {
    taskpane: './src/index.tsx',
  },
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: '[name].js',
    clean: true,
  },
  resolve: {
    extensions: ['.ts', '.tsx', '.js', '.jsx'],
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  module: {
    rules: [
      {
        test: /\.(ts|tsx)$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: [
              '@babel/preset-env',
              '@babel/preset-react',
              '@babel/preset-typescript',
            ],
          },
        },
      },
      {
        test: /\.css$/,
        use: ['style-loader', 'css-loader'],
      },
      {
        test: /\.(png|jpg|jpeg|gif|ico|svg)$/,
        type: 'asset/resource',
      },
    ],
  },
  plugins: [
    new HtmlWebpackPlugin({
      template: './public/taskpane.html',
      filename: 'taskpane.html',
      chunks: ['taskpane'],
    }),
    new CopyWebpackPlugin({
      patterns: [
        {
          from: 'public',
          to: '.',
          globOptions: {
            ignore: ['**/taskpane.html'],
          },
        },
      ],
    }),
  ],
  devServer: {
    static: {
      directory: path.join(__dirname, 'dist'),
    },
    headers: {
      'Access-Control-Allow-Origin': '*',
    },
    server: getHttpsOptions(),
    port: 3001,
    hot: true,
    allowedHosts: 'all',
  },
  devtool: isDevelopment ? 'eval-source-map' : 'source-map',
};
